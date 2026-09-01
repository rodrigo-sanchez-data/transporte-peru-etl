import pandas as pd
import logging
import sys
from config import (
    PATH_LOG, PATH_RAW_SINIESTROS, PATH_RAW_PERSONAS, PATH_RAW_VEHICULOS, PATH_RAW_POBLACION, 
    COLUMNAS_SINIESTROS, COLUMNAS_PERSONAS, COLUMNAS_VEHICULOS, COLUMNAS_POBLACION, CAMPOS_CRITICOS_SINIESTROS,
    CAMPOS_CRITICOS_PERSONAS, CAMPOS_CRITICOS_VEHICULOS,
    get_db_conn
)
from src.extract import extract_excel, extract_csv
from src.transform import (
    estandarizar_columnas, agrupar_columna, normalizar_columna, limpiar_texto, convertir_tipos_siniestros,
    filtrar_nulos_criticos, imputar_nulos_siniestros, generar_id_columna, asignar_id_departamento, convertir_tipos_personas,
    imputar_nulos_personas, imputar_nulos_vehiculos, convertir_tipos_vehiculos, resumen_pipeline, filtrar_huerfanos,
    eliminar_duplicados_personas, asignar_id_distrito, asignar_id_provincia, corregir_nasca
)
from src.load import load_to_postgres, crear_esquema, truncar_tablas

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=(
        logging.FileHandler(PATH_LOG),
        logging.StreamHandler()
    )
)

logger = logging.getLogger(__name__)

def preparar_distritos(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("[PIPELINE] Iniciando preparación de la tabla distritos...")
    df = df.copy()
    df_distritos_clean = (
        df
        .pipe(estandarizar_columnas)
        .pipe(normalizar_columna, lista_columnas=["departamento", "provincia", "distrito"])
        .pipe(corregir_nasca)
        .pipe(agrupar_columna, lista_columnas=["departamento", "provincia", "distrito"])
        .pipe(generar_id_columna, columna = "id_distrito")
    )
    return df_distritos_clean

def preparar_provincias(df_distritos: pd.DataFrame) -> pd.DataFrame:
    logger.info("[PIPELINE] Iniciando preparación de la tabla provincias...")
    df_provincias_clean = (
        df_distritos
        .pipe(agrupar_columna, lista_columnas=["departamento", "provincia"])
        .pipe(generar_id_columna, columna = "id_provincia")
    )
    return df_provincias_clean

def preparar_departamentos(df_provincias: pd.DataFrame) -> pd.DataFrame:
    logger.info("[PIPELINE] Iniciando preparación de la tabla departamentos...")
    df_departamentos_clean = (
        df_provincias
        .pipe(agrupar_columna, lista_columnas=["departamento"])
        .pipe(generar_id_columna, columna = "id_departamento")
    )
    return df_departamentos_clean

def preparar_siniestros(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("[PIPELINE] Iniciando preparación de la tabla siniestros...")
    df = df.copy()
    df_siniestros_clean = (
        df
        .pipe(estandarizar_columnas)
        .pipe(limpiar_texto)
        .pipe(normalizar_columna, lista_columnas=["departamento", "provincia", "distrito"])
        .pipe(convertir_tipos_siniestros)
        .pipe(filtrar_nulos_criticos, CAMPOS_CRITICOS_SINIESTROS)
        .pipe(imputar_nulos_siniestros)
    )
    return df_siniestros_clean

def preparar_personas(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("[PIPELINE] Iniciando preparación de la tabla personas...")
    df = df.copy()
    df_personas_clean = (
        df
        .pipe(estandarizar_columnas)
        .pipe(convertir_tipos_personas)
        .pipe(limpiar_texto)
        .pipe(filtrar_nulos_criticos, CAMPOS_CRITICOS_PERSONAS)
        .pipe(imputar_nulos_personas)
        .pipe(eliminar_duplicados_personas)
    )
    return df_personas_clean

def preparar_vehiculos(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("[PIPELINE] Iniciando preparación de la tabla vehiculos...")
    df = df.copy()
    df_vehiculos_clean = (
        df
        .pipe(estandarizar_columnas)
        .pipe(limpiar_texto)
        .pipe(imputar_nulos_vehiculos)
        .pipe(filtrar_nulos_criticos, CAMPOS_CRITICOS_VEHICULOS)
        .pipe(convertir_tipos_vehiculos)
    )
    return df_vehiculos_clean

def ejecutar_pipeline() -> None:
    logger.info("[PIPELINE] ==== Iniciando pipeline ====")
    resultados = {}

    # Extract
    df_poblacion = extract_csv(PATH_RAW_POBLACION, COLUMNAS_POBLACION)
    df_siniestros = extract_excel(PATH_RAW_SINIESTROS, COLUMNAS_SINIESTROS)
    df_personas = extract_excel(PATH_RAW_PERSONAS, COLUMNAS_PERSONAS)
    df_vehiculos = extract_excel(PATH_RAW_VEHICULOS, COLUMNAS_VEHICULOS)

    # Transform
    n_pob_in = len(df_poblacion)
    df_distritos_clean = preparar_distritos(df_poblacion)
    df_provincias_clean = preparar_provincias(df_distritos_clean)
    df_departamentos_clean = preparar_departamentos(df_provincias_clean)
    resultados["distritos"] = {"entrada": n_pob_in, "salida": len(df_distritos_clean)}
    resultados["provincias"] = {"entrada": len(df_distritos_clean), "salida": len(df_provincias_clean)}
    resultados["departamentos"] = {"entrada": len(df_provincias_clean), "salida": len(df_departamentos_clean)}

    n_sin_in = len(df_siniestros)
    df_siniestros_clean = preparar_siniestros(df_siniestros)
    resultados["siniestros"] = {"entrada": n_sin_in, "salida": len(df_siniestros_clean)}

    n_per_in = len(df_personas)
    df_personas_clean = preparar_personas(df_personas)
    resultados["personas"] = {"entrada": n_per_in, "salida": len(df_personas_clean)}

    n_veh_in = len(df_vehiculos)
    df_vehiculos_clean = preparar_vehiculos(df_vehiculos)
    resultados["vehiculos"] = {"entrada": n_veh_in, "salida": len(df_vehiculos_clean)}

    df_provincias_clean = asignar_id_departamento(df_provincias_clean, df_departamentos_clean)
    df_distritos_clean = asignar_id_provincia(df_distritos_clean, df_provincias_clean)
    df_siniestros_clean = asignar_id_distrito(df_siniestros_clean, df_distritos_clean)

    df_provincias_clean = df_provincias_clean.drop(columns=["departamento"])
    df_distritos_clean = df_distritos_clean.drop(columns=["departamento", "provincia"])

    df_personas_clean = filtrar_huerfanos(df_personas_clean, df_siniestros_clean, "codigo_siniestro", "codigo_siniestro")
    df_vehiculos_clean = filtrar_huerfanos(df_vehiculos_clean, df_siniestros_clean, "codigo_siniestro", "codigo_siniestro")

    resultados["personas"]["salida"] = len(df_personas_clean)
    resultados["vehiculos"]["salida"] = len(df_vehiculos_clean)

    # Load
    conn_string = get_db_conn()
    crear_esquema(conn_string)
    truncar_tablas(conn_string)

    load_to_postgres(df_departamentos_clean, "departamentos", conn_string)
    load_to_postgres(df_provincias_clean, "provincias", conn_string)
    load_to_postgres(df_distritos_clean, "distritos", conn_string)
    load_to_postgres(df_siniestros_clean, "siniestros", conn_string)
    load_to_postgres(df_personas_clean, "personas", conn_string)
    load_to_postgres(df_vehiculos_clean, "vehiculos", conn_string)


    resumen_pipeline(resultados)
    logger.info("[PIPELINE] ==== Pipeline finalizado con éxito ====")

    
def main() -> None:
    try:
        ejecutar_pipeline()

    except Exception as e:
        logger.critical(f"[PIPELINE] Falla critica {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()