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
    estandarizar_columnas, agrupar_departamentos, normalizar_departamentos, limpiar_texto, convertir_tipos_siniestros,
    filtrar_nulos_criticos, imputar_nulos_siniestros, generar_id_departamento, asignar_id_departamento, convertir_tipos_personas,
    imputar_nulos_personas, imputar_nulos_vehiculos, convertir_tipos_vehiculos, resumen_pipeline, filtrar_huerfanos,
    eliminar_duplicados_personas
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

def preparar_departamentos(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("[PIPELINE] Iniciando preparación de la tabla departamentos...")
    df = df.copy()
    df_departamento_clean = (
        df
        .pipe(estandarizar_columnas)
        .pipe(normalizar_departamentos)
        .pipe(agrupar_departamentos)
        .pipe(generar_id_departamento)
    )
    return df_departamento_clean

def preparar_siniestros(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("[PIPELINE] Iniciando preparación de la tabla siniestros...")
    df = df.copy()
    df_siniestros_clean = (
        df
        .pipe(estandarizar_columnas)
        .pipe(limpiar_texto)
        .pipe(normalizar_departamentos)
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
    df_departamentos_clean = preparar_departamentos(df_poblacion)
    resultados["departamentos"] = {"entrada": n_pob_in, "salida": len(df_departamentos_clean)}

    n_sin_in = len(df_siniestros)
    df_siniestros_clean = preparar_siniestros(df_siniestros)
    resultados["siniestros"] = {"entrada": n_sin_in, "salida": len(df_siniestros_clean)}

    n_per_in = len(df_personas)
    df_personas_clean = preparar_personas(df_personas)
    resultados["personas"] = {"entrada": n_per_in, "salida": len(df_personas_clean)}

    n_veh_in = len(df_vehiculos)
    df_vehiculos_clean = preparar_vehiculos(df_vehiculos)
    resultados["vehiculos"] = {"entrada": n_veh_in, "salida": len(df_vehiculos_clean)}

    df_siniestros_clean = asignar_id_departamento(df_siniestros_clean, df_departamentos_clean)
    df_personas_clean = filtrar_huerfanos(df_personas_clean, df_siniestros_clean, "c_digo_siniestro", "c_digo_siniestro")
    df_vehiculos_clean = filtrar_huerfanos(df_vehiculos_clean, df_siniestros_clean, "c_digo_siniestro", "c_digo_siniestro")

    # actualiza el resumen con los conteos finales, post-huérfanos
    resultados["personas"]["salida"] = len(df_personas_clean)
    resultados["vehiculos"]["salida"] = len(df_vehiculos_clean)

    # Load
    conn_string = get_db_conn()
    crear_esquema(conn_string)
    truncar_tablas(conn_string)

    load_to_postgres(df_departamentos_clean, "departamentos", conn_string)
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