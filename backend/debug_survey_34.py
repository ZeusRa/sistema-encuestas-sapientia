from app.database import SesionLocal
from app.modelos import Encuesta
import sys

def check_survey(id):
    db = SesionLocal()
    try:
        e = db.query(Encuesta).filter(Encuesta.id == id).first()
        if not e:
            print(f"Survey {id} NOT FOUND.")
            return
        
        print(f"\n=== Survey {id}: {e.nombre} ===")
        print(f"Status: {e.estado}")
        
        for p in e.preguntas:
            if "matriz" in str(p.tipo) or "opcion" in str(p.tipo):
                print(f" - Q{p.id}: {p.tipo} | {p.texto_pregunta}")
                print(f"   Config JSON: {p.configuracion_json}")
                if p.opciones:
                    print(f"   Options ({len(p.opciones)}):")
                    for o in p.opciones:
                        print(f"     - [{o.id}] {o.texto_opcion}")
                else:
                    print("   Options: [] (EMPTY!)")

    except Exception as err:
        print(f"Error: {err}")
    finally:
        db.close()

if __name__ == "__main__":
    check_survey(30)
