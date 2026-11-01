from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from core.enums import ResultadoPagamento


# Uma linha por tentativa de pagamento (no máximo 3 por pedido, regra do service)
class Pagamento(Base):
    __tablename__ = "pagamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(unique=True, default=uuid4)
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    resultado: Mapped[ResultadoPagamento] = mapped_column(Enum(ResultadoPagamento, name="resultado", native_enum=False, create_constraint=True))
    motivo_recusa: Mapped[Optional[str]] = mapped_column(String(300))
    data_hora_resposta: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True)) # vazia enquanto PENDENTE

    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedido.id", ondelete="RESTRICT"))
