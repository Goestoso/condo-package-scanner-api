from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from src.controller.log_controller import LogController
import traceback
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/api", summary="Baixar arquivo de log", tags=["Logs"])
async def download_logs():
    try:
        path = LogController.get_log_file_path()
        return FileResponse(
            path,
            media_type="text/plain",
            filename="api.log"
        )
    except Exception as e:
        tb = traceback.format_exc()
        logger.exception(f"Erro inesperado ao baixar o conteúdo do log: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "data": {
                    "message": str(e),
                    "traceback": tb
                }
            }
        )

@router.post("/clear", summary="Limpar arquivo(s) de log", tags=["Logs"])
async def clear_logs():
    LogController.clear_logs()
    return {"detail": "Logs limpos com sucesso."}
