from uuid import UUID

from core.erros import ErroApi
from repositories import unidade_repository


def listar_unidades() -> list:
    return unidade_repository.listar()


def consultar_cardapio(unidade_id: UUID) -> list:
    if unidade_repository.buscar_por_id(unidade_id) is None:
        raise ErroApi(404, "NAO_ENCONTRADO", "Unidade não encontrada.")
    return unidade_repository.listar_cardapio(unidade_id)
