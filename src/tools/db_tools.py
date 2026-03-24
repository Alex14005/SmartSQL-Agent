import sqlite3
import pandas as pd
import os

# Ajustamos la ruta para apuntar a data/database.db
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "database.db")

def get_database_schema() -> str:
    """
    Extrae el esquema de la base de datos (CREATE TABLE statements).
    Esto se inyectará en el prompt del LLM para que sepa qué tablas y columnas existen.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # En SQLite, la tabla sqlite_master guarda los schemas
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        schemas = cursor.fetchall()
        conn.close()
        
        schema_text = "\n\n".join([schema[0] for schema in schemas if schema[0]])
        return schema_text
    except Exception as e:
        return f"Error al obtener el esquema: {str(e)}"

def execute_sql_query(query: str) -> dict:
    """
    Ejecuta una query SQL en la base de datos usando Pandas.
    Retorna un diccionario con los resultados o el mensaje de error.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Usamos pandas para leer el SQL de manera limpia
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convertimos el DataFrame a una lista de diccionarios para guardarlo en nuestro State
        return {
            "success": True,
            "data": df.to_dict(orient="records"),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e)
        }