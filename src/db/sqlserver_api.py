# src/db/sqlserver_api.py
import pyodbc

class SQLServerConnection:
    def __init__(self, config):
        self.config = config
        self.connection = None

    def connect(self):
        conn_str = (
            f"DRIVER={self.config['driver']};"
            f"SERVER={self.config['server']};"
            f"DATABASE={self.config['database']};"
            f"UID={self.config['username']};"
            f"PWD={self.config['password']};"
            f"Encrypt={'yes' if self.config.get('encrypt', True) else 'no'};"
            f"TrustServerCertificate={'yes' if self.config.get('trust_server_certificate', False) else 'no'};"
            f"Connection Timeout={self.config.get('connection_timeout', 30)};"
        )
        self.connection = pyodbc.connect(conn_str)

    def close(self):
        if self.connection:
            self.connection.close()
