import pyodbc
from src.utils.config_loader import load_db_config, get_logger

logger = get_logger(__name__)

class ODBCConnection:
    """Gerencia a conexão ODBC com base nas configurações YAML."""

    @property
    def connection(self):
        return self.__connection

    def __init__(self):
        try:
            self.__config = load_db_config()
            logger.info("Arquivo de configuração do banco carregado com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao carregar configuração do banco: {e}")
            raise

        self.__connection = None

    def connect(self):
        """Estabelece a conexão com o banco."""
        encrypt_val = 'yes' if str(self.__config.get('encrypt', True)).lower() in ['yes', 'true', '1'] else 'no'
        trust_val = 'yes' if str(self.__config.get('trust_server_certificate', False)).lower() in ['yes', 'true', '1'] else 'no'

        conn_str = (
            f"DRIVER={self.__config['driver']};"
            f"SERVER={self.__config['server']};"
            f"DATABASE={self.__config['database']};"
            f"UID={self.__config['username']};"
            f"PWD={self.__config['password']};"
            f"Encrypt={encrypt_val};"
            f"TrustServerCertificate={trust_val};"
            f"Connection Timeout={self.__config.get('connection_timeout', 30)};"
        )

        try:
            self.__connection = pyodbc.connect(conn_str)
            logger.info(
                f"Conexão com o banco de dados '{self.__config['database']}' no servidor '{self.__config['server']}' estabelecida com sucesso."
            )
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            raise

    def close(self):
        """Fecha a conexão."""
        if self.__connection:
            try:
                self.__connection.close()
                logger.info("Conexão com o banco de dados encerrada com sucesso.")
            except Exception as e:
                logger.warning(f"Erro ao encerrar conexão com o banco de dados: {e}")
            finally:
                self.__connection = None
