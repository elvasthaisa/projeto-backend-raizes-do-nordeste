from uuid import UUID

from sqlalchemy.orm import Session

from core.erros import ErroApi
from repositories import unidade_repository

# Nas respostas, o "id" é sempre o uuid; o id numérico nunca sai da API


def listar_unidades(db: Session) -> list:
    return [
        {"id": unidade.uuid, "nome": unidade.nome, "endereco": unidade.endereco, "cidade": unidade.cidade, "uf": unidade.uf}
        for unidade in unidade_repository.listar(db)
    ]


def consultar_cardapio(db: Session, unidade_uuid: UUID) -> list:
    unidade = unidade_repository.buscar_por_uuid(db, unidade_uuid)
    if unidade is None:
        raise ErroApi(404, "NAO_ENCONTRADO", "Unidade não encontrada.")
    return [
        {
            "id": item.uuid,
            "nome": item.produto.nome,
            "descricao": item.produto.descricao,
            "categoria": item.produto.categoria,
            "preco": item.preco,
        }
        for item in unidade_repository.listar_cardapio(db, unidade.id)
    ]
