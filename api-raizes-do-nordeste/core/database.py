from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

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
