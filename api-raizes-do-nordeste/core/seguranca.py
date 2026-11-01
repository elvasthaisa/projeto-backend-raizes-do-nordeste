# Autenticação (JWT) e autorização por perfil de usuário

import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.enums import Perfil
from core.erros import ErroApi
from schemas.auth import UsuarioLogado

SECRET_KEY = os.getenv("JWT_SECRET", "chave-de-desenvolvimento") # vai vir do .env
ALGORITMO = "HS256"
MINUTOS_VALIDADE = 60


def criar_token(usuario: dict) -> str:
    payload = {
        "sub": str(usuario["id"]),
        "perfil": usuario["perfil"],
        "unidadeId": str(usuario["unidadeId"]) if usuario["unidadeId"] else None,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=MINUTOS_VALIDADE),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITMO)


bearer = HTTPBearer(auto_error=False)

def usuario_atual(credenciais: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer)]) -> UsuarioLogado:
    if credenciais is None:
        raise ErroApi(401, "NAO_AUTENTICADO", "Autenticação necessária.")
    try:
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=[ALGORITMO])
    except jwt.InvalidTokenError:
        raise ErroApi(401, "NAO_AUTENTICADO", "Token inválido ou expirado.")
    return UsuarioLogado(id=payload["sub"], perfil=payload["perfil"], unidadeId=payload["unidadeId"])

def exigir_perfis(*perfis: Perfil):
    def verificar(usuario: Annotated[UsuarioLogado, Depends(usuario_atual)]) -> UsuarioLogado:
        if usuario.perfil not in perfis:
            raise ErroApi(403, "ACESSO_NEGADO", "Seu perfil não tem permissão para esta ação.")
        return usuario
    return verificar
