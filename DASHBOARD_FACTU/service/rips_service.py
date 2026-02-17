"""
Lógica de negocio - RIPS
=========================
Funciones específicas para el procesamiento y análisis de RIPS.
"""

import pandas as pd
from data.processors import process_rips, merge_with_facturadores, aggregate_by_user
from data.validators import validate_rips, find_column_variant
from config.settings import COLUMN_NAMES
from utils.date_helpers import filter_by_date_range


def procesar_rips(df, df_facturadores=None):
    """
    Procesa el DataFrame de RIPS.

    Args:
        df (pd.DataFrame): DataFrame de RIPS
        df_facturadores (pd.DataFrame): DataFrame de facturadores (opcional)

    Returns:
        dict: Diccionario con df_rips procesado y errores
    """
    # Validar estructura
    is_valid, message = validate_rips(df)
    if not is_valid:
        return {"error": message, "df_rips": None}

    # Procesar
    df_rips = process_rips(df)

    # Combinar con facturadores si está disponible
    if df_facturadores is not None and df_rips is not None:
        usuario_col = find_column_variant(df_rips, COLUMN_NAMES["usuario"])
        if usuario_col:
            df_rips = merge_with_facturadores(df_rips, df_facturadores, usuario_col)

        # Cruzar documento a nombre
        df_rips = cruzar_documento_a_nombre(df_rips, df_facturadores)

    return {
        "df_rips": df_rips,
        "error": None
    }


def filtrar_rips(df, start_date, end_date, usuarios_seleccionados=None):
    """
    Filtra RIPS por fecha y usuarios.

    Args:
        df (pd.DataFrame): DataFrame de RIPS
        start_date (datetime.date): Fecha inicial
        end_date (datetime.date): Fecha final
        usuarios_seleccionados (list): Lista de usuarios a incluir (opcional)

    Returns:
        pd.DataFrame: DataFrame filtrado
    """
    if df is None or df.empty:
        return df

    # Encontrar columna de fecha
    fecha_col = find_column_variant(df, COLUMN_NAMES["fecha"])
    if fecha_col is None:
        return df

    # Filtrar por fecha
    df_filtered = filter_by_date_range(df, fecha_col, start_date, end_date)

    # Filtrar por usuarios si se especificaron y NO incluye "Todos"
    es_filtro_activo = usuarios_seleccionados and 'Todos' not in usuarios_seleccionados and len(usuarios_seleccionados) > 0
    if es_filtro_activo:
        usuario_col = find_column_variant(df_filtered, COLUMN_NAMES["usuario"])
        if usuario_col and usuario_col in df_filtered.columns:
            df_filtered = df_filtered[df_filtered[usuario_col].isin(usuarios_seleccionados)]

    return df_filtered

def cruzar_documento_a_nombre(df_rips, df_facturadores):
    """
    Reemplaza el DOCUMENTO del facturador por su NOMBRE en RIPS.

    Esta función realiza un cruce tipo BUSCARX/VLOOKUP:
    - df_rips: Contiene la columna de usuario con documentos
    - df_facturadores: Contiene el mapeo DOCUMENTO → NOMBRE

    Proceso:
    1. Valida que ambos DataFrames existan y no estén vacíos
    2. Busca la columna de usuario dinámicamente (ej: 'USUARIO FACTURÓ', 'USUARIO FACTUR')
    3. Normaliza documentos (mayúsculas, sin espacios)
    4. Crea mapeo DOCUMENTO → NOMBRE
    5. Reemplaza valores en columna de usuario por el nombre correspondiente

    Args:
        df_rips (pd.DataFrame): DataFrame de RIPS con columna de usuario.
        df_facturadores (pd.DataFrame): DataFrame con columnas 'DOCUMENTO' y 'NOMBRE'.

    Returns:
        pd.DataFrame: El DataFrame df_rips con columna de usuario actualizada a nombres.
                     Si no hay coincidencia, mantiene el documento original.
    """
    if df_rips is None or df_rips.empty:
        return df_rips

    if df_facturadores is None or df_facturadores.empty:
        return df_rips

    # Buscar la columna de usuario dinámicamente
    usuario_col = find_column_variant(df_rips, COLUMN_NAMES["usuario"])

    if usuario_col is None:
        return df_rips

    if 'DOCUMENTO' not in df_facturadores.columns or 'NOMBRE' not in df_facturadores.columns:
        return df_rips

    # Crear una copia para no modificar el original
    df_rips = df_rips.copy()

    # Normalizar DOCUMENTO en ambos DataFrames
    df_facturadores_norm = df_facturadores.copy()
    df_facturadores_norm['DOCUMENTO'] = (
        df_facturadores_norm['DOCUMENTO']
        .astype(str)
        .str.strip()
        .str.upper()
    )
    df_facturadores_norm['NOMBRE'] = (
        df_facturadores_norm['NOMBRE']
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Crear mapeo DOCUMENTO → NOMBRE
    mapa_nombre = (
        df_facturadores_norm
        .dropna(subset=['DOCUMENTO', 'NOMBRE'])
        .drop_duplicates(subset=['DOCUMENTO'])
        .set_index('DOCUMENTO')['NOMBRE']
    )

    # Normalizar columna en RIPS
    df_rips[usuario_col] = (
        df_rips[usuario_col]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Aplicar cruce: si encuentra el documento, lo reemplaza por el nombre
    df_rips[usuario_col] = df_rips[usuario_col].map(mapa_nombre).fillna(df_rips[usuario_col])

    return df_rips


def calcular_productividad_rips(df):
    """
    Calcula métricas de productividad de RIPS.

    Args:
        df (pd.DataFrame): DataFrame de RIPS

    Returns:
        dict: Diccionario con métricas calculadas
    """
    if df is None or df.empty:
        return {
            "total": 0,
            "por_usuario": None,
            "por_fecha": None,
            "promedio_diario": 0
        }

    usuario_col = find_column_variant(df, COLUMN_NAMES["usuario"])
    fecha_col = find_column_variant(df, COLUMN_NAMES["fecha"])

    # Total de RIPS
    total = len(df)

    # Por usuario
    por_usuario = None
    if usuario_col:
        por_usuario = aggregate_by_user(df, usuario_col, fecha_col, group_by_date=False)

    # Por fecha
    por_fecha = None
    if fecha_col:
        df['FECHA'] = pd.to_datetime(df[fecha_col]).dt.date
        por_fecha = df.groupby('FECHA').size().reset_index(name='CANTIDAD')

    # Promedio diario
    promedio_diario = 0
    if por_fecha is not None and not por_fecha.empty:
        promedio_diario = por_fecha['CANTIDAD'].mean()

    return {
        "total": total,
        "por_usuario": por_usuario,
        "por_fecha": por_fecha,
        "promedio_diario": promedio_diario
    }
