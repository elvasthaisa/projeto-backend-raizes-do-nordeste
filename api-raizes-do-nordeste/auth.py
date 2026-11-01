# Autenticação (JWT) e autorização por perfil

import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated, Optional
from uuid import UUID

import bcrypt
import jwt
from fastapi import APIRouter, Body, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from dados_exemplo import buscar_usuario_por_email
from erros import ErroApi, ErroResponse

SECRET_KEY = os.getenv("JWT_SECRET", "chave-de-desenvolvimento") # vai vir do .env
ALGORITMO = "HS256"
MINUTOS_VALIDADE = 60


class Perfil(str, Enum):
    CLIENTE = "CLIENTE"
    ATENDENTE = "ATENDENTE"
    COZINHA = "COZINHA"
    GERENTE = "GERENTE"
    ADMIN = "ADMIN"
    TOTEM = "TOTEM"

class LoginRequest(BaseModel):
    email: str
    senha: str = Field(max_length=72) # limite do bcrypt

class TokenResponse(BaseModel):
    accessToken: str
    tokenType: str = "bearer"

# Dados do usuário lidos do token
class UsuarioLogado(BaseModel):
    id: UUID
    perfil: Perfil
    unidadeId: Optional[UUID] = None


# Exemplos do Swagger (usuários de dados_exemplo.py)
EXEMPLOS_LOGIN = {
    "cliente": {"summary": "Cliente", "value": {"email": "cliente@raizes.com", "senha": "senha123"}},
    "admin": {"summary": "Admin", "value": {"email": "admin@raizes.com", "senha": "senha123"}},
    "atendente_recife": {"summary": "Atendente - Recife", "value": {"email": "atendente.recife@raizes.com", "senha": "senha123"}},
    "cozinha_recife": {"summary": "Cozinha - Recife", "value": {"email": "cozinha.recife@raizes.com", "senha": "senha123"}},
    "gerente_recife": {"summary": "Gerente - Recife", "value": {"email": "gerente.recife@raizes.com", "senha": "senha123"}},
    "totem_recife": {"summary": "Totem - Recife", "value": {"email": "totem.recife@raizes.com", "senha": "senha123"}},
    "atendente_saopaulo": {"summary": "Atendente - São Paulo", "value": {"email": "atendente.saopaulo@raizes.com", "senha": "senha123"}},
    "cozinha_saopaulo": {"summary": "Cozinha - São Paulo", "value": {"email": "cozinha.saopaulo@raizes.com", "senha": "senha123"}},
    "gerente_saopaulo": {"summary": "Gerente - São Paulo", "value": {"email": "gerente.saopaulo@raizes.com", "senha": "senha123"}},
    "totem_saopaulo": {"summary": "Totem - São Paulo", "value": {"email": "totem.saopaulo@raizes.com", "senha": "senha123"}},
    "atendente_fortaleza": {"summary": "Atendente - Fortaleza", "value": {"email": "atendente.fortaleza@raizes.com", "senha": "senha123"}},
    "cozinha_fortaleza": {"summary": "Cozinha - Fortaleza", "value": {"email": "cozinha.fortaleza@raizes.com", "senha": "senha123"}},
    "gerente_fortaleza": {"summary": "Gerente - Fortaleza", "value": {"email": "gerente.fortaleza@raizes.com", "senha": "senha123"}},
    "totem_fortaleza": {"summary": "Totem - Fortaleza", "value": {"email": "totem.fortaleza@raizes.com", "senha": "senha123"}},
}


router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post(
    "/login",
    summary="Fazer login",
    response_model=TokenResponse,
    responses={
        401: {"model": ErroResponse, "description": "CREDENCIAIS_INVALIDAS"},
        422: {"model": ErroResponse, "description": "VALIDACAO"},
    },
)
def login(dados: Annotated[LoginRequest, Body(openapi_examples=EXEMPLOS_LOGIN)]):
    usuario = buscar_usuario_por_email(dados.email)
    # Mesma resposta para e-mail inexistente e senha errada, para não revelar quem tem conta
    if not usuario or not usuario["ativo"] or not bcrypt.checkpw(dados.senha.encode(), usuario["senhaHash"].encode()):
        raise ErroApi(401, "CREDENCIAIS_INVALIDAS", "E-mail ou senha inválidos.")

    payload = {
        "sub": str(usuario["id"]),
        "perfil": usuario["perfil"],
        "unidadeId": str(usuario["unidadeId"]) if usuario["unidadeId"] else None,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=MINUTOS_VALIDADE),
    }
    return TokenResponse(accessToken=jwt.encode(payload, SECRET_KEY, algorithm=ALGORITMO))


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
