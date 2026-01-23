from typing import List, Optional
import enum
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
import time

class EscenarioSimulacion(str, enum.Enum):
    alumno_1_borrador = "alumno_1_borrador"
    alumno_2_completo = "alumno_2_completo"
    alumno_3_flujo_completo = "alumno_3_flujo_completo"

class SimulacionRequest(BaseModel):
    id_encuesta: int
    id_usuario: int # ID del usuario a simular
    crear_asignacion: bool = False
    escenario: EscenarioSimulacion = EscenarioSimulacion.alumno_2_completo

@router.post("/simulacion")
def simular_encuesta(
    req: SimulacionRequest,
    bd: Session = Depends(obtener_bd),
    admin: UsuarioAdmin = Depends(solo_admin)
):
    """
    Simula flujos complejos de encuesta.
    """
    logs = []
    
    try:
        logs.append(f"Iniciando simulación para usuario {req.id_usuario} en encuesta {req.id_encuesta}...")
        logs.append(f"Escenario seleccionado: {req.escenario}")
        
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
        
        if asignacion.estado == EstadoAsignacion.realizada and req.escenario != EscenarioSimulacion.alumno_3_flujo_completo:
             logs.append("ADVERTENCIA: La asignación ya estaba realizada.")

        # 2. Cargar Encuesta y Preguntas
        encuesta = bd.query(Encuesta).filter(Encuesta.id == req.id_encuesta).first()
        logs.append(f"Encuesta '{encuesta.nombre}' cargada. {len(encuesta.preguntas)} preguntas encontradas.")

        # Helper para generar respuestas
        def generar_respuestas_random():
            respuestas_gen = []
            for preg in encuesta.preguntas:
                val_resp = None
                id_op = None
                
                if preg.tipo in ["opcion_unica", "opcion_multiple"]:
                    if preg.opciones:
                        op_elegida = random.choice(preg.opciones)
                        id_op = op_elegida.id
                        val_resp = op_elegida.texto_opcion
                elif preg.tipo == "texto_libre":
                    val_resp = f"Respuesta simulada {random.randint(1000,9999)}"
                
                if preg.tipo != "seccion":
                    respuestas_gen.append({
                        "id_pregunta": preg.id,
                        "valor_respuesta": val_resp,
                        "id_opcion": id_op
                    })
            return respuestas_gen

        # Helper para guardar borrador
        def guardar_borrador_simulado(resps):
            from app.modelos import RespuestaBorrador
            
            borrador = bd.query(RespuestaBorrador).filter(
                RespuestaBorrador.id_asignacion == asignacion.id
            ).first()
            
            if not borrador:
                borrador = RespuestaBorrador(id_asignacion=asignacion.id, respuestas_json=resps)
                bd.add(borrador)
                logs.append("Nuevo borrador creado.")
            else:
                borrador.respuestas_json = resps
                logs.append("Borrador existente actualizado.")
            
            bd.commit()

        # Helper para finalizar (Transacción)
        def finalizar_simulado(resps):
            asignacion.estado = EstadoAsignacion.realizada
            asignacion.fecha_realizacion = func.now()
            
            import hashlib
            hash_user = hashlib.sha256(f"{req.id_usuario}SIM".encode()).hexdigest()

            nueva_transaccion = TransaccionEncuesta(
                id_encuesta=req.id_encuesta,
                metadatos_contexto={"origen": "simulacion", "hash": hash_user},
                procesado_etl=False
            )
            bd.add(nueva_transaccion)
            bd.flush()
            
            for r in resps:
                 bd.add(modelos.Respuesta(
                    id_transaccion=nueva_transaccion.id_transaccion,
                    id_pregunta=r["id_pregunta"],
                    valor_respuesta=r["valor_respuesta"],
                    id_opcion=r["id_opcion"]
                ))
            
            # Borrar borrador al finalizar
            if asignacion.borrador:
                bd.delete(asignacion.borrador)
                logs.append("Borrador eliminado tras finalizar.")

            bd.commit()
            logs.append("Encuesta FINALIZADA y guardada en OLTP.")

        # --- LÓGICA POR ESCENARIO ---

        respuestas = generar_respuestas_random()

        if req.escenario == EscenarioSimulacion.alumno_1_borrador:
            logs.append("EJECUTANDO: Alumno 1 (Solo Borrador)")
            guardar_borrador_simulado(respuestas)
            logs.append("Simulación detenida. El alumno NO finalizó.")

        elif req.escenario == EscenarioSimulacion.alumno_2_completo:
            logs.append("EJECUTANDO: Alumno 2 (Completar directo)")
            finalizar_simulado(respuestas)

        elif req.escenario == EscenarioSimulacion.alumno_3_flujo_completo:
            logs.append("EJECUTANDO: Alumno 3 (Flujo Completo)")
            
            # Paso 1: Guardar Borrador
            logs.append("Paso 1: Guardando borrador inicial...")
            guardar_borrador_simulado(respuestas)
            
            # Paso 2: Simular espera/abandono
            logs.append("Paso 2: Simulando espera (alumno sale del sistema)...")
            
            # Paso 3: Recuperar
            logs.append("Paso 3: Alumno regresa. Recuperando borrador...")
            bd.refresh(asignacion)
            if asignacion.borrador:
                logs.append(f"Borrador recuperado con {len(asignacion.borrador.respuestas_json)} respuestas.")
            else:
                logs.append("ERROR: No se encontró el borrador para recuperar.")
            
            # Paso 4: Completar
            logs.append("Paso 4: Alumno completa y envía.")
            finalizar_simulado(respuestas)

        return {
            "exito": True,
            "logs": logs
        }

    except Exception as e:
        bd.rollback()
        logs.append(f"ERROR CRITICO: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "exito": False,
            "logs": logs
        }

@router.get("/chequeo-sapientia/{id_alumno}")
def consultar_pendientes_sapientia(
    id_alumno: int,
    bd: Session = Depends(obtener_bd),
    admin: UsuarioAdmin = Depends(solo_admin)
):
    """
    Simula la consulta que hace el portal Sapientia para ver si hay bloqueos.
    """
    from app.routers.sapientia import verificar_estado_alumno
    return verificar_estado_alumno(id_alumno, bd)
