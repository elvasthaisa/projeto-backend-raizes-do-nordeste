from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from core.enums import Perfil


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(unique=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(60)) # o bcrypt gera 60 caracteres
    perfil: Mapped[Perfil] = mapped_column(Enum(Perfil, name="perfil", native_enum=False, create_constraint=True))
    ativo: Mapped[bool] = mapped_column(default=True)

    # Obrigatória para funcionários e totens; vazia para CLIENTE e ADMIN
    unidade_id: Mapped[Optional[int]] = mapped_column(ForeignKey("unidade.id", ondelete="RESTRICT"))

    unidade: Mapped[Optional["Unidade"]] = relationship()
