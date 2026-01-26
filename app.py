from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import db, Ubicacion, Cama, EstadoCama, HistorialCama

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///centro_comandos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

db.init_app(app)


def init_datos_dummy():
    """Inicializa datos dummy para la demo"""
    # Estados de cama
    estados = [
        {'nombre': 'Disponible', 'color': '#4CAF50', 'descripcion': 'Cama lista para recibir paciente', 'orden': 1},
        {'nombre': 'Ocupada', 'color': '#F44336', 'descripcion': 'Cama con paciente', 'orden': 2},
        {'nombre': 'En Limpieza', 'color': '#FF9800', 'descripcion': 'Cama en proceso de higienizacion', 'orden': 3},
        {'nombre': 'En Espera', 'color': '#FFC107', 'descripcion': 'Esperando asignacion', 'orden': 4},
        {'nombre': 'Mantenimiento', 'color': '#9E9E9E', 'descripcion': 'Cama en mantenimiento', 'orden': 5},
        {'nombre': 'Bloqueada', 'color': '#607D8B', 'descripcion': 'Cama no disponible', 'orden': 6},
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

    estado_disponible = EstadoCama.query.filter_by(nombre='Disponible').first()
    estado_ocupada = EstadoCama.query.filter_by(nombre='Ocupada').first()
    estado_limpieza = EstadoCama.query.filter_by(nombre='En Limpieza').first()

    estados_demo = [estado_disponible, estado_ocupada, estado_limpieza, estado_disponible, estado_ocupada]

    import random

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
                    cama = Cama(
                        codigo=f'{sector_nombre[:3].upper()}-{i:02d}',
                        nombre=f'Cama {i}',
                        ubicacion_id=sector.id,
                        estado_id=random.choice(estados_demo).id,
                        orden=i
                    )
                    db.session.add(cama)

    db.session.commit()


@app.route('/')
def index():
    """Vista principal - Monitor de camas"""
    torres = Ubicacion.query.filter_by(tipo='torre', activo=True).all()
    estados = EstadoCama.query.filter_by(activo=True).order_by(EstadoCama.orden).all()
    return render_template('index.html', torres=torres, estados=estados)


@app.route('/api/ubicacion/<int:ubicacion_id>/camas')
def get_camas_ubicacion(ubicacion_id):
    """Obtiene las camas de una ubicacion"""
    ubicacion = Ubicacion.query.get_or_404(ubicacion_id)
    camas = Cama.query.filter_by(ubicacion_id=ubicacion_id, activo=True).order_by(Cama.orden).all()
    return jsonify({
        'ubicacion': ubicacion.to_dict(),
        'camas': [c.to_dict() for c in camas]
    })


@app.route('/api/cama/<int:cama_id>/estado', methods=['POST'])
def cambiar_estado_cama(cama_id):
    """Cambia el estado de una cama"""
    cama = Cama.query.get_or_404(cama_id)
    data = request.get_json()

    nuevo_estado_id = data.get('estado_id')
    comentario = data.get('comentario', '')

    if not nuevo_estado_id:
        return jsonify({'error': 'estado_id es requerido'}), 400

    nuevo_estado = EstadoCama.query.get_or_404(nuevo_estado_id)

    # Guardar historial
    historial = HistorialCama(
        cama_id=cama.id,
        estado_anterior_id=cama.estado_id,
        estado_nuevo_id=nuevo_estado_id,
        comentario=comentario,
        usuario='Demo User'
    )
    db.session.add(historial)

    # Actualizar estado
    cama.estado_id = nuevo_estado_id
    db.session.commit()

    return jsonify({
        'success': True,
        'cama': cama.to_dict()
    })


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
    estados = EstadoCama.query.filter_by(activo=True).all()

    stats = {}
    for estado in estados:
        count = Cama.query.filter_by(estado_id=estado.id, activo=True).count()
        stats[estado.nombre] = {
            'count': count,
            'color': estado.color,
            'porcentaje': round((count / total_camas * 100) if total_camas > 0 else 0, 1)
        }

    return jsonify({
        'total': total_camas,
        'por_estado': stats
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_datos_dummy()
    app.run(debug=True, host='0.0.0.0', port=5000)
