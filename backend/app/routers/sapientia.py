from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.database import obtener_bd
from app import modelos, schemas
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de Seguridad (API Key)
API_KEY_SAPIENTIA = os.getenv("API_KEY_SAPIENTIA", "secreto_compartido_super_seguro")

router = APIRouter(
    prefix="/sapientia",
    tags=["Integración Sapientia (API Externa)"]
)

# Dependencia para validar la API Key
async def validar_api_key(x_api_key: Annotated[str, Header()]):
    if x_api_key != API_KEY_SAPIENTIA:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida"
        )

# --- ENDPOINTS ---

@router.get("/verificar-estado", response_model=schemas.RespuestaVerificacionEstado)
def verificar_estado_bloqueo(
    id_usuario: int,
    accion: str, # "al_inscribir_examen", etc.
    bd: Session = Depends(obtener_bd),
    autorizado: bool = Depends(validar_api_key)
):
    """
    CU11: Verifica si un usuario tiene encuestas pendientes que bloqueen una acción.
    Ruta crítica: Debe ser muy rápida.
    """
    # 1. Buscar asignaciones pendientes que coincidan con la acción disparadora
    # JOIN implícito para filtrar por la configuración de la encuesta
    asignacion_pendiente = bd.query(modelos.AsignacionUsuario).join(modelos.Encuesta).filter(
        modelos.AsignacionUsuario.id_usuario == id_usuario,
        modelos.AsignacionUsuario.estado == "pendiente",
        modelos.Encuesta.acciones_disparadoras.contains([accion]),
        modelos.Encuesta.activo == True,
        modelos.Encuesta.prioridad.in_(["obligatoria", "evaluacion_docente"]) # Solo estas bloquean
    ).first()

    if not asignacion_pendiente:
        return {
            "estado_bloqueo": False,
            "mensaje": "OK",
            "id_encuesta_pendiente": None
        }
    
    # Si hay bloqueo, obtenemos los datos básicos para que Sapientia sepa qué mostrar
    return {
        "estado_bloqueo": True,
        "mensaje": f"Debes completar la encuesta: {asignacion_pendiente.encuesta.nombre}",
        "id_encuesta_pendiente": asignacion_pendiente.encuesta.id
    }

@router.get("/encuestas/{id_encuesta}/estructura", response_model=schemas.EncuestaSalida)
def obtener_estructura_encuesta(
    id_encuesta: int,
    bd: Session = Depends(obtener_bd),
    autorizado: bool = Depends(validar_api_key)
):
    """
    CU06: Sapientia solicita la estructura para renderizar el formulario.
    """
    encuesta = bd.query(modelos.Encuesta).filter(modelos.Encuesta.id == id_encuesta).first()
    if not encuesta:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    return encuesta

@router.post("/respuestas", status_code=status.HTTP_201_CREATED)
def recibir_respuestas(
    envio: schemas.EnvioRespuestasAlumno,
    bd: Session = Depends(obtener_bd),
    autorizado: bool = Depends(validar_api_key)
):
    """
    CU07: Transacción Atómica (Guardar Respuestas + Desbloquear).
    """
    # 1. Buscar la asignación pendiente
    # Modificación JIT: Filtramos también por id_referencia_contexto para cerrar solo la instancia correcta
    asignacion = bd.query(modelos.AsignacionUsuario).filter(
        modelos.AsignacionUsuario.id_usuario == envio.id_usuario,
        modelos.AsignacionUsuario.id_encuesta == envio.id_encuesta,
        modelos.AsignacionUsuario.id_referencia_contexto == envio.id_referencia_contexto,
        modelos.AsignacionUsuario.estado == "pendiente"
    ).first()

    if not asignacion:
        # Puede ser que ya la completó o que no estaba asignada.
        # Si ya está 'realizada', devolvemos 200 OK.
        asignacion_realizada = bd.query(modelos.AsignacionUsuario).filter(
             modelos.AsignacionUsuario.id_usuario == envio.id_usuario,
             modelos.AsignacionUsuario.id_encuesta == envio.id_encuesta,
             modelos.AsignacionUsuario.id_referencia_contexto == envio.id_referencia_contexto,
             modelos.AsignacionUsuario.estado == "realizada"
        ).first()
        
        if asignacion_realizada:
             return {"mensaje": "Encuesta ya recibida previamente"}
             
        raise HTTPException(status_code=404, detail="Asignación no encontrada o inválida para este contexto")

    try:
        # 2. INICIO TRANSACCIÓN
        
        # A. Actualizar Estado (Desbloqueo - No Anónimo)
        asignacion.estado = "realizada"
        asignacion.fecha_realizacion = func.now()
        
        # B. Insertar Transacción (Datos Anónimos)
        nueva_transaccion = modelos.TransaccionEncuesta(
            id_encuesta=envio.id_encuesta,
            metadatos_contexto=envio.metadatos_contexto # JSON recibido de Sapientia
        )
        bd.add(nueva_transaccion)
        bd.flush() # Para tener el ID de transacción

        # C. Insertar Respuestas Detalladas (Anónimo)
        for resp in envio.respuestas:
            nueva_respuesta = modelos.Respuesta(
                id_transaccion=nueva_transaccion.id_transaccion,
                id_pregunta=resp.id_pregunta,
                valor_respuesta=resp.valor_respuesta,
                id_opcion=resp.id_opcion
            )
            bd.add(nueva_respuesta)
            
        # D. Borrar borrador si existía (Limpieza)
        if asignacion.borrador:
            bd.delete(asignacion.borrador)

        bd.commit()
        return {"mensaje": "Respuestas recibidas y procesadas correctamente"}

    except Exception as e:
        bd.rollback()
        raise HTTPException(status_code=500, detail=f"Error procesando respuestas: {str(e)}")

# Endpoint auxiliar para que Sapientia nos avise "Asigna esta encuesta a este alumno"
@router.post("/asignar-manualmente")
def asignar_encuesta_manual(
    id_usuario: int,
    id_encuesta: int,
    bd: Session = Depends(obtener_bd),
    autorizado: bool = Depends(validar_api_key)
):
    existe = bd.query(modelos.AsignacionUsuario).filter_by(id_usuario=id_usuario, id_encuesta=id_encuesta).first()
    if existe:
        return {"mensaje": "Ya asignada"}
    
    nueva = modelos.AsignacionUsuario(id_usuario=id_usuario, id_encuesta=id_encuesta)
    bd.add(nueva)
    bd.commit()
    return {"mensaje": "Asignada"}