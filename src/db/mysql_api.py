# src/db/mysql_api.py
import mysql.connector
from src.utils.logger import get_logger

logger = get_logger(__name__)

class MySQLConnection:
    def __init__(self, config: dict):
        self.config = config
        self.connection = None

    def connect(self):
        logger.debug(f"Conectando ao MySQL ({self.config['host']}:{self.config['port']})...")
        self.connection = mysql.connector.connect(
            host=self.config["host"],
            port=self.config["port"],
            user=self.config["username"],
            password=self.config["password"],
            database=self.config["database"],
            connect_timeout=self.config.get("connection_timeout", 30)
        )
        logger.info("Conexão MySQL estabelecida com sucesso.")

    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Conexão MySQL encerrada.")
