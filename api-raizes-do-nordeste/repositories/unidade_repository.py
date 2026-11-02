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

# Produtos da unidade com os uuids pedidos, mesmo os que estão fora do cardápio.
# Trava as linhas até o fim da transação, para dois pedidos ao mesmo tempo não usarem o mesmo estoque
def buscar_produtos_da_unidade(db: Session, unidade_id: int, uuids: list):
    consulta = (
        select(ProdutoUnidade)
        .join(ProdutoUnidade.produto)
        .options(contains_eager(ProdutoUnidade.produto))
        .where(ProdutoUnidade.unidade_id == unidade_id, ProdutoUnidade.uuid.in_(uuids))
        .order_by(ProdutoUnidade.id)
        .with_for_update(of=ProdutoUnidade)
    )
    return db.scalars(consulta).all()

# Trava os produtos e relê o estoque do banco, para a devolução não desfazer uma reserva feita ao mesmo tempo
def travar_produtos(db: Session, produto_unidade_ids: list):
    consulta = (
        select(ProdutoUnidade)
        .where(ProdutoUnidade.id.in_(produto_unidade_ids))
        .order_by(ProdutoUnidade.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    return db.scalars(consulta).all()
