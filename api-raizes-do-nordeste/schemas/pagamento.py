from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from core.enums import CenarioMock, ResultadoPagamento


# Pagamentos (UC3)

class NovaTentativaRequest(BaseModel):
    cenarioMock: CenarioMock = CenarioMock.APROVAR

EXEMPLOS_TENTATIVA = {
    "aprovar": {"summary": "Gateway aprova", "value": {"cenarioMock": "APROVAR"}},
    "recusar": {"summary": "Gateway recusa", "value": {"cenarioMock": "RECUSAR"}},
    "sem_resposta": {"summary": "Gateway não responde (expira)", "value": {"cenarioMock": "SEM_RESPOSTA"}},
}

class PagamentoResponse(BaseModel):
    id: UUID
    valor: Decimal = Field(max_digits=10, decimal_places=2)
    resultado: ResultadoPagamento
    motivoRecusa: Optional[str] = None
    dataHoraResposta: Optional[datetime] = None # vazia enquanto PENDENTE

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "id": "5d1e7a3c-9b2f-4c8e-a1d6-3f0b9c2e7a41",
        "valor": "30.00",
        "resultado": "RECUSADO",
        "motivoRecusa": "Pagamento recusado pela operadora.",
        "dataHoraResposta": "2026-10-31T14:30:05Z",
    }]})
