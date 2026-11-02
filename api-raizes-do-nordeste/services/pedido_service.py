from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.enums import CanalPedido, Perfil, ResultadoPagamento, StatusPedido, TipoResponsavel
from core.erros import DetalheErro, ErroApi
from models import HistoricoStatusPedido, ItemPedido, Pagamento, Pedido, Usuario
from repositories import pedido_repository, unidade_repository, usuario_repository
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


def validar_transicao_pedido(status_atual: StatusPedido, status_permitidos, acao: str):
    if status_atual not in status_permitidos:
        raise ErroApi(409, "TRANSICAO_INVALIDA", f"Não é possível {acao}: o pedido está em {status_atual.value}.")


# Toda mudança de status grava também uma linha no histórico, na mesma transação
def mudar_status(pedido: Pedido, novo_status: StatusPedido, tipo_responsavel: TipoResponsavel,
                 usuario: Optional[Usuario] = None, motivo: Optional[str] = None):
    pedido.historico.append(HistoricoStatusPedido(
        status_anterior=pedido.status,
        status_novo=novo_status,
        tipo_responsavel=tipo_responsavel,
        usuario=usuario,
        motivo=motivo,
    ))
    pedido.status = novo_status


# Quem fica registrado no histórico. O totem é registrado como CLIENTE anônimo, sem usuário
def identificar_responsavel(db: Session, usuario: UsuarioLogado) -> tuple:
    if usuario.perfil == Perfil.TOTEM:
        return TipoResponsavel.CLIENTE, None
    return TipoResponsavel(usuario.perfil.value), usuario_repository.buscar_por_uuid(db, usuario.id)


# O estoque reservado na criação do pedido volta para a venda
def devolver_estoque_do_pedido(db: Session, pedido: Pedido):
    unidade_repository.travar_produtos(db, [item.produto_unidade_id for item in pedido.itens])
    for item in pedido.itens:
        item.produto_unidade.devolver_estoque(item.quantidade)


def pedido_para_resposta(pedido: Pedido) -> dict:
    return {
        "id": pedido.uuid,
        "status": pedido.status,
        "canalPedido": pedido.canal_pedido,
        "unidade": {"id": pedido.unidade.uuid, "nome": pedido.unidade.nome},
        "dataHora": pedido.data_hora,
        "itens": [
            {
                "produtoUnidadeId": item.produto_unidade.uuid,
                "nomeProduto": item.nome_produto,
                "precoUnitario": item.preco_unitario,
                "quantidade": item.quantidade,
                "observacao": item.observacao,
            }
            for item in pedido.itens
        ],
        "total": pedido.calcular_total(),
        "senha": pedido.senha,
    }


def registrar_pedido(db: Session, dados: PedidoRequest, usuario: UsuarioLogado) -> dict:
    if dados.canalPedido not in CANAIS_POR_PERFIL[usuario.perfil]:
        raise ErroApi(403, "CANAL_NAO_PERMITIDO", f"O perfil {usuario.perfil.value} não pode criar pedidos no canal {dados.canalPedido.value}.")

    # Unidade do pedido: o cliente escolhe, e o atendente e o totem usam a da conta
    if usuario.perfil == Perfil.CLIENTE:
        if dados.unidadeId is None:
            raise ErroApi(422, "VALIDACAO", "Um ou mais campos são inválidos.", [DetalheErro(field="unidadeId", issue="campo obrigatório")])
        unidade_id = dados.unidadeId
    else:
        if dados.unidadeId and dados.unidadeId != usuario.unidadeId:
            raise ErroApi(403, "ACESSO_NEGADO", "A unidade informada é diferente da unidade da conta.")
        unidade_id = usuario.unidadeId

    unidade = unidade_repository.buscar_por_uuid(db, unidade_id)
    if unidade is None:
        raise ErroApi(404, "NAO_ENCONTRADO", "Unidade não encontrada.", [DetalheErro(field="unidadeId", issue="não existe")])

    # Cada item precisa ser um produto da unidade do pedido, estar disponível e ter estoque
    uuids_pedidos = [item.produtoUnidadeId for item in dados.itens]
    produtos = {produto_unidade.uuid: produto_unidade for produto_unidade in unidade_repository.buscar_produtos_da_unidade(db, unidade.id, uuids_pedidos)}
    for posicao, item in enumerate(dados.itens):
        campo = f"itens.{posicao}.produtoUnidadeId"
        produto_unidade = produtos.get(item.produtoUnidadeId)
        if produto_unidade is None:
            raise ErroApi(404, "NAO_ENCONTRADO", "Produto não encontrado no cardápio desta unidade.",
                          [DetalheErro(field=campo, issue="não existe nesta unidade")])
        # Existe na unidade, mas foi desativado pelo gerente ou está fora da temporada
        if not produto_unidade.ativo or not produto_unidade.disponivel_sazonal:
            raise ErroApi(409, "PRODUTO_INDISPONIVEL", f"{produto_unidade.produto.nome} está indisponível nesta unidade no momento.",
                          [DetalheErro(field=campo, issue="indisponível no momento")])
        if not produto_unidade.reservar_estoque(item.quantidade):
            raise ErroApi(409, "ESTOQUE_INSUFICIENTE", f"Estoque insuficiente de {produto_unidade.produto.nome} nesta unidade.",
                          [DetalheErro(field=f"itens.{posicao}.quantidade", issue="maior que o estoque disponível")])

    # Mesmo produto com a mesma observação vira uma linha só. Nome e preço são copiados do cardápio
    linhas = {}
    for item in dados.itens:
        observacao = (item.observacao or "").strip() or None
        chave = (item.produtoUnidadeId, observacao)
        if chave in linhas:
            linhas[chave].quantidade += item.quantidade
        else:
            produto_unidade = produtos[item.produtoUnidadeId]
            linhas[chave] = ItemPedido(
                produto_unidade=produto_unidade,
                nome_produto=produto_unidade.produto.nome,
                preco_unitario=produto_unidade.preco,
                quantidade=item.quantidade,
                observacao=observacao,
            )

    # No balcão e no totem anônimo o pedido fica sem cliente
    tipo_responsavel, responsavel = identificar_responsavel(db, usuario)
    pedido = Pedido(
        canal_pedido=dados.canalPedido,
        status=StatusPedido.AGUARDANDO_PAGAMENTO,
        unidade=unidade,
        cliente=responsavel if usuario.perfil == Perfil.CLIENTE else None,
        itens=list(linhas.values()),
    )
    # A 1ª tentativa de pagamento e a 1ª linha do histórico são gravadas junto com o pedido, na mesma transação
    pedido.pagamentos.append(Pagamento(valor=pedido.calcular_total(), resultado=ResultadoPagamento.PENDENTE))
    pedido.historico.append(HistoricoStatusPedido(status_novo=StatusPedido.AGUARDANDO_PAGAMENTO, tipo_responsavel=tipo_responsavel, usuario=responsavel))

    pedido_repository.adicionar(db, pedido)
    db.commit()
    return pedido_para_resposta(pedido)


def listar_pedidos(db: Session, usuario: UsuarioLogado, canal: Optional[CanalPedido], status: Optional[StatusPedido], page: int, limit: int) -> dict:
    # O cliente vê só os seus pedidos, os funcionários veem os da sua unidade e o admin vê todos
    cliente_id = unidade_id = None
    if usuario.perfil == Perfil.CLIENTE:
        cliente_id = usuario_repository.buscar_por_uuid(db, usuario.id).id
    elif usuario.perfil != Perfil.ADMIN:
        unidade_id = unidade_repository.buscar_por_uuid(db, usuario.unidadeId).id

    pedidos, total = pedido_repository.listar(db, canal, status, cliente_id, unidade_id, page, limit)
    return {"pedidos": [pedido_para_resposta(pedido) for pedido in pedidos], "page": page, "limit": limit, "total": total}


# Busca o pedido e confere se quem pede pode vê-lo: o cliente dono do pedido, os funcionários da unidade,
# o totem da unidade (só pedidos feitos no totem) e o admin
def buscar_pedido(db: Session, pedido_uuid: UUID, usuario: UsuarioLogado, travar: bool = False) -> Pedido:
    pedido = pedido_repository.buscar_por_uuid(db, pedido_uuid, travar)
    if pedido is None:
        raise ErroApi(404, "NAO_ENCONTRADO", "Pedido não encontrado.")

    if usuario.perfil == Perfil.ADMIN:
        permitido = True
    elif usuario.perfil == Perfil.CLIENTE:
        permitido = pedido.cliente is not None and pedido.cliente.uuid == usuario.id
    elif usuario.perfil == Perfil.TOTEM:
        permitido = pedido.unidade.uuid == usuario.unidadeId and pedido.canal_pedido == CanalPedido.TOTEM
    else:
        permitido = pedido.unidade.uuid == usuario.unidadeId
    if not permitido:
        raise ErroApi(403, "ACESSO_NEGADO", "Você não tem acesso a este pedido.")
    return pedido


def consultar_pedido(db: Session, pedido_uuid: UUID, usuario: UsuarioLogado) -> dict:
    return pedido_para_resposta(buscar_pedido(db, pedido_uuid, usuario))


# Mudanças de status. Próxima etapa: gravar o status e o histórico na mesma transação

def marcar_pronto(pedido_id: UUID) -> dict:
    pedido = pedido_repository.buscar_por_id(pedido_id, StatusPedido.EM_PREPARO)
    validar_transicao_pedido(pedido["status"], (StatusPedido.EM_PREPARO,), "marcar como pronto")
    pedido["status"] = StatusPedido.PRONTO
    return pedido


def confirmar_retirada(pedido_id: UUID, usuario: UsuarioLogado) -> dict:
    pedido = pedido_repository.buscar_por_id(pedido_id, StatusPedido.PRONTO)
    if pedido["canalPedido"] not in CANAIS_DA_RETIRADA[usuario.perfil]:
        raise ErroApi(403, "ACESSO_NEGADO", f"A retirada de pedidos do canal {pedido['canalPedido'].value} não é confirmada pelo perfil {usuario.perfil.value}.")
    validar_transicao_pedido(pedido["status"], (StatusPedido.PRONTO,), "confirmar a retirada")
    pedido["status"] = StatusPedido.ENTREGUE
    return pedido


def cancelar_pedido(db: Session, pedido_uuid: UUID, motivo: str, usuario: UsuarioLogado) -> dict:
    pedido = buscar_pedido(db, pedido_uuid, usuario, travar=True)
    validar_transicao_pedido(pedido.status, STATUS_CANCELAVEIS, "cancelar")

    devolver_estoque_do_pedido(db, pedido)
    tipo_responsavel, responsavel = identificar_responsavel(db, usuario)
    mudar_status(pedido, StatusPedido.PEDIDO_CANCELADO, tipo_responsavel, responsavel, motivo)
    db.commit()
    return pedido_para_resposta(pedido)


# Pagamento aprovado: o pedido vai para o preparo já com a senha de retirada.
# A senha é a maior do dia na unidade + 1. Se outra aprovação gravar o mesmo número antes,
# a restrição única do banco recusa e o número é calculado de novo
def enviar_para_preparo(db: Session, pedido: Pedido):
    hoje = date.today()
    while True:
        try:
            with db.begin_nested():
                pedido.senha = pedido_repository.maior_senha_do_dia(db, pedido.unidade_id, hoje) + 1
                pedido.data_senha = hoje
            break
        except IntegrityError:
            continue
    mudar_status(pedido, StatusPedido.EM_PREPARO, TipoResponsavel.SISTEMA)
