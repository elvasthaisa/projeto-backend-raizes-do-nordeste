import bcrypt

from core.erros import ErroApi
from core.seguranca import criar_token
from repositories import usuario_repository
from schemas.auth import LoginRequest


def login(dados: LoginRequest) -> str:
    usuario = usuario_repository.buscar_por_email(dados.email)
    # Mesma resposta para e-mail inexistente e senha errada, para não revelar quem tem conta
    if not usuario or not usuario["ativo"] or not bcrypt.checkpw(dados.senha.encode(), usuario["senhaHash"].encode()):
        raise ErroApi(401, "CREDENCIAIS_INVALIDAS", "E-mail ou senha inválidos.")
    return criar_token(usuario)
