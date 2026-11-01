from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from core.enums import Perfil


# Cadastro de cliente: só nome, e-mail e senha (minimização - RNF03)

class CadastroClienteRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    senha: str = Field(min_length=8, max_length=72) # 72 é o limite do bcrypt

    model_config = ConfigDict(json_schema_extra={"examples": [{"nome": "José da Silva", "email": "jose@email.com", "senha": "minhasenha123"}]})

class UsuarioResponse(BaseModel):
    id: UUID
    nome: str
    email: str
    perfil: Perfil # nunca devolve a senha nem o hash
