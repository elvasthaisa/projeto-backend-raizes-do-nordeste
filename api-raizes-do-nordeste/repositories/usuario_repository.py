from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Usuario


def buscar_por_email(db: Session, email: str):
    return db.scalar(select(Usuario).where(Usuario.email == email.lower()))

def adicionar(db: Session, usuario: Usuario):
    db.add(usuario)
