# src/db/db_factory.py
from src.utils.config_loader import load_db_config
from src.db.sqlserver_api import SQLServerConnection
from src.db.mysql_api import MySQLConnection

def get_db_connection():
    config = load_db_config()
    engine = config.get("engine", "sqlserver").lower()

    if engine == "sqlserver":
        return SQLServerConnection(config)
    else:
        return MySQLConnection(config)
