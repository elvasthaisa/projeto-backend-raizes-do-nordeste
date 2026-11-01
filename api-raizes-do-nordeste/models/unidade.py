from uuid import UUID, uuid4

from sqlalchemy import CHAR, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Unidade(Base):
    __tablename__ = "unidade"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(unique=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(100))
    endereco: Mapped[str] = mapped_column(String(200))
    cidade: Mapped[str] = mapped_column(String(100))
    uf: Mapped[str] = mapped_column(CHAR(2))
