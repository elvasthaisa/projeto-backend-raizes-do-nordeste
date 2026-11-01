from enum import Enum


class Perfil(str, Enum):
    CLIENTE = "CLIENTE"
    ATENDENTE = "ATENDENTE"
    COZINHA = "COZINHA"
    GERENTE = "GERENTE"
    ADMIN = "ADMIN"
    TOTEM = "TOTEM"

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
