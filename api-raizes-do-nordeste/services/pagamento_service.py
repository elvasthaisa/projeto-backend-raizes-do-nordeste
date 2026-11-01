from uuid import UUID, uuid4

from core.enums import CenarioMock, ResultadoPagamento, StatusPedido
from core.erros import ErroApi
from repositories import pagamento_repository, pedido_repository
from services.pedido_service import validar_transicao_pedido


def listar_pagamentos(pedido_id: UUID) -> list:
    return pagamento_repository.listar_por_pedido(pedido_id)


def nova_tentativa(pedido_id: UUID, cenario: CenarioMock) -> dict:
    # Dados de exemplo: pedido recusado na 1ª tentativa
    # Próxima etapa: gravar a tentativa e chamar o gateway mock com o cenário
    pedido = pedido_repository.buscar_por_id(pedido_id, StatusPedido.PAGAMENTO_RECUSADO)
    tentativas = pagamento_repository.listar_por_pedido(pedido_id)

    # Só pedido recusado ou expirado pode tentar de novo, até 3 tentativas (UC3 FA3)
    validar_transicao_pedido(pedido, (StatusPedido.PAGAMENTO_RECUSADO, StatusPedido.PAGAMENTO_EXPIRADO), "pedir nova tentativa de pagamento")
    if len(tentativas) >= 3:
        raise ErroApi(409, "LIMITE_TENTATIVAS", "O pedido já atingiu o limite de 3 tentativas de pagamento.")

    # A tentativa nasce PENDENTE; o resultado chega depois, pelo gateway
    return {"id": uuid4(), "valor": pedido["total"], "resultado": ResultadoPagamento.PENDENTE}
