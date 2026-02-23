from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import db, Ubicacion, Cama, EstadoCama, HistorialCama, Perfil, Paciente
from datetime import datetime, timedelta
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///centro_comandos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

db.init_app(app)


def init_datos_dummy():
    """Inicializa datos dummy para la demo"""
    # Perfiles de usuario
    perfiles = [
        {'nombre': 'Staff de Limpieza', 'color': '#8AC52F'},
        {'nombre': 'Enfermera', 'color': '#60B2B2'},
        {'nombre': 'Movilizador', 'color': '#9C27B0'},
    ]

    for perfil_data in perfiles:
        if not Perfil.query.filter_by(nombre=perfil_data['nombre']).first():
            perfil = Perfil(**perfil_data)
            db.session.add(perfil)

    db.session.commit()

    # Estados de cama
    estados = [
        {'nombre': 'Disponible', 'color': '#4CAF50', 'descripcion': 'Cama lista para recibir paciente', 'orden': 1},
        {'nombre': 'Ocupada', 'color': '#F44336', 'descripcion': 'Cama con paciente', 'orden': 2},
        {'nombre': 'Esperando Transporte', 'color': '#9C27B0', 'descripcion': 'Esperando traslado de paciente', 'orden': 3},
        {'nombre': 'Esperando Limpieza', 'color': '#FFC107', 'descripcion': 'Cama esperando ser limpiada', 'orden': 4},
        {'nombre': 'En Limpieza', 'color': '#FF9800', 'descripcion': 'Cama en proceso de higienizacion', 'orden': 5},
        {'nombre': 'Mantenimiento', 'color': '#9E9E9E', 'descripcion': 'Cama en mantenimiento', 'orden': 6},
        {'nombre': 'Bloqueada', 'color': '#607D8B', 'descripcion': 'Cama no disponible', 'orden': 7},
    ]

    for estado_data in estados:
        if not EstadoCama.query.filter_by(nombre=estado_data['nombre']).first():
            estado = EstadoCama(**estado_data)
            db.session.add(estado)

    db.session.commit()

    # Ubicaciones - Estructura jerarquica
    estructuras = [
        {
            'nombre': 'Torre A',
            'tipo': 'torre',
            'pisos': [
                {'nombre': 'Piso 1', 'sectores': ['UCI', 'Urgencias']},
                {'nombre': 'Piso 2', 'sectores': ['Medicina General', 'Cardiologia']},
                {'nombre': 'Piso 3', 'sectores': ['Cirugia', 'Traumatologia']},
            ]
        },
        {
            'nombre': 'Torre B',
            'tipo': 'torre',
            'pisos': [
                {'nombre': 'Piso 1', 'sectores': ['Pediatria', 'Neonatologia']},
                {'nombre': 'Piso 2', 'sectores': ['Maternidad', 'Ginecologia']},
            ]
        },
    ]

    # Obtener todos los estados
    estado_disponible = EstadoCama.query.filter_by(nombre='Disponible').first()
    estado_ocupada = EstadoCama.query.filter_by(nombre='Ocupada').first()
    estado_esp_transporte = EstadoCama.query.filter_by(nombre='Esperando Transporte').first()
    estado_esp_limpieza = EstadoCama.query.filter_by(nombre='Esperando Limpieza').first()
    estado_en_limpieza = EstadoCama.query.filter_by(nombre='En Limpieza').first()

    estados_demo = [
        estado_disponible, estado_ocupada, estado_ocupada,
        estado_esp_transporte, estado_esp_limpieza, estado_en_limpieza,
        estado_disponible, estado_ocupada
    ]

    import random

    # Crear pacientes dummy
    pacientes_dummy = [
        {'nombre': 'Juan Pérez', 'rut': '12.345.678-9'},
        {'nombre': 'María González', 'rut': '9.876.543-2'},
        {'nombre': 'Pedro Soto', 'rut': '15.432.167-K'},
        {'nombre': 'Ana Martínez', 'rut': '8.765.432-1'},
        {'nombre': 'Carlos Rojas', 'rut': '11.222.333-4'},
        {'nombre': 'Lucía Fernández', 'rut': '14.555.666-7'},
        {'nombre': 'Roberto Silva', 'rut': '7.888.999-0'},
        {'nombre': 'Carmen López', 'rut': '16.111.222-3'},
    ]

    for paciente_data in pacientes_dummy:
        if not Paciente.query.filter_by(rut=paciente_data['rut']).first():
            paciente = Paciente(**paciente_data)
            db.session.add(paciente)

    db.session.commit()

    pacientes = Paciente.query.all()
    perfiles = Perfil.query.all()

    for torre_data in estructuras:
        if Ubicacion.query.filter_by(nombre=torre_data['nombre'], tipo='torre').first():
            continue

        torre = Ubicacion(nombre=torre_data['nombre'], tipo='torre', camas_por_fila=4)
        db.session.add(torre)
        db.session.flush()

        for piso_data in torre_data['pisos']:
            piso = Ubicacion(
                nombre=piso_data['nombre'],
                tipo='piso',
                padre_id=torre.id,
                camas_por_fila=3
            )
            db.session.add(piso)
            db.session.flush()

            for sector_nombre in piso_data['sectores']:
                sector = Ubicacion(
                    nombre=sector_nombre,
                    tipo='sector',
                    padre_id=piso.id,
                    camas_por_fila=3
                )
                db.session.add(sector)
                db.session.flush()

                # Crear camas para cada sector
                num_camas = random.randint(4, 9)
                for i in range(1, num_camas + 1):
                    estado_cama = random.choice(estados_demo)
                    # Tiempo aleatorio: 15-58 minutos con segundos únicos usando random()
                    # Usamos random.random() para obtener fracciones de segundo únicas
                    total_segundos = random.randint(15 * 60, 58 * 60) + random.random() * 59
                    tiempo_random = timedelta(seconds=total_segundos)
                    estado_inicio = datetime.utcnow() - tiempo_random

                    # Asignar paciente solo si la cama está ocupada o en transporte
                    paciente_id = None
                    if estado_cama.nombre in ['Ocupada', 'Esperando Transporte']:
                        paciente_id = random.choice(pacientes).id if pacientes else None

                    cama = Cama(
                        codigo=f'{sector_nombre[:3].upper()}-{i:02d}',
                        nombre=f'Cama {i}',
                        ubicacion_id=sector.id,
                        estado_id=estado_cama.id,
                        paciente_id=paciente_id,
                        estado_inicio=estado_inicio,
                        orden=i
                    )
                    db.session.add(cama)

    db.session.commit()

    # Generar historial dummy para estadísticas (últimas 6 semanas)
    camas = Cama.query.all()
    for semana in range(6):
        for _ in range(random.randint(15, 40)):
            cama = random.choice(camas)
            perfil = random.choice(perfiles)
            estado_anterior = random.choice(estados_demo)
            estado_nuevo = random.choice(estados_demo)

            fecha = datetime.utcnow() - timedelta(weeks=semana, days=random.randint(0, 6), hours=random.randint(0, 23))

            historial = HistorialCama(
                cama_id=cama.id,
                estado_anterior_id=estado_anterior.id,
                estado_nuevo_id=estado_nuevo.id,
                perfil_id=perfil.id,
                usuario=f'Usuario {perfil.nombre}',
                created_at=fecha
            )
            db.session.add(historial)

    db.session.commit()


@app.route('/')
def index():
    """Vista principal - Monitor de camas"""
    torres = Ubicacion.query.filter_by(tipo='torre', activo=True).all()
    estados = EstadoCama.query.filter_by(activo=True).order_by(EstadoCama.orden).all()
    perfiles = Perfil.query.filter_by(activo=True).all()
    return render_template('index.html', torres=torres, estados=estados, perfiles=perfiles)


@app.route('/api/ubicacion/<int:ubicacion_id>/camas')
def get_camas_ubicacion(ubicacion_id):
    """Obtiene las camas de una ubicacion"""
    ubicacion = Ubicacion.query.get_or_404(ubicacion_id)
    camas = Cama.query.filter_by(ubicacion_id=ubicacion_id, activo=True).order_by(Cama.orden).all()
    return jsonify({
        'ubicacion': ubicacion.to_dict(),
        'camas': [c.to_dict() for c in camas]
    })


@app.route('/api/cama/<int:cama_id>')
def get_cama(cama_id):
    """Obtiene los datos de una cama"""
    cama = Cama.query.get_or_404(cama_id)
    return jsonify(cama.to_dict())


@app.route('/api/cama/<int:cama_id>/estado', methods=['POST'])
def cambiar_estado_cama(cama_id):
    """Cambia el estado de una cama"""
    cama = Cama.query.get_or_404(cama_id)
    data = request.get_json()

    nuevo_estado_id = data.get('estado_id')
    perfil_id = data.get('perfil_id')
    comentario = data.get('comentario', '')
    paciente_nombre = data.get('paciente_nombre', '').strip()
    paciente_rut = data.get('paciente_rut', '').strip()
    paciente_id = data.get('paciente_id')
    confirmar_traslado = data.get('confirmar_traslado', False)

    if not nuevo_estado_id:
        return jsonify({'error': 'estado_id es requerido'}), 400

    nuevo_estado = EstadoCama.query.get_or_404(nuevo_estado_id)

    cama_anterior = None  # Para registrar si hubo traslado

    # Manejar paciente si el nuevo estado es "Ocupada"
    if nuevo_estado.nombre == 'Ocupada':
        paciente = None

        if paciente_id:
            # Usar paciente existente por ID
            paciente = Paciente.query.get(paciente_id)
        elif paciente_rut:
            # Buscar por RUT primero
            paciente = Paciente.query.filter_by(rut=paciente_rut).first()
            if not paciente:
                paciente = Paciente(nombre=paciente_nombre, rut=paciente_rut)
                db.session.add(paciente)
                db.session.flush()
        elif paciente_nombre:
            # Crear nuevo paciente solo con nombre
            paciente = Paciente(nombre=paciente_nombre, rut='')
            db.session.add(paciente)
            db.session.flush()

        if paciente:
            # Verificar si el paciente ya está en otra cama
            cama_actual_paciente = Cama.query.filter(
                Cama.paciente_id == paciente.id,
                Cama.id != cama_id,
                Cama.activo == True
            ).first()

            if cama_actual_paciente and not confirmar_traslado:
                # Advertir al usuario sobre el traslado
                return jsonify({
                    'warning': True,
                    'message': f'El paciente {paciente.nombre or paciente.rut} ya está asignado a la cama {cama_actual_paciente.codigo}. ¿Desea trasladarlo?',
                    'paciente': paciente.to_dict(),
                    'cama_anterior': cama_actual_paciente.to_dict()
                })

            # Si hay cama anterior y se confirma el traslado, liberarla
            if cama_actual_paciente and confirmar_traslado:
                cama_anterior = cama_actual_paciente
                # Poner la cama anterior en estado "Esperando Limpieza"
                estado_limpieza = EstadoCama.query.filter_by(nombre='Esperando Limpieza').first()
                if estado_limpieza:
                    # Guardar historial de la cama anterior
                    historial_anterior = HistorialCama(
                        cama_id=cama_anterior.id,
                        estado_anterior_id=cama_anterior.estado_id,
                        estado_nuevo_id=estado_limpieza.id,
                        perfil_id=perfil_id,
                        paciente_id=paciente.id,
                        comentario=f'Paciente trasladado a cama {cama.codigo}',
                        usuario='Demo User'
                    )
                    db.session.add(historial_anterior)
                    cama_anterior.estado_id = estado_limpieza.id
                    cama_anterior.estado_inicio = datetime.utcnow()

                cama_anterior.paciente_id = None

            cama.paciente_id = paciente.id

    elif nuevo_estado.nombre == 'Disponible':
        # Limpiar paciente cuando la cama queda disponible
        cama.paciente_id = None

    # Guardar historial
    historial = HistorialCama(
        cama_id=cama.id,
        estado_anterior_id=cama.estado_id,
        estado_nuevo_id=nuevo_estado_id,
        perfil_id=perfil_id,
        paciente_id=cama.paciente_id,
        comentario=comentario,
        usuario='Demo User'
    )
    db.session.add(historial)

    # Actualizar estado y resetear tiempo
    cama.estado_id = nuevo_estado_id
    cama.estado_inicio = datetime.utcnow()
    db.session.commit()

    response_data = {
        'success': True,
        'cama': cama.to_dict()
    }

    if cama_anterior:
        response_data['traslado'] = True
        response_data['cama_anterior'] = cama_anterior.to_dict()

    return jsonify(response_data)


@app.route('/ubicaciones')
def ubicaciones():
    """Mantenedor de ubicaciones"""
    torres = Ubicacion.query.filter_by(tipo='torre', activo=True).all()
    return render_template('ubicaciones.html', torres=torres)


@app.route('/api/ubicacion', methods=['POST'])
def crear_ubicacion():
    """Crea una nueva ubicacion"""
    data = request.get_json()

    ubicacion = Ubicacion(
        nombre=data['nombre'],
        tipo=data['tipo'],
        padre_id=data.get('padre_id'),
        camas_por_fila=data.get('camas_por_fila', 3)
    )
    db.session.add(ubicacion)
    db.session.commit()

    return jsonify({'success': True, 'ubicacion': ubicacion.to_dict()})


@app.route('/api/ubicacion/<int:ubicacion_id>', methods=['PUT'])
def actualizar_ubicacion(ubicacion_id):
    """Actualiza una ubicacion"""
    ubicacion = Ubicacion.query.get_or_404(ubicacion_id)
    data = request.get_json()

    ubicacion.nombre = data.get('nombre', ubicacion.nombre)
    ubicacion.camas_por_fila = data.get('camas_por_fila', ubicacion.camas_por_fila)

    db.session.commit()
    return jsonify({'success': True, 'ubicacion': ubicacion.to_dict()})


@app.route('/api/ubicacion/<int:ubicacion_id>', methods=['DELETE'])
def eliminar_ubicacion(ubicacion_id):
    """Elimina (desactiva) una ubicacion"""
    ubicacion = Ubicacion.query.get_or_404(ubicacion_id)
    ubicacion.activo = False
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/cama', methods=['POST'])
def crear_cama():
    """Crea una nueva cama"""
    data = request.get_json()

    estado_default = EstadoCama.query.filter_by(nombre='Disponible').first()

    cama = Cama(
        codigo=data['codigo'],
        nombre=data.get('nombre', ''),
        ubicacion_id=data['ubicacion_id'],
        estado_id=data.get('estado_id', estado_default.id)
    )
    db.session.add(cama)
    db.session.commit()

    return jsonify({'success': True, 'cama': cama.to_dict()})


@app.route('/api/cama/<int:cama_id>', methods=['DELETE'])
def eliminar_cama(cama_id):
    """Elimina (desactiva) una cama"""
    cama = Cama.query.get_or_404(cama_id)
    cama.activo = False
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/estadisticas')
def estadisticas():
    """Obtiene estadisticas generales"""
    total_camas = Cama.query.filter_by(activo=True).count()
    estados = EstadoCama.query.filter_by(activo=True).order_by(EstadoCama.orden).all()

    stats = {}
    for estado in estados:
        count = Cama.query.filter_by(estado_id=estado.id, activo=True).count()
        stats[estado.nombre] = {
            'count': count,
            'color': estado.color,
            'orden': estado.orden,
            'porcentaje': round((count / total_camas * 100) if total_camas > 0 else 0, 1)
        }

    return jsonify({
        'total': total_camas,
        'por_estado': stats
    })


@app.route('/dashboard')
def dashboard():
    """Vista del dashboard con estadísticas"""
    perfiles = Perfil.query.filter_by(activo=True).all()
    estados = EstadoCama.query.filter_by(activo=True).order_by(EstadoCama.orden).all()
    return render_template('dashboard.html', perfiles=perfiles, estados=estados)


@app.route('/api/dashboard/registros-semana')
def registros_por_semana():
    """Obtiene registros históricos agrupados por semana y perfil"""
    perfiles = Perfil.query.filter_by(activo=True).all()

    # Obtener las últimas 6 semanas
    hoy = datetime.utcnow()
    semanas = []

    for i in range(5, -1, -1):
        inicio_semana = hoy - timedelta(weeks=i, days=hoy.weekday())
        inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
        fin_semana = inicio_semana + timedelta(days=6, hours=23, minutes=59, seconds=59)

        semana_data = {
            'semana': inicio_semana.strftime('%d/%m/%Y'),
            'perfiles': {}
        }

        for perfil in perfiles:
            count = HistorialCama.query.filter(
                HistorialCama.perfil_id == perfil.id,
                HistorialCama.created_at >= inicio_semana,
                HistorialCama.created_at <= fin_semana
            ).count()
            semana_data['perfiles'][perfil.nombre] = count

        semanas.append(semana_data)

    return jsonify({
        'semanas': semanas,
        'perfiles': [{'nombre': p.nombre, 'color': p.color} for p in perfiles]
    })


@app.route('/api/dashboard/tiempos-por-estado')
def tiempos_por_estado():
    """Obtiene las camas agrupadas por estado con tiempo transcurrido"""
    # Estados que queremos mostrar con tiempos
    estados_tiempo = ['Esperando Transporte', 'Esperando Limpieza', 'En Limpieza']

    resultado = {}

    for estado_nombre in estados_tiempo:
        estado = EstadoCama.query.filter_by(nombre=estado_nombre).first()
        if estado:
            camas = Cama.query.filter_by(estado_id=estado.id, activo=True).all()
            camas_data = []
            for cama in camas:
                camas_data.append({
                    'codigo': cama.codigo,
                    'tiempo_hms': cama.tiempo_en_estado_str(),
                    'tiempo_segundos': int(cama.tiempo_en_estado().total_seconds()),
                    'estado_inicio': cama.estado_inicio.isoformat() if cama.estado_inicio else None,
                    'paciente': cama.paciente.to_dict() if cama.paciente else None
                })
            # Ordenar por tiempo descendente
            camas_data.sort(key=lambda x: x['tiempo_segundos'], reverse=True)
            resultado[estado_nombre] = {
                'color': estado.color,
                'camas': camas_data
            }

    return jsonify(resultado)


@app.route('/api/perfiles')
def get_perfiles():
    """Obtiene todos los perfiles activos"""
    perfiles = Perfil.query.filter_by(activo=True).all()
    return jsonify([p.to_dict() for p in perfiles])


@app.route('/api/pacientes')
def get_pacientes():
    """Obtiene todos los pacientes activos"""
    pacientes = Paciente.query.filter_by(activo=True).all()
    return jsonify([p.to_dict() for p in pacientes])


@app.route('/api/paciente', methods=['POST'])
def crear_paciente():
    """Crea un nuevo paciente"""
    data = request.get_json()

    nombre = data.get('nombre', '').strip()
    rut = data.get('rut', '').strip()

    if not nombre and not rut:
        return jsonify({'error': 'Se requiere al menos nombre o RUT'}), 400

    # Verificar si el paciente ya existe por RUT
    if rut:
        paciente_existente = Paciente.query.filter_by(rut=rut).first()
        if paciente_existente:
            return jsonify({'success': True, 'paciente': paciente_existente.to_dict(), 'existente': True})

    paciente = Paciente(nombre=nombre, rut=rut)
    db.session.add(paciente)
    db.session.commit()

    return jsonify({'success': True, 'paciente': paciente.to_dict(), 'existente': False})


with app.app_context():
    db.create_all()
    init_datos_dummy()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
