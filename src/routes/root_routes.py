from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.utils.logger import get_logger
from pydantic import BaseModel

router = APIRouter()
logger = get_logger(__name__)

# Modelo de resposta
class RootResponse(BaseModel):
    status: str
    message: str

@router.get(
    "/",
    response_model=RootResponse,
    summary="Healthcheck simples da API",
    description="Retorna o status atual da API.",
    response_description="Status da API"
)
async def root():
    logger.info("Healthcheck solicitado.")
    return JSONResponse(
        content={"status": "online", "message": "Condo Package Scanner API ativa."}
    )
