from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from core.enums import CanalPedido, Perfil, StatusPedido
from core.erros import DetalheErro, ErroApi
from repositories import pedido_repository, unidade_repository
from schemas.auth import UsuarioLogado
from schemas.pedido import PedidoRequest

# Canais que cada perfil pode usar ao criar um pedido
CANAIS_POR_PERFIL = {
    Perfil.CLIENTE: {CanalPedido.APP, CanalPedido.WEB, CanalPedido.PICKUP, CanalPedido.TOTEM},
    Perfil.ATENDENTE: {CanalPedido.BALCAO},
    Perfil.TOTEM: {CanalPedido.TOTEM},
}

# Quem confirma a retirada, por canal
CANAIS_DA_RETIRADA = {
    Perfil.CLIENTE: {CanalPedido.APP, CanalPedido.WEB, CanalPedido.PICKUP},
    Perfil.ATENDENTE: {CanalPedido.BALCAO, CanalPedido.TOTEM},
}

# Status a partir dos quais o pedido ainda pode ser cancelado
STATUS_CANCELAVEIS = (StatusPedido.AGUARDANDO_PAGAMENTO, StatusPedido.PAGAMENTO_RECUSADO, StatusPedido.PAGAMENTO_EXPIRADO)


def validar_transicao_pedido(pedido: dict, status_permitidos, acao: str):
    if pedido["status"] not in status_permitidos:
        raise ErroApi(409, "TRANSICAO_INVALIDA", f"Não é possível {acao}: o pedido está em {pedido['status'].value}.")


def registrar_pedido(dados: PedidoRequest, usuario: UsuarioLogado) -> dict:
    if dados.canalPedido not in CANAIS_POR_PERFIL[usuario.perfil]:
        raise ErroApi(403, "CANAL_NAO_PERMITIDO", f"O perfil {usuario.perfil.value} não pode criar pedidos no canal {dados.canalPedido.value}.")

    # Unidade do pedido: o cliente escolhe; atendente e totem usam a da conta
    if usuario.perfil == Perfil.CLIENTE:
        if dados.unidadeId is None:
            raise ErroApi(422, "VALIDACAO", "Um ou mais campos são inválidos.", [DetalheErro(field="unidadeId", issue="campo obrigatório")])
        unidade_id = dados.unidadeId
    else:
        if dados.unidadeId and dados.unidadeId != usuario.unidadeId:
            raise ErroApi(403, "ACESSO_NEGADO", "A unidade informada é diferente da unidade da conta.")
        unidade_id = usuario.unidadeId

    unidade = unidade_repository.buscar_por_id(unidade_id)
    if unidade is None:
        raise ErroApi(404, "NAO_ENCONTRADO", "Unidade não encontrada.", [DetalheErro(field="unidadeId", issue="não existe")])

    # Cada item precisa estar no cardápio da unidade do pedido; nome e preço vêm do cardápio
    cardapio = {produto["id"]: produto for produto in unidade_repository.listar_cardapio(unidade_id)}
    itens = []
    for posicao, item in enumerate(dados.itens):
        produto = cardapio.get(item.produtoUnidadeId)
        if produto is None:
            raise ErroApi(404, "NAO_ENCONTRADO", "Produto não encontrado no cardápio desta unidade.",
                          [DetalheErro(field=f"itens.{posicao}.produtoUnidadeId", issue="não existe nesta unidade")])
        itens.append({
            "produtoUnidadeId": item.produtoUnidadeId,
            "nomeProduto": produto["nome"],
            "precoUnitario": produto["preco"],
            "quantidade": item.quantidade,
            "observacao": item.observacao,
        })

    # Próxima etapa: gravar o pedido, reservar o estoque e criar a 1ª tentativa de pagamento
    return {
        "id": uuid4(),
        "status": StatusPedido.AGUARDANDO_PAGAMENTO,
        "canalPedido": dados.canalPedido,
        "unidade": {"id": unidade_id, "nome": unidade["nome"]},
        "dataHora": datetime.now(timezone.utc),
        "itens": itens,
        "total": sum(item["precoUnitario"] * item["quantidade"] for item in itens),
        "senha": None,
    }


def listar_pedidos(canal: Optional[CanalPedido], status: Optional[StatusPedido], page: int, limit: int) -> dict:
    # Com o banco: CLIENTE vê só os seus pedidos; funcionários, os da sua unidade; ADMIN, todos
    pedidos = pedido_repository.listar(canal, status)
    return {"pedidos": pedidos, "page": page, "limit": limit, "total": len(pedidos)}


def consultar_pedido(pedido_id: UUID) -> dict:
    # Com o banco: checagem do dono do pedido ou da unidade
    return pedido_repository.buscar_por_id(pedido_id)


# Mudanças de status. Próxima etapa: gravar o status e o histórico na mesma transação

def marcar_pronto(pedido_id: UUID) -> dict:
    pedido = pedido_repository.buscar_por_id(pedido_id, StatusPedido.EM_PREPARO)
    validar_transicao_pedido(pedido, (StatusPedido.EM_PREPARO,), "marcar como pronto")
    pedido["status"] = StatusPedido.PRONTO
    return pedido


def confirmar_retirada(pedido_id: UUID, usuario: UsuarioLogado) -> dict:
    pedido = pedido_repository.buscar_por_id(pedido_id, StatusPedido.PRONTO)
    if pedido["canalPedido"] not in CANAIS_DA_RETIRADA[usuario.perfil]:
        raise ErroApi(403, "ACESSO_NEGADO", f"A retirada de pedidos do canal {pedido['canalPedido'].value} não é confirmada pelo perfil {usuario.perfil.value}.")
    validar_transicao_pedido(pedido, (StatusPedido.PRONTO,), "confirmar a retirada")
    pedido["status"] = StatusPedido.ENTREGUE
    return pedido


def cancelar_pedido(pedido_id: UUID, motivo: str) -> dict:
    # Próxima etapa: o motivo vai para o histórico e o estoque reservado é devolvido
    pedido = pedido_repository.buscar_por_id(pedido_id, StatusPedido.AGUARDANDO_PAGAMENTO)
    validar_transicao_pedido(pedido, STATUS_CANCELAVEIS, "cancelar")
    pedido["status"] = StatusPedido.PEDIDO_CANCELADO
    return pedido
