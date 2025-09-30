import os

class Config:
    # Configuración de la base de datos
    MYSQL_HOST = 'localhost'  # O 'mysql_db' si usas Docker
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'vaacomerlapapa'
    MYSQL_DB = 'Base'
    SECRET_KEY = 'tu_clave_secreta_aqui'  # Cambia esto en producción
