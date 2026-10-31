```mermaid
erDiagram
    USUARIO |o--o{ PEDIDO : faz
    PEDIDO ||--|{ PAGAMENTO : possui
    PEDIDO ||--|{ ITEM_PEDIDO : possui
    PEDIDO ||--|{ HISTORICO_STATUS_PEDIDO : tem
    USUARIO |o--o{ HISTORICO_STATUS_PEDIDO : tem
    UNIDADE ||--o{ PEDIDO : possui
    UNIDADE |o--o{ USUARIO : tem
    UNIDADE ||--o{ PRODUTO_UNIDADE : possui
    PRODUTO ||--o{ PRODUTO_UNIDADE : possui
    PRODUTO_UNIDADE ||--o{ ITEM_PEDIDO : "está em"

    USUARIO {
        int id PK
        uuid uuid UK
        varchar nome
        varchar email UK
        varchar senha_hash
        varchar perfil "ENUM: CLIENTE, ATENDENTE, COZINHA, GERENTE, ADMIN" 
        bool ativo

        int unidade_id FK "anulável"
    }
    PEDIDO {
        int id PK
        uuid uuid UK
        varchar canal_pedido "ENUM: APP, BALCAO, TOTEM, WEB, PICKUP"
        timestamp data_hora 
        varchar status "ENUM: AGUARDANDO_PAGAMENTO, PAGAMENTO_RECUSADO, PAGAMENTO_EXPIRADO, EM_PREPARO, PRONTO, ENTREGUE, PEDIDO_CANCELADO"
        int senha "anulável; único com unidade_id + data_senha"
        date data_senha "anulável; único com unidade_id + senha"
        
        int unidade_id FK "único com data_senha + senha"
        int cliente_id FK "anulável"
    }
    ITEM_PEDIDO {
        int id PK
        varchar nome_produto
        numeric(10,2) preco_unitario
        int quantidade ">0"
        varchar observacao "anulável"

        int pedido_id FK
        int produto_unidade_id FK
    }
    PAGAMENTO {
        int id PK 
        uuid uuid UK
        numeric(10,2) valor
        varchar resultado "ENUM: PENDENTE, APROVADO, RECUSADO, EXPIRADO"
        varchar motivo_recusa "anulável"
        timestamp data_hora_resposta "anulável"

        int pedido_id FK "máximo 3 pagamentos por pedido"
    }
    HISTORICO_STATUS_PEDIDO {
        int id PK
        varchar status_anterior "anulável"
        varchar status_novo "ENUM: AGUARDANDO_PAGAMENTO, PAGAMENTO_RECUSADO, PAGAMENTO_EXPIRADO, EM_PREPARO, PRONTO, ENTREGUE, PEDIDO_CANCELADO"
        timestamp data_hora
        varchar tipo_responsavel "ENUM:  CLIENTE, ATENDENTE, COZINHA, GERENTE, ADMIN, SISTEMA" 
        varchar motivo "anulável"

        int pedido_id FK
        int usuario_id FK "anulável só com SISTEMA ou CLIENTE anônimo"

    }
    PRODUTO {
        int id PK
        uuid uuid UK
        varchar nome
        varchar descricao "anulável"
        varchar categoria "ENUM: PRATO_PRINCIPAL, LANCHE, BEBIDA, SOBREMESA"
        bool ativo
    }
    PRODUTO_UNIDADE {
        int id PK
        uuid uuid UK
        numeric(10,2) preco ">0"
        int estoque ">=0"
        bool ativo
        bool disponivel_sazonal
        
        int produto_id FK "único com unidade_id"
        int unidade_id FK "único com produto_id"
    }
    UNIDADE {
        int id PK
        uuid uuid UK
        varchar nome
        varchar endereco
        varchar cidade
        char(2) uf
    }
```