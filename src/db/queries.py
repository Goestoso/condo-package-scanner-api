from src.db.factory import get_db_connection
from src.utils.logger import get_logger

logger = get_logger(__name__)

def _get_placeholder(conn) -> str:
    """
    Retorna o placeholder correto para parâmetros de query.
    - SQL Server (pyodbc): usa '?'
    - MySQL (mysql.connector): usa '%s'
    """
    return "?" if conn.__class__.__name__ == "SQLServerConnection" else "%s"


def search_person_like(name_candidate: str) -> list[str]:
    """
    Busca nomes similares no banco usando LIKE na tabela 'moradores'.
    
    Args:
        name_candidate: Nome ou parte do nome a ser pesquisado.
        
    Returns:
        Lista de nomes completos encontrados.
    """
    results = []
    conn = get_db_connection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()
        placeholder = _get_placeholder(conn)
        like_pattern = f"%{name_candidate}%"

        query = f"SELECT nome FROM moradores WHERE nome LIKE {placeholder}"
        cursor.execute(query, (like_pattern,))
        rows = cursor.fetchall()
        results = [row[0] for row in rows]

        logger.debug(f"search_person_like('{name_candidate}') -> {results}")
    except Exception as e:
        logger.error(f"Erro ao executar search_person_like('{name_candidate}'): {e}")
        raise   # <= deixa a exceção subir para o controller
    finally:
        conn.close()
    return results


def get_max_name_length() -> int:
    """
    Retorna o comprimento máximo do campo nome na tabela 'moradores'.
    Lança exceção se não for possível capturar corretamente.
    """
    max_len = 0
    conn = get_db_connection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()

        # Função LEN() para SQL Server / LENGTH() para MySQL
        func = "LEN" if conn.__class__.__name__ == "SQLServerConnection" else "LENGTH"
        cursor.execute(f"SELECT MAX({func}(nome)) FROM moradores")

        row = cursor.fetchone()
        if row and row[0]:
            max_len = row[0]

        if max_len <= 0:
            raise ValueError("Não foi possível capturar o tamanho máximo de nome. Resultado inválido ou tabela vazia.")

        logger.debug(f"get_max_name_length() -> {max_len}")

        return max_len

    except Exception as e:
        logger.error(f"Erro ao executar get_max_name_length(): {e}")
        raise  # deixa a exceção subir para o controller
    finally:
        conn.close()

def get_all_person_names() -> list[str]:
    """
    Retorna todos os nomes da tabela 'moradores'.
    """
    names = []
    conn = get_db_connection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()
        cursor.execute("SELECT nome FROM moradores")
        names = [row[0] for row in cursor.fetchall()]
        logger.debug(f"get_all_person_names() -> {len(names)} nomes")
    except Exception as e:
        logger.error(f"Erro ao executar get_all_person_names(): {e}")
        raise   # <= deixa a exceção subir para o controller
    finally:
        conn.close()
    return names


def get_residents_by_unit(unidade: str, bloco: str) -> list[str]:
    """
    Retorna os nomes de moradores que vivem em uma unidade específica de um bloco.
    """
    results = []
    conn = get_db_connection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()
        placeholder = _get_placeholder(conn)

        query = f"""
            SELECT m.nome
            FROM moradores m
            JOIN unidades u ON m.id_unidade = u.id_unidade
            JOIN blocos b ON u.id_bloco = b.id_bloco
            WHERE u.numero_unidade = {placeholder} AND b.nome_bloco = {placeholder}
        """
        cursor.execute(query, (unidade, bloco))
        results = [row[0] for row in cursor.fetchall()]
        logger.debug(f"get_residents_by_unit(unidade={unidade}, bloco={bloco}) -> {results}")
    except Exception as e:
        logger.error(f"Erro ao executar get_residents_by_unit(unidade={unidade}, bloco={bloco}): {e}")
        raise   # <= deixa a exceção subir para o controller
    finally:
        conn.close()
    return results


def get_residents_by_apartment(unidade: str) -> list[str]:
    """
    Retorna os nomes de moradores que vivem em uma determinada unidade, independente do bloco.
    """
    results = []
    conn = get_db_connection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()
        placeholder = _get_placeholder(conn)

        query = f"""
            SELECT m.nome
            FROM moradores m
            JOIN unidades u ON m.id_unidade = u.id_unidade
            WHERE u.numero_unidade = {placeholder}
        """
        cursor.execute(query, (unidade,))
        results = [row[0] for row in cursor.fetchall()]
        logger.debug(f"get_residents_by_apartment(unidade={unidade}) -> {results}")
    except Exception as e:
        logger.error(f"Erro ao executar get_residents_by_apartment(unidade={unidade}): {e}")
        raise   # <= deixa a exceção subir para o controller
    finally:
        conn.close()
    return results


def get_residents_by_block(bloco: str, name_like: str | None = None) -> list[str]:
    """
    Retorna os nomes de moradores de um bloco específico.
    Se name_like for fornecido, aplica filtro LIKE no nome.
    """
    results = []
    conn = get_db_connection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()
        placeholder = _get_placeholder(conn)

        if name_like:
            like_pattern = f"%{name_like}%"
            query = f"""
                SELECT m.nome
                FROM moradores m
                JOIN unidades u ON m.id_unidade = u.id_unidade
                JOIN blocos b ON u.id_bloco = b.id_bloco
                WHERE b.nome_bloco = {placeholder} AND m.nome LIKE {placeholder}
            """
            cursor.execute(query, (bloco, like_pattern))
        else:
            query = f"""
                SELECT m.nome
                FROM moradores m
                JOIN unidades u ON m.id_unidade = u.id_unidade
                JOIN blocos b ON u.id_bloco = b.id_bloco
                WHERE b.nome_bloco = {placeholder}
            """
            cursor.execute(query, (bloco,))

        results = [row[0] for row in cursor.fetchall()]
        logger.debug(f"get_residents_by_block(bloco={bloco}, like={name_like}) -> {results}")
    except Exception as e:
        logger.error(f"Erro ao executar get_residents_by_block(bloco={bloco}, like={name_like}): {e}")
        raise   # <= deixa a exceção subir para o controller
    finally:
        conn.close()
    return results

def get_unit_info_by_name(name: str) -> dict | None:
    """
    Consulta o banco e retorna a unidade (apartamento + bloco) de um morador pelo nome exato.
    
    Retorna:
        {'apartment': ..., 'block': ...} ou None se não encontrado
    """
    conn = get_db_connection()
    try:
        conn.connect()
        cursor = conn.connection.cursor()
        placeholder = _get_placeholder(conn)

        query = f"""
            SELECT u.numero_unidade, b.nome_bloco
            FROM moradores m
            JOIN unidades u ON m.id_unidade = u.id_unidade
            JOIN blocos b ON u.id_bloco = b.id_bloco
            WHERE m.nome = {placeholder}
        """
        cursor.execute(query, (name,))
        row = cursor.fetchone()
        if row:
            return {"apartment": row[0], "block": row[1]}
    except Exception as e:
        logger.error(f"Erro ao executar get_unit_info_by_name('{name}'): {e}")
        raise   # <= deixa a exceção subir para o controller
    finally:
        conn.close()
    return None