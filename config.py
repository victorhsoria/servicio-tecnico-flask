import os

# Obtiene la ruta base del directorio de la aplicación
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Configuración de la base de datos SQLite
    # La base de datos se creará en el mismo directorio de la aplicación
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'servicio_tecnico.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Puedes añadir una clave secreta para seguridad en futuras etapas
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_cadena_secreta_muy_dificil_de_adivinar'