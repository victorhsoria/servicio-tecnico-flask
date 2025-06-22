from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from config import Config
import os
from datetime import datetime

# --- Inicialización de la Aplicación ---
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# --- Modelos de la Base de Datos ---
# Aquí definiremos nuestras tablas (Clientes, Servicios, Historial de Estados)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True)
    dni_cuit = db.Column(db.String(20), unique=True)
    # Relación con Servicios: un cliente puede tener muchos servicios
    servicios = db.relationship('Servicio', backref='cliente', lazy=True)

    def __repr__(self):
        return f'<Cliente {self.nombre} {self.apellido}>'

class Servicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    fecha_ingreso = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    tipo_equipo = db.Column(db.String(50), nullable=False)
    marca_modelo = db.Column(db.String(100))
    numero_serie = db.Column(db.String(100))
    problema_reportado = db.Column(db.Text, nullable=False)
    diagnostico = db.Column(db.Text)
    acciones_tomadas = db.Column(db.Text)
    componentes_utilizados = db.Column(db.Text)
    costo_total = db.Column(db.Float, default=0.0)
    fecha_finalizacion = db.Column(db.DateTime)
    fecha_entrega = db.Column(db.DateTime)
    # Estado actual del servicio
    estado_actual = db.Column(db.String(50), default='Pendiente') # Ejemplo: Pendiente, En Diagnostico, En Reparacion, Listo para retirar, Entregado
    # Relación con HistorialEstado: un servicio puede tener muchos cambios de estado
    historial_estados = db.relationship('HistorialEstado', backref='servicio', lazy=True, order_by='HistorialEstado.fecha.asc()')

    def __repr__(self):
        return f'<Servicio {self.id} - Cliente {self.cliente_id}>'

class HistorialEstado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicio.id'), nullable=False)
    estado = db.Column(db.String(50), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # Aquí podríamos añadir un campo para el usuario que realizó el cambio,
    # pero por ahora, como no gestionamos usuarios, lo omitimos.
    # usuario = db.Column(db.String(50)) # Para futuras implementaciones

    def __repr__(self):
        return f'<HistorialEstado Servicio: {self.servicio_id} - Estado: {self.estado} - Fecha: {self.fecha}>'

# --- Rutas de la Aplicación ---
# Aquí definiremos las URL y las funciones que las manejarán.

@app.route('/')
def index():
    # Una ruta simple para la página de inicio
    return render_template('index.html')

# --- Ejecución de la Aplicación ---
if __name__ == '__main__':
    # Esto crea la base de datos y las tablas si no existen
    with app.app_context():
        db.create_all()
    app.run(debug=True)