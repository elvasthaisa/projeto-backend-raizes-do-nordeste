from uuid import uuid4

import bcrypt

from core.erros import ErroApi
from repositories import usuario_repository
from schemas.usuario import CadastroClienteRequest


def cadastrar_cliente(dados: CadastroClienteRequest) -> dict:
    if usuario_repository.buscar_por_email(dados.email):
        raise ErroApi(409, "EMAIL_JA_CADASTRADO", "Já existe uma conta com este e-mail.")

    usuario = {
        "id": uuid4(),
        "nome": dados.nome,
        "email": dados.email.lower(),
        "perfil": "CLIENTE", # cadastro público é só de cliente; funcionários e totens vêm do seed
        "unidadeId": None,
        "senhaHash": bcrypt.hashpw(dados.senha.encode(), bcrypt.gensalt()).decode(),
        "ativo": True,
    }
    usuario_repository.adicionar(usuario)
    return usuario
