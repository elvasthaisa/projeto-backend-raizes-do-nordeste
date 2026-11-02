from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.enums import CenarioMock, ResultadoPagamento, StatusPedido, TipoResponsavel
from core.erros import ErroApi
from gateway.gateway_mock import GatewayMock
from gateway.gateway_pagamento import GatewayPagamento, RespostaGateway
from models import Pagamento
from repositories import pedido_repository
from schemas.auth import UsuarioLogado
from services.pedido_service import (buscar_pedido, devolver_estoque_do_pedido, enviar_para_preparo, identificar_responsavel,
                                     mudar_status, validar_transicao_pedido)

# Novas chamadas ao gateway dentro da mesma tentativa, quando ele não responde
RETENTATIVAS_GATEWAY = 3

# Tentativas de pagamento por pedido
LIMITE_TENTATIVAS = 3

# Prazo para pagar depois de uma tentativa sem sucesso, contado da resposta do gateway
PRAZO_PAGAMENTO = timedelta(minutes=10)

# Status de onde o cliente pode tentar pagar de novo
STATUS_SEM_SUCESSO = (StatusPedido.PAGAMENTO_RECUSADO, StatusPedido.PAGAMENTO_EXPIRADO)


def pagamento_para_resposta(pagamento: Pagamento) -> dict:
    return {
        "id": pagamento.uuid,
        "valor": pagamento.valor,
        "resultado": pagamento.resultado,
        "motivoRecusa": pagamento.motivo_recusa,
        "dataHoraResposta": pagamento.data_hora_resposta,
    }


# Mesmas regras de acesso do GET /pedidos/{id}
def listar_pagamentos(db: Session, pedido_uuid: UUID, usuario: UsuarioLogado) -> list:
    pedido = buscar_pedido(db, pedido_uuid, usuario)
    return [pagamento_para_resposta(pagamento) for pagamento in pedido.pagamentos]


# Roda em segundo plano, depois da resposta da requisição, por isso abre a própria sessão do banco
def processar_pagamento(pedido_uuid: UUID, valor: Decimal, cenario: CenarioMock):
    gateway: GatewayPagamento = GatewayMock(cenario)
    resposta = None
    for _ in range(1 + RETENTATIVAS_GATEWAY):
        try:
            resposta = gateway.cobrar(valor)
            break
        except TimeoutError:
            continue

    with SessionLocal() as db:
        registrar_resposta(db, pedido_uuid, resposta)


# Sem resposta mesmo depois das retentativas, a tentativa expira
def registrar_resposta(db: Session, pedido_uuid: UUID, resposta: Optional[RespostaGateway]):
    pedido = pedido_repository.buscar_por_uuid(db, pedido_uuid, travar=True)
    pagamento = pedido.pagamentos[-1]
    if resposta is None:
        pagamento.registrar_resposta(ResultadoPagamento.EXPIRADO)
        novo_status = StatusPedido.PAGAMENTO_EXPIRADO
    elif resposta.aprovado:
        pagamento.registrar_resposta(ResultadoPagamento.APROVADO)
        novo_status = StatusPedido.EM_PREPARO
    else:
        pagamento.registrar_resposta(ResultadoPagamento.RECUSADO, resposta.motivo_recusa)
        novo_status = StatusPedido.PAGAMENTO_RECUSADO

    # Se o pedido foi cancelado enquanto o gateway respondia, a resposta fica registrada só no pagamento
    if pedido.status == StatusPedido.AGUARDANDO_PAGAMENTO:
        if novo_status == StatusPedido.EM_PREPARO:
            enviar_para_preparo(db, pedido)
        else:
            mudar_status(pedido, novo_status, TipoResponsavel.SISTEMA)
            # Na 3ª tentativa sem sucesso o pedido é cancelado na hora, sem esperar os 10 minutos
            if len(pedido.pagamentos) >= LIMITE_TENTATIVAS:
                devolver_estoque_do_pedido(db, pedido)
                mudar_status(pedido, StatusPedido.PEDIDO_CANCELADO, TipoResponsavel.SISTEMA,
                             motivo="Limite de 3 tentativas de pagamento sem sucesso.")
    db.commit()


def nova_tentativa(db: Session, pedido_uuid: UUID, usuario: UsuarioLogado) -> dict:
    pedido = buscar_pedido(db, pedido_uuid, usuario)

    # Só pedido recusado ou expirado pode tentar de novo, até 3 tentativas (UC3 FA3)
    validar_transicao_pedido(pedido.status, STATUS_SEM_SUCESSO, "pedir nova tentativa de pagamento")

    # Dois cliques ao mesmo tempo: o primeiro muda o status, o segundo não encontra mais o status lido e recebe 409
    if not pedido_repository.trocar_status_se_igual(db, pedido.id, pedido.status, StatusPedido.AGUARDANDO_PAGAMENTO):
        raise ErroApi(409, "TRANSICAO_INVALIDA", "O pedido mudou de status enquanto a tentativa era pedida. Consulte o pedido.")
    if len(pedido.pagamentos) >= LIMITE_TENTATIVAS:
        raise ErroApi(409, "LIMITE_TENTATIVAS", "O pedido já atingiu o limite de 3 tentativas de pagamento.")

    tipo_responsavel, responsavel = identificar_responsavel(db, usuario)
    mudar_status(pedido, StatusPedido.AGUARDANDO_PAGAMENTO, tipo_responsavel, responsavel)

    # A tentativa nasce PENDENTE; o resultado chega depois, pelo gateway
    pagamento = Pagamento(valor=pedido.calcular_total(), resultado=ResultadoPagamento.PENDENTE)
    pedido.pagamentos.append(pagamento)
    db.commit()
    return pagamento_para_resposta(pagamento)


# Chamada pela rotina que roda a cada minuto. Cada pedido é cancelado na sua própria transação
def cancelar_pedidos_com_prazo_vencido():
    limite = datetime.now(timezone.utc) - PRAZO_PAGAMENTO
    with SessionLocal() as db:
        for pedido_uuid in pedido_repository.listar_prazo_vencido(db, STATUS_SEM_SUCESSO, limite):
            pedido = pedido_repository.buscar_por_uuid(db, pedido_uuid, travar=True)
            # Confere de novo com o pedido travado, porque uma nova tentativa pode ter chegado depois da consulta
            if pedido.status in STATUS_SEM_SUCESSO and pedido.pagamentos[-1].data_hora_resposta < limite:
                devolver_estoque_do_pedido(db, pedido)
                mudar_status(pedido, StatusPedido.PEDIDO_CANCELADO, TipoResponsavel.SISTEMA,
                             motivo="Prazo de 10 minutos para o pagamento esgotado.")
            db.commit()
