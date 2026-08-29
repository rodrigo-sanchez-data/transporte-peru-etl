import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def extract_excel(path: Path, columnas: list) -> pd.DataFrame:
    logger.info(f"[EXTRACT] Iniciando extración de datos desde: {path}")
    try:
        df = pd.read_excel(
            path,
            header=4,
            usecols=columnas,
            na_values=["#N/A", "#REF!", "-"]
        )
        logger.info(f"[EXTRACT] Archivo cargado con éxito | Filas: {len(df):,} | Columnas: {df.shape[1]:,}")
        return df
    except FileNotFoundError:
        logger.error(f"[EXTRACT] No se encontró el arhivo en: {path}")
        raise
    except Exception:
        logger.exception(f"[EXTRACT] Error durante la extracción")
        raise

def extract_csv(path:Path, columnas: list) -> pd.DataFrame:
    logger.info(f"[EXTRACT] Iniciando extración de datos desde: {path}")
    try:
        df = pd.read_csv(
            path,
            sep=";",
            usecols=columnas
        )
        logger.info(f"[EXTRACT] Archivo cargado con éxito | Filas: {len(df):,} | Columnas: {df.shape[1]:,}")
        return df
    except FileNotFoundError:
        logger.error(f"[EXTRACT] No se encontró el arhivo en: {path}")
        raise
    except Exception:
        logger.exception(f"[EXTRACT] Error durante la extracción")
        raise