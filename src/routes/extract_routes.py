from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from src.controller.extract_controller import extract_package_info_controller
from src.models.responses import SuccessResponse, ErrorResponse
from src.utils.logger import get_logger
import traceback

router = APIRouter()
logger = get_logger(__name__)

@router.post(
    "/",
    response_model=SuccessResponse,
    responses={500: {"model": ErrorResponse, "description": "Erro interno no servidor"}},
    summary="Extrai informações de uma imagem de encomenda",
)
async def extract_package_info_route(file: UploadFile = File(...)):
    try:
        logger.info(f"Solicitação POST extract CondoPackageScanner: arquivo '{file.filename}' ({file.content_type})")
        image_bytes = await file.read()
        result = extract_package_info_controller(image_bytes)

        # Se o controller retornou um erro interno
        if "traceback" in result:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "data": {
                        "message": result.get("message"),
                        "traceback": result.get("traceback")
                    }
                }
            )

        # Retorno de sucesso padronizado
        return {
            "status": "success",
            "data": result
        }

    except Exception as e:
        tb = traceback.format_exc()
        logger.exception(f"Erro inesperado ao processar '{file.filename}': {e}")
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
