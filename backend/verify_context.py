from app.database import SesionLocal
from app.modelos import AsignacionUsuario, TransaccionEncuesta, Respuesta, EstadoAsignacion
from app.routers.sapientia import recibir_respuestas
from app.schemas import EnvioRespuestasAlumno, RespuestaIndividual
from datetime import datetime

def verify_data_context():
    db = SesionLocal()
    try:
        # 1. Find an assignment from our Mass Assign test (Survey 33)
        # We need one that is PENDIENTE
        # Assuming survey 33 exists from previous step. If not, pick any with metadata.
        
        target_survey_id = 33 
        asignacion = db.query(AsignacionUsuario).filter(
            AsignacionUsuario.id_encuesta == target_survey_id,
            AsignacionUsuario.estado == EstadoAsignacion.pendiente
        ).first()

        if not asignacion:
            print("No pending assignment found for survey 33. Searching any...")
            asignacion = db.query(AsignacionUsuario).filter(
                AsignacionUsuario.metadatos_asignacion != None,
                AsignacionUsuario.estado == EstadoAsignacion.pendiente
            ).first()

        if not asignacion:
            print("No valid assignment found to test.")
            return

        # Inject Dummy Metadata for testing the merge logic
        asignacion.metadatos_asignacion = {
            "docente": "Profesor Test",
            "materia": "Materia Test 101",
            "nombre_alumno": "Alumno Test"
        }
        db.commit()

        print(f"Testing with Assignment ID: {asignacion.id}")
        print(f"Original Metadata: {asignacion.metadatos_asignacion}")

        # 2. Simulate Payload
        payload = EnvioRespuestasAlumno(
            id_usuario=asignacion.id_usuario,
            id_encuesta=asignacion.id_encuesta,
            id_referencia_contexto=asignacion.id_referencia_contexto,
            metadatos_contexto={"device": "script_test"},
            respuestas=[
                # Dummy response, assuming question ID 1 exists or similar. 
                # Actually, we should check which questions exist.
                # But `recibir_respuestas` validates integrity.
            ]
        )
        
        # Add dummy valid answers
        from app.modelos import Pregunta
        preguntas = db.query(Pregunta).filter(Pregunta.id_encuesta == asignacion.id_encuesta).all()
        if preguntas:
            for p in preguntas:
                payload.respuestas.append(
                    RespuestaIndividual(id_pregunta=p.id, valor_respuesta="Test Context")
                )

        # 3. Call endpoint function directly
        print("Sending responses...")
        recibir_respuestas(payload, db)
        print("Responses processed.")

        # 4. Verify Transaction
        # Get latest transaction for this user
        trans = db.query(TransaccionEncuesta).filter(
            TransaccionEncuesta.id_encuesta == asignacion.id_encuesta
        ).order_by(TransaccionEncuesta.id_transaccion.desc()).first()
        
        print("--- Transaction Context ---")
        print(trans.metadatos_contexto)
        
        # Check for remapped keys
        meta = trans.metadatos_contexto
        if "profesor" in meta or "asignatura" in meta:
            print("SUCCESS: Context keys 'profesor'/'asignatura' found!")
        else:
            print("FAILURE: Context keys missing. Check if assignment had 'docente'/'materia'.")

    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    verify_data_context()
