import mysql.connector
from config import Config
import bcrypt

class Database:
    """Clase para manejar la conexión a MySQL"""
    
    @staticmethod
    def get_connection():
        """Obtiene una conexión a la base de datos"""
        try:
            connection = mysql.connector.connect(**Config.DB_CONFIG)
            return connection
        except mysql.connector.Error as err:
            print(f"Error de conexión: {err}")
            return None
    
    @staticmethod
    def init_db():
        """Inicializa la base de datos creando las tablas necesarias"""
        connection = Database.get_connection()
        if connection is None:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Crear tabla de usuarios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    apellido VARCHAR(100) NOT NULL,
                    email VARCHAR(150) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultimo_acceso TIMESTAMP NULL,
                    activo BOOLEAN DEFAULT TRUE
                )
            """)
            
            connection.commit()
            print("✓ Base de datos inicializada correctamente")
            return True
            
        except mysql.connector.Error as err:
            print(f"Error al crear tabla: {err}")
            return False
        finally:
            cursor.close()
            connection.close()


class Usuario:
    """Modelo de Usuario"""
    
    @staticmethod
    def crear_usuario(nombre, apellido, email, password):
        """Crea un nuevo usuario en la base de datos"""
        connection = Database.get_connection()
        if connection is None:
            return {'success': False, 'message': 'Error de conexión a la base de datos'}
        
        try:
            cursor = connection.cursor()
            
            # Verificar si el email ya existe
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            if cursor.fetchone():
                return {'success': False, 'message': 'El correo electrónico ya está registrado'}
            
            # Encriptar contraseña
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Insertar usuario
            query = """
                INSERT INTO usuarios (nombre, apellido, email, password)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (nombre, apellido, email, password_hash))
            connection.commit()
            
            return {
                'success': True, 
                'message': 'Usuario registrado exitosamente',
                'user_id': cursor.lastrowid
            }
            
        except mysql.connector.Error as err:
            return {'success': False, 'message': f'Error al crear usuario: {err}'}
        finally:
            cursor.close()
            connection.close()
    
    @staticmethod
    def verificar_credenciales(email, password):
        """Verifica las credenciales de login"""
        connection = Database.get_connection()
        if connection is None:
            return {'success': False, 'message': 'Error de conexión a la base de datos'}
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Buscar usuario por email
            cursor.execute("""
                SELECT id, nombre, apellido, email, password, activo 
                FROM usuarios 
                WHERE email = %s
            """, (email,))
            
            usuario = cursor.fetchone()
            
            if not usuario:
                return {'success': False, 'message': 'Credenciales incorrectas'}
            
            if not usuario['activo']:
                return {'success': False, 'message': 'Usuario inactivo'}
            
            # Verificar contraseña
            if bcrypt.checkpw(password.encode('utf-8'), usuario['password'].encode('utf-8')):
                # Actualizar último acceso
                cursor.execute("""
                    UPDATE usuarios 
                    SET ultimo_acceso = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (usuario['id'],))
                connection.commit()
                
                return {
                    'success': True,
                    'message': 'Login exitoso',
                    'user': {
                        'id': usuario['id'],
                        'nombre': usuario['nombre'],
                        'apellido': usuario['apellido'],
                        'email': usuario['email']
                    }
                }
            else:
                return {'success': False, 'message': 'Credenciales incorrectas'}
                
        except mysql.connector.Error as err:
            return {'success': False, 'message': f'Error en la consulta: {err}'}
        finally:
            cursor.close()
            connection.close()
    
    @staticmethod
    def email_existe(email):
        """Verifica si un email ya está registrado"""
        connection = Database.get_connection()
        if connection is None:
            return False
        
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            existe = cursor.fetchone() is not None
            return existe
        except mysql.connector.Error:
            return False
        finally:
            cursor.close()
            connection.close()