# Autenticação (JWT) e autorização por perfil de usuário

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import JWT_SECRET
from core.enums import Perfil
from core.erros import ErroApi
from models import Usuario
from schemas.auth import UsuarioLogado

ALGORITMO = "HS256"
MINUTOS_VALIDADE = 60


# O token leva os uuids, nunca o id numérico
def criar_token(usuario: Usuario) -> str:
    payload = {
        "sub": str(usuario.uuid),
        "perfil": usuario.perfil.value,
        "unidadeId": str(usuario.unidade.uuid) if usuario.unidade else None,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=MINUTOS_VALIDADE),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITMO)


bearer = HTTPBearer(auto_error=False)

def usuario_atual(credenciais: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer)]) -> UsuarioLogado:
    if credenciais is None:
        raise ErroApi(401, "NAO_AUTENTICADO", "Autenticação necessária.")
    try:
        payload = jwt.decode(credenciais.credentials, JWT_SECRET, algorithms=[ALGORITMO])
    except jwt.InvalidTokenError:
        raise ErroApi(401, "NAO_AUTENTICADO", "Token inválido ou expirado.")
    return UsuarioLogado(id=payload["sub"], perfil=payload["perfil"], unidadeId=payload["unidadeId"])

def exigir_perfis(*perfis: Perfil):
    def verificar(usuario: Annotated[UsuarioLogado, Depends(usuario_atual)]) -> UsuarioLogado:
        if usuario.perfil not in perfis:
            raise ErroApi(403, "ACESSO_NEGADO", "Seu perfil não tem permissão para esta ação.")
        return usuario
    return verificar
