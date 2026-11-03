# API Raízes do Nordeste


> Projeto pessoal de uma API de back-end da rede de restaurantes Raízes do Nordeste desenvolvido para a disciplina **Projeto Multidisciplinar (trilha Back-end)**, do Centro Universitário Internacional UNINTER (Escola Superior Politécnica – ESP).

O fluxo implementado é o **Fluxo A: Pedido → Pagamento mock → Atualização de
status**. O cliente escolhe a unidade e os itens do cardápio, o pedido é
registrado com o canal de origem (`APP`, `WEB`, `PICKUP`, `TOTEM` ou
`BALCAO`), o pagamento passa por um gateway simulado e o pedido segue até a
retirada, passando pelo preparo.

## Links

- **Swagger** (com a API rodando): http://127.0.0.1:8000/docs
- **Coleção do Postman:** [`api-raizes-do-nordeste/postman/raizes-do-nordeste.postman_collection.json`](api-raizes-do-nordeste/postman/raizes-do-nordeste.postman_collection.json)

## Tecnologias

- Python 3.10 com FastAPI
- SQLAlchemy 2 e Alembic (migrations)
- PostgreSQL 15, rodando no Docker
- JWT (PyJWT) para o login e bcrypt para as senhas
- Postman para os testes

## Pré-requisitos

- [Python](https://www.python.org/downloads/) (versão 3.10 ou superior)
- [Postman](https://www.postman.com/downloads/)
- [Git](https://git-scm.com/downloads)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

Não é preciso instalar o PostgreSQL na máquina, ele roda dentro do container.

## Estrutura do projeto

```
api-raizes-do-nordeste/
├── main.py            # cria a API, registra as rotas e a rotina de prazo de pagamento
├── controllers/       # rotas HTTP
├── services/          # regras de negócio
├── repositories/      # consultas ao banco
├── models/            # tabelas do banco (SQLAlchemy)
├── schemas/           # formato dos dados de entrada e saída
├── gateway/           # gateway de pagamento simulado
├── core/              # configuração, banco, segurança e padrão de erro
├── migrations/        # migrations do Alembic
├── seed.py            # dados iniciais (unidades, cardápios e usuários)
├── postman/           # coleção de testes
├── compose.yaml       # banco PostgreSQL no Docker
├── .env.example       # modelo das variáveis de ambiente
└── requirements.txt   # dependências do Python
docs/diagramas/        # diagramas da modelagem
```

## Como rodar

Todos os comandos abaixo, a partir do passo 2, são feitos dentro da pasta
`api-raizes-do-nordeste`.

### 1. Baixar o repositório

```
git clone https://github.com/elvasthaisa/projeto-backend-raizes-do-nordeste.git
cd projeto-backend-raizes-do-nordeste/api-raizes-do-nordeste
```

### 2. Configurar as variáveis de ambiente

Copie o modelo para um arquivo `.env`:

```
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux, macOS ou Git Bash
cp .env.example .env
```

Abra o `.env` e troque a senha e a chave:

| Variável | O que é |
|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Usuário, senha e nome do banco. O Docker Compose usa esses valores para criar o banco |
| `DATABASE_URL` | Endereço do banco usado pela API. O usuário, a senha e o nome do banco precisam ser os mesmos de cima |
| `JWT_SECRET` | Chave que assina os tokens de login. Use 32 caracteres ou mais |

Para gerar uma chave aleatória:

```
python -c "import secrets; print(secrets.token_hex(32))"
```

O `.env` fica fora do Git porque guarda a senha e a chave.

### 3. Subir o banco com o Docker Compose

Com o Docker Desktop aberto:

```
docker compose up -d
```

Esse comando baixa a imagem do PostgreSQL 15 (só na primeira vez), cria o
container `raizes-db` e deixa o banco no ar na porta `5432`. O `-d` faz o
container rodar em segundo plano, liberando o terminal.

Para conferir se o banco está no ar:

```
docker compose ps
```

O container `raizes-db` deve aparecer com o status `running` (ou `Up`).

Os dados ficam guardados no volume `db-data`, então continuam lá mesmo
depois de desligar o container.

### 4. Criar o ambiente virtual e instalar as dependências

```
python -m venv .venv
```

Ative o ambiente virtual:

```
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Git Bash
source .venv/Scripts/activate

# Linux ou macOS
source .venv/bin/activate
```

Se o PowerShell bloquear a ativação, rode antes
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

Instale as dependências:

```
pip install -r requirements.txt
```

### 5. Criar as tabelas (migrations)

```
alembic upgrade head
```

### 6. Inserir os dados iniciais (seed)

```
python seed.py
```

O seed cria 3 unidades (Recife, São Paulo e Fortaleza), 22 produtos, 42
itens de cardápio e 14 usuários. Se o banco já tiver dados, ele não insere
nada de novo.

### 7. Iniciar a API

```
uvicorn main:app --reload
```

A API fica no ar em http://127.0.0.1:8000. Para desligar, use `Ctrl+C`.

Para conferir se a API e o banco estão respondendo, acesse
http://127.0.0.1:8000/health. A resposta esperada é `200` com
`"status": "UP"`. Se o banco estiver fora do ar, a resposta é `503`.

Da próxima vez, basta abrir o Docker Desktop, ativar o ambiente virtual e
rodar `docker compose up -d` e `uvicorn main:app --reload`. Os passos 2, 5
e 6 só são feitos uma vez.

## Documentação da API (Swagger)

Com a API rodando, acesse **http://127.0.0.1:8000/docs**.

Para usar as rotas que pedem login:

1. Em `POST /auth/login`, clique em **Try it out**, escolha um usuário da
   tabela abaixo e envie.
2. Copie o `accessToken` da resposta.
3. Clique em **Authorize** (cadeado no topo da página), cole o token e
   confirme.

O token vale 60 minutos. Se recarregar a página, faça o Authorize de novo.

## Usuários de teste

Todos os usuários criados pelo seed usam a senha `senha123`.

| E-mail | Perfil | Unidade |
|---|---|---|
| `cliente@raizes.com` | CLIENTE | escolhe no pedido |
| `admin@raizes.com` | ADMIN | todas |
| `atendente.<unidade>@raizes.com` | ATENDENTE | a da conta |
| `cozinha.<unidade>@raizes.com` | COZINHA | a da conta |
| `gerente.<unidade>@raizes.com` | GERENTE | a da conta |
| `totem.<unidade>@raizes.com` | TOTEM | a da conta |

Troque `<unidade>` por `recife`, `saopaulo` ou `fortaleza`. Exemplo:
`cozinha.recife@raizes.com`.

Para testar com um cliente novo, cadastre-o em `POST /usuarios`.

## Como rodar os testes (Postman)

Os testes estão na coleção
`api-raizes-do-nordeste/postman/raizes-do-nordeste.postman_collection.json`:
32 requisições em 6 pastas, com verificações automáticas em cada uma.

| Pasta | Requisições | O que testa |
|---|---|---|
| Health | T00 | Healthcheck: API e banco no ar (`GET /health`) |
| Auth | T01 a T05 | Login, token, 401 e 403 |
| Unidades | T06 a T07c | Unidades e cardápio de cada unidade |
| Erros | T08 a T12 | Validação (422) e unidade ou produto inexistente (404) |
| Pedidos | T13 a T19 e T29 | Fluxo principal (pedido → pagamento aprovado → pronto → retirada), erros de estoque (409) e filtro de pedidos por canal |
| Pagamento | T20 a T28 | Pagamento recusado, nova tentativa, cancelamento e histórico do pedido |

**Antes de rodar:** a API precisa estar no ar e o banco precisa ter os
dados do seed (passos 3 a 7).

1. No Postman, clique em **Import** e escolha o arquivo da coleção.
2. Abra a coleção, clique em **Run** e mantenha a ordem das requisições.
3. Clique em **Run API Raízes do Nordeste**.

A ordem importa: T01 e T02 fazem o login e guardam os tokens, e as
requisições que criam pedidos (T13, T20 e T26) guardam o id do pedido para
as seguintes. Todas as variáveis ficam na própria coleção (aba
**Variables**), não é preciso criar um ambiente.

Para rodar uma requisição sozinha, rode antes T01 e T02 (login) e, nas
pastas Pedidos e Pagamento, a requisição que cria o pedido.

O pagamento é processado em segundo plano. Por isso, as consultas logo
depois do pagamento esperam 1 segundo antes de enviar.

A coleção pode ser rodada mais de uma vez seguida. Cada rodada consome
estoque e senhas do dia. Para voltar o banco ao estado inicial, veja
[Recarregar o banco](#recarregar-o-banco).

## Comandos úteis do Docker

| Comando | O que faz |
|---|---|
| `docker compose up -d` | Sobe o banco em segundo plano |
| `docker compose ps` | Mostra se o container está no ar |
| `docker compose logs db` | Mostra o log do PostgreSQL |
| `docker compose stop` | Desliga o banco, mantendo os dados |
| `docker compose down` | Desliga e remove o container, mantendo os dados no volume |
| `docker compose down -v` | Desliga, remove o container **e apaga os dados** |

## Recarregar o banco

Para apagar os pedidos e voltar aos dados do seed, com o ambiente virtual
ativado:

```
alembic downgrade base
alembic upgrade head
python seed.py
```

Outra forma é apagar o volume e criar o banco do zero:

```
docker compose down -v
docker compose up -d
alembic upgrade head
python seed.py
```
