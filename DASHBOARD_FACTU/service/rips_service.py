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

    # Filtrar por usuarios si se especificaron
    if usuarios_seleccionados:
        usuario_col = find_column_variant(df_filtered, COLUMN_NAMES["usuario"])
        if usuario_col and usuario_col in df_filtered.columns:
            df_filtered = df_filtered[df_filtered[usuario_col].isin(usuarios_seleccionados)]

    return df_filtered


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
