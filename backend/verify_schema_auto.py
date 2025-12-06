import sys
from sqlalchemy import inspect
from app.database import motor as engine, Base
from app import modelos  # Import models to register them

# Encoding safe output
sys.stdout.reconfigure(encoding='utf-8')

def verify_models():
    inspector = inspect(engine)
    
    # Map of Model Class -> Table Name
    # We want to check specifically the tables defined in our schema "encuestas_oltp"
    models_to_check = [
        modelos.UsuarioAdmin,
        modelos.Permiso,
        modelos.RolPermiso,
        modelos.UsuarioPermiso,
        modelos.PlantillaOpciones,
        modelos.PlantillaOpcionDetalle,
        modelos.Encuesta,
        modelos.ReglaAsignacion,
        modelos.Pregunta,
        modelos.OpcionRespuesta,
        modelos.AsignacionUsuario,
        modelos.RespuestaBorrador,
        modelos.TransaccionEncuesta,
        modelos.Respuesta
    ]

    with open("schema_report.txt", "w", encoding="utf-8") as f:
        f.write("--- INICIANDO VERIFICACIÓN DE ESQUEMA ---\n")
        
        for model in models_to_check:
            table_name = model.__tablename__
            # Handle __table_args__ being a tuple or dict
            args = model.__table_args__
            schema = 'public'
            if isinstance(args, dict):
                schema = args.get('schema', 'public')
            elif isinstance(args, tuple):
                for arg in args:
                    if isinstance(arg, dict) and 'schema' in arg:
                        schema = arg['schema']
                        break
            
            try:
                # Get columns from DB
                db_columns = inspector.get_columns(table_name, schema=schema)
                db_col_names = set(c['name'] for c in db_columns)
                
                # Get columns from Model
                model_cols = set(c.name for c in model.__table__.columns)
                
                # Find missing in DB
                missing_in_db = model_cols - db_col_names
                
                if missing_in_db:
                    f.write(f"[FALLO] Tabla '{schema}.{table_name}' MISSING COLS: {missing_in_db}\n")
                    all_good = False
                # else:
                #     f.write(f"[OK] {schema}.{table_name}\n")
                    
            except Exception as e:
                f.write(f"[ERROR] No se pudo inspeccionar {table_name}: {e}\n")
                all_good = False

        if all_good:
            f.write("\n>>> ESQUEMA ALINEADO CORRECTAMENTE <<<\n")
        else:
            f.write("\n>>> SE ENCONTRARON DISCREPANCIAS <<<\n")

    print("Verificación completada. Revisar schema_report.txt")

if __name__ == "__main__":
    verify_models()
