import sys
from pathlib import Path

# Adiciona a pasta src ao sys.path
sys.path.append(str(Path(__file__).parent.parent))

# test_db_connection.py
from src.odbc_api import ODBCConnection
from src.utils.logger import get_logger

logger = get_logger(__name__)

def test_connection():
    """Simula uma conexão ao banco e executa uma query simples."""
    db = ODBCConnection()  # Instancia o gerenciador de conexão

    try:
        db.connect()
        cursor = db.connection.cursor()

        # Executa uma query simples só pra testar
        cursor.execute("SELECT 1 AS test_result;")
        result = cursor.fetchone()

        logger.info(f"Resultado da query de teste: {result[0]}")
        print(f"✅ Conexão bem-sucedida! Resultado da query: {result[0]}")

    except Exception as e:
        logger.error(f"❌ Falha ao testar conexão com o banco: {e}")
        print(f"❌ Erro: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    test_connection()
