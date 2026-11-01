# Dados iniciais para desenvolvimento e testes: unidades, catálogo, cardápios e usuários.
# Uso (na pasta da API, com o banco no ar e as migrations aplicadas): python seed.py
# Os uuids são fixos porque a coleção do Postman usa alguns deles.

from decimal import Decimal
from uuid import UUID

import bcrypt
from sqlalchemy import select

from core.database import SessionLocal
from core.enums import Categoria, Perfil
from models import Produto, ProdutoUnidade, Unidade, Usuario

UNIDADES = {
    "recife": Unidade(uuid=UUID("3f2b8c1e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"), nome="Recife", endereco="Av. Boa Viagem, 1000", cidade="Recife", uf="PE"),
    "saopaulo": Unidade(uuid=UUID("4a3c9d2f-2b3c-4d4e-9f0a-1b2c3d4e5f60"), nome="São Paulo", endereco="Rua Augusta, 500", cidade="São Paulo", uf="SP"),
    "fortaleza": Unidade(uuid=UUID("5b4d0e3a-3c4d-4e5f-a01b-2c3d4e5f6071"), nome="Fortaleza", endereco="Av. Beira Mar, 2000", cidade="Fortaleza", uf="CE"),
}

# Catálogo da rede: cada produto é cadastrado uma vez e vendido pelas unidades
PRODUTOS = {
    "cuscuz": Produto(nome="Cuscuz com charque", descricao="Cuscuz de milho com charque acebolada", categoria=Categoria.PRATO_PRINCIPAL),
    "cuscuz_paulista": Produto(nome="Cuscuz paulista", descricao="Cuscuz de farinha de milho com sardinha, ovo e legumes", categoria=Categoria.PRATO_PRINCIPAL),
    "baiao": Produto(nome="Baião de dois", descricao="Arroz, feijão verde, queijo coalho e nata", categoria=Categoria.PRATO_PRINCIPAL),
    "tapioca": Produto(nome="Tapioca de queijo coalho", categoria=Categoria.PRATO_PRINCIPAL),
    "suco_caju": Produto(nome="Suco de caju", descricao="Copo de 400 ml", categoria=Categoria.BEBIDA),
    "suco_caja": Produto(nome="Suco de cajá", descricao="Copo de 400 ml", categoria=Categoria.BEBIDA),
    "cartola": Produto(nome="Cartola", descricao="Banana, queijo coalho, açúcar e canela", categoria=Categoria.SOBREMESA),
    "bolo_rolo": Produto(nome="Bolo de rolo", descricao="Fatia, com recheio de goiabada", categoria=Categoria.SOBREMESA),
    "bolo_noiva": Produto(nome="Bolo de noiva", descricao="Fatia, bolo de ameixa com vinho moscatel e frutas cristalizadas, com cobertura de açúcar", categoria=Categoria.SOBREMESA),
    "escondidinho": Produto(nome="Escondidinho de charque", descricao="Purê de macaxeira com charque e queijo coalho gratinado", categoria=Categoria.PRATO_PRINCIPAL),
    "carne_de_sol": Produto(nome="Carne de sol com macaxeira", descricao="Carne de sol na manteiga de garrafa com macaxeira cozida", categoria=Categoria.PRATO_PRINCIPAL),
    "tapioca_carne_de_sol": Produto(nome="Tapioca de carne de sol", descricao="Tapioca recheada com carne de sol desfiada e queijo coalho", categoria=Categoria.PRATO_PRINCIPAL),
    "pamonha": Produto(nome="Pamonha", descricao="Pamonha de milho verde cozida na palha", categoria=Categoria.LANCHE),
    "canjica": Produto(nome="Canjica", descricao="Creme de milho verde com leite de coco e canela", categoria=Categoria.LANCHE),
    "empada_camarao": Produto(nome="Empada de camarão", categoria=Categoria.LANCHE),
    "empada_frango": Produto(nome="Empada de frango", categoria=Categoria.LANCHE),
    "agua_coco": Produto(nome="Água de coco", descricao="Copo de 400 ml", categoria=Categoria.BEBIDA),
    "caldo_cana": Produto(nome="Caldo de cana", descricao="Copo de 400 ml", categoria=Categoria.BEBIDA),
    "sao_geraldo": Produto(nome="Refrigerante São Geraldo", descricao="Lata de 350 ml", categoria=Categoria.BEBIDA),
    "coca": Produto(nome="Coca-Cola", descricao="Lata de 350 ml", categoria=Categoria.BEBIDA),
    "cocada": Produto(nome="Cocada", descricao="Cocada de forno", categoria=Categoria.SOBREMESA),
    "curau": Produto(nome="Curau de milho", descricao="Creme de milho verde com leite e canela", categoria=Categoria.SOBREMESA),
}

ESTOQUE_INICIAL = 50

# Cardápio de cada unidade: (unidade, produto, uuid do produto na unidade, preço)
CARDAPIOS = [
    ("recife", "cuscuz", "b0000000-0000-4000-8000-000000000001", "15.00"),
    ("recife", "tapioca", "b0000000-0000-4000-8000-000000000002", "12.00"),
    ("recife", "suco_caju", "b0000000-0000-4000-8000-000000000003", "8.00"),
    ("recife", "cartola", "b0000000-0000-4000-8000-000000000004", "10.00"),
    ("recife", "bolo_rolo", "b0000000-0000-4000-8000-000000000005", "9.00"),
    ("recife", "bolo_noiva", "b0000000-0000-4000-8000-000000000006", "11.00"),
    ("recife", "escondidinho", "b0000000-0000-4000-8000-000000000007", "24.00"),
    ("recife", "tapioca_carne_de_sol", "b0000000-0000-4000-8000-000000000008", "16.00"),
    ("recife", "caldo_cana", "b0000000-0000-4000-8000-000000000009", "7.00"),
    ("recife", "pamonha", "b0000000-0000-4000-8000-000000000010", "8.00"),
    ("recife", "canjica", "b0000000-0000-4000-8000-000000000011", "9.00"),
    ("recife", "cocada", "b0000000-0000-4000-8000-000000000012", "6.00"),
    ("recife", "sao_geraldo", "b0000000-0000-4000-8000-000000000013", "6.00"),
    ("recife", "coca", "b0000000-0000-4000-8000-000000000014", "6.00"),
    ("recife", "empada_camarao", "b0000000-0000-4000-8000-000000000015", "9.00"),
    ("recife", "empada_frango", "b0000000-0000-4000-8000-000000000016", "7.00"),

    ("saopaulo", "cuscuz", "b1000000-0000-4000-8000-000000000001", "18.00"),
    ("saopaulo", "tapioca", "b1000000-0000-4000-8000-000000000002", "14.00"),
    ("saopaulo", "suco_caju", "b1000000-0000-4000-8000-000000000003", "10.00"),
    ("saopaulo", "cuscuz_paulista", "b1000000-0000-4000-8000-000000000004", "20.00"),
    ("saopaulo", "escondidinho", "b1000000-0000-4000-8000-000000000005", "28.00"),
    ("saopaulo", "tapioca_carne_de_sol", "b1000000-0000-4000-8000-000000000006", "19.00"),
    ("saopaulo", "agua_coco", "b1000000-0000-4000-8000-000000000007", "9.00"),
    ("saopaulo", "cocada", "b1000000-0000-4000-8000-000000000008", "8.00"),
    ("saopaulo", "curau", "b1000000-0000-4000-8000-000000000009", "10.00"),
    ("saopaulo", "pamonha", "b1000000-0000-4000-8000-000000000010", "11.00"),
    ("saopaulo", "coca", "b1000000-0000-4000-8000-000000000011", "7.00"),
    ("saopaulo", "empada_camarao", "b1000000-0000-4000-8000-000000000012", "11.00"),
    ("saopaulo", "empada_frango", "b1000000-0000-4000-8000-000000000013", "9.00"),

    ("fortaleza", "baiao", "b2000000-0000-4000-8000-000000000001", "22.00"),
    ("fortaleza", "tapioca", "b2000000-0000-4000-8000-000000000002", "10.00"),
    ("fortaleza", "suco_caja", "b2000000-0000-4000-8000-000000000003", "7.00"),
    ("fortaleza", "cartola", "b2000000-0000-4000-8000-000000000004", "9.00"),
    ("fortaleza", "cuscuz", "b2000000-0000-4000-8000-000000000005", "14.00"),
    ("fortaleza", "carne_de_sol", "b2000000-0000-4000-8000-000000000006", "26.00"),
    ("fortaleza", "agua_coco", "b2000000-0000-4000-8000-000000000007", "6.00"),
    ("fortaleza", "caldo_cana", "b2000000-0000-4000-8000-000000000008", "6.00"),
    ("fortaleza", "cocada", "b2000000-0000-4000-8000-000000000009", "5.00"),
    ("fortaleza", "sao_geraldo", "b2000000-0000-4000-8000-000000000010", "5.00"),
    ("fortaleza", "coca", "b2000000-0000-4000-8000-000000000011", "5.00"),
    ("fortaleza", "empada_camarao", "b2000000-0000-4000-8000-000000000012", "8.00"),
    ("fortaleza", "empada_frango", "b2000000-0000-4000-8000-000000000013", "6.00"),
]

# Itens cadastrados que não aparecem no cardápio agora (regra da D23)
FORA_DA_TEMPORADA = {("saopaulo", "curau"), ("saopaulo", "pamonha")} # em São Paulo, só no São João
DESATIVADOS_PELO_GERENTE = {("recife", "cocada")}

# (uuid, nome, e-mail, perfil, unidade). Cliente e admin não têm unidade
USUARIOS = [
    ("a1b2c3d4-0001-4000-8000-000000000001", "Maria Cliente", "cliente@raizes.com", Perfil.CLIENTE, None),
    ("a1b2c3d4-0002-4000-8000-000000000002", "Admin", "admin@raizes.com", Perfil.ADMIN, None),

    ("a1b2c3d4-0003-4000-8000-000000000003", "João Atendente", "atendente.recife@raizes.com", Perfil.ATENDENTE, "recife"),
    ("a1b2c3d4-0004-4000-8000-000000000004", "Ana Cozinha", "cozinha.recife@raizes.com", Perfil.COZINHA, "recife"),
    ("a1b2c3d4-0005-4000-8000-000000000005", "Carlos Gerente", "gerente.recife@raizes.com", Perfil.GERENTE, "recife"),
    ("a1b2c3d4-0006-4000-8000-000000000006", "Totem Recife 1", "totem.recife@raizes.com", Perfil.TOTEM, "recife"),

    ("a1b2c3d4-0007-4000-8000-000000000007", "Paula Atendente", "atendente.saopaulo@raizes.com", Perfil.ATENDENTE, "saopaulo"),
    ("a1b2c3d4-0008-4000-8000-000000000008", "Rafael Cozinha", "cozinha.saopaulo@raizes.com", Perfil.COZINHA, "saopaulo"),
    ("a1b2c3d4-0009-4000-8000-000000000009", "Beatriz Gerente", "gerente.saopaulo@raizes.com", Perfil.GERENTE, "saopaulo"),
    ("a1b2c3d4-0010-4000-8000-000000000010", "Totem São Paulo 1", "totem.saopaulo@raizes.com", Perfil.TOTEM, "saopaulo"),

    ("a1b2c3d4-0011-4000-8000-000000000011", "Francisco Atendente", "atendente.fortaleza@raizes.com", Perfil.ATENDENTE, "fortaleza"),
    ("a1b2c3d4-0012-4000-8000-000000000012", "Luiza Cozinha", "cozinha.fortaleza@raizes.com", Perfil.COZINHA, "fortaleza"),
    ("a1b2c3d4-0013-4000-8000-000000000013", "Antônio Gerente", "gerente.fortaleza@raizes.com", Perfil.GERENTE, "fortaleza"),
    ("a1b2c3d4-0014-4000-8000-000000000014", "Totem Fortaleza 1", "totem.fortaleza@raizes.com", Perfil.TOTEM, "fortaleza"),
]

# Mesma senha para todos ("senha123"), só para desenvolvimento
SENHA_HASH = bcrypt.hashpw(b"senha123", bcrypt.gensalt()).decode()


def popular():
    with SessionLocal() as db:
        if db.scalar(select(Unidade).limit(1)):
            print("O banco já tem dados. Nada novo foi inserido.")
            return

        db.add_all(UNIDADES.values())
        db.add_all(PRODUTOS.values())

        for unidade, produto, uuid, preco in CARDAPIOS:
            db.add(ProdutoUnidade(
                uuid=UUID(uuid),
                unidade=UNIDADES[unidade],
                produto=PRODUTOS[produto],
                preco=Decimal(preco),
                estoque=ESTOQUE_INICIAL,
                disponivel_sazonal=(unidade, produto) not in FORA_DA_TEMPORADA,
                ativo=(unidade, produto) not in DESATIVADOS_PELO_GERENTE,
            ))

        for uuid, nome, email, perfil, unidade in USUARIOS:
            db.add(Usuario(
                uuid=UUID(uuid),
                nome=nome,
                email=email,
                senha_hash=SENHA_HASH,
                perfil=perfil,
                unidade=UNIDADES[unidade] if unidade else None,
            ))

        db.commit()
        print(f"Inseridos: {len(UNIDADES)} unidades, {len(PRODUTOS)} produtos, {len(CARDAPIOS)} itens de cardápio e {len(USUARIOS)} usuários.")


if __name__ == "__main__":
    popular()
