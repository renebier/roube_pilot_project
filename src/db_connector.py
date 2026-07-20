import os
import pymssql
import pandas as pd
class DatabaseConnector(object):
    """
    A class to handle database connections and queries.
    """
    def __init__(self):
        self.server = os.getenv("SQL_SERVER", "database")
        self.database = os.getenv("SQL_DATABASE")
        self.username = os.getenv("SQL_SA_USERNAME", "sa")  # Default to 'sa' if not set
        self.password = os.getenv("SQL_SA_PASSWORD")
        self.port = os.getenv("SQL_PORT")
        self.connection = self._connect()

    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        if self.connection:
            self.connection.close()
    def _connect(self):
        """
        Establishes a connection to the database.
        """
        try:
            connection = pymssql.connect(
                server=self.server,
                user=self.username,
                password=self.password,
                database=self.database,
                port=self.port
            )
            if self._test_connection(connection):
                return connection
            else:
                print("Connection test failed.")
                raise Exception("Connection test failed.")
        except pymssql.Error as e:
            print(f"Error connecting to the database: {e}")
            return None
        
    def _test_connection(self, connection):
        """
        Tests the database connection by executing a simple query.
        """
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT TOP 1 name FROM sys.databases;")
            result = cursor.fetchone()
            print(f"Connection to the database was successful. First database: {result[0]}")
            return True
        else:
            print("Failed to connect to the database.")
            return False
        

    def execute_query(self, query = "SELECT 1;"):
        """
        Executes a SQL query and returns the results.
        """
        if self.connection:
            cursor = self.connection.cursor()
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            df = pd.DataFrame(results, columns=columns)
            return df
        else:
            print("No active database connection.")
            return None