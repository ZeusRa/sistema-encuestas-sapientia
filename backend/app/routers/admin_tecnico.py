from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.database import obtener_bd
from app import modelos, schemas
from app.routers.auth import obtener_usuario_actual
from app.modelos import UsuarioAdmin, RolAdmin, Encuesta, AsignacionUsuario, EstadoAsignacion, TransaccionEncuesta
import etl
import random
import json

router = APIRouter(
    prefix="/admin/tecnico",
    tags=["Administración Técnica"],
    dependencies=[Depends(obtener_usuario_actual)]  # Todos requieren autenticación
)

# Dependencia de Rol Administrador
def solo_admin(usuario: UsuarioAdmin = Depends(obtener_usuario_actual)):
    if usuario.rol != RolAdmin.ADMINISTRADOR:
        raise HTTPException(status_code=403, detail="Requiere rol ADMINISTRADOR")
    return usuario

@router.get("/encuestas")
def listar_encuestas_tecnico(
    bd: Session = Depends(obtener_bd),
    admin: UsuarioAdmin = Depends(solo_admin)
):
    encuestas = bd.query(Encuesta).all()
    # Retornamos estructura simplificada para la tabla
    res = []
    for e in encuestas:
        res.append({
            "id": e.id,
            "nombre": e.nombre,
            "estado": e.estado,
            "acciones": e.acciones_disparadoras,
            "preguntas": len(e.preguntas),
            "asignaciones": len(e.asignaciones)
        })
    return res

@router.get("/encuestas/{id_encuesta}/preview")
def preview_encuesta(
    id_encuesta: int,
    bd: Session = Depends(obtener_bd),
    admin: UsuarioAdmin = Depends(solo_admin)
):
    encuesta = bd.query(Encuesta).filter(Encuesta.id == id_encuesta).first()
    if not encuesta:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    return encuesta

@router.get("/asignaciones")
def listar_asignaciones_tecnico(
    limit: int = 50,
    bd: Session = Depends(obtener_bd),
    admin: UsuarioAdmin = Depends(solo_admin)
):
    asignaciones = bd.query(AsignacionUsuario).order_by(AsignacionUsuario.fecha_asignacion.desc()).limit(limit).all()
    return asignaciones

@router.get("/etl/estado")
def estado_etl(
    bd: Session = Depends(obtener_bd),
    admin: UsuarioAdmin = Depends(solo_admin)
):
    pendientes = bd.query(TransaccionEncuesta).filter(TransaccionEncuesta.procesado_etl == False).count()
    total = bd.query(TransaccionEncuesta).count()
    return {
        "pendientes_etl": pendientes,
        "total_transacciones": total
    }

@router.post("/etl/ejecutar")
def trigger_etl(
    bd: Session = Depends(obtener_bd),
    admin: UsuarioAdmin = Depends(solo_admin)
):
    try:
        # Ejecutamos la función del script etl.py
        # Nota: Esto es sincrónico y bloqueará el request. Para MVP está bien.
        etl.ejecutar_etl()
        return {"mensaje": "ETL Ejecutado Correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en ETL: {str(e)}")

# --- SIMULACIÓN ---

from pydantic import BaseModel

class SimulacionRequest(BaseModel):
    id_encuesta: int
    id_usuario: int # ID del usuario a simular (debe tener asignación pendiente o creamos una al vuelo?)
    crear_asignacion: bool = False

@router.post("/simulacion")
def simular_encuesta(
    req: SimulacionRequest,
    bd: Session = Depends(obtener_bd),
    admin: UsuarioAdmin = Depends(solo_admin)
):
    """
    Simula el flujo completo:
    1. Verifica/Crea asignación.
    2. Obtiene preguntas.
    3. Genera respuestas random.
    4. Envía respuestas (usando lógica similar a sapientia.py).
    """
    logs = []
    
    try:
        logs.append("Iniciando simulación...")
        
        # 1. Buscar o crear asignación
        asignacion = bd.query(AsignacionUsuario).filter(
            AsignacionUsuario.id_usuario == req.id_usuario,
            AsignacionUsuario.id_encuesta == req.id_encuesta
        ).first()

        if not asignacion:
            if req.crear_asignacion:
                logs.append("Asignación no encontrada. Creando asignación temporal...")
                asignacion = AsignacionUsuario(
                    id_usuario=req.id_usuario, 
                    id_encuesta=req.id_encuesta,

                    estado=EstadoAsignacion.pendiente
                )
                bd.add(asignacion)
                bd.commit()
                bd.refresh(asignacion)
            else:
                 raise HTTPException(status_code=404, detail="Asignación no encontrada y no se solicitó crearla.")
        
        if asignacion.estado == EstadoAsignacion.realizada:
             logs.append("ADVERTENCIA: La asignación ya estaba realizada. Se intentará procesar igual (posible error de duplicado).")

        # 2. Obtener preguntas
        encuesta = bd.query(Encuesta).filter(Encuesta.id == req.id_encuesta).first()
        logs.append(f"Encuesta '{encuesta.nombre}' cargada. {len(encuesta.preguntas)} preguntas encontradas.")

        # 3. Generar respuestas
        respuestas_generadas = []
        import app.routers.sapientia as sapientia_router # Reutilizamos schemas si es posible o definimos dicts

        for preg in encuesta.preguntas:
            val_resp = None
            id_op = None
            
            if preg.tipo in ["opcion_unica", "opcion_multiple"]:
                if preg.opciones:
                    op_elegida = random.choice(preg.opciones)
                    id_op = op_elegida.id
                    val_resp = op_elegida.texto_opcion
            elif preg.tipo == "texto_libre":
                val_resp = "Respuesta simulada automática " + str(random.randint(1000,9999))
            
            # Solo agregamos si se generó algo (secciones no se responden)
            if preg.tipo != "seccion":
                respuestas_generadas.append(
                    schemas.RespuestaIndividual(
                        id_pregunta=preg.id,
                        valor_respuesta=val_resp,
                        id_opcion=id_op
                    )
                )
        
        logs.append(f"Generadas {len(respuestas_generadas)} respuestas aleatorias.")

        # 4. Enviar (Llamamos a la lógica interna de sapientia.py o la reimplementamos aqui para tener control)
        # Reimplementamos para no depender del endpoint HTTP y poder loguear mejor
        
        # TRANSACCION
        logs.append("Iniciando transacción de base de datos...")
        asignacion.estado = EstadoAsignacion.realizada
        asignacion.fecha_realizacion = func.now()
        
        nueva_transaccion = TransaccionEncuesta(
            id_encuesta=req.id_encuesta,
            metadatos_contexto={"origen": "simulacion_tecnica", "admin_user": admin.nombre_usuario},
            procesado_etl=False
        )
        bd.add(nueva_transaccion)
        bd.flush()
        
        for r in respuestas_generadas:
             nueva_respuesta = modelos.Respuesta(
                id_transaccion=nueva_transaccion.id_transaccion,
                id_pregunta=r.id_pregunta,
                valor_respuesta=r.valor_respuesta,
                id_opcion=r.id_opcion
            )
             bd.add(nueva_respuesta)
        
        if asignacion.borrador:
            bd.delete(asignacion.borrador)
            
        bd.commit()
        logs.append("Transacción completada exitosamente. Encuesta guardada.")

        return {
            "exito": True,
            "logs": logs,
            "transaccion_id": nueva_transaccion.id_transaccion
        }

    except Exception as e:
        bd.rollback()
        logs.append(f"ERROR CRITICO: {str(e)}")
        return {
            "exito": False,
            "logs": logs
        }
