from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from core.enums import Categoria


class UnidadeResponse(BaseModel):
    id: UUID
    nome: str
    endereco: str
    cidade: str
    uf: str

class ItemCardapioResponse(BaseModel):
    id: UUID # uuid do ProdutoUnidade: é o que vai em produtoUnidadeId no pedido
    nome: str
    descricao: Optional[str] = None
    categoria: Categoria
    preco: Decimal = Field(max_digits=10, decimal_places=2)
