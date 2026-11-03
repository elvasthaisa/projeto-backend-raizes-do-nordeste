from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import banco_disponivel, get_db
from core.erros import ErroApi, ErroResponse
from schemas.health import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


# Rota pública (sem login): usada por monitoramento e balanceador de carga para saber se a API está apta a
# atender. Responde 200 quando a API e o banco respondem, e 503 (no padrão de erro da API) quando o banco não responde
@router.get(
    "",
    summary="Verificar se a API e o banco estão no ar (healthcheck)",
    response_model=HealthResponse,
    responses={503: {"model": ErroResponse, "description": "SERVICO_INDISPONIVEL (banco não responde)"}},
)
def verificar_saude(db: Annotated[Session, Depends(get_db)]):
    if not banco_disponivel(db):
        raise ErroApi(503, "SERVICO_INDISPONIVEL", "O banco de dados não está respondendo.")
    return HealthResponse(status="UP", banco="UP", timestamp=datetime.now(timezone.utc).replace(microsecond=0))
