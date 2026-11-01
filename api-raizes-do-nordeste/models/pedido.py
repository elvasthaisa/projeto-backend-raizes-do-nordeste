from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from core.enums import CanalPedido, StatusPedido, TipoResponsavel


class Pedido(Base):
    __tablename__ = "pedido"
    __table_args__ = (UniqueConstraint("unidade_id", "data_senha", "senha"),) # senha única por unidade e por dia

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(unique=True, default=uuid4)
    canal_pedido: Mapped[CanalPedido] = mapped_column(Enum(CanalPedido, name="canal_pedido", native_enum=False, create_constraint=True))
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[StatusPedido] = mapped_column(Enum(StatusPedido, name="status", native_enum=False, create_constraint=True))
    senha: Mapped[Optional[int]] # vazia até o pagamento ser aprovado
    data_senha: Mapped[Optional[date]] # data da aprovação, gravada junto com a senha

    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidade.id", ondelete="RESTRICT"))
    cliente_id: Mapped[Optional[int]] = mapped_column(ForeignKey("usuario.id", ondelete="RESTRICT")) # vazio no balcão e no totem anônimo

    unidade: Mapped["Unidade"] = relationship()
    cliente: Mapped[Optional["Usuario"]] = relationship()
    itens: Mapped[List["ItemPedido"]] = relationship()
    pagamentos: Mapped[List["Pagamento"]] = relationship()
    historico: Mapped[List["HistoricoStatusPedido"]] = relationship()


# Uma linha do pedido. Nome e preço são cópias do cardápio no momento da compra
class ItemPedido(Base):
    __tablename__ = "item_pedido"
    __table_args__ = (CheckConstraint("quantidade > 0", name="quantidade_positiva"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_produto: Mapped[str] = mapped_column(String(100))
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantidade: Mapped[int]
    observacao: Mapped[Optional[str]] = mapped_column(String(300))

    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedido.id", ondelete="RESTRICT"))
    produto_unidade_id: Mapped[int] = mapped_column(ForeignKey("produto_unidade.id", ondelete="RESTRICT"))

    produto_unidade: Mapped["ProdutoUnidade"] = relationship()


# Uma linha por mudança de status. As linhas nunca são alteradas
class HistoricoStatusPedido(Base):
    __tablename__ = "historico_status_pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    status_anterior: Mapped[Optional[StatusPedido]] = mapped_column(Enum(StatusPedido, name="status_anterior", native_enum=False, create_constraint=True))
    status_novo: Mapped[StatusPedido] = mapped_column(Enum(StatusPedido, name="status_novo", native_enum=False, create_constraint=True))
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    tipo_responsavel: Mapped[TipoResponsavel] = mapped_column(Enum(TipoResponsavel, name="tipo_responsavel", native_enum=False, create_constraint=True))
    motivo: Mapped[Optional[str]] = mapped_column(String(300))

    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedido.id", ondelete="RESTRICT"))
    usuario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("usuario.id", ondelete="RESTRICT")) # vazio só com SISTEMA ou CLIENTE anônimo

    usuario: Mapped[Optional["Usuario"]] = relationship()
