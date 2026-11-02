from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class RespostaGateway:
    aprovado: bool
    motivo_recusa: Optional[str] = None


# O PagamentoService só conhece esta interface. Para usar um gateway real, basta criar outra implementação
class GatewayPagamento(ABC):
    @abstractmethod
    def cobrar(self, valor: Decimal) -> RespostaGateway:
        # Lança TimeoutError quando o gateway não responde a tempo
        ...
