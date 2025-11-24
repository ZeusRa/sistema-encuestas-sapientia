import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import urllib.parse
import numpy as np

# Cargar configuración
load_dotenv()

USUARIO_BD = os.getenv("BD_USUARIO", "postgres")
CLAVE_BD = os.getenv("BD_CLAVE", "")
SERVIDOR_BD = os.getenv("BD_SERVIDOR", "localhost")
PUERTO_BD = os.getenv("BD_PUERTO", "5432")
NOMBRE_BD = os.getenv("BD_NOMBRE", "postgres")

clave_codificada = urllib.parse.quote_plus(CLAVE_BD)
URL_BASE_DATOS = f"postgresql://{USUARIO_BD}:{clave_codificada}@{SERVIDOR_BD}:{PUERTO_BD}/{NOMBRE_BD}"

motor = create_engine(URL_BASE_DATOS)

def cargar_dimension(conn, df_source, table_name, schema, key_cols, id_col):
    """
    Función para cargar dimensiones en lote.
    1. Identifica valores únicos en el dataframe origen.
    2. Lee los valores existentes en la BD.
    3. Inserta solo los nuevos (evitando duplicados).
    4. Devuelve el dataframe original con el ID de la dimensión pegado (merge).
    """
    if df_source.empty:
        return df_source

    # 1. Extraer únicos del lote actual
    unique_new = df_source[key_cols].drop_duplicates().dropna()
    
    # 2. Leer existentes de la BD 
    # Aquí asumimos que la dimensión cabe en memoria (millones de filas ok, billones no)
    query_existing = f"SELECT {id_col}, {', '.join(key_cols)} FROM {schema}.{table_name}"
    df_existing = pd.read_sql(query_existing, conn)
    
    # 3. Filtrar lo que ya existe
    # Hacemos un merge left. Si id_col es NaN, es nuevo.
    merged = unique_new.merge(df_existing, on=key_cols, how='left', indicator=True)
    to_insert = merged[merged['_merge'] == 'left_only'][key_cols]
    
    if not to_insert.empty:
        print(f"   -> Insertando {len(to_insert)} nuevos registros en {table_name}...")
        to_insert.to_sql(table_name, conn, schema=schema, if_exists='append', index=False)
        # Recargamos el mapa de IDs con los nuevos insertados
        df_existing = pd.read_sql(query_existing, conn)
    
    # 4. Mapear los IDs al dataframe original
    # Hacemos merge para traer el ID a cada fila de transacciones
    df_final = df_source.merge(df_existing, on=key_cols, how='left')
    
    return df_final

def ejecutar_etl():
    print("Iniciando proceso ETL Masivo (Batch)...")
    
    # Usamos una conexión para todo el proceso
    with motor.begin() as conn:
        # ---------------------------------------------------------
        # 1. EXTRACCIÓN (JOIN MASIVO)
        # ---------------------------------------------------------
        print("1. Extrayendo datos transaccionales...")
        
        # Traemos todo de una vez: Transacción + Respuesta + Pregunta + Encuesta
        query_full = text("""
            SELECT 
                t.id_transaccion,
                t.fecha_finalizacion,
                t.metadatos_contexto,
                r.valor_respuesta,
                p.texto_pregunta,
                p.tipo as tipo_pregunta,
                e.nombre as nombre_encuesta
            FROM encuestas_oltp.transaccion_encuesta t
            JOIN encuestas_oltp.respuesta r ON t.id_transaccion = r.id_transaccion
            JOIN encuestas_oltp.pregunta p ON r.id_pregunta = p.id
            JOIN encuestas_oltp.encuesta e ON p.id_encuesta = e.id
            WHERE t.procesado_etl = FALSE
        """)
        
        df = pd.read_sql(query_full, conn)
        
        if df.empty:
            print("No hay datos nuevos para procesar.")
            return

        print(f"   -> Procesando {len(df)} registros de respuestas...")

        # ---------------------------------------------------------
        # 2. TRANSFORMACIÓN (PANDAS EN MEMORIA)
        # ---------------------------------------------------------
        
        # A. Normalizar Metadatos JSON (Expandir columnas)
        # Convertimos la columna JSON en columnas de dataframe: facultad, carrera, etc.
        df_meta = pd.json_normalize(df['metadatos_contexto'])
        # Aseguramos que existan las columnas aunque el JSON venga vacío
        for col in ['facultad', 'carrera', 'campus', 'profesor', 'asignatura', 'semestre']:
            if col not in df_meta.columns:
                df_meta[col] = "Desconocido"
        
        # Unimos metadatos al dataframe principal
        df = df.join(df_meta).fillna("Desconocido")

        # B. Preparar datos de Tiempo
        df['fecha_dt'] = pd.to_datetime(df['fecha_finalizacion'])
        df['fecha'] = df['fecha_dt'].dt.date
        df['anho'] = df['fecha_dt'].dt.year
        df['mes'] = df['fecha_dt'].dt.month
        df['dia_semana'] = df['fecha_dt'].dt.day_name()
        # Semestre 1 o 2
        df['semestre'] = np.where(df['mes'] <= 6, 1, 2)

        # ---------------------------------------------------------
        # 3. CARGA DE DIMENSIONES (GESTIÓN DE IDENTIDAD)
        # ---------------------------------------------------------
        print("2. Gestionando Dimensiones...")

        # --- Dimensión Tiempo ---
        # Columnas clave para identificar unicidad
        cols_tiempo = ['fecha', 'anho', 'semestre', 'mes', 'dia_semana']
        df = cargar_dimension(conn, df, 'dim_tiempo', 'encuestas_olap', cols_tiempo, 'id_dim_tiempo')

        # --- Dimensión Ubicación ---
        # Mapeamos nombres de DF a nombres de BD
        df['nombre_facultad'] = df['facultad']
        df['nombre_carrera'] = df['carrera']
        df['nombre_campus'] = df['campus']
        cols_ubi = ['nombre_facultad', 'nombre_carrera', 'nombre_campus']
        df = cargar_dimension(conn, df, 'dim_ubicacion', 'encuestas_olap', cols_ubi, 'id_dim_ubicacion')

        # --- Dimensión Contexto Académico ---
        df['nombre_profesor'] = df['profesor']
        df['nombre_asignatura'] = df['asignatura']
        # Asegurar que semestre sea int
        df['semestre_curso'] = pd.to_numeric(df['semestre'], errors='coerce').fillna(0).astype(int)
        
        cols_ctx = ['nombre_profesor', 'nombre_asignatura'] # Clave única definida en SQL
        df = cargar_dimension(conn, df, 'dim_contexto_academico', 'encuestas_olap', cols_ctx, 'id_dim_contexto')

        # --- Dimensión Pregunta ---
        cols_preg = ['texto_pregunta', 'nombre_encuesta', 'tipo_pregunta']
        df = cargar_dimension(conn, df, 'dim_pregunta', 'encuestas_olap', cols_preg, 'id_dim_pregunta')

        # ---------------------------------------------------------
        # 4. CARGA DE HECHOS (BULK INSERT)
        # ---------------------------------------------------------
        print("3. Cargando Tabla de Hechos...")

        # Preparamos el DataFrame final para la tabla de hechos
        df_hechos = pd.DataFrame()
        df_hechos['id_transaccion_origen'] = df['id_transaccion']
        df_hechos['id_dim_tiempo'] = df['id_dim_tiempo']
        df_hechos['id_dim_ubicacion'] = df['id_dim_ubicacion']
        df_hechos['id_dim_contexto'] = df['id_dim_contexto']
        df_hechos['id_dim_pregunta'] = df['id_dim_pregunta']
        df_hechos['respuesta_texto'] = df['valor_respuesta']
        
        # Convertir respuesta numérica si es posible
        df_hechos['respuesta_numerica'] = pd.to_numeric(df['valor_respuesta'], errors='coerce')
        df_hechos['conteo'] = 1

        # Insertar masivamente
        df_hechos.to_sql('hechos_respuestas', conn, schema='encuestas_olap', if_exists='append', index=False)

        # ---------------------------------------------------------
        # 5. ACTUALIZAR ESTADO (CIERRE)
        # ---------------------------------------------------------
        print("4. Actualizando estado en OLTP...")
        
        # Obtenemos la lista única de IDs procesados
        ids_procesados = df['id_transaccion'].unique().tolist()
        
        # Actualizamos en un solo query usando IN (...)
        if ids_procesados:
            # Convertimos la lista a string para el query: (1, 2, 3)
            ids_str = ",".join(map(str, ids_procesados))
            query_update = text(f"UPDATE encuestas_oltp.transaccion_encuesta SET procesado_etl = TRUE WHERE id_transaccion IN ({ids_str})")
            conn.execute(query_update)

    print(f"ETL Finalizado. {len(df_hechos)} hechos insertados.")

if __name__ == "__main__":
    ejecutar_etl()