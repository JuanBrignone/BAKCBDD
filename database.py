import mysql.connector

# Configuración de conexión
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "rootpassword",
    "database": "Obligatorio 2024",
}

def get_db_connection():
    """Establece una conexión con la base de datos."""
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as e:
        print(f"Error al conectar con la base de datos: {e}")
        raise
