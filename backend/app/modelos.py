from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Enum, Numeric, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
import enum
from .database import Base

# =============================================================================
# ENUMS (Creados en tambien en la Base de Datos)
# =============================================================================

class PrioridadEncuesta(str, enum.Enum):
    obligatoria = "obligatoria"
    opcional = "opcional"
    evaluacion_docente = "evaluacion_docente"

class AccionDisparadora(str, enum.Enum):
    al_iniciar_sesion = "al_iniciar_sesion"
    al_ver_curso = "al_ver_curso"
    al_inscribir_examen = "al_inscribir_examen"

class TipoPregunta(str, enum.Enum):
    texto_libre = "texto_libre"
    opcion_unica = "opcion_unica"
    opcion_multiple = "opcion_multiple"
    matriz = "matriz"
    seccion = "seccion"

class EstadoAsignacion(str, enum.Enum):
    pendiente = "pendiente"
    realizada = "realizada"
    cancelada = "cancelada"

class PublicoObjetivo(str, enum.Enum):
    alumnos = "alumnos"
    docentes = "docentes"
    ambos = "ambos"

class RolAdmin(str, enum.Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    DIRECTIVO = "DIRECTIVO"

class EstadoEncuesta(str, enum.Enum):
    borrador = "borrador"
    publicado = "publicado"
    en_curso = "en_curso"
    finalizado = "finalizado"

# =============================================================================
# ESQUEMA OLTP (Transaccional)
# =============================================================================

class UsuarioAdmin(Base):
    __tablename__ = "usuario_admin"
    __table_args__ = {"schema": "encuestas_oltp"}

    id_admin = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String(50), unique=True, nullable=False)
    clave_encriptada = Column(String(255), nullable=False)
    rol = Column(Enum(RolAdmin, schema="encuestas_oltp"), nullable=False)
    fecha_creacion = Column(DateTime, nullable=False)
    fecha_ultimo_login = Column(DateTime, nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    debe_cambiar_clave = Column(Boolean, default=False, nullable=False)

    permisos_especificos = relationship("UsuarioPermiso", back_populates="usuario", cascade="all, delete-orphan")

class Permiso(Base):
    __tablename__ = "permiso"
    __table_args__ = {"schema": "encuestas_oltp"}

    id_permiso = Column(Integer, primary_key=True)
    codigo = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    categoria = Column(String(30), nullable=False)

    asignaciones_rol = relationship("RolPermiso", back_populates="permiso", cascade="all, delete-orphan")
    asignaciones_usuario = relationship("UsuarioPermiso", back_populates="permiso", cascade="all, delete-orphan")

class RolPermiso(Base):
    __tablename__ = "rol_permiso"
    __table_args__ = {"schema": "encuestas_oltp"}

    id_rol = Column(Enum(RolAdmin, schema="encuestas_oltp"), ForeignKey("encuestas_oltp.usuario_admin.rol"), primary_key=True) # Nota: referencia a enum o solo tipo, el SQL usa id_rol como enum
    # En SQLAlchemy, ForeignKey a un Enum puede ser tricky si no hay tabla de roles.
    # Dado que el esquema SQL define id_rol como tipo enum y no FK a una tabla, aquí lo modelamos como columna simple parte de la PK compuesta.
    # Pero para consistencia con el SQL proveido:
    # id_rol encuestas_oltp.rol_admin NOT NULL
    id_rol = Column(Enum(RolAdmin, schema="encuestas_oltp"), primary_key=True)
    id_permiso = Column(Integer, ForeignKey("encuestas_oltp.permiso.id_permiso"), primary_key=True)

    permiso = relationship("Permiso", back_populates="asignaciones_rol")

class UsuarioPermiso(Base):
    __tablename__ = "usuario_permiso"
    __table_args__ = {"schema": "encuestas_oltp"}

    id_usuario = Column(Integer, ForeignKey("encuestas_oltp.usuario_admin.id_admin"), primary_key=True)
    id_permiso = Column(Integer, ForeignKey("encuestas_oltp.permiso.id_permiso"), primary_key=True)
    tiene = Column(Boolean, default=True, nullable=False)

    usuario = relationship("UsuarioAdmin", back_populates="permisos_especificos")
    permiso = relationship("Permiso", back_populates="asignaciones_usuario")

class Encuesta(Base):
    __tablename__ = "encuesta"
    __table_args__ = {"schema": "encuestas_oltp"}

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    mensaje_final = Column(Text, nullable=True)
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)
    prioridad = Column(Enum(PrioridadEncuesta, schema="encuestas_oltp"), nullable=False)
    acciones_disparadoras = Column(JSONB, default=list) 
    activo = Column(Boolean, default=True)
    configuracion = Column(JSONB, default=dict) 
    estado = Column(Enum(EstadoEncuesta, schema="encuestas_oltp"), default=EstadoEncuesta.borrador)

    # Relaciones
    reglas = relationship("ReglaAsignacion", back_populates="encuesta", cascade="all, delete-orphan")
    preguntas = relationship("Pregunta", back_populates="encuesta", cascade="all, delete-orphan")
    asignaciones = relationship("AsignacionUsuario", back_populates="encuesta")

    usuario_creacion = Column(
        Integer,
        ForeignKey("encuestas_oltp.usuario_admin.id_admin", ondelete="RESTRICT"),
        nullable=False
    )
    usuario_modificacion = Column(
        Integer,
        ForeignKey("encuestas_oltp.usuario_admin.id_admin", ondelete="SET NULL"),
        nullable=True
    )
    fecha_creacion = Column(
        DateTime,
        server_default=func.now(), # ← establece automáticamente en INSERT
        nullable=False
    )
    fecha_modificacion = Column(
        DateTime,
        onupdate=func.now(),  # ← actualiza automáticamente en UPDATE
        nullable=True
    )

 # === RELACIONES ===
    creador = relationship(
        "UsuarioAdmin",
        foreign_keys=[usuario_creacion],
        backref="encuestas_creadas"
    )
    modificador = relationship(
        "UsuarioAdmin",
        foreign_keys=[usuario_modificacion],
        backref="encuestas_modificadas"
    )


    @property
    def cantidad_preguntas(self):
        return sum(1 for p in self.preguntas if p.tipo != TipoPregunta.seccion)

    @property
    def cantidad_respuestas(self):
        return sum(1 for a in self.asignaciones if a.estado == EstadoAsignacion.realizada)

class ReglaAsignacion(Base):
    __tablename__ = "regla_asignacion"
    __table_args__ = {"schema": "encuestas_oltp"}

    id = Column(Integer, primary_key=True)
    id_encuesta = Column(Integer, ForeignKey("encuestas_oltp.encuesta.id"), nullable=False)
    id_facultad = Column(Integer, nullable=True)
    id_carrera = Column(Integer, nullable=True)
    id_asignatura = Column(Integer, nullable=True)
    publico_objetivo = Column(Enum(PublicoObjetivo, schema="encuestas_oltp"), nullable=False)

    encuesta = relationship("Encuesta", back_populates="reglas")

class Pregunta(Base):
    __tablename__ = "pregunta"
    __table_args__ = {"schema": "encuestas_oltp"}

    id = Column(Integer, primary_key=True)
    id_encuesta = Column(Integer, ForeignKey("encuestas_oltp.encuesta.id"), nullable=False)
    texto_pregunta = Column(Text, nullable=False)
    orden = Column(Integer, nullable=False)
    tipo = Column(Enum(TipoPregunta, schema="encuestas_oltp"), nullable=False)
    configuracion_json = Column(JSONB, nullable=True)
    activo = Column(Boolean, default=True)

    encuesta = relationship("Encuesta", back_populates="preguntas")
    opciones = relationship("OpcionRespuesta", back_populates="pregunta", cascade="all, delete-orphan")

class OpcionRespuesta(Base):
    __tablename__ = "opcion_respuesta"
    __table_args__ = {"schema": "encuestas_oltp"}

    id = Column(Integer, primary_key=True)
    id_pregunta = Column(Integer, ForeignKey("encuestas_oltp.pregunta.id"), nullable=False)
    texto_opcion = Column(String(255), nullable=False)
    orden = Column(Integer, nullable=False)

    pregunta = relationship("Pregunta", back_populates="opciones")

class AsignacionUsuario(Base):
    __tablename__ = "asignacion_usuario"
    __table_args__ = (
        UniqueConstraint('id_usuario', 'id_encuesta', name='uq_usuario_encuesta'),
        {"schema": "encuestas_oltp"}
    )

    id = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, nullable=False, index=True) # ID externo
    id_encuesta = Column(Integer, ForeignKey("encuestas_oltp.encuesta.id"), nullable=False)
    estado = Column(Enum(EstadoAsignacion, schema="encuestas_oltp"), default=EstadoAsignacion.pendiente, index=True)
    fecha_asignacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_realizacion = Column(DateTime(timezone=True), nullable=True)

    encuesta = relationship("Encuesta", back_populates="asignaciones")
    borrador = relationship("RespuestaBorrador", back_populates="asignacion", uselist=False, cascade="all, delete-orphan")

class RespuestaBorrador(Base):
    __tablename__ = "respuesta_borrador"
    __table_args__ = {"schema": "encuestas_oltp"}

    id = Column(Integer, primary_key=True)
    id_asignacion = Column(Integer, ForeignKey("encuestas_oltp.asignacion_usuario.id"), unique=True, nullable=False)
    respuestas_json = Column(JSONB, nullable=False)
    fecha_actualizacion = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    asignacion = relationship("AsignacionUsuario", back_populates="borrador")

class TransaccionEncuesta(Base):
    __tablename__ = "transaccion_encuesta"
    __table_args__ = {"schema": "encuestas_oltp"}

    id_transaccion = Column(Integer, primary_key=True)
    id_encuesta = Column(Integer, ForeignKey("encuestas_oltp.encuesta.id"), nullable=False)
    fecha_finalizacion = Column(DateTime(timezone=True), server_default=func.now())
    metadatos_contexto = Column(JSONB, nullable=False)
    procesado_etl = Column(Boolean, default=False)

    respuestas = relationship("Respuesta", back_populates="transaccion", cascade="all, delete-orphan")

class Respuesta(Base):
    __tablename__ = "respuesta"
    __table_args__ = {"schema": "encuestas_oltp"}

    id_respuesta = Column(Integer, primary_key=True)
    id_transaccion = Column(Integer, ForeignKey("encuestas_oltp.transaccion_encuesta.id_transaccion"), nullable=False)
    id_pregunta = Column(Integer, ForeignKey("encuestas_oltp.pregunta.id"), nullable=False)
    valor_respuesta = Column(Text, nullable=True)
    id_opcion = Column(Integer, ForeignKey("encuestas_oltp.opcion_respuesta.id"), nullable=True)

    transaccion = relationship("TransaccionEncuesta", back_populates="respuestas")


# =============================================================================
# ESQUEMA OLAP (Analítico) - Solo lectura desde la API
# =============================================================================

class DimTiempo(Base):
    __tablename__ = "dim_tiempo"
    __table_args__ = {"schema": "encuestas_olap"}

    id_dim_tiempo = Column(Integer, primary_key=True)
    fecha = Column(Date, unique=True, nullable=False)
    anho = Column(Integer, nullable=False)
    semestre = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    dia_semana = Column(String(20), nullable=True)

class DimUbicacion(Base):
    __tablename__ = "dim_ubicacion"
    __table_args__ = {"schema": "encuestas_olap"}

    id_dim_ubicacion = Column(Integer, primary_key=True)
    nombre_facultad = Column(String(100))
    nombre_carrera = Column(String(100))
    nombre_campus = Column(String(100))

class DimContextoAcademico(Base):
    __tablename__ = "dim_contexto_academico"
    __table_args__ = {"schema": "encuestas_olap"}

    id_dim_contexto = Column(Integer, primary_key=True)
    nombre_profesor = Column(String(100))
    nombre_asignatura = Column(String(100))
    semestre_curso = Column(Integer)

class DimPregunta(Base):
    __tablename__ = "dim_pregunta"
    __table_args__ = {"schema": "encuestas_olap"}

    id_dim_pregunta = Column(Integer, primary_key=True)
    texto_pregunta = Column(Text, nullable=False)
    nombre_encuesta = Column(String(100), nullable=False)
    tipo_pregunta = Column(String(50))

class HechosRespuestas(Base):
    __tablename__ = "hechos_respuestas"
    __table_args__ = {"schema": "encuestas_olap"}

    id_hecho = Column(Integer, primary_key=True)
    id_transaccion_origen = Column(Integer)
    
    id_dim_tiempo = Column(Integer, ForeignKey("encuestas_olap.dim_tiempo.id_dim_tiempo"))
    id_dim_ubicacion = Column(Integer, ForeignKey("encuestas_olap.dim_ubicacion.id_dim_ubicacion"))
    id_dim_contexto = Column(Integer, ForeignKey("encuestas_olap.dim_contexto_academico.id_dim_contexto"))
    id_dim_pregunta = Column(Integer, ForeignKey("encuestas_olap.dim_pregunta.id_dim_pregunta"))
    
    respuesta_numerica = Column(Numeric, nullable=True)
    respuesta_texto = Column(Text, nullable=True)
    conteo = Column(Integer, default=1)

    tiempo = relationship("DimTiempo")
    ubicacion = relationship("DimUbicacion")
    contexto = relationship("DimContextoAcademico")
    pregunta = relationship("DimPregunta")