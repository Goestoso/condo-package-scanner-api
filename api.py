from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from src.main import main
from src.utils.logger import get_logger
import traceback
from contextlib import asynccontextmanager
from src.utils.logger import get_logger

# Instancia o logger
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Condo Package Scanner API iniciada.")
    yield
    # Shutdown
    logger.info("🛑 Condo Package Scanner API encerrada.")


# Instancia o app
app = FastAPI(title="Condo Package Scanner API", version="0.1.0", lifespan=lifespan)


@app.post("/extract")
async def extract_package_info(file: UploadFile = File(...)):
    """
    Recebe uma imagem (arquivo) e retorna o resultado da extração de dados.
    """
    try:
        logger.info(f"Requisição recebida: arquivo '{file.filename}' ({file.content_type})")

        # Lê os bytes da imagem
        image_bytes = await file.read()

        # Executa o core da aplicação
        result = main(image_bytes)

        logger.info(f"Extração concluída para '{file.filename}': {result}")
        return JSONResponse(status_code=200, content={"status": "success", "data": result})

    except HTTPException as e:
        # Erros controlados da própria FastAPI
        logger.error(f"Erro HTTP ao processar '{file.filename}': {e.detail}")
        return JSONResponse(status_code=e.status_code, content={"status": "error", "detail": e.detail})

    except Exception as e:
        # Erros inesperados
        tb = traceback.format_exc()
        logger.exception(f"Erro inesperado ao processar '{file.filename}': {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": str(e),
                "traceback": tb
            }
        )

@app.get("/")
async def root():
    """Rota simples para checar se a API está ativa."""
    logger.info("Healthcheck solicitado.")
    return {"status": "online", "message": "Condo Package Scanner API ativa."}
