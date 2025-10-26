from flask import Flask, request, jsonify, session
from flask_cors import CORS
from config import Config
from models import Database, Usuario
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Configurar CORS
CORS(app, supports_credentials=True, origins=Config.CORS_ORIGINS)

# Inicializar la base de datos
with app.app_context():
    Database.init_db()


def validar_email(email):
    """Valida formato de email"""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None


def validar_password(password):
    """Valida que la contraseña tenga al menos 6 caracteres"""
    return len(password) >= 6


@app.route('/')
def index():
    """Ruta de prueba"""
    return jsonify({
        'message': 'API de ComparaPre funcionando correctamente',
        'status': 'online'
    })


@app.route('/api/registro', methods=['POST'])
def registro():
    """Endpoint para registrar un nuevo usuario"""
    try:
        data = request.get_json()
        
        # Validar datos recibidos
        nombre = data.get('nombre', '').strip()
        apellido = data.get('apellido', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        password_confirmacion = data.get('password_confirmacion', '')
        
        # Validaciones
        if not all([nombre, apellido, email, password, password_confirmacion]):
            return jsonify({
                'success': False,
                'message': 'Todos los campos son obligatorios'
            }), 400
        
        if not validar_email(email):
            return jsonify({
                'success': False,
                'message': 'El formato del correo electrónico no es válido'
            }), 400
        
        if password != password_confirmacion:
            return jsonify({
                'success': False,
                'message': 'Las contraseñas no coinciden'
            }), 400
        
        if not validar_password(password):
            return jsonify({
                'success': False,
                'message': 'La contraseña debe tener al menos 6 caracteres'
            }), 400
        
        # Crear usuario
        resultado = Usuario.crear_usuario(nombre, apellido, email, password)
        
        if resultado['success']:
            return jsonify(resultado), 201
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error en el servidor: {str(e)}'
        }), 500


@app.route('/api/login', methods=['POST'])
def login():
    """Endpoint para iniciar sesión"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        recordar = data.get('recordar', False)
        
        # Validaciones
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email y contraseña son obligatorios'
            }), 400
        
        if not validar_email(email):
            return jsonify({
                'success': False,
                'message': 'El formato del correo electrónico no es válido'
            }), 400
        
        # Verificar credenciales
        resultado = Usuario.verificar_credenciales(email, password)
        
        if resultado['success']:
            # Guardar información en sesión
            session['user_id'] = resultado['user']['id']
            session['user_email'] = resultado['user']['email']
            session['user_nombre'] = resultado['user']['nombre']
            
            # Configurar duración de sesión
            if recordar:
                session.permanent = True
            
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error en el servidor: {str(e)}'
        }), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    """Endpoint para cerrar sesión"""
    try:
        session.clear()
        return jsonify({
            'success': True,
            'message': 'Sesión cerrada correctamente'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al cerrar sesión: {str(e)}'
        }), 500


@app.route('/api/verificar-email', methods=['POST'])
def verificar_email():
    """Endpoint para verificar si un email ya existe"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Email requerido'
            }), 400
        
        existe = Usuario.email_existe(email)
        
        return jsonify({
            'success': True,
            'existe': existe
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/api/usuario-actual', methods=['GET'])
def usuario_actual():
    """Endpoint para obtener información del usuario en sesión"""
    try:
        if 'user_id' in session:
            return jsonify({
                'success': True,
                'user': {
                    'id': session['user_id'],
                    'email': session['user_email'],
                    'nombre': session['user_nombre']
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'No hay sesión activa'
            }), 401
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Servidor iniciado en http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)