from fastapi import FastAPI

from controllers import auth_controller, pedido_controller, unidade_controller, usuario_controller
from core.erros import registrar_tratadores_de_erro

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
app.include_router(auth_controller.router)
app.include_router(pedido_controller.router)
app.include_router(usuario_controller.router)
app.include_router(unidade_controller.router)
