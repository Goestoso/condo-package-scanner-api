from fastapi import APIRouter
from src.controller.health_controller import healthcheck_controller
from src.models.responses import HealthResponse

router = APIRouter()  # sempre router

@router.get(
    "/",
    summary="Healthcheck avançado da API",
    description="Verifica se a API está online e se o banco de dados está acessível.",
    response_model=HealthResponse
)
async def healthcheck():
    return healthcheck_controller()
