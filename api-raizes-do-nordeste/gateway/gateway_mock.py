import time
from decimal import Decimal

from core.enums import CenarioMock
from gateway.gateway_pagamento import GatewayPagamento, RespostaGateway

# Quanto tempo o sistema espera o gateway antes de desistir da chamada
TEMPO_LIMITE_SEGUNDOS = 2


# Gateway simulado. Responde conforme o cenário enviado no pedido, como os cartões de teste dos gateways reais
class GatewayMock(GatewayPagamento):
    def __init__(self, cenario: CenarioMock):
        self.cenario = cenario

    def cobrar(self, valor: Decimal) -> RespostaGateway:
        if self.cenario == CenarioMock.SEM_RESPOSTA:
            time.sleep(TEMPO_LIMITE_SEGUNDOS)
            raise TimeoutError("O gateway não respondeu.")
        if self.cenario == CenarioMock.RECUSAR:
            return RespostaGateway(aprovado=False, motivo_recusa="Pagamento recusado pela operadora.")
        return RespostaGateway(aprovado=True)
