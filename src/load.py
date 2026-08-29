import pandas as pd
import logging
from sqlalchemy import create_engine, text
from pathlib import Path

logger =  logging.getLogger(__name__)

def load(df: pd.DataFrame, path: Path) -> None:
    logger.info("[LOAD] Iniciando carga de datos...")
    try:
        df.to_parquet(path, compression="snappy", engine="pyarrow", index=False)
        logger.info(f"[LOAD] Cargo con exito | registros totales: {len(df)}")
    except Exception:
        logger.exception("[LOAD] Error en la carga de datos")
        raise

def load_to_postgres(df: pd.DataFrame, tabla:str, conn_string: str) -> None:
    if df.empty:
        logger.warning("[LOAD] DataFrame vacío, no se insertaron registros")
        return
    logger.info(f"[LOAD] Iniciando conexion al motor de base de datos para la tabla: {tabla}")
    try:
        engine = create_engine(conn_string)
        df.to_sql(tabla, engine, if_exists="append", index=False, chunksize=10000, method="multi")
        logger.info(f"[LOAD] Carga exitosa | {len(df):,} registros insertados en la tabla: {tabla}")
    except Exception:
        logger.exception("[LOAD] Error al cargar en PostgreSQL")
        raise
    finally:
        engine.dispose()

def crear_esquema(conn_string: str, ruta_schema: str = "sql/schema.sql") -> None:
    engine = create_engine(conn_string)
    try:
        with open(ruta_schema, "r", encoding="utf-8") as f:
            ddl = f.read()
        with engine.connect() as conn:
            conn.execute(text(ddl))
            conn.commit()
        logger.info("[LOAD] Esquema verificado/creado desde schema.sql")
    finally:
        engine.dispose()
        
def truncar_tablas(conn_string: str) -> None:
    engine = create_engine(conn_string)
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "TRUNCATE TABLE personas, vehiculos, siniestros, departamentos RESTART IDENTITY CASCADE"
            ))
            conn.commit()
        logger.info("[LOAD] Tablas truncadas antes de la carga")
    finally:
        engine.dispose()


