from typing import Annotated

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.erros import ErroResponse
from schemas.auth import EXEMPLOS_LOGIN, LoginRequest, TokenResponse
from services import auth_service

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
def login(dados: Annotated[LoginRequest, Body(openapi_examples=EXEMPLOS_LOGIN)], db: Annotated[Session, Depends(get_db)]):
    return TokenResponse(accessToken=auth_service.login(db, dados))
