from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


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
    orden = db.Column(db.Integer, default=0)
    activo = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    estado = db.relationship('EstadoCama', backref='camas')

    def __repr__(self):
        return f'<Cama {self.codigo}>'

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'ubicacion_id': self.ubicacion_id,
            'estado_id': self.estado_id,
            'estado': self.estado.to_dict() if self.estado else None,
            'orden': self.orden
        }


class HistorialCama(db.Model):
    """Historial de cambios de estado de camas"""
    __tablename__ = 'historial_camas'

    id = db.Column(db.Integer, primary_key=True)
    cama_id = db.Column(db.Integer, db.ForeignKey('camas.id'), nullable=False)
    estado_anterior_id = db.Column(db.Integer, db.ForeignKey('estados_cama.id'))
    estado_nuevo_id = db.Column(db.Integer, db.ForeignKey('estados_cama.id'), nullable=False)
    usuario = db.Column(db.String(100))
    comentario = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    cama = db.relationship('Cama', backref='historial')
    estado_anterior = db.relationship('EstadoCama', foreign_keys=[estado_anterior_id])
    estado_nuevo = db.relationship('EstadoCama', foreign_keys=[estado_nuevo_id])
