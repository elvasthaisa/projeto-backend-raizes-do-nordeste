from fastapi import APIRouter

from core.erros import ErroResponse
from schemas.usuario import CadastroClienteRequest, UsuarioResponse
from services import usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


# Rota pública (sem login)
@router.post(
    "",
    summary="Cadastrar cliente",
    response_model=UsuarioResponse, # só os campos do UsuarioResponse saem na resposta
    status_code=201,
    responses={
        409: {"model": ErroResponse, "description": "EMAIL_JA_CADASTRADO"},
        422: {"model": ErroResponse, "description": "VALIDACAO"},
    },
)
def cadastrar_cliente(dados: CadastroClienteRequest):
    return usuario_service.cadastrar_cliente(dados)
