# Dados fictícios até existir o banco. Só os repositories leem daqui.

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import bcrypt

from core.enums import CanalPedido, ResultadoPagamento, StatusPedido

UNIDADE_RECIFE = UUID("3f2b8c1e-1a2b-4c3d-8e9f-0a1b2c3d4e5f")
UNIDADE_SAO_PAULO = UUID("4a3c9d2f-2b3c-4d4e-9f0a-1b2c3d4e5f60")
UNIDADE_FORTALEZA = UUID("5b4d0e3a-3c4d-4e5f-a01b-2c3d4e5f6071")

UNIDADES = {
    UNIDADE_RECIFE: {"nome": "Recife", "endereco": "Av. Boa Viagem, 1000", "cidade": "Recife", "uf": "PE"},
    UNIDADE_SAO_PAULO: {"nome": "São Paulo", "endereco": "Rua Augusta, 500", "cidade": "São Paulo", "uf": "SP"},
    UNIDADE_FORTALEZA: {"nome": "Fortaleza", "endereco": "Av. Beira Mar, 2000", "cidade": "Fortaleza", "uf": "CE"},
}

# Produto do cardápio de Recife usado nos exemplos
PRODUTO_CUSCUZ_RECIFE = UUID("7c9e6679-7425-40de-944b-e07fc1f90ae7")

# Cardápio por unidade: só produtos ativos, na temporada e com estoque; preço de cada unidade
CARDAPIOS = {
    UNIDADE_RECIFE: [
        {"id": PRODUTO_CUSCUZ_RECIFE, "nome": "Cuscuz com charque", "descricao": "Cuscuz de milho com charque acebolada", "categoria": "PRATO_PRINCIPAL", "preco": Decimal("15.00")},
        {"id": UUID("8d0f7780-8536-41ef-a55c-f18ad2e01bf8"), "nome": "Tapioca de queijo coalho", "descricao": None, "categoria": "LANCHE", "preco": Decimal("12.00")},
        {"id": UUID("9e1a8891-9647-42f0-b66d-0a9be3f12c09"), "nome": "Suco de caju", "descricao": "Copo de 400 ml", "categoria": "BEBIDA", "preco": Decimal("8.00")},
        {"id": UUID("af2b99a2-a758-4301-877e-1bacf4023d1a"), "nome": "Cartola", "descricao": "Banana, queijo coalho, açúcar e canela", "categoria": "SOBREMESA", "preco": Decimal("10.00")},
        {"id": UUID("b0000000-0000-4000-8000-000000000005"), "nome": "Bolo de rolo", "descricao": "Fatia, com recheio de goiabada", "categoria": "SOBREMESA", "preco": Decimal("9.00")},
        {"id": UUID("b0000000-0000-4000-8000-000000000006"), "nome": "Bolo de noiva", "descricao": "Fatia, bolo de ameixa com vinho moscatel e frutas cristalizadas, com cobertura de açúcar", "categoria": "SOBREMESA", "preco": Decimal("11.00")},
    ],
    UNIDADE_SAO_PAULO: [
        {"id": UUID("b1000000-0000-4000-8000-000000000001"), "nome": "Cuscuz com charque", "descricao": "Cuscuz de milho com charque acebolada", "categoria": "PRATO_PRINCIPAL", "preco": Decimal("18.00")},
        {"id": UUID("b1000000-0000-4000-8000-000000000002"), "nome": "Tapioca de queijo coalho", "descricao": None, "categoria": "LANCHE", "preco": Decimal("14.00")},
        {"id": UUID("b1000000-0000-4000-8000-000000000003"), "nome": "Suco de caju", "descricao": "Copo de 400 ml", "categoria": "BEBIDA", "preco": Decimal("10.00")},
        {"id": UUID("b1000000-0000-4000-8000-000000000004"), "nome": "Cuscuz paulista", "descricao": "Cuscuz de farinha de milho com sardinha, ovo e legumes", "categoria": "PRATO_PRINCIPAL", "preco": Decimal("20.00")},
    ],
    UNIDADE_FORTALEZA: [
        {"id": UUID("b2000000-0000-4000-8000-000000000001"), "nome": "Baião de dois", "descricao": "Arroz, feijão verde, queijo coalho e nata", "categoria": "PRATO_PRINCIPAL", "preco": Decimal("22.00")},
        {"id": UUID("b2000000-0000-4000-8000-000000000002"), "nome": "Tapioca de queijo coalho", "descricao": None, "categoria": "LANCHE", "preco": Decimal("10.00")},
        {"id": UUID("b2000000-0000-4000-8000-000000000003"), "nome": "Suco de cajá", "descricao": "Copo de 400 ml", "categoria": "BEBIDA", "preco": Decimal("7.00")},
        {"id": UUID("b2000000-0000-4000-8000-000000000004"), "nome": "Cartola", "descricao": "Banana, queijo coalho, açúcar e canela", "categoria": "SOBREMESA", "preco": Decimal("9.00")},
    ],
}

# Mesma senha para todos ("senha123"), só para desenvolvimento
SENHA_HASH = bcrypt.hashpw(b"senha123", bcrypt.gensalt()).decode()

USUARIOS = [
    {"id": UUID("a1b2c3d4-0001-4000-8000-000000000001"), "nome": "Maria Cliente", "email": "cliente@raizes.com", "perfil": "CLIENTE", "unidadeId": None},
    {"id": UUID("a1b2c3d4-0002-4000-8000-000000000002"), "nome": "Admin", "email": "admin@raizes.com", "perfil": "ADMIN", "unidadeId": None},

    {"id": UUID("a1b2c3d4-0003-4000-8000-000000000003"), "nome": "João Atendente", "email": "atendente.recife@raizes.com", "perfil": "ATENDENTE", "unidadeId": UNIDADE_RECIFE},
    {"id": UUID("a1b2c3d4-0004-4000-8000-000000000004"), "nome": "Ana Cozinha", "email": "cozinha.recife@raizes.com", "perfil": "COZINHA", "unidadeId": UNIDADE_RECIFE},
    {"id": UUID("a1b2c3d4-0005-4000-8000-000000000005"), "nome": "Carlos Gerente", "email": "gerente.recife@raizes.com", "perfil": "GERENTE", "unidadeId": UNIDADE_RECIFE},
    {"id": UUID("a1b2c3d4-0006-4000-8000-000000000006"), "nome": "Totem Recife 1", "email": "totem.recife@raizes.com", "perfil": "TOTEM", "unidadeId": UNIDADE_RECIFE},

    {"id": UUID("a1b2c3d4-0007-4000-8000-000000000007"), "nome": "Paula Atendente", "email": "atendente.saopaulo@raizes.com", "perfil": "ATENDENTE", "unidadeId": UNIDADE_SAO_PAULO},
    {"id": UUID("a1b2c3d4-0008-4000-8000-000000000008"), "nome": "Rafael Cozinha", "email": "cozinha.saopaulo@raizes.com", "perfil": "COZINHA", "unidadeId": UNIDADE_SAO_PAULO},
    {"id": UUID("a1b2c3d4-0009-4000-8000-000000000009"), "nome": "Beatriz Gerente", "email": "gerente.saopaulo@raizes.com", "perfil": "GERENTE", "unidadeId": UNIDADE_SAO_PAULO},
    {"id": UUID("a1b2c3d4-0010-4000-8000-000000000010"), "nome": "Totem São Paulo 1", "email": "totem.saopaulo@raizes.com", "perfil": "TOTEM", "unidadeId": UNIDADE_SAO_PAULO},

    {"id": UUID("a1b2c3d4-0011-4000-8000-000000000011"), "nome": "Francisco Atendente", "email": "atendente.fortaleza@raizes.com", "perfil": "ATENDENTE", "unidadeId": UNIDADE_FORTALEZA},
    {"id": UUID("a1b2c3d4-0012-4000-8000-000000000012"), "nome": "Luiza Cozinha", "email": "cozinha.fortaleza@raizes.com", "perfil": "COZINHA", "unidadeId": UNIDADE_FORTALEZA},
    {"id": UUID("a1b2c3d4-0013-4000-8000-000000000013"), "nome": "Antônio Gerente", "email": "gerente.fortaleza@raizes.com", "perfil": "GERENTE", "unidadeId": UNIDADE_FORTALEZA},
    {"id": UUID("a1b2c3d4-0014-4000-8000-000000000014"), "nome": "Totem Fortaleza 1", "email": "totem.fortaleza@raizes.com", "perfil": "TOTEM", "unidadeId": UNIDADE_FORTALEZA},
]
for usuario in USUARIOS:
    usuario["senhaHash"] = SENHA_HASH
    usuario["ativo"] = True


# Pedido fictício: o status é escolhido por quem chama, para cada rota simular o caso de sucesso
def pedido_exemplo(pedido_id: UUID, status: StatusPedido = StatusPedido.EM_PREPARO) -> dict:
    return {
        "id": pedido_id,
        "status": status,
        "canalPedido": CanalPedido.APP,
        "unidade": {"id": UNIDADE_RECIFE, "nome": UNIDADES[UNIDADE_RECIFE]["nome"]},
        "dataHora": datetime.now(timezone.utc),
        "itens": [
            {"produtoUnidadeId": PRODUTO_CUSCUZ_RECIFE, "nomeProduto": "Cuscuz com charque", "precoUnitario": Decimal("15.00"), "quantidade": 2},
            {"produtoUnidadeId": uuid4(), "nomeProduto": "Suco de caju", "precoUnitario": Decimal("8.00"), "quantidade": 1},
        ],
        "total": Decimal("38.00"),
        "senha": 42 if status in (StatusPedido.EM_PREPARO, StatusPedido.PRONTO, StatusPedido.ENTREGUE) else None,
    }

# Tentativas fictícias: uma recusada
def pagamentos_exemplo() -> list:
    return [
        {
            "id": uuid4(),
            "valor": Decimal("38.00"),
            "resultado": ResultadoPagamento.RECUSADO,
            "motivoRecusa": "Pagamento recusado pela operadora.",
            "dataHoraResposta": datetime.now(timezone.utc),
        }
    ]
