import logging

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Padrão de nomes das restrições, para as migrations saberem o nome de cada uma
NOMES_RESTRICOES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# Classe base dos models do SQLAlchemy
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NOMES_RESTRICOES)


# Uma sessão por requisição, fechada no final
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Healthcheck: o banco responde a uma consulta simples? A falha fica no log com o motivo
def banco_disponivel(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        logging.exception("Healthcheck: banco de dados indisponível")
        return False
