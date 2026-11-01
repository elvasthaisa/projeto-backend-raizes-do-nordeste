from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from core.enums import CanalPedido, CenarioMock, StatusPedido

# Ids de Recife usados nos exemplos do Swagger (os mesmos de repositories/dados_exemplo.py)
UNIDADE_RECIFE = "3f2b8c1e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"
PRODUTO_CUSCUZ_RECIFE = "b0000000-0000-4000-8000-000000000001"


# Request do POST /pedidos
# Não recebe clienteId (vem do token), formaPagamento nem preço

class ItemPedidoRequest(BaseModel):
    produtoUnidadeId: UUID # uuid do produto no cardápio da unidade
    quantidade: int = Field(gt=0)
    observacao: Optional[str] = Field(default=None, max_length=300)

class PedidoRequest(BaseModel):
    canalPedido: CanalPedido
    unidadeId: Optional[UUID] = None # obrigatório para CLIENTE; ATENDENTE e TOTEM usam a unidade da conta
    itens: List[ItemPedidoRequest] = Field(min_length=1)
    cenarioMock: CenarioMock = CenarioMock.APROVAR

# Exemplos do Swagger, um por perfil que cria pedidos
ITEM_EXEMPLO = {"produtoUnidadeId": PRODUTO_CUSCUZ_RECIFE, "quantidade": 2, "observacao": "Sem cebola"}
EXEMPLOS_PEDIDO = {
    "cliente": {
        "summary": "Cliente no app (login cliente@raizes.com)",
        "value": {"canalPedido": "APP", "unidadeId": UNIDADE_RECIFE, "itens": [ITEM_EXEMPLO], "cenarioMock": "APROVAR"},
    },
    "atendente": {
        "summary": "Atendente no balcão (login atendente.recife@raizes.com)",
        "value": {"canalPedido": "BALCAO", "itens": [ITEM_EXEMPLO]},
    },
    "totem": {
        "summary": "Totem, cliente anônimo (login totem.recife@raizes.com)",
        "value": {"canalPedido": "TOTEM", "itens": [ITEM_EXEMPLO]},
    },
}

# Response dos pedidos

class UnidadeResumo(BaseModel):
    id: UUID
    nome: str

class ItemPedidoResponse(BaseModel):
    produtoUnidadeId: UUID
    nomeProduto: str
    precoUnitario: Decimal = Field(max_digits=10, decimal_places=2) # mesmo limite do numeric(10,2) do banco
    quantidade: int
    observacao: Optional[str] = None

class PedidoResponse(BaseModel):
    id: UUID # o valor é o uuid; o id interno não sai da API
    status: StatusPedido
    canalPedido: CanalPedido
    unidade: UnidadeResumo
    dataHora: datetime
    itens: List[ItemPedidoResponse]
    total: Decimal # calculado, não é gravado
    senha: Optional[int] = None # vazia até o pagamento ser aprovado

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "id": "b8340e16-4ca9-4144-a1e1-155512ea2ce7",
        "status": "AGUARDANDO_PAGAMENTO",
        "canalPedido": "APP",
        "unidade": {"id": UNIDADE_RECIFE, "nome": "Recife"},
        "dataHora": "2026-10-31T14:30:00Z",
        "itens": [{"produtoUnidadeId": PRODUTO_CUSCUZ_RECIFE, "nomeProduto": "Cuscuz com charque", "precoUnitario": "15.00", "quantidade": 2, "observacao": "Sem cebola"}],
        "total": "30.00",
        "senha": None,
    }]})

class PaginaPedidos(BaseModel):
    pedidos: List[PedidoResponse]
    page: int
    limit: int
    total: int # total de pedidos encontrados com os filtros


# Cancelamento (UC4)

class CancelamentoRequest(BaseModel):
    motivo: str = Field(min_length=1, max_length=300)

    model_config = ConfigDict(json_schema_extra={"examples": [{"motivo": "Cliente desistiu do pedido."}]})
