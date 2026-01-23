from app.database import SesionLocal
from app.modelos import Encuesta, ReglaAsignacion, PublicoObjetivo, AsignacionUsuario, EstadoEncuesta
from app.servicios.encuesta_servicio import EncuestaServicio
from app.modelos import UsuarioAdmin, RolAdmin
import json

def verify_mass_assignment():
    db = SesionLocal()
    try:
        # 1. Find a base survey (ID 30 or any)
        base_id = 30
        base = db.query(Encuesta).filter(Encuesta.id == base_id).first()
        if not base:
            print(f"Survey {base_id} not found, picking first available...")
            base = db.query(Encuesta).first()
            if not base:
                print("No surveys found in DB.")
                return

        print(f"Using base survey: {base.id} - {base.nombre}")

        # 2. Duplicate via Service
        # We need a dummy admin user ID
        admin = db.query(UsuarioAdmin).first()
        if not admin:
            print("No admin user found.")
            return
        
        new_survey = EncuestaServicio.duplicar_encuesta(db, base.id, admin.id_admin)
        print(f"Duplicated Survey Created: ID {new_survey.id}")

        # 3. Configure Rule for Campus = Asuncion
        # First, clear existing rules (duplicated) and add new one
        db.query(ReglaAsignacion).filter(ReglaAsignacion.id_encuesta == new_survey.id).delete()
        
        # Note: In a real app we might need valid IDs for facultad/carrera, 
        # but the mass assignment logic in sapientia_service uses filters_json mainly.
        # We'll set filters_json to target Campus Asuncion.
        
        filtros = [{"campo": "campus", "valor": "Campus Asunción"}]
        
        new_rule = ReglaAsignacion(
            id_encuesta=new_survey.id,
            publico_objetivo=PublicoObjetivo.alumnos,
            filtros_json=filtros,
            # dummy IDs if schema requires them (they are nullable in model?)
            # Let's check model... usually nullable or 0. Using None.
            id_facultad=None,
            id_carrera=None,
            id_asignatura=None
        )
        db.add(new_rule)
        
        # Ensure dates are valid for publishing
        from datetime import datetime, timedelta
        new_survey.fecha_inicio = datetime.now() - timedelta(days=1)
        new_survey.fecha_fin = datetime.now() + timedelta(days=30)
        new_survey.nombre = "Auto-Test Mass Assignment"
        
        db.commit()
        print("Survey Configured with Campus=Asuncion filter.")

        # 4. Publish
        print("Publishing survey...")
        EncuestaServicio.publicar_encuesta(db, new_survey.id, admin.id_admin)
        print("Survey Published.")

        # 5. Verify Assignments
        count = db.query(AsignacionUsuario).filter(AsignacionUsuario.id_encuesta == new_survey.id).count()
        print(f"Assignments created: {count}")
        
        if count > 0:
            print("SUCCESS: Mass assignment worked!")
        else:
            print("WARNING: No assignments created. Check if 'Asuncion' campus has students in mock DB.")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    verify_mass_assignment()
