from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.enums import CenarioMock, ResultadoPagamento, StatusPedido, TipoResponsavel
from core.erros import ErroApi
from gateway.gateway_mock import GatewayMock
from gateway.gateway_pagamento import GatewayPagamento, RespostaGateway
from repositories import pagamento_repository, pedido_repository
from schemas.auth import UsuarioLogado
from services.pedido_service import buscar_pedido, enviar_para_preparo, mudar_status, validar_transicao_pedido

# Novas chamadas ao gateway dentro da mesma tentativa, quando ele não responde
RETENTATIVAS_GATEWAY = 3


# Mesmas regras de acesso do GET /pedidos/{id}
def listar_pagamentos(db: Session, pedido_uuid: UUID, usuario: UsuarioLogado) -> list:
    pedido = buscar_pedido(db, pedido_uuid, usuario)
    return [
        {
            "id": pagamento.uuid,
            "valor": pagamento.valor,
            "resultado": pagamento.resultado,
            "motivoRecusa": pagamento.motivo_recusa,
            "dataHoraResposta": pagamento.data_hora_resposta,
        }
        for pagamento in pedido.pagamentos
    ]


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
    db.commit()


def nova_tentativa(pedido_id: UUID, cenario: CenarioMock) -> dict:
    # Dados de exemplo: pedido recusado na 1ª tentativa
    # Próxima etapa: gravar a tentativa e chamar o gateway mock com o cenário
    pedido = pedido_repository.buscar_por_id(pedido_id, StatusPedido.PAGAMENTO_RECUSADO)
    tentativas = pagamento_repository.listar_por_pedido(pedido_id)

    # Só pedido recusado ou expirado pode tentar de novo, até 3 tentativas (UC3 FA3)
    validar_transicao_pedido(pedido["status"], (StatusPedido.PAGAMENTO_RECUSADO, StatusPedido.PAGAMENTO_EXPIRADO), "pedir nova tentativa de pagamento")
    if len(tentativas) >= 3:
        raise ErroApi(409, "LIMITE_TENTATIVAS", "O pedido já atingiu o limite de 3 tentativas de pagamento.")

    # A tentativa nasce PENDENTE; o resultado chega depois, pelo gateway
    return {"id": uuid4(), "valor": pedido["total"], "resultado": ResultadoPagamento.PENDENTE}
