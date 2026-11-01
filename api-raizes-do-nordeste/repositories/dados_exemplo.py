# Pedidos e pagamentos fictícios, até essas rotas usarem o banco. Só os repositories leem daqui.

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from core.enums import CanalPedido, ResultadoPagamento, StatusPedido

# Ids de Recife do seed.py
UNIDADE_RECIFE = UUID("3f2b8c1e-1a2b-4c3d-8e9f-0a1b2c3d4e5f")
PRODUTO_CUSCUZ_RECIFE = UUID("b0000000-0000-4000-8000-000000000001")


# Pedido fictício: o status é escolhido por quem chama, para cada rota simular o caso de sucesso
def pedido_exemplo(pedido_id: UUID, status: StatusPedido = StatusPedido.EM_PREPARO) -> dict:
    return {
        "id": pedido_id,
        "status": status,
        "canalPedido": CanalPedido.APP,
        "unidade": {"id": UNIDADE_RECIFE, "nome": "Recife"},
        "dataHora": datetime.now(timezone.utc),
        "itens": [
            {"produtoUnidadeId": PRODUTO_CUSCUZ_RECIFE, "nomeProduto": "Cuscuz com charque", "precoUnitario": Decimal("15.00"), "quantidade": 2},
            {"produtoUnidadeId": uuid4(), "nomeProduto": "Suco de caju", "precoUnitario": Decimal("8.00"), "quantidade": 1},
        ],
        "total": Decimal("38.00"),
        "senha": 42 if status in (StatusPedido.EM_PREPARO, StatusPedido.PRONTO, StatusPedido.ENTREGUE) else None,
    }

# Tentativas fictícias: uma recusada
def pagamentos_exemplo() -> list:
    return [
        {
            "id": uuid4(),
            "valor": Decimal("38.00"),
            "resultado": ResultadoPagamento.RECUSADO,
            "motivoRecusa": "Pagamento recusado pela operadora.",
            "dataHoraResposta": datetime.now(timezone.utc),
        }
    ]
