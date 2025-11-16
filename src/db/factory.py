# src/db/db_factory.py
from src.utils.config_loader import load_db_config

def get_db_connection():
    config = load_db_config()
    engine = config.get("engine", "sqlserver").lower()

    if engine == "sqlserver":
        import pyodbc  # só importa se for SQL Server
        from src.db.sqlserver_api import SQLServerConnection
        return SQLServerConnection(config)
    else:
        from src.db.mysql_api import MySQLConnection
        return MySQLConnection(config)

