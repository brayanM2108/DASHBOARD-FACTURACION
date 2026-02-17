"""
Lógica de negocio - Legalizaciones
===================================
Funciones específicas para el procesamiento y análisis de legalizaciones.
"""

import pandas as pd
from data.processors import process_legalizaciones, merge_with_facturadores, aggregate_by_user
from data.validators import validate_legalizaciones, find_column_variant
from config.settings import COLUMN_NAMES
from utils.date_helpers import filter_by_date_range


def procesar_legalizaciones(df, df_facturadores=None):
    """
    Procesa el DataFrame de legalizaciones completo.

    Args:
        df (pd.DataFrame): DataFrame de legalizaciones
        df_facturadores (pd.DataFrame): DataFrame de facturadores (opcional)

    Returns:
        dict: Diccionario con df_ppl y df_convenios procesados
    """
    # Validar estructura
    is_valid, message = validate_legalizaciones(df)
    if not is_valid:
        return {"error": message, "df_ppl": None, "df_convenios": None}

    # Procesar y separar
    df_ppl, df_convenios = process_legalizaciones(df)

    # Combinar con facturadores si está disponible
    if df_facturadores is not None:
        usuario_col = find_column_variant(df_ppl, COLUMN_NAMES["usuario"]) if df_ppl is not None else None
        if usuario_col:
            df_ppl = merge_with_facturadores(df_ppl, df_facturadores, usuario_col)

        usuario_col = find_column_variant(df_convenios, COLUMN_NAMES["usuario"]) if df_convenios is not None else None
        if usuario_col:
            df_convenios = merge_with_facturadores(df_convenios, df_facturadores, usuario_col)

    return {
        "df_ppl": df_ppl,
        "df_convenios": df_convenios,
        "error": None
    }


def filtrar_legalizaciones(df, start_date, end_date, usuarios_seleccionados=None):
    """
    Filtra legalizaciones por fecha y usuarios.

    Args:
        df (pd.DataFrame): DataFrame de legalizaciones
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


def calcular_productividad_legalizaciones(df, tipo="PPL"):
    """
    Calcula métricas de productividad de legalizaciones.

    Args:
        df (pd.DataFrame): DataFrame de legalizaciones
        tipo (str): Tipo de legalizaciones ("PPL" o "Convenios")

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

    # Total de legalizaciones
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
        "promedio_diario": promedio_diario,
        "tipo": tipo
    }
