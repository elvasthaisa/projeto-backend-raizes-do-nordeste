from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from core.enums import Perfil


class LoginRequest(BaseModel):
    email: str
    senha: str = Field(max_length=72) # limite do bcrypt

class TokenResponse(BaseModel):
    accessToken: str
    tokenType: str = "bearer"

# Dados do usuário lidos do token
class UsuarioLogado(BaseModel):
    id: UUID
    perfil: Perfil
    unidadeId: Optional[UUID] = None


# Exemplos do Swagger (usuários de repositories/dados_exemplo.py)
EXEMPLOS_LOGIN = {
    "cliente": {"summary": "Cliente", "value": {"email": "cliente@raizes.com", "senha": "senha123"}},
    "admin": {"summary": "Admin", "value": {"email": "admin@raizes.com", "senha": "senha123"}},
    "atendente_recife": {"summary": "Atendente - Recife", "value": {"email": "atendente.recife@raizes.com", "senha": "senha123"}},
    "cozinha_recife": {"summary": "Cozinha - Recife", "value": {"email": "cozinha.recife@raizes.com", "senha": "senha123"}},
    "gerente_recife": {"summary": "Gerente - Recife", "value": {"email": "gerente.recife@raizes.com", "senha": "senha123"}},
    "totem_recife": {"summary": "Totem - Recife", "value": {"email": "totem.recife@raizes.com", "senha": "senha123"}},
    "atendente_saopaulo": {"summary": "Atendente - São Paulo", "value": {"email": "atendente.saopaulo@raizes.com", "senha": "senha123"}},
    "cozinha_saopaulo": {"summary": "Cozinha - São Paulo", "value": {"email": "cozinha.saopaulo@raizes.com", "senha": "senha123"}},
    "gerente_saopaulo": {"summary": "Gerente - São Paulo", "value": {"email": "gerente.saopaulo@raizes.com", "senha": "senha123"}},
    "totem_saopaulo": {"summary": "Totem - São Paulo", "value": {"email": "totem.saopaulo@raizes.com", "senha": "senha123"}},
    "atendente_fortaleza": {"summary": "Atendente - Fortaleza", "value": {"email": "atendente.fortaleza@raizes.com", "senha": "senha123"}},
    "cozinha_fortaleza": {"summary": "Cozinha - Fortaleza", "value": {"email": "cozinha.fortaleza@raizes.com", "senha": "senha123"}},
    "gerente_fortaleza": {"summary": "Gerente - Fortaleza", "value": {"email": "gerente.fortaleza@raizes.com", "senha": "senha123"}},
    "totem_fortaleza": {"summary": "Totem - Fortaleza", "value": {"email": "totem.fortaleza@raizes.com", "senha": "senha123"}},
}
