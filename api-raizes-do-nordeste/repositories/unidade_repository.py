from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, contains_eager

from models import Produto, ProdutoUnidade, Unidade


def listar(db: Session):
    return db.scalars(select(Unidade).order_by(Unidade.id)).all()

def buscar_por_uuid(db: Session, unidade_uuid: UUID):
    return db.scalar(select(Unidade).where(Unidade.uuid == unidade_uuid))

# Cardápio só com itens ativos, na temporada e com estoque
def listar_cardapio(db: Session, unidade_id: int):
    consulta = (
        select(ProdutoUnidade)
        .join(ProdutoUnidade.produto)
        .options(contains_eager(ProdutoUnidade.produto)) # traz o produto na mesma consulta
        .where(
            ProdutoUnidade.unidade_id == unidade_id,
            ProdutoUnidade.ativo,
            ProdutoUnidade.disponivel_sazonal,
            ProdutoUnidade.estoque > 0,
        )
        .order_by(Produto.categoria, Produto.nome)
    )
    return db.scalars(consulta).all()

# Produtos da unidade com os uuids pedidos, mesmo os que estão fora do cardápio
def buscar_produtos_da_unidade(db: Session, unidade_id: int, uuids: list):
    consulta = (
        select(ProdutoUnidade)
        .join(ProdutoUnidade.produto)
        .options(contains_eager(ProdutoUnidade.produto))
        .where(ProdutoUnidade.unidade_id == unidade_id, ProdutoUnidade.uuid.in_(uuids))
    )
    return db.scalars(consulta).all()
