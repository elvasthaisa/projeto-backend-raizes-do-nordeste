from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.erros import ErroResponse
from schemas.unidade import ItemCardapioResponse, UnidadeResponse
from services import unidade_service

router = APIRouter(prefix="/unidades", tags=["Unidades"])


# Rotas públicas (sem login)

@router.get("", summary="Listar unidades da rede Raízes do Nordeste", response_model=List[UnidadeResponse])
def listar_unidades(db: Annotated[Session, Depends(get_db)]):
    return unidade_service.listar_unidades(db)

@router.get(
    "/{id}/cardapio",
    summary="Consultar o cardápio da unidade",
    response_model=List[ItemCardapioResponse],
    responses={
        404: {"model": ErroResponse, "description": "NAO_ENCONTRADO"},
        422: {"model": ErroResponse, "description": "VALIDACAO (id não é um uuid)"},
    },
)
def consultar_cardapio(id: UUID, db: Annotated[Session, Depends(get_db)]):
    return unidade_service.consultar_cardapio(db, id)
