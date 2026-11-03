from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str  # UP quando a API e o banco respondem
    banco: str
    timestamp: datetime
