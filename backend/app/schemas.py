from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
from app.modelos import (
    PrioridadEncuesta, AccionDisparadora, TipoPregunta,
    EstadoAsignacion, PublicoObjetivo, RolAdmin, EstadoEncuesta
)

# =============================================================================
# ESQUEMAS BASE Y DE UTILIDAD
# =============================================================================

# Para que Pydantic lea objetos de SQLAlchemy
class EsquemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# USUARIOS ADMINISTRATIVOS (Login y Gestión de Acceso)
# =============================================================================

class UsuarioAdminBase(EsquemaBase):
    nombre_usuario: str
    rol: RolAdmin

class UsuarioAdminCrear(UsuarioAdminBase):
    clave: Optional[str] = None # Opcional: si no se envía, se genera una genérica

class UsuarioAdminSalida(UsuarioAdminBase):
    id_admin: int
    fecha_creacion: datetime
    fecha_ultimo_login: Optional[datetime] = None
    activo: bool
    debe_cambiar_clave: bool

class UsuarioActualizarEstado(BaseModel):
    activo: bool

class UsuarioActualizarRol(BaseModel):
    rol: RolAdmin

# Esquemas para el Login (JWT)
class SolicitudLogin(BaseModel):
    usuario: str
    clave: str

class Token(BaseModel):
    access_token: str
    token_type: str

class DatosToken(BaseModel):
    nombre_usuario: Optional[str] = None
    rol: Optional[str] = None

class CambioClave(BaseModel):
    clave_actual: str
    clave_nueva: str
    confirmacion_clave_nueva: str

    @property
    def claves_coinciden(self) -> bool:
        return self.clave_nueva == self.confirmacion_clave_nueva

class PermisoSalida(EsquemaBase):
    id_permiso: int
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    categoria: str

class AsignacionPermisoRol(BaseModel):
    id_permisos: List[int] # Lista de IDs de permisos a asignar al rol

# =============================================================================
# PLANTILLAS DE OPCIONES
# =============================================================================

class PlantillaOpcionDetalleBase(EsquemaBase):
    texto_opcion: str
    orden: int

class PlantillaOpcionDetalleCrear(PlantillaOpcionDetalleBase):
    pass

class PlantillaOpcionDetalleSalida(PlantillaOpcionDetalleBase):
    id: int
    id_plantilla: int

class PlantillaOpcionesBase(EsquemaBase):
    nombre: str
    descripcion: Optional[str] = None

class PlantillaOpcionesCrear(PlantillaOpcionesBase):
    detalles: List[PlantillaOpcionDetalleCrear] = []

class PlantillaOpcionesSalida(PlantillaOpcionesBase):
    id: int
    fecha_creacion: datetime
    detalles: List[PlantillaOpcionDetalleSalida] = []

# =============================================================================
# GESTIÓN DE ENCUESTAS (Configuración)
# =============================================================================

# --- Opciones de Respuesta ---
class OpcionRespuestaBase(EsquemaBase):
    texto_opcion: str
    orden: int

class OpcionRespuestaCrear(OpcionRespuestaBase):
    pass

class OpcionRespuestaSalida(OpcionRespuestaBase):
    id: int
    id_pregunta: int

# --- Preguntas ---
class PreguntaBase(EsquemaBase):
    texto_pregunta: str
    orden: int
    tipo: TipoPregunta
    configuracion_json: Optional[Dict[str, Any]] = None # Ej: {"max_opciones": 3}
    activo: bool = True

class PreguntaCrear(PreguntaBase):
    # Al crear una pregunta, podemos enviar sus opciones de una vez
    opciones: List[OpcionRespuestaCrear] = []

class PreguntaSalida(PreguntaBase):
    id: int
    id_encuesta: int
    opciones: List[OpcionRespuestaSalida] = []

# --- Reglas de Asignación ---
class ReglaAsignacionBase(EsquemaBase):
    id_facultad: Optional[int] = None
    id_carrera: Optional[int] = None
    id_asignatura: Optional[int] = None
    publico_objetivo: PublicoObjetivo

class ReglaAsignacionCrear(ReglaAsignacionBase):
    pass

class ReglaAsignacionSalida(ReglaAsignacionBase):
    id: int
    id_encuesta: int

# --- Encuesta (La entidad principal) ---
class EncuestaBase(EsquemaBase):
    nombre: str
    descripcion: Optional[str] = None
    mensaje_final: Optional[str] = None
    fecha_inicio: datetime
    fecha_fin: datetime
    prioridad: PrioridadEncuesta
    acciones_disparadoras: List[AccionDisparadora] = [] 
    configuracion: Dict[str, Any] = {}
    estado: Optional[EstadoEncuesta] = EstadoEncuesta.borrador
    activo: bool = True

class EncuestaCrear(EncuestaBase):
    # Al crear encuesta, podemos enviar reglas y preguntas anidadas
    reglas: List[ReglaAsignacionCrear] = []
    preguntas: List[PreguntaCrear] = []

class UsuarioResumen(BaseModel):
    id_admin: int
    nombre_usuario: str
    rol: RolAdmin

class EncuestaSalida(EncuestaBase):
    id: int
    
    # === Campos de auditoría (solo lectura) ===
    usuario_creacion: int
    fecha_creacion: datetime
    usuario_modificacion: Optional[int] = None
    fecha_modificacion: Optional[datetime] = None
    
    # === Opcional: incluir datos del creador/modificador (mejor UX para frontend) ===
    creador: Optional[UsuarioResumen] = None
    modificador: Optional[UsuarioResumen] = None

    # Relaciones
    reglas: List[ReglaAsignacionSalida] = []
    preguntas: List[PreguntaSalida] = []
    cantidad_preguntas: Optional[int] = 0
    cantidad_respuestas: Optional[int] = 0

# =============================================================================
# INTEGRACIÓN CON SAPIENTIA (Operación en Vivo)
# =============================================================================
# CU11: Verificar Estado (Respuesta a Sapientia)
class RespuestaVerificacionEstado(BaseModel):
    estado_bloqueo: bool # True = BLOQUEADO, False = OK
    mensaje: str
    id_encuesta_pendiente: Optional[int] = None
    datos_encuesta: Optional[EncuestaSalida] = None # Opcional: Enviar la encuesta ahí mismo

# CU07: Recepción de Respuestas (Desde Sapientia)
class RespuestaIndividual(BaseModel):
    id_pregunta: int
    valor_respuesta: Optional[str] = None # Texto o número
    id_opcion: Optional[int] = None       # ID si fue opción múltiple

class EnvioRespuestasAlumno(BaseModel):
    id_usuario: int
    id_encuesta: int
    metadatos_contexto: Dict[str, Any] # JSON para el OLAP (Facultad, Carrera, etc.)
    respuestas: List[RespuestaIndividual]

# =============================================================================
# REPORTES Y ANALÍTICA (OLAP) - ¡SECCIÓN FALTANTE AÑADIDA!
# =============================================================================

class ReporteParticipacion(BaseModel):
    facultad: str
    cantidad_respuestas: int

class ReportePromedioPregunta(BaseModel):
    pregunta: str
    promedio: float
    total_respuestas: int

class DashboardStats(BaseModel):
    total_encuestas_completadas: int
    total_respuestas_procesadas: int
    ultime_actualizacion_etl: Optional[datetime] = None