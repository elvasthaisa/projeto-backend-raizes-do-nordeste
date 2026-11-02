from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from core.enums import CanalPedido, StatusPedido
from models import ItemPedido, Pedido
from repositories.dados_exemplo import pedido_exemplo


def adicionar(db: Session, pedido: Pedido):
    db.add(pedido)


# Com travar=True, o pedido fica travado até o fim da transação, para duas mudanças de status não acontecerem ao mesmo tempo
def buscar_por_uuid(db: Session, pedido_uuid: UUID, travar: bool = False):
    consulta = select(Pedido).where(Pedido.uuid == pedido_uuid)
    if travar:
        consulta = consulta.with_for_update()
    return db.scalar(consulta)


# Do pedido mais recente para o mais antigo
def listar(db: Session, canal: Optional[CanalPedido], status: Optional[StatusPedido],
           cliente_id: Optional[int], unidade_id: Optional[int], page: int, limit: int):
    consulta = select(Pedido)
    if canal:
        consulta = consulta.where(Pedido.canal_pedido == canal)
    if status:
        consulta = consulta.where(Pedido.status == status)
    if cliente_id is not None:
        consulta = consulta.where(Pedido.cliente_id == cliente_id)
    if unidade_id is not None:
        consulta = consulta.where(Pedido.unidade_id == unidade_id)

    total = db.scalar(select(func.count()).select_from(consulta.subquery()))
    pedidos = db.scalars(
        consulta
        .options(selectinload(Pedido.unidade), selectinload(Pedido.itens).selectinload(ItemPedido.produto_unidade))
        .order_by(Pedido.data_hora.desc(), Pedido.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    return pedidos, total


# Pedido fictício das rotas que ainda não usam o banco (pronto, retirada e nova tentativa)
def buscar_por_id(pedido_id: UUID, status_exemplo: StatusPedido = StatusPedido.EM_PREPARO):
    return pedido_exemplo(pedido_id, status_exemplo)
