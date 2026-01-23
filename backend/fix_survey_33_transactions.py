from app.database import SesionLocal
from app.modelos import TransaccionEncuesta, AsignacionUsuario
from sqlalchemy.orm.attributes import flag_modified
import sys

def fix_survey_33_transactions():
    db = SesionLocal()
    try:
        transactions = db.query(TransaccionEncuesta).filter(TransaccionEncuesta.id_encuesta == 33).all()
        print(f"Found {len(transactions)} transactions.")
        
        updated_count = 0
        for tx in transactions:
            meta = tx.metadatos_contexto or {}
            
            # Try to identify user by id_usuario OR id_referencia
            uid = meta.get('id_usuario') or meta.get('user_id')
            ref_id = meta.get('id_referencia')
            
            assign = None
            if uid:
                assign = db.query(AsignacionUsuario).filter(
                    AsignacionUsuario.id_encuesta == 33,
                    AsignacionUsuario.id_usuario == uid
                ).first()
            elif ref_id:
                assign = db.query(AsignacionUsuario).filter(
                    AsignacionUsuario.id_encuesta == 33,
                    AsignacionUsuario.id_referencia_contexto == ref_id
                ).first()
            
            if assign and assign.metadatos_asignacion:
                # Merge logic: source is assign.metadatos_asignacion
                # We want campus, facultar, carrera
                assign_meta = assign.metadatos_asignacion
                
                updates = {}
                for key in ['campus', 'facultad', 'carrera', 'departamento']:
                    if key in assign_meta:
                        updates[key] = assign_meta[key]
                
                if updates:
                    meta.update(updates)
                    tx.metadatos_contexto = meta
                    flag_modified(tx, "metadatos_contexto")
                    updated_count += 1
            else:
                print(f"Transaction {tx.id_transaccion}: No assignment found for user {uid}")

        db.commit()
        print(f"Updated {updated_count} transactions.")

    except Exception as err:
        db.rollback()
        print(f"Error: {err}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_survey_33_transactions()
