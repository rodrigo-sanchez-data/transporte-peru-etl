from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).parent

PATH_LOG = BASE_DIR / "etl_transporte.log"
PATH_RAW_SINIESTROS = BASE_DIR / "data" / "raw" / "BBDD ONSV - SINIESTROS FATALES 2021-2025.xlsx"
PATH_RAW_PERSONAS = BASE_DIR / "data" / "raw" / "BBDD ONSV - PERSONAS 2021-2025.xlsx"
PATH_RAW_VEHICULOS = BASE_DIR / "data" / "raw" / "BBDD ONSV - VEHICULOS 2021-2025.xlsx"
PATH_RAW_POBLACION = BASE_DIR / "data" / "raw" / "TB_POBLACION_INEI.csv"


COLUMNAS_SINIESTROS = ["CÓDIGO SINIESTRO", "FECHA SINIESTRO", "HORA SINIESTRO", "CLASE SINIESTRO", "CANTIDAD DE FALLECIDOS",
                     "CANTIDAD DE LESIONADOS", "CANTIDAD DE VEHICULOS DAÑADOS", "DEPARTAMENTO", "ZONA", "COORDENADAS LATITUD",
                     "COORDENADAS  LONGITUD", "CAUSA FACTOR PRINCIPAL", "COD CARRETERA", "PROVINCIA", "DISTRITO"]

COLUMNAS_PERSONAS = ["CÓDIGO PERSONA", "CÓDIGO SINIESTRO", "TIPO PERSONA", "GRAVEDAD", "EDAD", "SEXO",
                     "POSEE LICENCIA", "ESTADO LICENCIA", "¿SE SOMETIÓ A DOSAJE ETÍLICO CUANTITATIVO?", "RESULTADO DEL DOSAJE ETÍLICO CUALITATIVO"]

COLUMNAS_VEHICULOS = ["CÓDIGO VEHICULO", "CÓDIGO SINIESTRO", "VEHÍCULO", "SITUACIÓN VEHÍCULO", "POSEE SEGURO",
                      "ESTADO SOAT", "MODALIDAD DE TRANSPORTE"]

COLUMNAS_POBLACION = ["Departamento", "Provincia", "Distrito", "Cantidad",]

CAMPOS_CRITICOS_SINIESTROS = ["codigo_siniestro", "fecha_siniestro", "zona", "cod_carretera", "coordenadas_longitud"]
CAMPOS_CRITICOS_PERSONAS = ["codigo_siniestro", "codigo_persona"]
CAMPOS_CRITICOS_VEHICULOS = ["codigo_siniestro", "codigo_vehiculo"]

def get_db_conn() -> str:
    requeridos = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
    faltantes = [var for var in requeridos if not os.getenv(var)]
    if faltantes:
        raise EnvironmentError(f"Variables faltantes: {faltantes}")

    return(
        f"postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}"
        f"@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}"
    )
