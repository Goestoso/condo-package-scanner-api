from src.db.odbc_api import ODBCConnection
from src.utils.logger import get_logger

logger = get_logger(__name__)

def search_person_like(name_candidate: str) -> list[str]:
    """
    Busca nomes similares no banco usando LIKE na tabela 'moradores'.
    
    Args:
        name_candidate: Nome ou parte do nome a ser pesquisado.
        
    Returns:
        Lista de nomes completos encontrados.
    """
    results = []
    conn = ODBCConnection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()
        like_pattern = f"%{name_candidate}%"

        query = "SELECT nome FROM moradores WHERE nome LIKE ?"
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
    Retorna o comprimento máximo do campo nome na tabela 'moradores'.
    """
    max_len = 0
    conn = ODBCConnection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()
        cursor.execute("SELECT MAX(LEN(nome)) FROM moradores")
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
    Retorna todos os nomes da tabela 'moradores'.
    """
    names = []
    conn = ODBCConnection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()
        cursor.execute("SELECT nome FROM moradores")
        names = [row[0] for row in cursor.fetchall()]
        logger.debug(f"get_all_person_names() retornou {len(names)} nomes")
    except Exception as e:
        logger.error(f"Erro ao executar get_all_person_names(): {e}")
    finally:
        conn.close()
    return names


def get_residents_by_unit(unidade: str, bloco: str) -> list[str]:
    """
    Retorna os nomes de moradores que vivem em uma unidade específica de um bloco.
    """
    results = []
    conn = ODBCConnection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()

        query = """
            SELECT m.nome
            FROM moradores m
            JOIN unidades u ON m.id_unidade = u.id_unidade
            JOIN blocos b ON u.id_bloco = b.id_bloco
            WHERE u.numero_unidade = ? AND b.nome_bloco = ?
        """
        cursor.execute(query, (unidade, bloco))
        results = [row[0] for row in cursor.fetchall()]
        logger.debug(f"get_residents_by_unit(unidade={unidade}, bloco={bloco}) -> {results}")
    except Exception as e:
        logger.error(f"Erro ao executar get_residents_by_unit(unidade={unidade}, bloco={bloco}): {e}")
    finally:
        conn.close()
    return results


def get_residents_by_apartment(unidade: str) -> list[str]:
    """
    Retorna os nomes de moradores que vivem em uma determinada unidade, independente do bloco.
    """
    results = []
    conn = ODBCConnection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()

        query = """
            SELECT m.nome
            FROM moradores m
            JOIN unidades u ON m.unidade_id = u.id
            WHERE u.numero_unidade = ?
        """
        cursor.execute(query, (unidade,))
        results = [row[0] for row in cursor.fetchall()]
        logger.debug(f"get_residents_by_apartment(unidade={unidade}) -> {results}")
    except Exception as e:
        logger.error(f"Erro ao executar get_residents_by_apartment(unidade={unidade}): {e}")
    finally:
        conn.close()
    return results


def get_residents_by_block(bloco: str, name_like: str | None = None) -> list[str]:
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
                SELECT m.nome
                FROM moradores m
                JOIN unidades u ON m.unidade_id = u.id
                JOIN blocos b ON u.bloco_id = b.id
                WHERE b.nome_bloco = ? AND m.nome LIKE ?
            """
            like_pattern = f"%{name_like}%"
            cursor.execute(query, (bloco, like_pattern))
        else:
            query = """
                SELECT m.nome
                FROM moradores m
                JOIN unidades u ON m.unidade_id = u.id
                JOIN blocos b ON u.bloco_id = b.id
                WHERE b.nome_bloco = ?
            """
            cursor.execute(query, (bloco,))

        results = [row[0] for row in cursor.fetchall()]
        logger.debug(f"get_residents_by_block(bloco={bloco}, like={name_like}) -> {results}")
    except Exception as e:
        logger.error(f"Erro ao executar get_residents_by_block(bloco={bloco}, like={name_like}): {e}")
    finally:
        conn.close()
    return results