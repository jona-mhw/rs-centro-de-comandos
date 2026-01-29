from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

db = SQLAlchemy()


class Perfil(db.Model):
    """Modelo para perfiles de usuario (roles)"""
    __tablename__ = 'perfiles'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(7), default='#2F7E81')
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Perfil {self.nombre}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'color': self.color
        }


class Paciente(db.Model):
    """Modelo para pacientes"""
    __tablename__ = 'pacientes'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200))
    rut = db.Column(db.String(12))
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Paciente {self.nombre or self.rut}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'rut': self.rut
        }


class Ubicacion(db.Model):
    """Modelo para ubicaciones (Torre/Piso/Sector)"""
    __tablename__ = 'ubicaciones'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # torre, piso, sector
    padre_id = db.Column(db.Integer, db.ForeignKey('ubicaciones.id'), nullable=True)
    camas_por_fila = db.Column(db.Integer, default=3)
    orden = db.Column(db.Integer, default=0)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    padre = db.relationship('Ubicacion', remote_side=[id], backref='hijos')
    camas = db.relationship('Cama', backref='ubicacion', lazy=True)

    def __repr__(self):
        return f'<Ubicacion {self.nombre}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'tipo': self.tipo,
            'padre_id': self.padre_id,
            'camas_por_fila': self.camas_por_fila,
            'orden': self.orden,
            'activo': self.activo
        }


class EstadoCama(db.Model):
    """Modelo para estados de cama"""
    __tablename__ = 'estados_cama'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), nullable=False)  # Color hexadecimal
    descripcion = db.Column(db.String(200))
    orden = db.Column(db.Integer, default=0)
    activo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<EstadoCama {self.nombre}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'color': self.color,
            'descripcion': self.descripcion
        }


class Cama(db.Model):
    """Modelo para camas"""
    __tablename__ = 'camas'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False)
    nombre = db.Column(db.String(100))
    ubicacion_id = db.Column(db.Integer, db.ForeignKey('ubicaciones.id'), nullable=False)
    estado_id = db.Column(db.Integer, db.ForeignKey('estados_cama.id'), nullable=False)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=True)
    estado_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    orden = db.Column(db.Integer, default=0)
    activo = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    estado = db.relationship('EstadoCama', backref='camas')
    paciente = db.relationship('Paciente', backref='camas')

    def __repr__(self):
        return f'<Cama {self.codigo}>'

    def tiempo_en_estado(self):
        """Calcula el tiempo transcurrido en el estado actual"""
        if self.estado_inicio:
            delta = datetime.utcnow() - self.estado_inicio
            return delta
        return timedelta(0)

    def tiempo_en_estado_str(self):
        """Retorna el tiempo en formato HH:MM:SS"""
        delta = self.tiempo_en_estado()
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours}:{minutes:02d}:{seconds:02d}"

    def tiempo_en_estado_minutos(self):
        """Retorna el tiempo en minutos"""
        delta = self.tiempo_en_estado()
        return int(delta.total_seconds() // 60)

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'ubicacion_id': self.ubicacion_id,
            'estado_id': self.estado_id,
            'estado': self.estado.to_dict() if self.estado else None,
            'paciente': self.paciente.to_dict() if self.paciente else None,
            'paciente_id': self.paciente_id,
            'tiempo_estado': self.tiempo_en_estado_str(),
            'tiempo_minutos': self.tiempo_en_estado_minutos(),
            'orden': self.orden
        }


class HistorialCama(db.Model):
    """Historial de cambios de estado de camas"""
    __tablename__ = 'historial_camas'

    id = db.Column(db.Integer, primary_key=True)
    cama_id = db.Column(db.Integer, db.ForeignKey('camas.id'), nullable=False)
    estado_anterior_id = db.Column(db.Integer, db.ForeignKey('estados_cama.id'))
    estado_nuevo_id = db.Column(db.Integer, db.ForeignKey('estados_cama.id'), nullable=False)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfiles.id'), nullable=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=True)
    usuario = db.Column(db.String(100))
    comentario = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    cama = db.relationship('Cama', backref='historial')
    estado_anterior = db.relationship('EstadoCama', foreign_keys=[estado_anterior_id])
    estado_nuevo = db.relationship('EstadoCama', foreign_keys=[estado_nuevo_id])
    perfil = db.relationship('Perfil', backref='historial')
    paciente = db.relationship('Paciente', backref='historial')

    def to_dict(self):
        return {
            'id': self.id,
            'cama_id': self.cama_id,
            'cama': self.cama.codigo if self.cama else None,
            'estado_anterior': self.estado_anterior.nombre if self.estado_anterior else None,
            'estado_nuevo': self.estado_nuevo.nombre if self.estado_nuevo else None,
            'perfil': self.perfil.nombre if self.perfil else None,
            'perfil_id': self.perfil_id,
            'paciente': self.paciente.to_dict() if self.paciente else None,
            'usuario': self.usuario,
            'comentario': self.comentario,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
