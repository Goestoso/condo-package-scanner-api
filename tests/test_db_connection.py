import sys
from pathlib import Path

# Adiciona a pasta src ao sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.db.factory import get_db_connection

def test_database_connection():
    """
    Testa se a conexão com o banco de dados pode ser aberta e fechada com sucesso.
    """
    conn = get_db_connection()
    try:
        conn.connect()
        assert conn.connection is not None, "A conexão deveria estar ativa, mas está None."
        print("✅ Conexão estabelecida com sucesso!")
    except Exception as e:
        print(f"Falha ao conectar com o banco: {e}")
    finally:
        conn.close()
        print("🔒 Conexão encerrada.")

if __name__ == "__main__":
    test_database_connection()