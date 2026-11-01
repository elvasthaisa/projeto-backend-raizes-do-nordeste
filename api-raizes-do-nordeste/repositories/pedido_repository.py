from typing import Optional
from uuid import UUID, uuid4

from core.enums import CanalPedido, StatusPedido
from repositories.dados_exemplo import pedido_exemplo


def buscar_por_id(pedido_id: UUID, status_exemplo: StatusPedido = StatusPedido.EM_PREPARO):
    # Com o banco, o status vem do registro e o parâmetro status_exemplo sai
    return pedido_exemplo(pedido_id, status_exemplo)

def listar(canal: Optional[CanalPedido], status: Optional[StatusPedido]):
    # Com o banco, os filtros e a paginação viram parte da consulta
    pedidos = [pedido_exemplo(uuid4())]
    if canal:
        pedidos = [p for p in pedidos if p["canalPedido"] == canal]
    if status:
        pedidos = [p for p in pedidos if p["status"] == status]
    return pedidos
