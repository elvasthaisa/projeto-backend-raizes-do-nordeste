import bcrypt
from sqlalchemy.orm import Session

from core.enums import Perfil
from core.erros import ErroApi
from models import Usuario
from repositories import usuario_repository
from schemas.usuario import CadastroClienteRequest


def cadastrar_cliente(db: Session, dados: CadastroClienteRequest) -> dict:
    if usuario_repository.buscar_por_email(db, dados.email):
        raise ErroApi(409, "EMAIL_JA_CADASTRADO", "Já existe uma conta com este e-mail.")

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email.lower(),
        senha_hash=bcrypt.hashpw(dados.senha.encode(), bcrypt.gensalt()).decode(),
        perfil=Perfil.CLIENTE, # cadastro público é só de cliente; funcionários e totens vêm do seed
    )
    usuario_repository.adicionar(db, usuario)
    db.commit()
    return {"id": usuario.uuid, "nome": usuario.nome, "email": usuario.email, "perfil": usuario.perfil}
