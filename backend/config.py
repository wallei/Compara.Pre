import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    """Configuración de la aplicación"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave-por-defecto-insegura')
    
    # MySQL
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'comparapre_db'),
        'port': int(os.getenv('DB_PORT', 3306))
    }
    
    # CORS (para permitir peticiones desde el frontend)
    CORS_ORIGINS = ['http://127.0.0.1:5500', 'http://localhost:5500', 'null']