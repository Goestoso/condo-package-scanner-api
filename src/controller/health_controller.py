# src/controller/health_controller.py
from src.db.factory import get_db_connection
from src.utils.logger import get_logger

logger = get_logger(__name__)

def healthcheck_controller():
    """
    Verifica se a API e o banco de dados estão online.
    """
    db_connected = False
    try:
        conn = get_db_connection()
        conn.connect()
        cursor = conn.connection.cursor()
        cursor.execute("SELECT 1")  # Teste rápido de conexão
        db_connected = True
        conn.close()
    except Exception as e:
        logger.warning(f"Banco de dados indisponível: {e}")

    if db_connected:
        return {
            "status": "online",
            "db_connected": True,
            "message": "Condo Package Scanner API ativa e conectada ao banco de dados."
        }
    else:
        return {
            "status": "online",
            "db_connected": False,
            "message": "Condo Package Scanner API ativa, porém banco de dados está indisponível."
        }
