from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from core.enums import Categoria


# Catálogo da rede (matriz)
class Produto(Base):
    __tablename__ = "produto"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(unique=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(100))
    descricao: Mapped[Optional[str]] = mapped_column(String(300))
    categoria: Mapped[Categoria] = mapped_column(Enum(Categoria, name="categoria", native_enum=False, create_constraint=True))
    ativo: Mapped[bool] = mapped_column(default=True)


# O produto dentro de uma unidade: preço e estoque são de cada unidade
class ProdutoUnidade(Base):
    __tablename__ = "produto_unidade"
    __table_args__ = (
        UniqueConstraint("produto_id", "unidade_id"),
        CheckConstraint("preco > 0", name="preco_positivo"),
        CheckConstraint("estoque >= 0", name="estoque_nao_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(unique=True, default=uuid4)
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    estoque: Mapped[int]
    ativo: Mapped[bool] = mapped_column(default=True)
    disponivel_sazonal: Mapped[bool] = mapped_column(default=True)

    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id", ondelete="RESTRICT"))
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidade.id", ondelete="RESTRICT"))

    produto: Mapped["Produto"] = relationship()
    unidade: Mapped["Unidade"] = relationship()
