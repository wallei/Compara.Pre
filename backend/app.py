from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Configuración de CORS
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:8080", "http://127.0.0.1:8080"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configuración de la aplicación
class Config:
    DEBUG = True
    SECRET_KEY = 'clave_secreta_para_flask'  # Usada para firmar cookies de sesión
    
    # Configuración de MySQL para Docker Compose
    MYSQL_HOST = '127.0.0.1'  # Usamos 127.0.0.1 en lugar de localhost para evitar problemas con sockets
    MYSQL_PORT = 3306
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'vaacomerlapapa'  # La contraseña que definiste en docker-compose.yml
    MYSQL_DB = 'Base'  # El nombre de la base de datos que definiste en docker-compose.yml
    
    # Configuración de la conexión a la base de datos
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

app.config.from_object(Config)

# Configuración de Swagger
authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}

api = Api(
    app,
    version='1.0',
    title='API de Autenticación',
    description='API para manejo de autenticación de usuarios',
    doc='/api/docs',
    authorizations=authorizations
)

# Modelos para la documentación de la API
login_model = api.model('Login', {
    'email': fields.String(required=True, description='Email del usuario'),
    'password': fields.String(required=True, description='Contraseña del usuario')
})

registro_model = api.model('Registro', {
    'nombre': fields.String(required=True, description='Nombre del usuario'),
    'apellido': fields.String(required=True, description='Apellido del usuario'),
    'email': fields.String(required=True, description='Email del usuario'),
    'password': fields.String(required=True, description='Contraseña del usuario')
})
app.config.from_object(Config)

def get_db_connection():
    try:
        print(f"Intentando conectar a la base de datos...")
        print(f"Host: {app.config['MYSQL_HOST']}")
        print(f"Usuario: {app.config['MYSQL_USER']}")
        print(f"Base de datos: {app.config['MYSQL_DB']}")
        
        connection = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            port=app.config['MYSQL_PORT'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB']
        )
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"Conectado a MySQL Server versión {db_info}")
            return connection
        else:
            print("No se pudo establecer la conexión")
            return None
            
    except Error as e:
        print(f"Error al conectar a MySQL: {str(e)}")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje completo: {str(e)}")
        return None

def get_all_routes():
    """Obtiene todas las rutas registradas en la aplicación"""
    routes = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        routes.append({
            'endpoint': rule.endpoint,
            'methods': methods,
            'path': str(rule),
            'arguments': list(rule.arguments)
        })
    return routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/endpoints')
def list_endpoints():
    """Muestra todos los endpoints disponibles en HTML"""
    routes = get_all_routes()
    
    # Filtrar solo las rutas de la API (opcional)
    api_routes = [r for r in routes if not r['path'].startswith('/static') and r['path'] != '/']
    
    # Generar tabla HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Endpoints Disponibles</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .method-get { color: #61affe; font-weight: bold; }
            .method-post { color: #49cc90; font-weight: bold; }
            .method-put { color: #fca130; font-weight: bold; }
            .method-delete { color: #f93e3e; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Endpoints Disponibles</h1>
        <table>
            <tr>
                <th>Método</th>
                <th>Ruta</th>
                <th>Endpoint</th>
                <th>Argumentos</th>
            </tr>
    """
    
    for route in sorted(api_routes, key=lambda x: x['path']):
        methods = route['methods'].split(',')
        methods_html = ', '.join([f'<span class="method-{m.lower()}">{m}</span>' for m in methods])
        
        html += f"""
        <tr>
            <td>{methods_html}</td>
            <td><a href="{route['path']}" target="_blank">{route['path']}</a></td>
            <td>{route['endpoint']}</td>
            <td>{', '.join(route['arguments']) or '-'}</td>
        </tr>
        """
    
    html += """
        </table>
        <p><a href="/api/docs" target="_blank">Documentación Swagger UI</a></p>
    </body>
    </html>
    """
    
    return html

@api.route('/api/registro')
class Registro(Resource):
    @api.doc('registrar_usuario')
    @api.expect(registro_model)
    @api.response(201, 'Usuario registrado exitosamente')
    @api.response(400, 'Datos inválidos')
    @api.response(500, 'Error del servidor')
    def post(self):
        """Registra un nuevo usuario"""
        data = api.payload
        
        nombre = data.get('nombre')
        apellido = data.get('apellido')
        email = data.get('email')
        password = data.get('password')
        
        if not all([nombre, apellido, email, password]):
            api.abort(400, 'Faltan campos requeridos')
        
        connection = None
        try:
            connection = get_db_connection()
            if not connection:
                api.abort(500, 'Error de conexión a la base de datos')
                
            cursor = connection.cursor(dictionary=True)
            
            # Verificar si el email ya existe
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            if cursor.fetchone():
                api.abort(400, 'El correo electrónico ya está registrado')
            
            # Hashear la contraseña
            hashed_password = generate_password_hash(password)
            
            # Insertar el nuevo usuario
            query = """
            INSERT INTO usuarios (nombre, apellido, email, password)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (nombre, apellido, email, hashed_password))
            connection.commit()
            
            return {
                'mensaje': 'Usuario registrado exitosamente',
                'usuario': {
                    'nombre': nombre,
                    'email': email
                }
            }, 201
            
        except Error as e:
            api.abort(500, f'Error en la base de datos: {str(e)}')
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

@api.route('/api/login')
class Login(Resource):
    @api.doc('iniciar_sesion')
    @api.expect(login_model)
    @api.response(200, 'Inicio de sesión exitoso')
    @api.response(401, 'Credenciales inválidas')
    @api.response(400, 'Datos inválidos')
    def post(self):
        """Inicia sesión con email y contraseña"""
        data = api.payload
        
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            api.abort(400, 'Email y contraseña son requeridos')
        
        connection = None
        try:
            connection = get_db_connection()
            if not connection:
                api.abort(500, 'Error de conexión a la base de datos')
                
            cursor = connection.cursor(dictionary=True)
            
            # Buscar usuario por email
            cursor.execute("""
                SELECT id, nombre, apellido, email, password 
                FROM usuarios 
                WHERE email = %s AND estado = 'activo'
            """, (email,))
            
            usuario = cursor.fetchone()
            
            if not usuario:
                api.abort(401, 'Credenciales inválidas')
            
            # Verificar contraseña
            if not check_password_hash(usuario['password'], password):
                api.abort(401, 'Credenciales inválidas')
            
            # Eliminar la contraseña del hash de la respuesta
            usuario.pop('password', None)
            
            return {
                'mensaje': 'Inicio de sesión exitoso',
                'usuario': usuario
            }, 200
            
        except Error as e:
            api.abort(500, f'Error en la base de datos: {str(e)}')
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

# Agregar los recursos a la API
api.add_resource(Registro, '/api/registro')
api.add_resource(Login, '/api/login')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
