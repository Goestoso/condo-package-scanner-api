from src.db.odbc_api import ODBCConnection
from src.utils.logger import get_logger

logger = get_logger(__name__)

def search_person_like(name_candidate: str) -> list[str]:
    """
    Busca nomes similares no banco usando LIKE.
    
    Args:
        name_candidate: Nome ou parte do nome a ser pesquisado.
        
    Returns:
        Lista de nomes completos encontrados.
    """
    results = []

    # Abre a conexão
    conn = ODBCConnection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()
        like_pattern = f"%{name_candidate}%"

        query = "SELECT nome_completo FROM destinatarios WHERE nome_completo LIKE ?"

        cursor.execute(query, (like_pattern,))
        rows = cursor.fetchall()
        results = [row[0] for row in rows]

        logger.debug(f"search_person_like('{name_candidate}') retornou {len(results)} resultados: {results}")
    except Exception as e:
        logger.error(f"Erro ao executar search_person_like('{name_candidate}'): {e}")
    finally:
        conn.close()

    return results

def get_max_name_length() -> int:
    """
    Retorna o comprimento máximo do campo nome_completo na tabela destinatarios.
    """
    max_len = 0
    conn = ODBCConnection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()
        cursor.execute("SELECT MAX(LEN(nome_completo)) FROM destinatarios")
        row = cursor.fetchone()
        if row and row[0]:
            max_len = row[0]
        logger.debug(f"get_max_name_length() -> {max_len}")
    except Exception as e:
        logger.error(f"Erro ao executar get_max_name_length(): {e}")
    finally:
        conn.close()
    return max_len

def get_all_person_names() -> list[str]:
    """
    Retorna todos os nomes da tabela destinatarios.
    """
    names = []
    conn = ODBCConnection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()
        cursor.execute("SELECT nome_completo FROM destinatarios")
        names = [row[0] for row in cursor.fetchall()]
        logger.debug(f"get_all_person_names() retornou {len(names)} nomes")
    except Exception as e:
        logger.error(f"Erro ao executar get_all_person_names(): {e}")
    finally:
        conn.close()
    return names

def get_residents_by_unit(apartment: str, block: str) -> list[str]:
    """
    Retorna os nomes de moradores que vivem em um apartamento específico de um bloco.
    """
    results = []
    conn = ODBCConnection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()

        query = """
            SELECT nome_completo
            FROM destinatarios
            WHERE apartamento = ? AND bloco = ?
        """
        cursor.execute(query, (apartment, block))
        results = [row[0] for row in cursor.fetchall()]
        logger.debug(f"get_residents_by_unit(ap={apartment}, bl={block}) -> {results}")
    except Exception as e:
        logger.error(f"Erro ao executar get_residents_by_unit(ap={apartment}, bl={block}): {e}")
    finally:
        conn.close()
    return results


def get_residents_by_apartment(apartment: str) -> list[str]:
    """
    Retorna os nomes de moradores que vivem em um determinado apartamento,
    independente do bloco.
    """
    results = []
    conn = ODBCConnection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()

        query = """
            SELECT nome_completo
            FROM destinatarios
            WHERE apartamento = ?
        """
        cursor.execute(query, (apartment,))
        results = [row[0] for row in cursor.fetchall()]
        logger.debug(f"get_residents_by_apartment(ap={apartment}) -> {results}")
    except Exception as e:
        logger.error(f"Erro ao executar get_residents_by_apartment(ap={apartment}): {e}")
    finally:
        conn.close()
    return results


def get_residents_by_block(block: str, name_like: str | None = None) -> list[str]:
    """
    Retorna os nomes de moradores de um bloco específico.
    Se name_like for fornecido, aplica filtro LIKE no nome.
    """
    results = []
    conn = ODBCConnection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()

        if name_like:
            query = """
                SELECT nome_completo
                FROM destinatarios
                WHERE bloco = ? AND nome_completo LIKE ?
            """
            like_pattern = f"%{name_like}%"
            cursor.execute(query, (block, like_pattern))
        else:
            query = "SELECT nome_completo FROM destinatarios WHERE bloco = ?"
            cursor.execute(query, (block,))

        results = [row[0] for row in cursor.fetchall()]
        logger.debug(f"get_residents_by_block(bl={block}, like={name_like}) -> {results}")
    except Exception as e:
        logger.error(f"Erro ao executar get_residents_by_block(bl={block}, like={name_like}): {e}")
    finally:
        conn.close()
    return results



