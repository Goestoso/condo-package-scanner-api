from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.utils.logger import get_logger
from src.routes.extract_routes import router as extract_router
from src.routes.root_routes import router as root_router
from src.routes.health_routes import router as health_router

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Condo Package Scanner API iniciada.")
    yield
    logger.info("🛑 Condo Package Scanner API encerrada.")

app = FastAPI(
    title="Condo Package Scanner API",
    version="0.5.0",
    lifespan=lifespan
)

app.include_router(extract_router, prefix="/extract", tags=["Extract"])
app.include_router(root_router, tags=["Root"])
app.include_router(health_router, prefix="/health", tags=["Health"])
