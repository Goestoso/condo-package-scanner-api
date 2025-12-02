import os
from fastapi import HTTPException
from src.utils.logger import load_logger_config, get_logger

logger = get_logger(__name__)

class LogController:

    @staticmethod
    def get_log_file_path() -> str:
        cfg = load_logger_config()
        log_path = cfg["log_file"]

        if not os.path.exists(log_path):
            logger.error("Arquivo de log não foi encontrado")
            raise HTTPException(status_code=404, detail="Arquivo de log não encontrado.")
        
        logger.debug("Solicitação GET log CondoPackageScanner: arquivo log carregado e enviado com sucesso.")

        return log_path

    @staticmethod
    def clear_logs() -> None:
        cfg = load_logger_config()
        log_path = cfg["log_file"]

        directory = os.path.dirname(log_path)
        base_name = os.path.basename(log_path)

        try:
            # ---1) Limpa o arquivo principal---
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("")

            # ---2) Remove arquivos de backup---
            for file in os.listdir(directory):
                # identifica arquivos do rotating log
                if file.startswith(base_name) and file != base_name:
                    backup_path = os.path.join(directory, file)
                    os.remove(backup_path)

            logger.warning("Solicitação POST log CondoPackageScanner: arquivo(s) de log limpo(s) com sucesso.")

        except Exception as e:
            logger.error(f"Erro ao limpar logs: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao limpar logs: {str(e)}"
            )
