from app.scraping.scraper import fetch_lawyer_data
from fastapi import APIRouter, Depends, HTTPException
from app.main import app
from app.schemas.schemas import OABRequest, OABResponse

fetch_routes = APIRouter()

@fetch_routes.post("/fetch_oab", response_model=OABResponse, tags=["OAB"])
async def fetch_router(request: OABRequest):
    """
    Recebe um nome e uma UF, busca no site da OAB e retorna os dados do advogado.
    """
    print(f"Recebida requisição para: Nome='{request.name}', UF='{request.uf}'")
    
    data = fetch_lawyer_data(request.name, request.uf)

    if data and "error" in data:
        if "não encontrado" in data["error"]:
            raise HTTPException(status_code=404, detail=data["error"])
        raise HTTPException(status_code=500, detail=f"Erro durante o scraping: {data['error']}")
    
    if not data:
         raise HTTPException(status_code=500, detail="Erro interno: o scraping não retornou dados.")

    return data
