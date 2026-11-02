# Log de quem consultou dados de pedidos, no terminal e em logs/acesso.log
# Guarda só o uuid e o perfil de quem consultou, sem nome, e-mail nem token

import logging
from pathlib import Path

from fastapi import Request

from schemas.auth import UsuarioLogado

PASTA_LOGS = Path(__file__).parent.parent / "logs"
PASTA_LOGS.mkdir(exist_ok=True)

log_acesso = logging.getLogger("acesso")
log_acesso.setLevel(logging.INFO)
formato = logging.Formatter("%(asctime)s ACESSO %(message)s")
for destino in (logging.StreamHandler(), logging.FileHandler(PASTA_LOGS / "acesso.log", encoding="utf-8")):
    destino.setFormatter(formato)
    log_acesso.addHandler(destino)


def registrar_acesso(request: Request, usuario: UsuarioLogado):
    consulta = request.url.path
    if request.url.query:
        consulta += "?" + request.url.query
    log_acesso.info("usuario=%s perfil=%s %s %s", usuario.id, usuario.perfil.value, request.method, consulta)
