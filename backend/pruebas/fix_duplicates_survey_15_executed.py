import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

URL_BASE_DATOS = os.getenv("DATABASE_URL")
if URL_BASE_DATOS and URL_BASE_DATOS.startswith("postgres://"):
    URL_BASE_DATOS = URL_BASE_DATOS.replace("postgres://", "postgresql://", 1)

engine = create_engine(URL_BASE_DATOS)

def fix_duplicates(survey_id=15):
    print(f"\n--- Iniciando corrección de duplicados para Encuesta {survey_id} ---")
    
    with engine.begin() as conn:
        # 1. Obtener todas las preguntas
        print("Leyendo preguntas...")
        sql_questions = f"""
            SELECT id, texto_pregunta, orden, tipo
            FROM encuestas_oltp.pregunta 
            WHERE id_encuesta = {survey_id} 
            ORDER BY orden, id
        """
        df_questions = pd.read_sql(sql_questions, conn)
        
        # Agrupar por texto, tipo y orden para encontrar duplicados
        duplicates_groups = df_questions.groupby(['texto_pregunta', 'tipo', 'orden'])
        
        questions_deleted = 0
        options_deleted = 0
        answers_migrated = 0
        
        for name, group in duplicates_groups:
            if len(group) > 1:
                # Ordenar por ID para elegir el "Master" (el más antiguo/menor ID)
                group = group.sort_values('id')
                master_id = group.iloc[0]['id']
                duplicate_ids = group.iloc[1:]['id'].tolist()
                
                print(f"Procesando: '{name[0][:30]}...' (Master: {master_id}, Duplicados: {duplicate_ids})")
                
                # --- MIGRAR RESPUESTAS DE PREGUNTAS ---
                dup_ids_str = ",".join(map(str, duplicate_ids))
                
                # Mover respuestas que apuntan a preguntas duplicadas -> pregunta master
                sql_update_answers_q = f"""
                    UPDATE encuestas_oltp.respuesta
                    SET id_pregunta = {master_id}
                    WHERE id_pregunta IN ({dup_ids_str})
                """
                res = conn.execute(text(sql_update_answers_q))
                answers_migrated += res.rowcount
                
                # --- PROCESAR OPCIONES ---
                # Obtener opciones del Master
                sql_opts_master = f"SELECT id, texto_opcion FROM encuestas_oltp.opcion_respuesta WHERE id_pregunta = {master_id}"
                df_opts_master = pd.read_sql(sql_opts_master, conn)
                
                # Obtener opciones de los Duplicados
                sql_opts_dups = f"SELECT id, texto_opcion, id_pregunta FROM encuestas_oltp.opcion_respuesta WHERE id_pregunta IN ({dup_ids_str})"
                df_opts_dups = pd.read_sql(sql_opts_dups, conn)
                
                if not df_opts_dups.empty:
                    for _, bad_opt in df_opts_dups.iterrows():
                        # Buscar opción equivalente en Master
                        match = df_opts_master[df_opts_master['texto_opcion'] == bad_opt['texto_opcion']]
                        if not match.empty:
                            master_opt_id = match.iloc[0]['id']
                            bad_opt_id = bad_opt['id']
                            
                            # Mover respuestas que apuntan a esta opción duplicada
                            sql_update_answers_o = f"""
                                UPDATE encuestas_oltp.respuesta
                                SET id_opcion = {master_opt_id}
                                WHERE id_opcion = {bad_opt_id}
                            """
                            conn.execute(text(sql_update_answers_o))
                            
                            # La opción duplicada se eliminará en cascada o manualmente
                            # (La eliminamos manualmente para ser seguros)
                            conn.execute(text(f"DELETE FROM encuestas_oltp.opcion_respuesta WHERE id = {bad_opt_id}"))
                            options_deleted += 1
                
                # --- ELIMINAR PREGUNTAS DUPLICADAS ---
                # Primero borrar sus opciones restantes (si las hay)
                conn.execute(text(f"DELETE FROM encuestas_oltp.opcion_respuesta WHERE id_pregunta IN ({dup_ids_str})"))
                
                # Borrar preguntas
                conn.execute(text(f"DELETE FROM encuestas_oltp.pregunta WHERE id IN ({dup_ids_str})"))
                questions_deleted += len(duplicate_ids)

        print("-" * 30)
        print("RESUMEN DE OPERACIONES:")
        print(f"Respuestas migradas: {answers_migrated}")
        print(f"Opciones duplicadas eliminadas: {options_deleted}")
        print(f"Preguntas duplicadas eliminadas: {questions_deleted}")
        print("-" * 30)

if __name__ == "__main__":
    fix_duplicates()
