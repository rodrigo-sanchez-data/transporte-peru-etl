import pandas as pd
import logging
import unicodedata

logger = logging.getLogger(__name__)

def estandarizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    columnas_sin_tilde = (
        df.columns
        .str.normalize("NFKD")
        .str.encode("ascii", errors="ignore")
        .str.decode("utf-8")
    )
    df.columns = (
        columnas_sin_tilde
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace(r"[^\w]", "_", regex=True)
        .str.replace("_+", "_", regex=True)
        .str.strip("_")
    )
    logger.info("[TRANSFORM] Nombres de columnas estandarizadas")
    return df

def normalizar_columna(df: pd.DataFrame, lista_columnas: list[str]) -> pd.DataFrame:
    for col in lista_columnas:
        df[col] = (
            df[col]
            .str.strip()
            .str.upper()
            .str.normalize("NFKD")
            .str.encode("ascii", errors="ignore")
            .str.decode("utf-8")
        )
    logger.info(f"[TRANSFORM] Columnas {lista_columnas} normalizadas")
    return df

def agrupar_columna(df: pd.DataFrame, lista_columnas: list[str]) -> pd.DataFrame:
    df_grupo = df.groupby(lista_columnas, as_index=False).agg({
        "cantidad": "sum"
    })
    logger.info(f"[TRANSFORM] {lista_columnas} agrupados: {len(df_grupo)} {lista_columnas} únicos")
    return df_grupo

def generar_id_columna(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    df[columna] = range(1, len(df) + 1)
    logger.info(f"[TRANSFORM] Columna {columna} generada")
    return df

def limpiar_texto(df: pd.DataFrame) -> pd.DataFrame:
    cols_texto = df.select_dtypes(include=["string", "object"]).columns.tolist()
    for col in cols_texto:
        df[col] = df[col].str.strip().astype("string")

    if cols_texto:
        logger.info(f"[TRANSFORM] Texto limpiado en {len(cols_texto)} columnas")

    return df

def corregir_nasca(df: pd.DataFrame) -> pd.DataFrame:
    n_afectados = (df["provincia"] == "NAZCA").sum()
    df["provincia"] = df["provincia"].replace("NAZCA", "NASCA")
    df["distrito"] = df["distrito"].replace("NAZCA", "NASCA")
    if n_afectados:
        logger.info(f"[TRANSFORM] Corregidas {n_afectados:,} filas de NAZCA -> NASCA (variante de escritura)")
    return df

def convertir_tipos_siniestros(df: pd.DataFrame) -> pd.DataFrame:
    df["fecha_siniestro"] = pd.to_datetime(df["fecha_siniestro"], errors="coerce", format="%d/%m/%Y")
    df["zona"] = df["zona"].astype("category")
    df["causa_factor_principal"] = df["causa_factor_principal"].astype("category")
    df["clase_siniestro"] = df["clase_siniestro"].astype("category")
    df["cantidad_de_vehiculos_danados"] = pd.to_numeric(df["cantidad_de_vehiculos_danados"], errors="coerce").astype("Int64")

    df["coordenadas_longitud"] = (
        df["coordenadas_longitud"]
        .astype(str)
        .str.replace("°", "", regex=False)
        .str.strip()
    )
    df["coordenadas_longitud"] = pd.to_numeric(df["coordenadas_longitud"], errors="coerce").astype("float64")

    logger.info("[TRANSFORM] Tipos de datos convertidos en siniestros")
    return df

def convertir_tipos_personas(df: pd.DataFrame) -> pd.DataFrame:
    df["edad"] = pd.to_numeric(df["edad"], errors="coerce").astype("Int64")
    logger.info("[TRANSFORM] Tipos de datos convertidos en personas")

    return df

def filtrar_nulos_criticos(df: pd.DataFrame, campos_criticos: list[str]) -> pd.DataFrame:
    n_antes = len(df)

    filas_con_nulos = df[campos_criticos].isna().any(axis=1).sum()
    if filas_con_nulos > 0:
        logger.warning(f"[TRANSFORM] Eliminadas {filas_con_nulos:,} filas por campos nulos en campos críticos")
        df = df.dropna(subset=campos_criticos)
    else:
        logger.info("[TRANSFORM] Validación exitosa: Cero nulos en campos criticos")

    logger.info(f"[TRANSFORM] Filtrar Nulos Criticos | Entrantes: {n_antes:,} -> Salientes: {len(df):,}")
    return df

def imputar_nulos_siniestros(df: pd.DataFrame) -> pd.DataFrame:
    nulos_vehiculos = df["cantidad_de_vehiculos_danados"].isna().sum()

    if nulos_vehiculos:
        logger.info(f"[TRANSFORM] Imputados {nulos_vehiculos:,} nulos en cantidad_de_vehiculos_danados con 0")
        df["cantidad_de_vehiculos_danados"] = df["cantidad_de_vehiculos_danados"].fillna(0).astype("Int64")
    return df

def imputar_nulos_personas(df: pd.DataFrame) -> pd.DataFrame:

    condicion_no_conductor = ~df["tipo_persona"].isin(["CONDUCTOR", "CONDUCTOR FUGADO"])
    mask_no_aplica_licencia = condicion_no_conductor & df["posee_licencia"].isna()

    n_no_aplica_licencia = mask_no_aplica_licencia.sum()
    df.loc[mask_no_aplica_licencia, "posee_licencia"] = "NO APLICA"
    if n_no_aplica_licencia:
        logger.info(f"[TRANSFORM] posee_licencia: {n_no_aplica_licencia:,} filas marcadas como NO APLICA (no conductores)")

    n_licencia_pendiente = df["posee_licencia"].isna().sum()
    if n_licencia_pendiente:
        logger.warning(f"[TRANSFORM] posee_licencia: {n_licencia_pendiente:,} nulos reales en CONDUCTOR/CONDUCTOR FUGADO, se dejan como NaN")

    condicion_no_se_sometio = df["se_sometio_a_dosaje_etilico_cuantitativo"] == "NO"
    mask_no_aplica_dosaje = condicion_no_se_sometio & df["resultado_del_dosaje_etilico_cualitativo"].isna()

    n_no_aplica_dosaje = mask_no_aplica_dosaje.sum()
    df.loc[mask_no_aplica_dosaje, "resultado_del_dosaje_etilico_cualitativo"] = "NO APLICA"
    if n_no_aplica_dosaje:
        logger.info(f"[TRANSFORM] resultado_dosaje_cualitativo: {n_no_aplica_dosaje:,} filas marcadas como NO APLICA (no se sometió)")

    n_dosaje_pendiente = df["resultado_del_dosaje_etilico_cualitativo"].isna().sum()
    if n_dosaje_pendiente:
        logger.warning(f"[TRANSFORM] resultado_dosaje_cualitativo: {n_dosaje_pendiente:,} nulos reales, se dejan como NaN")

    for col in ["edad", "sexo", "estado_licencia", "se_sometio_a_dosaje_etilico_cuantitativo"]:
        n_nulos = df[col].isna().sum()
        if n_nulos:
            logger.info(f"[TRANSFORM] {col}: {n_nulos:,} nulos sin imputar")

    return df

def asignar_id_departamento(df_provincias: pd.DataFrame, df_departamentos: pd.DataFrame) -> pd.DataFrame:
    df = pd.merge(
        left=df_provincias,
        right=df_departamentos[["id_departamento", "departamento"]],
        on="departamento",
        how="left",
        validate="many_to_one"
    )

    huerfanos = df["id_departamento"].isna().sum()
    if huerfanos > 0:
        logger.warning(f"[TRANSFORM] {huerfanos:,} provincias sin id_departamento asignado")
    else:
        logger.info("[TRANSFORM] id_departamento asignado correctamente a todas las provincias")

    return df

def asignar_id_provincia(df_distritos: pd.DataFrame, df_provincias: pd.DataFrame) -> pd.DataFrame:
    df = pd.merge(
        left=df_distritos,
        right=df_provincias[["id_provincia", "departamento", "provincia"]],
        on=["departamento", "provincia"],
        how="left",
        validate="many_to_one"
    )
    
    huerfanos = df["id_provincia"].isna().sum()
    if huerfanos > 0:
        logger.warning(f"[TRANSFORM] {huerfanos:,} distritos sin id_provincia asignado")
    else:
        logger.info("[TRANSFORM] id_provincia asignado correctamente a todos los distritos")

    return df

def asignar_id_distrito(df_siniestros: pd.DataFrame, df_distritos: pd.DataFrame) -> pd.DataFrame:
    df = pd.merge(
        left=df_siniestros,
        right=df_distritos[["id_distrito", "departamento", "provincia", "distrito"]],
        on=["departamento", "provincia", "distrito"],
        how="left",
        validate="many_to_one"
    ).drop(columns=["departamento", "provincia", "distrito"])

    huerfanos = df["id_distrito"].isna().sum()
    if huerfanos > 0:
        logger.warning(f"[TRANSFORM] {huerfanos:,} siniestros sin id_distrito asignado (revisar cruce de nombres)")
    else:
        logger.info("[TRANSFORM] id_distrito asignado correctamente a todos los siniestros")

    return df

def convertir_tipos_vehiculos(df: pd.DataFrame) -> pd.DataFrame:
    df["situacion_vehiculo"] = df["situacion_vehiculo"].astype("category")
    df["modalidad_de_transporte"] = df["modalidad_de_transporte"].astype("category")
    df["posee_seguro"] = df["posee_seguro"].astype("category")
    df["estado_soat"] = df["estado_soat"].astype("category")
    df["vehiculo"] = df["vehiculo"].astype("category")

    logger.info("[TRANSFORM] Tipos de datos convertidos en vehiculos")
    return df

def imputar_nulos_vehiculos(df: pd.DataFrame) -> pd.DataFrame:

    n_seguro = df["posee_seguro"].isna().sum()
    if n_seguro:
        df["posee_seguro"] = df["posee_seguro"].fillna("NO ESPECIFICA")
        logger.info(f"[TRANSFORM] posee_seguro: {n_seguro:,} nulos imputados con (NO ESPECIFICA)")

    n_modalidad = df["modalidad_de_transporte"].isna().sum()
    if n_modalidad:
        df["modalidad_de_transporte"] = df["modalidad_de_transporte"].fillna("SIN DATO")
        logger.info(f"[TRANSFORM] modalidad_transporte: {n_modalidad:,} nulos imputados con (SIN DATO)")

    n_soat = df["estado_soat"].isna().sum()
    if n_soat:
        df["estado_soat"] = df["estado_soat"].fillna("SIN DATO")
        logger.info(f"[TRANSFORM] estado_soat: {n_soat:,} nulos imputados con (SIN DATO)")

    return df

def filtrar_huerfanos(df_hijo: pd.DataFrame, df_padre: pd.DataFrame, col_fk: str, col_pk: str) -> pd.DataFrame:
    n_antes = len(df_hijo)
    df_filtrado = df_hijo[df_hijo[col_fk].isin(df_padre[col_pk])]
    n_huerfanos = n_antes - len(df_filtrado)
    if n_huerfanos > 0:
        logger.warning(f"[TRANSFORM] Eliminados {n_huerfanos:,} registros huérfanos (FK sin match en tabla padre)")
    return df_filtrado

def resumen_pipeline(resultados: dict) -> None:
    logger.info("=" * 60)
    logger.info("[RESUMEN] Resultados del pipeline ETL")
    logger.info("=" * 60)
    for tabla, info in resultados.items():
        logger.info(
            f"{tabla:15s} | entraron: {info['entrada']:,} | "
            f"salieron: {info['salida']:,} | "
            f"eliminados: {info['entrada'] - info['salida']:,} | "
        )
    logger.info("=" * 60)

def eliminar_duplicados_personas(df: pd.DataFrame) -> pd.DataFrame:
    n_antes = len(df)
    df = df.drop_duplicates(subset=["codigo_persona"], keep="first")
    n_eliminados = n_antes - len(df)
    if n_eliminados:
        logger.warning(f"[TRANSFORM] Eliminados {n_eliminados:,} registros duplicados en codigo_persona")
    return df