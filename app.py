from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from config import Config
import os
from datetime import datetime, timedelta
from sqlalchemy import func, extract # Asegúrate de que 'extract' también esté importado

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# --- Context Processor para 'now' (Fecha/Hora Actual) ---
@app.context_processor
def inject_now():
    """Hace que la variable 'now' (datetime.now()) esté disponible en todas las plantillas."""
    return {'now': datetime.now()}

# --- Filtro personalizado para Jinja2 ---
@app.template_filter('format_currency')
def format_currency_filter(value):
    if value is None:
        return "$ 0.00"
    return f"$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- Modelos de la Base de Datos ---
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    dni_cuit = db.Column(db.String(20), unique=True, nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    servicios = db.relationship('Servicio', backref='cliente', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"Cliente('{self.nombre}', '{self.apellido}', '{self.dni_cuit}')"

class Servicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    tipo_equipo = db.Column(db.String(100), nullable=False)
    marca_modelo = db.Column(db.String(100), nullable=True)
    problema_reportado = db.Column(db.Text, nullable=False)
    observaciones_tecnicas = db.Column(db.Text, nullable=True)
    solucion_implementada = db.Column(db.Text, nullable=True)
    costo_total = db.Column(db.Float, nullable=True, default=0.0)
    fecha_ingreso = db.Column(db.DateTime, nullable=False, default=datetime.now)
    fecha_entrega = db.Column(db.DateTime, nullable=True)
    estado_actual = db.Column(db.String(50), nullable=False, default='Pendiente')
    historial_estados = db.relationship('HistorialEstado', backref='servicio', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"Servicio('{self.id}', '{self.cliente.nombre} {self.cliente.apellido}', '{self.tipo_equipo}', '{self.estado_actual}')"

class HistorialEstado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicio.id'), nullable=False)
    estado = db.Column(db.String(50), nullable=False)
    fecha_cambio = db.Column(db.DateTime, nullable=False, default=datetime.now)
    observaciones = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"HistorialEstado('{self.servicio_id}', '{self.estado}', '{self.fecha_cambio}')"

# --- Rutas de la Aplicación ---
@app.route('/')
def index():
    # Obtener el número total de clientes
    total_clientes = Cliente.query.count()

    # Obtener el número total de servicios
    total_servicios = Servicio.query.count()

    # Obtener el conteo de servicios por estado
    servicios_por_estado = db.session.query(
        Servicio.estado_actual,
        func.count(Servicio.id)
    ).group_by(Servicio.estado_actual).all()

    # Convertir la lista de tuplas a un diccionario para fácil acceso en la plantilla
    # Ejemplo: {'Pendiente': 5, 'En Reparación': 3, ...}
    estado_counts = {estado: count for estado, count in servicios_por_estado}

    # Definir los estados que queremos mostrar y su clase CSS de Bootstrap
    estados_interes = [
        {'estado': 'Pendiente', 'clase': 'secondary', 'icono': 'bi-clock'},
        {'estado': 'En Diagnóstico', 'clase': 'info', 'icono': 'bi-search'},
        {'estado': 'En Reparación', 'clase': 'primary', 'icono': 'bi-wrench'},
        {'estado': 'En Espera de Repuestos', 'clase': 'warning', 'icono': 'bi-hourglass-split'},
        {'estado': 'Listo para Retirar', 'clase': 'success', 'icono': 'bi-check-circle'},
        # No incluimos 'Entregado' ni 'Cancelado' aquí ya que son estados "finales",
        # pero puedes añadirlos si te interesa ver su conteo en la pantalla principal.
    ]
    
    # Asegurarse de que cada estado en estados_interes tenga un conteo (0 si no hay servicios)
    servicios_resumen = []
    for estado_info in estados_interes:
        estado = estado_info['estado']
        count = estado_counts.get(estado, 0)
        servicios_resumen.append({
            'estado': estado,
            'count': count,
            'clase': estado_info['clase'],
            'icono': estado_info['icono']
        })


    return render_template('index.html',
                           total_clientes=total_clientes,
                           total_servicios=total_servicios,
                           servicios_resumen=servicios_resumen)

# Clientes
@app.route('/clientes')
def listar_clientes():
    query = request.args.get('q', '').strip()
    if query:
        clientes = Cliente.query.filter(
            (Cliente.nombre.ilike(f'%{query}%')) |
            (Cliente.apellido.ilike(f'%{query}%'))
        ).order_by(Cliente.apellido).all()
    else:
        clientes = Cliente.query.order_by(Cliente.apellido).all()
    return render_template('clientes/listar.html', clientes=clientes, query=query)

@app.route('/clientes/nuevo', methods=['GET', 'POST'])
def nuevo_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        dni_cuit = request.form['dni_cuit'] if request.form['dni_cuit'] else None
        telefono = request.form['telefono'] if request.form['telefono'] else None
        email = request.form['email'] if request.form['email'] else None
        direccion = request.form['direccion'] if request.form['direccion'] else None

        if Cliente.query.filter_by(dni_cuit=dni_cuit).first() and dni_cuit:
            flash('Ya existe un cliente con ese DNI/CUIT.', 'danger')
            return render_template('clientes/formulario.html', cliente=None)
        if Cliente.query.filter_by(email=email).first() and email:
            flash('Ya existe un cliente con ese Email.', 'danger')
            return render_template('clientes/formulario.html', cliente=None)

        nuevo = Cliente(nombre=nombre, apellido=apellido, dni_cuit=dni_cuit,
                        telefono=telefono, email=email, direccion=direccion)
        db.session.add(nuevo)
        db.session.commit()
        flash('Cliente agregado exitosamente!', 'success')
        return redirect(url_for('listar_clientes'))
    return render_template('clientes/formulario.html', cliente=None)

@app.route('/clientes/editar/<int:cliente_id>', methods=['GET', 'POST'])
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    if request.method == 'POST':
        cliente.nombre = request.form['nombre']
        cliente.apellido = request.form['apellido']
        
        new_dni_cuit = request.form['dni_cuit'] if request.form['dni_cuit'] else None
        if new_dni_cuit and Cliente.query.filter_by(dni_cuit=new_dni_cuit).first() and Cliente.query.filter_by(dni_cuit=new_dni_cuit).first().id != cliente.id:
            flash('Ya existe otro cliente con ese DNI/CUIT.', 'danger')
            return render_template('clientes/formulario.html', cliente=cliente)
        cliente.dni_cuit = new_dni_cuit

        new_email = request.form['email'] if request.form['email'] else None
        if new_email and Cliente.query.filter_by(email=new_email).first() and Cliente.query.filter_by(email=new_email).first().id != cliente.id:
            flash('Ya existe otro cliente con ese Email.', 'danger')
            return render_template('clientes/formulario.html', cliente=cliente)
        cliente.email = new_email

        cliente.telefono = request.form['telefono'] if request.form['telefono'] else None
        cliente.direccion = request.form['direccion'] if request.form['direccion'] else None
        
        db.session.commit()
        flash('Cliente actualizado exitosamente!', 'success')
        return redirect(url_for('listar_clientes'))
    return render_template('clientes/formulario.html', cliente=cliente)

@app.route('/clientes/eliminar/<int:cliente_id>', methods=['POST'])
def eliminar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente eliminado exitosamente!', 'success')
    return redirect(url_for('listar_clientes'))

# Servicios
@app.route('/servicios')
def listar_servicios():
    query = request.args.get('q', '').strip()
    estado_filtro = request.args.get('estado_filtro', '').strip()
    mes_filtro = request.args.get('mes_filtro', '').strip()

    servicios = Servicio.query

    if query:
        # Buscar por nombre o apellido del cliente asociado al servicio
        servicios = servicios.join(Cliente).filter(
            (Cliente.nombre.ilike(f'%{query}%')) |
            (Cliente.apellido.ilike(f'%{query}%'))
        )

    if estado_filtro:
        servicios = servicios.filter_by(estado_actual=estado_filtro)

    if mes_filtro == 'ultimo_mes':
        # Calcular la fecha de inicio del último mes (últimos 30 días desde hoy)
        fecha_hace_un_mes = datetime.now() - timedelta(days=30)
        servicios = servicios.filter(Servicio.fecha_ingreso >= fecha_hace_un_mes)

    servicios = servicios.order_by(Servicio.fecha_ingreso.desc()).all()

    # Pasar los valores de filtro actuales a la plantilla para que se mantengan seleccionados
    return render_template(
        'servicios/listar.html',
        servicios=servicios,
        query=query,
        estado_filtro_actual=estado_filtro,
        mes_filtro_actual=mes_filtro
    )

@app.route('/servicios/nuevo', methods=['GET', 'POST'])
def nuevo_servicio():
    clientes = Cliente.query.order_by(Cliente.apellido, Cliente.nombre).all()
    if not clientes:
        flash('Debe registrar al menos un cliente antes de agregar un servicio.', 'warning')
        return redirect(url_for('nuevo_cliente'))

    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        tipo_equipo = request.form['tipo_equipo']
        problema_reportado = request.form['problema_reportado']

        # Usar .get() para campos opcionales que pueden no estar presentes o estar vacíos
        marca_modelo = request.form.get('marca_modelo')
        observaciones_tecnicas = request.form.get('observaciones_tecnicas')
        solucion_implementada = request.form.get('solucion_implementada')
        
        # Manejo de costo_total: obtenerlo de forma segura y convertir a float
        costo_total_str = request.form.get('costo_total', '0.0') # Default a '0.0' si no está presente
        try:
            costo_total = float(costo_total_str) if costo_total_str else 0.0
        except ValueError:
            flash('El costo total debe ser un número válido.', 'danger')
            return render_template('servicios/formulario.html', clientes=clientes, servicio=None)

        estado_actual = request.form.get('estado_actual', 'Pendiente') # Default a 'Pendiente'
        fecha_entrega_str = request.form.get('fecha_entrega')
        
        fecha_entrega = None
        if fecha_entrega_str:
            try:
                fecha_entrega = datetime.strptime(fecha_entrega_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Formato de fecha de entrega inválido.', 'danger')
                return render_template('servicios/formulario.html', clientes=clientes, servicio=None)

        nuevo = Servicio(cliente_id=cliente_id, tipo_equipo=tipo_equipo,
                         marca_modelo=marca_modelo, problema_reportado=problema_reportado,
                         observaciones_tecnicas=observaciones_tecnicas,
                         solucion_implementada=solucion_implementada,
                         costo_total=costo_total, estado_actual=estado_actual,
                         fecha_entrega=fecha_entrega)
        db.session.add(nuevo)
        db.session.commit() # Primero guardamos el servicio para obtener su ID

        # Guardar el estado inicial en el historial
        historial_inicial = HistorialEstado(servicio_id=nuevo.id, estado=estado_actual, observaciones='Estado inicial al crear el servicio')
        db.session.add(historial_inicial)
        db.session.commit()

        flash('Servicio agregado exitosamente!', 'success')
        return redirect(url_for('listar_servicios'))
    return render_template('servicios/formulario.html', clientes=clientes, servicio=None)

@app.route('/servicios/editar/<int:servicio_id>', methods=['GET', 'POST'])
def editar_servicio(servicio_id):
    servicio = Servicio.query.get_or_404(servicio_id)
    clientes = Cliente.query.order_by(Cliente.apellido, Cliente.nombre).all()
    estados_posibles = ['Pendiente', 'En Diagnóstico', 'En Reparación', 'En Espera de Repuestos', 'Listo para Retirar', 'Entregado', 'Cancelado']

    if request.method == 'POST':
        old_estado = servicio.estado_actual # Guardar el estado anterior para comparar

        servicio.cliente_id = request.form['cliente_id']
        servicio.tipo_equipo = request.form['tipo_equipo']
        servicio.marca_modelo = request.form.get('marca_modelo') # Usar .get()
        servicio.problema_reportado = request.form['problema_reportado']
        servicio.observaciones_tecnicas = request.form.get('observaciones_tecnicas') # Usar .get()
        servicio.solucion_implementada = request.form.get('solucion_implementada') # Usar .get()
        
        # Manejo de costo_total: obtenerlo de forma segura y convertir a float
        costo_total_str = request.form.get('costo_total', '0.0') # Default a '0.0' si no está presente
        try:
            servicio.costo_total = float(costo_total_str) if costo_total_str else 0.0
        except ValueError:
            flash('El costo total debe ser un número válido.', 'danger')
            return render_template('servicios/formulario.html', clientes=clientes, servicio=servicio, estados_posibles=estados_posibles)

        new_estado = request.form.get('estado_actual', 'Pendiente') # Usar .get(), default a 'Pendiente'
        servicio.estado_actual = new_estado

        fecha_entrega_str = request.form.get('fecha_entrega') # Usar .get()
        if fecha_entrega_str:
            try:
                servicio.fecha_entrega = datetime.strptime(fecha_entrega_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Formato de fecha de entrega inválido.', 'danger')
                return render_template('servicios/formulario.html', clientes=clientes, servicio=servicio, estados_posibles=estados_posibles)
        else:
            servicio.fecha_entrega = None

        # Si el estado ha cambiado, guardar en el historial
        if old_estado != new_estado:
            historial_nuevo = HistorialEstado(servicio_id=servicio.id, estado=new_estado, observaciones=f"Estado cambiado de '{old_estado}' a '{new_estado}'")
            db.session.add(historial_nuevo)

        db.session.commit()
        flash('Servicio actualizado exitosamente!', 'success')
        return redirect(url_for('listar_servicios'))
    
    # Formatear la fecha de entrega para el campo datetime-local
    fecha_entrega_formato = servicio.fecha_entrega.strftime('%Y-%m-%dT%H:%M') if servicio.fecha_entrega else ''
    
    return render_template('servicios/formulario.html', clientes=clientes, servicio=servicio, 
                           estados_posibles=estados_posibles, fecha_entrega_formato=fecha_entrega_formato)

@app.route('/servicios/detalle/<int:servicio_id>')
def detalle_servicio(servicio_id):
    servicio = Servicio.query.get_or_404(servicio_id)
    # Ordenar el historial de estados por fecha de cambio descendente para mostrar el más reciente primero
    historial = HistorialEstado.query.filter_by(servicio_id=servicio.id).order_by(HistorialEstado.fecha_cambio.desc()).all()
    return render_template('servicios/detalle.html', servicio=servicio, historial=historial)

@app.route('/servicios/eliminar/<int:servicio_id>', methods=['POST'])
def eliminar_servicio(servicio_id):
    servicio = Servicio.query.get_or_404(servicio_id)
    db.session.delete(servicio)
    db.session.commit()
    flash('Servicio eliminado exitosamente!', 'success')
    return redirect(url_for('listar_servicios'))

@app.route('/servicios/imprimir/<int:servicio_id>')
def imprimir_servicio(servicio_id):
    servicio = Servicio.query.get_or_404(servicio_id)
    # Aquí es donde podrías cargar un historial si lo necesitaras para la impresión,
    # pero para la primera versión simplemente pasamos el servicio.

    # En el futuro, aquí renderizarías una plantilla específica para impresión
    # que tendría un diseño optimizado para eso (sin menú, sin pie de página, etc.).
    return render_template('servicios/imprimir_servicio.html', servicio=servicio)

@app.route('/reportes', methods=['GET'])
def reportes():
    # Parámetros de filtro de fecha
    fecha_inicio_str = request.args.get('fecha_inicio')
    fecha_fin_str = request.args.get('fecha_fin')

    fecha_inicio = None
    fecha_fin = None

    if fecha_inicio_str:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
        except ValueError:
            flash('Formato de fecha de inicio inválido.', 'danger')
            fecha_inicio_str = None # Reset para no mantener un valor erróneo
            
    if fecha_fin_str:
        try:
            # Asegurar que fecha_fin incluye todo el día seleccionado
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
        except ValueError:
            flash('Formato de fecha de fin inválido.', 'danger')
            fecha_fin_str = None # Reset para no mantener un valor erróneo

    # Consulta base para servicios, aplicando filtros de fecha si existen
    query_servicios = Servicio.query
    if fecha_inicio:
        query_servicios = query_servicios.filter(Servicio.fecha_ingreso >= fecha_inicio)
    if fecha_fin:
        query_servicios = query_servicios.filter(Servicio.fecha_ingreso <= fecha_fin)

    # 1. Ingresos por período (Solo de servicios 'Entregado' para un ingreso real)
    # Aquí podríamos considerar si los servicios están en estado 'Entregado'
    # para considerarlos como ingresos realizados.
    ingresos_query = Servicio.query.filter(Servicio.estado_actual == 'Entregado')
    if fecha_inicio:
        ingresos_query = ingresos_query.filter(Servicio.fecha_ingreso >= fecha_inicio)
    if fecha_fin:
        ingresos_query = ingresos_query.filter(Servicio.fecha_ingreso <= fecha_fin)
    
    total_ingresos = ingresos_query.with_entities(func.sum(Servicio.costo_total)).scalar() or 0.0

    # 2. Servicios por Estado
    servicios_por_estado = query_servicios.with_entities(
        Servicio.estado_actual,
        func.count(Servicio.id)
    ).group_by(Servicio.estado_actual).order_by(func.count(Servicio.id).desc()).all()
    
    # Calcular el total de servicios filtrados para los porcentajes
    total_servicios_filtrados = sum(count for _, count in servicios_por_estado)

    # 3. Servicios por Tipo de Equipo
    servicios_por_tipo_equipo = query_servicios.with_entities(
        Servicio.tipo_equipo,
        func.count(Servicio.id)
    ).group_by(Servicio.tipo_equipo).order_by(func.count(Servicio.id).desc()).all()

    # 4. Servicios por Cliente (Top 5)
    servicios_por_cliente = query_servicios.join(Cliente).with_entities(
        Cliente.nombre,
        Cliente.apellido,
        func.count(Servicio.id)
    ).group_by(Cliente.id, Cliente.nombre, Cliente.apellido).order_by(func.count(Servicio.id).desc()).limit(5).all()


    return render_template('reportes/index.html',
                           total_ingresos=total_ingresos,
                           servicios_por_estado=servicios_por_estado,
                           total_servicios_filtrados=total_servicios_filtrados,
                           servicios_por_tipo_equipo=servicios_por_tipo_equipo,
                           servicios_por_cliente=servicios_por_cliente,
                           fecha_inicio_str=fecha_inicio_str,
                           fecha_fin_str=request.args.get('fecha_fin')) # Pasar el string original de fecha_fin


# --- Ejecución de la Aplicación ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)