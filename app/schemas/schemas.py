from pydantic import BaseModel, Field
from typing import Optional

class OABRequest(BaseModel):
    name: str = Field(...)
    uf: str = Field(...)

class OABResponse(BaseModel):
    oab: Optional[str] = "Não encontrado"
    nome: Optional[str] = "Não encontrado"
    uf: Optional[str] = "Não encontrado"
    categoria: Optional[str] = "Não encontrado"
    data_inscricao: Optional[str] = "Não encontrado"
    situacao: Optional[str] = "Não encontrado"
