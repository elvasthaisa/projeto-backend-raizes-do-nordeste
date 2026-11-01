from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query

from core.enums import CanalPedido, Perfil, StatusPedido
from core.erros import ErroResponse
from core.seguranca import exigir_perfis, usuario_atual
from schemas.auth import UsuarioLogado
from schemas.pagamento import EXEMPLOS_TENTATIVA, NovaTentativaRequest, PagamentoResponse
from schemas.pedido import EXEMPLOS_PEDIDO, CancelamentoRequest, PaginaPedidos, PedidoRequest, PedidoResponse
from services import pagamento_service, pedido_service

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.post(
    "",
    summary="Registrar um novo pedido",
    response_model=PedidoResponse,
    status_code=201,
    responses={
        401: {"model": ErroResponse, "description": "NAO_AUTENTICADO"},
        403: {"model": ErroResponse, "description": "ACESSO_NEGADO ou CANAL_NAO_PERMITIDO"},
        404: {"model": ErroResponse, "description": "NAO_ENCONTRADO (unidade ou produto)"},
        409: {"model": ErroResponse, "description": "PRODUTO_INDISPONIVEL ou ESTOQUE_INSUFICIENTE"},
        422: {"model": ErroResponse, "description": "VALIDACAO"},
    },
)
def registrar_pedido(
    pedido: Annotated[PedidoRequest, Body(openapi_examples=EXEMPLOS_PEDIDO)],
    usuario: Annotated[UsuarioLogado, Depends(exigir_perfis(Perfil.CLIENTE, Perfil.ATENDENTE, Perfil.TOTEM))],
):
    return pedido_service.registrar_pedido(pedido, usuario)

@router.get(
    "",
    summary="Listar pedidos",
    response_model=PaginaPedidos,
    dependencies=[Depends(exigir_perfis(Perfil.CLIENTE, Perfil.ATENDENTE, Perfil.COZINHA, Perfil.GERENTE, Perfil.ADMIN))],
    responses={
        401: {"model": ErroResponse, "description": "NAO_AUTENTICADO"},
        403: {"model": ErroResponse, "description": "ACESSO_NEGADO"},
        422: {"model": ErroResponse, "description": "VALIDACAO"},
    },
)
def listar_pedidos(
    canalPedido: Optional[CanalPedido] = None,
    status: Optional[StatusPedido] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return pedido_service.listar_pedidos(canalPedido, status, page, limit)

@router.get(
    "/{id}",
    summary="Consultar um pedido",
    response_model=PedidoResponse,
    dependencies=[Depends(usuario_atual)], # todos os perfis; a checagem do dono/unidade entra com o banco
    responses={
        401: {"model": ErroResponse, "description": "NAO_AUTENTICADO"},
        403: {"model": ErroResponse, "description": "ACESSO_NEGADO (pedido de outro cliente ou de outra unidade)"},
        404: {"model": ErroResponse, "description": "NAO_ENCONTRADO"},
        422: {"model": ErroResponse, "description": "VALIDACAO (id não é um uuid)"},
    },
)
def consultar_pedido(id: UUID):
    return pedido_service.consultar_pedido(id)

@router.get(
    "/{id}/pagamentos",
    summary="Listar as tentativas de pagamento do pedido",
    response_model=List[PagamentoResponse],
    dependencies=[Depends(usuario_atual)], # mesmos perfis do GET /pedidos/{id}
    responses={
        401: {"model": ErroResponse, "description": "NAO_AUTENTICADO"},
        403: {"model": ErroResponse, "description": "ACESSO_NEGADO (pedido de outro cliente ou de outra unidade)"},
        404: {"model": ErroResponse, "description": "NAO_ENCONTRADO"},
        422: {"model": ErroResponse, "description": "VALIDACAO (id não é um uuid)"},
    },
)
def listar_pagamentos(id: UUID):
    return pagamento_service.listar_pagamentos(id)

@router.post(
    "/{id}/pagamentos",
    summary="Pedir nova tentativa de pagamento",
    response_model=PagamentoResponse,
    status_code=201,
    dependencies=[Depends(exigir_perfis(Perfil.CLIENTE, Perfil.ATENDENTE, Perfil.TOTEM))],
    responses={
        401: {"model": ErroResponse, "description": "NAO_AUTENTICADO"},
        403: {"model": ErroResponse, "description": "ACESSO_NEGADO"},
        404: {"model": ErroResponse, "description": "NAO_ENCONTRADO"},
        409: {"model": ErroResponse, "description": "TRANSICAO_INVALIDA ou LIMITE_TENTATIVAS"},
        422: {"model": ErroResponse, "description": "VALIDACAO"},
    },
)
def nova_tentativa(id: UUID, tentativa: Annotated[NovaTentativaRequest, Body(openapi_examples=EXEMPLOS_TENTATIVA)]):
    return pagamento_service.nova_tentativa(id, tentativa.cenarioMock)


# Mudanças de status: uma rota por ação

@router.post(
    "/{id}/pronto",
    summary="Marcar pedido como pronto",
    response_model=PedidoResponse,
    dependencies=[Depends(exigir_perfis(Perfil.COZINHA))],
    responses={
        401: {"model": ErroResponse, "description": "NAO_AUTENTICADO"},
        403: {"model": ErroResponse, "description": "ACESSO_NEGADO"},
        404: {"model": ErroResponse, "description": "NAO_ENCONTRADO"},
        409: {"model": ErroResponse, "description": "TRANSICAO_INVALIDA (pedido não está EM_PREPARO)"},
        422: {"model": ErroResponse, "description": "VALIDACAO"},
    },
)
def marcar_pronto(id: UUID):
    return pedido_service.marcar_pronto(id)

@router.post(
    "/{id}/retirada",
    summary="Confirmar a retirada do pedido",
    response_model=PedidoResponse,
    responses={
        401: {"model": ErroResponse, "description": "NAO_AUTENTICADO"},
        403: {"model": ErroResponse, "description": "ACESSO_NEGADO (perfil não confirma retiradas deste canal)"},
        404: {"model": ErroResponse, "description": "NAO_ENCONTRADO"},
        409: {"model": ErroResponse, "description": "TRANSICAO_INVALIDA (pedido não está PRONTO)"},
        422: {"model": ErroResponse, "description": "VALIDACAO"},
    },
)
def confirmar_retirada(id: UUID, usuario: Annotated[UsuarioLogado, Depends(exigir_perfis(Perfil.CLIENTE, Perfil.ATENDENTE))]):
    return pedido_service.confirmar_retirada(id, usuario)

@router.post(
    "/{id}/cancelamento",
    summary="Cancelar pedido",
    response_model=PedidoResponse,
    dependencies=[Depends(exigir_perfis(Perfil.CLIENTE, Perfil.ATENDENTE, Perfil.GERENTE))],
    responses={
        401: {"model": ErroResponse, "description": "NAO_AUTENTICADO"},
        403: {"model": ErroResponse, "description": "ACESSO_NEGADO"},
        404: {"model": ErroResponse, "description": "NAO_ENCONTRADO"},
        409: {"model": ErroResponse, "description": "TRANSICAO_INVALIDA (pedido já em preparo, pronto, entregue ou cancelado)"},
        422: {"model": ErroResponse, "description": "VALIDACAO (motivo ausente)"},
    },
)
def cancelar_pedido(id: UUID, cancelamento: CancelamentoRequest):
    return pedido_service.cancelar_pedido(id, cancelamento.motivo)
