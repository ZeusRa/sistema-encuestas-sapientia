from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app import modelos
from app import schemas
from datetime import datetime, timezone
import logging
import copy
from app.services import sapientia_service

# Configurar logger
logger = logging.getLogger(__name__)

class EncuestaServicio:
    """
    Servicio de dominio para la gestión del ciclo de vida de encuestas.
    Aplica lógica de negocio para crear, publicar, duplicar y finalizar encuestas.
    """

    @staticmethod
    def validar_reglas(encuesta: modelos.Encuesta):
        """
        Valida que una encuesta tenga reglas de asignación definidas.
        """
        if not encuesta.reglas or len(encuesta.reglas) == 0:
            raise HTTPException(
                status_code=400,
                detail="La encuesta debe tener al menos una regla de asignación definida"
            )

    @staticmethod
    def duplicar_encuesta(db: Session, encuesta_id: int, usuario_id: int) -> modelos.Encuesta:
        """
        Duplica una encuesta existente, copiando configuración, reglas y preguntas.
        """
        encuesta_original = (
            db.query(modelos.Encuesta)
            .filter(modelos.Encuesta.id == encuesta_id)
            .first()
        )

        if not encuesta_original:
            raise HTTPException(status_code=404, detail="Encuesta no encontrada")

        # Clonar Encuesta Base
        nueva_encuesta = modelos.Encuesta(
            nombre=f"{encuesta_original.nombre} - (copia)",
            descripcion=encuesta_original.descripcion,
            mensaje_final=encuesta_original.mensaje_final,
            # Resetear fechas para obligar a configurar ??? o mantengo? Mejor copiar igual pero validar al activar.
            fecha_inicio=encuesta_original.fecha_inicio,
            fecha_fin=encuesta_original.fecha_fin,
            prioridad=encuesta_original.prioridad,
            acciones_disparadoras=list(encuesta_original.acciones_disparadoras),
            configuracion=copy.deepcopy(encuesta_original.configuracion),
            estado=modelos.EstadoEncuesta.borrador,
            activo=True,
            usuario_creacion=usuario_id
        )

        db.add(nueva_encuesta)
        db.flush()

        # Clonar Reglas
        for regla in encuesta_original.reglas:
            nueva_regla = modelos.ReglaAsignacion(
                id_encuesta=nueva_encuesta.id,
                id_facultad=regla.id_facultad,
                id_carrera=regla.id_carrera,
                id_asignatura=regla.id_asignatura,
                publico_objetivo=regla.publico_objetivo,
                filtros_json=copy.deepcopy(regla.filtros_json) if regla.filtros_json else None
            )
            db.add(nueva_regla)

        # Clonar Preguntas y Opciones
        for preg in encuesta_original.preguntas:
            nueva_pregunta = modelos.Pregunta(
                id_encuesta=nueva_encuesta.id,
                texto_pregunta=preg.texto_pregunta,
                orden=preg.orden,
                tipo=preg.tipo,
                configuracion_json=copy.deepcopy(preg.configuracion_json) if preg.configuracion_json else None,
                activo=preg.activo
            )
            db.add(nueva_pregunta)
            db.flush()

            for opc in preg.opciones:
                nueva_opcion = modelos.OpcionRespuesta(
                    id_pregunta=nueva_pregunta.id,
                    texto_opcion=opc.texto_opcion,
                    orden=opc.orden
                )
                db.add(nueva_opcion)

        db.commit()
        db.refresh(nueva_encuesta)
        return nueva_encuesta

    @staticmethod
    def publicar_encuesta(db: Session, encuesta_id: int, usuario_id: int, batch_size_jit: int = 1000, batch_size_pub: int = 1000) -> modelos.Encuesta:
        """
        Cambia el estado de una encuesta a EN_CURSO y genera las asignaciones de usuarios correspondientes.
        Maneja lógica de batching y deduplicación.
        """
        encuesta = db.query(modelos.Encuesta).filter(modelos.Encuesta.id == encuesta_id).first()
        if not encuesta:
            raise HTTPException(status_code=404, detail="Encuesta no encontrada")
        
        if encuesta.estado != modelos.EstadoEncuesta.borrador:
            raise HTTPException(status_code=400, detail="Solo se pueden publicar encuestas en estado BORRADOR")
        
        EncuestaServicio.validar_reglas(encuesta)

        try:
            # Lógica de asignaciones según público
            regla = encuesta.reglas[0]
            
            # --- EVALUACIÓN DOCENTE (JIT) ---
            if encuesta.prioridad == modelos.PrioridadEncuesta.evaluacion_docente and regla.publico_objetivo == modelos.PublicoObjetivo.alumnos:
                EncuestaServicio._procesar_evaluacion_docente(db, encuesta, batch_size_jit)
            
            # --- ENCUESTA GENERAL (ALUMNOS) ---
            elif regla.publico_objetivo in [modelos.PublicoObjetivo.alumnos, modelos.PublicoObjetivo.ambos]:
                EncuestaServicio._procesar_asignacion_alumnos(db, encuesta, batch_size_pub)
                
            # --- ENCUESTA GENERAL (DOCENTES) ---
            if regla.publico_objetivo in [modelos.PublicoObjetivo.docentes, modelos.PublicoObjetivo.ambos]:
                 # Si es evaluacion docente, no aplica a docentes (ya está el raise en admin original, pero validamos aqui)
                 if encuesta.prioridad != modelos.PrioridadEncuesta.evaluacion_docente:
                    EncuestaServicio._procesar_asignacion_docentes(db, encuesta)

            # Actualizar Estado
            encuesta.estado = modelos.EstadoEncuesta.en_curso
            encuesta.usuario_modificacion = usuario_id
            encuesta.fecha_publicacion = datetime.now(timezone.utc) # Opcional si agregamos campo
            db.commit()
            db.refresh(encuesta)
            return encuesta

        except Exception as e:
            db.rollback()
            logger.exception(f"Error publicando encuesta {encuesta_id}: {e}")
            raise HTTPException(status_code=500, detail="Error interno al publicar la encuesta")

    # --- MÉTODOS PRIVADOS DE ASIGNACIÓN ---
    
    @staticmethod
    def _procesar_evaluacion_docente(db: Session, encuesta: modelos.Encuesta, batch_size: int):
        batch_mappings = []
        
        for item in sapientia_service.get_contexto_evaluacion_docente(db):
            batch_mappings.append({
                "id_usuario": item['id_usuario'],
                "id_encuesta": encuesta.id,
                "id_referencia_contexto": item['id_referencia_contexto'],
                "metadatos_asignacion": item['metadatos'],
                "estado": modelos.EstadoAsignacion.pendiente,
                "fecha_asignacion": datetime.now(timezone.utc)
            })

            if len(batch_mappings) >= batch_size:
                EncuestaServicio._insertar_lote_seguro(db, encuesta.id, batch_mappings)
                batch_mappings = []
        
        if batch_mappings:
            EncuestaServicio._insertar_lote_seguro(db, encuesta.id, batch_mappings)

    @staticmethod
    def _procesar_asignacion_alumnos(db: Session, encuesta: modelos.Encuesta, batch_size: int):
        filtros = encuesta.reglas[0].filtros_json if encuesta.reglas else None
        batch_mappings = []
        used_ids = set() # Set local para dedup en memoria si el generador trae repetidos

        for alu in sapientia_service.get_alumnos_cursando(db, filtros_json=filtros):
            if alu['id'] in used_ids:
                continue
            used_ids.add(alu['id'])
            
            batch_mappings.append({
                "id_usuario": alu['id'],
                "id_encuesta": encuesta.id,
                "id_referencia_contexto": f"GEN-ALU-{alu['id']}",
                "metadatos_asignacion": {
                    "nombre_alumno": alu['nombre'],
                    "campus": alu['campus'],
                    "facultad": alu['facultad'],
                    "carrera": alu['carrera']
                },
                "estado": modelos.EstadoAsignacion.pendiente,
                "fecha_asignacion": datetime.now(timezone.utc)
            })

            if len(batch_mappings) >= batch_size:
                 # Check existencia contra DB antes de insertar
                 # Optimización: Solo checkear si ya había asignaciones previas... pero asumimos idempotencia
                 EncuestaServicio._insertar_lote_por_usuario(db, encuesta.id, batch_mappings)
                 batch_mappings = []
        
        if batch_mappings:
            EncuestaServicio._insertar_lote_por_usuario(db, encuesta.id, batch_mappings)

    @staticmethod
    def _procesar_asignacion_docentes(db: Session, encuesta: modelos.Encuesta):
        # Asumimos volumen bajo para docentes
        docentes = sapientia_service.get_docentes_activos(db)
        mappings = []
        for doc in docentes:
             mappings.append({
                "id_usuario": doc['id'],
                "id_encuesta": encuesta.id,
                "id_referencia_contexto": f"GEN-DOC-{doc['id']}",
                "metadatos_asignacion": {"nombre_docente": doc['nombre']},
                "estado": modelos.EstadoAsignacion.pendiente,
                "fecha_asignacion": datetime.now(timezone.utc)
            })
        
        if mappings:
            EncuestaServicio._insertar_lote_por_usuario(db, encuesta.id, mappings)

    @staticmethod
    def _insertar_lote_seguro(db: Session, encuesta_id: int, mappings: list):
        """Inserta ignorando duplicados por id_referencia_contexto"""
        if not mappings: return
        
        ctx_ids = [m['id_referencia_contexto'] for m in mappings]
        existentes = db.query(modelos.AsignacionUsuario.id_referencia_contexto).filter(
            modelos.AsignacionUsuario.id_encuesta == encuesta_id,
            modelos.AsignacionUsuario.id_referencia_contexto.in_(ctx_ids)
        ).all()
        ctx_existentes = {e[0] for e in existentes}
        
        final_batch = [m for m in mappings if m['id_referencia_contexto'] not in ctx_existentes]
        if final_batch:
            db.bulk_insert_mappings(modelos.AsignacionUsuario, final_batch)
            db.commit()

    @staticmethod
    def _insertar_lote_por_usuario(db: Session, encuesta_id: int, mappings: list):
        """Inserta ignorando duplicados por id_usuario (para encuestas generales)"""
        if not mappings: return
        
        u_ids = [m['id_usuario'] for m in mappings]
        existentes = db.query(modelos.AsignacionUsuario.id_usuario).filter(
            modelos.AsignacionUsuario.id_encuesta == encuesta_id,
            modelos.AsignacionUsuario.id_usuario.in_(u_ids)
        ).all()
        id_existentes = {e[0] for e in existentes}
        
        final_batch = [m for m in mappings if m['id_usuario'] not in id_existentes]
        if final_batch:
            db.bulk_insert_mappings(modelos.AsignacionUsuario, final_batch)
            db.commit()
