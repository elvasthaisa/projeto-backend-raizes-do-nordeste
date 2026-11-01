from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Annotated, List, Optional
from uuid import UUID, uuid4

import bcrypt
from fastapi import Body, Depends, FastAPI, Query
from pydantic import BaseModel, ConfigDict, Field

from auth import Perfil, UsuarioLogado, exigir_perfis, router as auth_router, usuario_atual
from dados_exemplo import CARDAPIOS, PRODUTO_CUSCUZ_RECIFE, UNIDADE_RECIFE, UNIDADES, USUARIOS, buscar_usuario_por_email
from erros import DetalheErro, ErroApi, ErroResponse, registrar_tratadores_de_erro

DESCRICAO = """
API de back-end da rede de restaurantes Raízes do Nordeste.

Cobre o fluxo de pedido de ponta a ponta: o cliente escolhe a unidade e os itens do cardápio, o pedido é registrado
com o canal de origem (`APP`, `WEB`, `PICKUP`, `TOTEM` ou `BALCAO`), o pagamento é processado por um gateway simulado
e o pedido segue até a entrega, passando por preparo e retirada.

O acesso é controlado por login (JWT) e perfis: cliente, atendente, cozinha, gerente, administrador e totem.

**Como testar:**
1. Faça login em `POST /auth/login` (escolha um usuário na lista de exemplos; senha `senha123`).
   Para testar com um cliente novo, cadastre-o antes em `POST /usuarios`.
2. Copie o `accessToken` da resposta.
3. Clique em **Authorize** (cadeado no topo), cole o token e confirme.
4. Use as rotas. Para trocar de perfil, repita os passos 1 a 3. Se recarregar a página, faça o Authorize de novo.

| Usuário | Perfil | Unidade |
|---|---|---|
| cliente@raizes.com | CLIENTE | escolhe no pedido |
| admin@raizes.com | ADMIN | todas |
| atendente.`unidade`@raizes.com | ATENDENTE | a da conta |
| cozinha.`unidade`@raizes.com | COZINHA | a da conta |
| gerente.`unidade`@raizes.com | GERENTE | a da conta |
| totem.`unidade`@raizes.com | TOTEM | a da conta |

Onde `unidade` é `recife`, `saopaulo` ou `fortaleza`. Exemplo: `atendente.recife@raizes.com`.
Os ids das unidades estão em `GET /unidades`, e os dos produtos, em `GET /unidades/{id}/cardapio`.
"""

app = FastAPI(
    title="API Raízes do Nordeste",
    description=DESCRICAO,
    version="1.0.0")

registrar_tratadores_de_erro(app)
app.include_router(auth_router)


# ENUMs

class CanalPedido(str, Enum):
    APP = "APP"
    BALCAO = "BALCAO"
    TOTEM = "TOTEM"
    WEB = "WEB"
    PICKUP = "PICKUP"

class StatusPedido(str, Enum):
    AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
    PAGAMENTO_RECUSADO = "PAGAMENTO_RECUSADO"
    PAGAMENTO_EXPIRADO = "PAGAMENTO_EXPIRADO"
    EM_PREPARO = "EM_PREPARO"
    PRONTO = "PRONTO"
    ENTREGUE = "ENTREGUE"
    PEDIDO_CANCELADO = "PEDIDO_CANCELADO"

# Resposta que o gateway mock vai simular
class CenarioMock(str, Enum):
    APROVAR = "APROVAR"
    RECUSAR = "RECUSAR"
    SEM_RESPOSTA = "SEM_RESPOSTA"

class ResultadoPagamento(str, Enum):
    PENDENTE = "PENDENTE"
    APROVADO = "APROVADO"
    RECUSADO = "RECUSADO"
    EXPIRADO = "EXPIRADO"

class Categoria(str, Enum):
    PRATO_PRINCIPAL = "PRATO_PRINCIPAL"
    LANCHE = "LANCHE"
    BEBIDA = "BEBIDA"
    SOBREMESA = "SOBREMESA"


# Request do POST /pedidos
# Não recebe clienteId (vem do token), formaPagamento nem preço 

class ItemPedidoRequest(BaseModel):
    produtoUnidadeId: UUID # uuid do produto no cardápio da unidade
    quantidade: int = Field(gt=0)
    observacao: Optional[str] = Field(default=None, max_length=300)

class PedidoRequest(BaseModel):
    canalPedido: CanalPedido
    unidadeId: Optional[UUID] = None # obrigatório para CLIENTE; ATENDENTE e TOTEM usam a unidade da conta
    itens: List[ItemPedidoRequest] = Field(min_length=1)
    cenarioMock: CenarioMock = CenarioMock.APROVAR

# Exemplos do Swagger, um por perfil que cria pedidos
ITEM_EXEMPLO = {"produtoUnidadeId": str(PRODUTO_CUSCUZ_RECIFE), "quantidade": 2, "observacao": "Sem cebola"}
EXEMPLOS_PEDIDO = {
    "cliente": {
        "summary": "Cliente no app (login cliente@raizes.com)",
        "value": {"canalPedido": "APP", "unidadeId": str(UNIDADE_RECIFE), "itens": [ITEM_EXEMPLO], "cenarioMock": "APROVAR"},
    },
    "atendente": {
        "summary": "Atendente no balcão (login atendente.recife@raizes.com)",
        "value": {"canalPedido": "BALCAO", "itens": [ITEM_EXEMPLO]},
    },
    "totem": {
        "summary": "Totem, cliente anônimo (login totem.recife@raizes.com)",
        "value": {"canalPedido": "TOTEM", "itens": [ITEM_EXEMPLO]},
    },
}

# Response dos pedidos

class UnidadeResumo(BaseModel):
    id: UUID
    nome: str

class ItemPedidoResponse(BaseModel):
    produtoUnidadeId: UUID
    nomeProduto: str
    precoUnitario: Decimal = Field(max_digits=10, decimal_places=2) # mesmo limite do numeric(10,2) do banco
    quantidade: int
    observacao: Optional[str] = None

class PedidoResponse(BaseModel):
    id: UUID # o valor é o uuid; o id interno não sai da API
    status: StatusPedido
    canalPedido: CanalPedido
    unidade: UnidadeResumo
    dataHora: datetime
    itens: List[ItemPedidoResponse]
    total: Decimal # calculado, não é gravado
    senha: Optional[int] = None # vazia até o pagamento ser aprovado

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "id": "b8340e16-4ca9-4144-a1e1-155512ea2ce7",
        "status": "AGUARDANDO_PAGAMENTO",
        "canalPedido": "APP",
        "unidade": {"id": str(UNIDADE_RECIFE), "nome": "Recife"},
        "dataHora": "2026-10-31T14:30:00Z",
        "itens": [{"produtoUnidadeId": str(PRODUTO_CUSCUZ_RECIFE), "nomeProduto": "Cuscuz com charque", "precoUnitario": "15.00", "quantidade": 2, "observacao": "Sem cebola"}],
        "total": "30.00",
        "senha": None,
    }]})

class PaginaPedidos(BaseModel):
    pedidos: List[PedidoResponse]
    page: int
    limit: int
    total: int # total de pedidos encontrados com os filtros


# Pagamentos (UC3)

class NovaTentativaRequest(BaseModel):
    cenarioMock: CenarioMock = CenarioMock.APROVAR

EXEMPLOS_TENTATIVA = {
    "aprovar": {"summary": "Gateway aprova", "value": {"cenarioMock": "APROVAR"}},
    "recusar": {"summary": "Gateway recusa", "value": {"cenarioMock": "RECUSAR"}},
    "sem_resposta": {"summary": "Gateway não responde (expira)", "value": {"cenarioMock": "SEM_RESPOSTA"}},
}

class PagamentoResponse(BaseModel):
    id: UUID
    valor: Decimal = Field(max_digits=10, decimal_places=2)
    resultado: ResultadoPagamento
    motivoRecusa: Optional[str] = None
    dataHoraResposta: Optional[datetime] = None # vazia enquanto PENDENTE

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "id": "5d1e7a3c-9b2f-4c8e-a1d6-3f0b9c2e7a41",
        "valor": "30.00",
        "resultado": "RECUSADO",
        "motivoRecusa": "Pagamento recusado pela operadora.",
        "dataHoraResposta": "2026-10-31T14:30:05Z",
    }]})


# Cancelamento (UC4)

class CancelamentoRequest(BaseModel):
    motivo: str = Field(min_length=1, max_length=300)

    model_config = ConfigDict(json_schema_extra={"examples": [{"motivo": "Cliente desistiu do pedido."}]})


# Cadastro de cliente: só nome, e-mail e senha (minimização - RNF03)

class CadastroClienteRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    senha: str = Field(min_length=8, max_length=72) # 72 é o limite do bcrypt

    model_config = ConfigDict(json_schema_extra={"examples": [{"nome": "José da Silva", "email": "jose@email.com", "senha": "minhasenha123"}]})

class UsuarioResponse(BaseModel):
    id: UUID
    nome: str
    email: str
    perfil: Perfil # nunca devolve a senha nem o hash


# Unidades e cardápio

class UnidadeResponse(BaseModel):
    id: UUID
    nome: str
    endereco: str
    cidade: str
    uf: str

class ItemCardapioResponse(BaseModel):
    id: UUID # uuid do ProdutoUnidade: é o que vai em produtoUnidadeId no pedido
    nome: str
    descricao: Optional[str] = None
    categoria: Categoria
    preco: Decimal = Field(max_digits=10, decimal_places=2)


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


def validar_transicao_pedido(pedido: PedidoResponse, status_permitidos, acao: str):
    if pedido.status not in status_permitidos:
        raise ErroApi(409, "TRANSICAO_INVALIDA", f"Não é possível {acao}: o pedido está em {pedido.status.value}.")


@app.post(
    "/pedidos",
    summary="Registrar um novo pedido",
    tags=["Pedidos"],
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
    if pedido.canalPedido not in CANAIS_POR_PERFIL[usuario.perfil]:
        raise ErroApi(403, "CANAL_NAO_PERMITIDO", f"O perfil {usuario.perfil.value} não pode criar pedidos no canal {pedido.canalPedido.value}.")

    # Unidade do pedido: o cliente escolhe; atendente e totem usam a da conta
    if usuario.perfil == Perfil.CLIENTE:
        if pedido.unidadeId is None:
            raise ErroApi(422, "VALIDACAO", "Um ou mais campos são inválidos.", [DetalheErro(field="unidadeId", issue="campo obrigatório")])
        unidade_id = pedido.unidadeId
    else:
        if pedido.unidadeId and pedido.unidadeId != usuario.unidadeId:
            raise ErroApi(403, "ACESSO_NEGADO", "A unidade informada é diferente da unidade da conta.")
        unidade_id = usuario.unidadeId

    if unidade_id not in UNIDADES:
        raise ErroApi(404, "NAO_ENCONTRADO", "Unidade não encontrada.", [DetalheErro(field="unidadeId", issue="não existe")])

    # Cada item precisa estar no cardápio da unidade do pedido; nome e preço vêm do cardápio
    cardapio = {produto["id"]: produto for produto in CARDAPIOS[unidade_id]}
    itens = []
    for posicao, item in enumerate(pedido.itens):
        produto = cardapio.get(item.produtoUnidadeId)
        if produto is None:
            raise ErroApi(404, "NAO_ENCONTRADO", "Produto não encontrado no cardápio desta unidade.",
                          [DetalheErro(field=f"itens.{posicao}.produtoUnidadeId", issue="não existe nesta unidade")])
        itens.append(ItemPedidoResponse(
            produtoUnidadeId=item.produtoUnidadeId,
            nomeProduto=produto["nome"],
            precoUnitario=produto["preco"],
            quantidade=item.quantidade,
            observacao=item.observacao,
        ))

    return PedidoResponse(
        id=uuid4(),
        status=StatusPedido.AGUARDANDO_PAGAMENTO,
        canalPedido=pedido.canalPedido,
        unidade=UnidadeResumo(id=unidade_id, nome=UNIDADES[unidade_id]["nome"]),
        dataHora=datetime.now(timezone.utc),
        itens=itens,
        total=sum(item.precoUnitario * item.quantidade for item in itens),
        senha=None,
    )

# Pedido mockado, até existir o banco
def pedido_exemplo(pedido_id: UUID, status: StatusPedido = StatusPedido.EM_PREPARO) -> PedidoResponse:
    return PedidoResponse(
        id=pedido_id,
        status=status,
        canalPedido=CanalPedido.APP,
        unidade=UnidadeResumo(id=UNIDADE_RECIFE, nome=UNIDADES[UNIDADE_RECIFE]["nome"]),
        dataHora=datetime.now(timezone.utc),
        itens=[
            ItemPedidoResponse(produtoUnidadeId=PRODUTO_CUSCUZ_RECIFE, nomeProduto="Cuscuz com charque", precoUnitario=Decimal("15.00"), quantidade=2),
            ItemPedidoResponse(produtoUnidadeId=uuid4(), nomeProduto="Suco de caju", precoUnitario=Decimal("8.00"), quantidade=1),
        ],
        total=Decimal("38.00"),
        senha=42 if status in (StatusPedido.EM_PREPARO, StatusPedido.PRONTO, StatusPedido.ENTREGUE) else None,
    )

# Tentativas fictícias: uma recusada
def pagamentos_exemplo() -> List[PagamentoResponse]:
    return [
        PagamentoResponse(
            id=uuid4(),
            valor=Decimal("38.00"),
            resultado=ResultadoPagamento.RECUSADO,
            motivoRecusa="Pagamento recusado pela operadora.",
            dataHoraResposta=datetime.now(timezone.utc),
        )
    ]

@app.get(
    "/pedidos",
    summary="Listar pedidos",
    tags=["Pedidos"],
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
    # Dados de exemplo: a consulta no banco com filtros e paginação entra depois
    # (CLIENTE vê só os seus pedidos; funcionários, os da sua unidade; ADMIN, todos)
    pedidos = [pedido_exemplo(uuid4())]
    if canalPedido:
        pedidos = [p for p in pedidos if p.canalPedido == canalPedido]
    if status:
        pedidos = [p for p in pedidos if p.status == status]
    return PaginaPedidos(pedidos=pedidos, page=page, limit=limit, total=len(pedidos))

@app.get(
    "/pedidos/{id}",
    summary="Consultar um pedido",
    tags=["Pedidos"],
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
    return pedido_exemplo(id)

@app.get(
    "/pedidos/{id}/pagamentos",
    summary="Listar as tentativas de pagamento do pedido",
    tags=["Pedidos"],
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
    return pagamentos_exemplo()

@app.post(
    "/pedidos/{id}/pagamentos",
    summary="Pedir nova tentativa de pagamento",
    tags=["Pedidos"],
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
    # Dados de exemplo: pedido recusado na 1ª tentativa
    # Na próxima etapa: busca no banco, gravação da tentativa e chamada ao gateway mock com o cenarioMock
    pedido = pedido_exemplo(id, StatusPedido.PAGAMENTO_RECUSADO)
    tentativas = pagamentos_exemplo()

    # Só pedido recusado ou expirado pode tentar de novo, até 3 tentativas (UC3 FA3)
    validar_transicao_pedido(pedido, (StatusPedido.PAGAMENTO_RECUSADO, StatusPedido.PAGAMENTO_EXPIRADO), "pedir nova tentativa de pagamento")
    if len(tentativas) >= 3:
        raise ErroApi(409, "LIMITE_TENTATIVAS", "O pedido já atingiu o limite de 3 tentativas de pagamento.")

    # A tentativa nasce PENDENTE; o resultado chega depois, pelo gateway
    return PagamentoResponse(id=uuid4(), valor=pedido.total, resultado=ResultadoPagamento.PENDENTE)


# Mudanças de status: uma rota por ação

@app.post(
    "/pedidos/{id}/pronto",
    summary="Marcar pedido como pronto",
    tags=["Pedidos"],
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
    # Dados de exemplo: pedido em preparo. Na próxima etapa: busca, gravação do status e do histórico
    pedido = pedido_exemplo(id, StatusPedido.EM_PREPARO)
    validar_transicao_pedido(pedido, (StatusPedido.EM_PREPARO,), "marcar como pronto")
    pedido.status = StatusPedido.PRONTO
    return pedido

@app.post(
    "/pedidos/{id}/retirada",
    summary="Confirmar a retirada do pedido",
    tags=["Pedidos"],
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
    # Dados de exemplo: pedido do app, pronto. Na próxima etapa: busca, gravação do status e do histórico
    pedido = pedido_exemplo(id, StatusPedido.PRONTO)
    if pedido.canalPedido not in CANAIS_DA_RETIRADA[usuario.perfil]:
        raise ErroApi(403, "ACESSO_NEGADO", f"A retirada de pedidos do canal {pedido.canalPedido.value} não é confirmada pelo perfil {usuario.perfil.value}.")
    validar_transicao_pedido(pedido, (StatusPedido.PRONTO,), "confirmar a retirada")
    pedido.status = StatusPedido.ENTREGUE
    return pedido

@app.post(
    "/pedidos/{id}/cancelamento",
    summary="Cancelar pedido",
    tags=["Pedidos"],
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
    # Dados de exemplo: pedido aguardando pagamento
    # Na próxima etapa: busca, gravação do status e do histórico com o motivo, devolução do estoque
    pedido = pedido_exemplo(id, StatusPedido.AGUARDANDO_PAGAMENTO)
    validar_transicao_pedido(pedido, STATUS_CANCELAVEIS, "cancelar")
    pedido.status = StatusPedido.PEDIDO_CANCELADO
    return pedido


# Rotas públicas (sem login)

@app.post(
    "/usuarios",
    summary="Cadastrar cliente",
    tags=["Usuários"],
    response_model=UsuarioResponse,
    status_code=201,
    responses={
        409: {"model": ErroResponse, "description": "EMAIL_JA_CADASTRADO"},
        422: {"model": ErroResponse, "description": "VALIDACAO"},
    },
)
def cadastrar_cliente(dados: CadastroClienteRequest):
    if buscar_usuario_por_email(dados.email):
        raise ErroApi(409, "EMAIL_JA_CADASTRADO", "Já existe uma conta com este e-mail.")

    usuario = {
        "id": uuid4(),
        "nome": dados.nome,
        "email": dados.email.lower(),
        "perfil": "CLIENTE", # cadastro público é só de cliente; funcionários e totens vêm do seed
        "unidadeId": None,
        "senhaHash": bcrypt.hashpw(dados.senha.encode(), bcrypt.gensalt()).decode(),
        "ativo": True,
    }
    USUARIOS.append(usuario) # Próxima etapa: gravar no banco
    return UsuarioResponse(id=usuario["id"], nome=usuario["nome"], email=usuario["email"], perfil=Perfil.CLIENTE)

@app.get("/unidades", summary="Listar unidades", tags=["Unidades"], response_model=List[UnidadeResponse])
def listar_unidades():
    return [UnidadeResponse(id=id, **dados) for id, dados in UNIDADES.items()]

@app.get(
    "/unidades/{id}/cardapio",
    summary="Consultar o cardápio da unidade",
    tags=["Unidades"],
    response_model=List[ItemCardapioResponse],
    responses={
        404: {"model": ErroResponse, "description": "NAO_ENCONTRADO"},
        422: {"model": ErroResponse, "description": "VALIDACAO (id não é um uuid)"},
    },
)
def consultar_cardapio(id: UUID):
    if id not in UNIDADES:
        raise ErroApi(404, "NAO_ENCONTRADO", "Unidade não encontrada.")
    return CARDAPIOS.get(id, [])
