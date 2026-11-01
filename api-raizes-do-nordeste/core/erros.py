# Padrão de erro da API

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException


class DetalheErro(BaseModel):
    field: str
    issue: str

class ErroResponse(BaseModel):
    error: str
    message: str
    details: List[DetalheErro] = []
    timestamp: datetime
    path: str
    requestId: str


# Erro de regra de negócio. Ex.: raise ErroApi(409, "ESTOQUE_INSUFICIENTE", "Estoque insuficiente.")
class ErroApi(Exception):
    def __init__(self, status_code: int, error: str, message: str, details: Optional[List[DetalheErro]] = None):
        self.status_code = status_code
        self.error = error
        self.message = message
        self.details = details or []


def resposta_erro(request: Request, status_code: int, error: str, message: str, details: Optional[List[DetalheErro]] = None):
    corpo = ErroResponse(
        error=error,
        message=message,
        details=details or [],
        timestamp=datetime.now(timezone.utc).replace(microsecond=0),
        path=request.url.path,
        requestId=str(uuid4()),
    )
    return JSONResponse(status_code=status_code, content=corpo.model_dump(mode="json"))


# Mensagens para os erros de validação mais comuns
PROBLEMAS = {
    "missing": "campo obrigatório",
    "enum": "valor inválido",
    "uuid_parsing": "uuid inválido",
    "greater_than": "deve ser maior que 0",
    "greater_than_equal": "valor abaixo do mínimo",
    "less_than_equal": "valor acima do máximo",
    "too_short": "não pode ser vazio",
    "string_too_long": "texto muito longo",
    "string_too_short": "texto muito curto",
    "string_pattern_mismatch": "formato inválido",
    "json_invalid": "JSON mal formado",
}

ERROS_HTTP = {
    401: ("NAO_AUTENTICADO", "Autenticação necessária."),
    403: ("ACESSO_NEGADO", "Acesso negado."),
    404: ("NAO_ENCONTRADO", "Recurso não encontrado."),
    405: ("METODO_NAO_PERMITIDO", "Método não permitido."),
}


def registrar_tratadores_de_erro(app: FastAPI):

    @app.exception_handler(RequestValidationError)
    async def tratar_validacao(request: Request, exc: RequestValidationError):
        details = [
            DetalheErro(
                field=".".join(str(parte) for parte in e["loc"][1:]) or "body", # o 1º é a origem: body, query ou path
                issue=PROBLEMAS.get(e["type"], e["msg"]),
            )
            for e in exc.errors()
        ]
        return resposta_erro(request, 422, "VALIDACAO", "Um ou mais campos são inválidos.", details)

    @app.exception_handler(ErroApi)
    async def tratar_erro_api(request: Request, exc: ErroApi):
        return resposta_erro(request, exc.status_code, exc.error, exc.message, exc.details)

    @app.exception_handler(HTTPException)
    async def tratar_http(request: Request, exc: HTTPException):
        error, message = ERROS_HTTP.get(exc.status_code, ("ERRO", str(exc.detail)))
        return resposta_erro(request, exc.status_code, error, message)

    # Erro não previsto: não expõe detalhes internos
    @app.exception_handler(Exception)
    async def tratar_inesperado(request: Request, exc: Exception):
        return resposta_erro(request, 500, "ERRO_INTERNO", "Erro interno. Tente novamente mais tarde.")
