from uuid import UUID

from repositories.dados_exemplo import CARDAPIOS, UNIDADES


def listar():
    return [{"id": id, **dados} for id, dados in UNIDADES.items()]

def buscar_por_id(unidade_id: UUID):
    dados = UNIDADES.get(unidade_id)
    return {"id": unidade_id, **dados} if dados else None

def listar_cardapio(unidade_id: UUID):
    return CARDAPIOS.get(unidade_id, [])
