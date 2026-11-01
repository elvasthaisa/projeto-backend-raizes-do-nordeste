from uuid import UUID

from repositories.dados_exemplo import pagamentos_exemplo


def listar_por_pedido(pedido_id: UUID):
    return pagamentos_exemplo()
