import pandas as pd
from sqlalchemy import create_engine, text
import os
import sys

# Ajuste de path para importar 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.database import URL_BASE_DATOS

def cargar_datos():
    print(f"Conectando a: {URL_BASE_DATOS.split('@')[1]}") 
    engine = create_engine(URL_BASE_DATOS)
    
    # 1. Asegurar que el esquema existe
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS sapientia;"))
        conn.commit()

    # ---------------------------------------------------------
    # PARTE 1: CARGAR OFERTA ACADÉMICA DESDE EXCEL
    # ---------------------------------------------------------
    print("Cargando Oferta Académica desde Excel...")
    
    # Leemos específicamente la hoja "Contexto Docentes" del archivo Excel
    try:
        df_oferta = pd.read_excel(
            "Contexto Sapientia.xlsx", 
            sheet_name="Contexto Docentes",
            engine="openpyxl"
        )
        
        # Limpieza de nombres de columnas (quitar espacios en blanco si los hay)
        df_oferta.columns = df_oferta.columns.str.strip()
        
        df_oferta.to_sql(
            'oferta_academica', 
            engine, 
            schema='sapientia', 
            if_exists='replace', 
            index=False,
            chunksize=500,
            method='multi'
        )
        print(f" -> {len(df_oferta)} registros de oferta insertados.")
        
    except FileNotFoundError:
        print("ERROR: No se encontró el archivo 'Contexto Sapientia.xlsx'")
        return

    # ---------------------------------------------------------
    # PARTE 2: CARGAR INSCRIPCIONES (ALUMNOS SINTÉTICOS)
    # ---------------------------------------------------------
    # Nota: Mantenemos el CSV para los alumnos ya que son datos generados (sintéticos)
    # y no parte del Excel original de contexto, a menos que los hayas movido ahí.
    print("Cargando Inscripciones...")
    try:
        df_alumnos = pd.read_csv("alumnos_sinteticos.csv")
        df_alumnos.columns = df_alumnos.columns.str.strip()

        df_alumnos.to_sql(
            'inscripciones', 
            engine, 
            schema='sapientia', 
            if_exists='replace', 
            index=False,
            chunksize=500,
            method='multi'
        )
        print(f" -> {len(df_alumnos)} inscripciones insertadas.")
        
    except FileNotFoundError:
        print("ERROR: No se encontró el archivo 'alumnos_sinteticos.csv'")

    print("¡Proceso de carga finalizado!")

if __name__ == "__main__":
    cargar_datos()