"""
Lógica de negocio - RIPS
=========================
Funciones específicas para el procesamiento y análisis de RIPS.
"""

import pandas as pd
from data.processors import process_rips, merge_with_facturadores, aggregate_by_user, filtrar_por_facturadores
from data.validators import validate_rips, find_column_variant
from config.settings import COLUMN_NAMES
from utils.date_helpers import filter_by_date_range


def procesar_rips(df, df_facturadores=None):
    """
    Procesa el DataFrame de RIPS.
    """
    is_valid, message = validate_rips(df)
    if not is_valid:
        return {"error": message, "df_rips": None}

    df_rips = process_rips(df)

    if df_facturadores is not None and df_rips is not None:
        usuario_col = find_column_variant(df_rips, COLUMN_NAMES["usuario"])
        if usuario_col:
            df_rips = merge_with_facturadores(df_rips, df_facturadores, usuario_col)

        # Cruzar documento a nombre
        df_rips = cruzar_documento_a_nombre(df_rips, df_facturadores)

        # Filtrar por facturadores DESPUÉS del cruce (comparar por NOMBRE)
        usuario_col_post = find_column_variant(df_rips, COLUMN_NAMES["usuario"])
        df_rips = filtrar_por_facturadores(df_rips, df_facturadores, usuario_col_post, 'NOMBRE')

    return {
        "df_rips": df_rips,
        "error": None
    }


def filtrar_rips(df, start_date, end_date, usuarios_seleccionados=None):
    """
    Filtra RIPS por fecha y usuarios.
    """
    if df is None or df.empty:
        return df

    fecha_col = find_column_variant(df, COLUMN_NAMES["fecha"])
    if fecha_col is None:
        return df

    df_filtered = filter_by_date_range(df, fecha_col, start_date, end_date)

    es_filtro_activo = usuarios_seleccionados and 'Todos' not in usuarios_seleccionados and len(usuarios_seleccionados) > 0
    if es_filtro_activo:
        usuario_col = find_column_variant(df_filtered, COLUMN_NAMES["usuario"])
        if usuario_col and usuario_col in df_filtered.columns:
            df_filtered = df_filtered[df_filtered[usuario_col].isin(usuarios_seleccionados)]

    return df_filtered


def cruzar_documento_a_nombre(df_rips, df_facturadores):
    """
    Reemplaza el DOCUMENTO del facturador por su NOMBRE en RIPS.
    """
    if df_rips is None or df_rips.empty:
        return df_rips

    if df_facturadores is None or df_facturadores.empty:
        return df_rips

    usuario_col = find_column_variant(df_rips, COLUMN_NAMES["usuario"])

    if usuario_col is None:
        return df_rips

    if 'DOCUMENTO' not in df_facturadores.columns or 'NOMBRE' not in df_facturadores.columns:
        return df_rips

    df_rips = df_rips.copy()

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

    mapa_nombre = (
        df_facturadores_norm
        .dropna(subset=['DOCUMENTO', 'NOMBRE'])
        .drop_duplicates(subset=['DOCUMENTO'])
        .set_index('DOCUMENTO')['NOMBRE']
    )

    df_rips[usuario_col] = (
        df_rips[usuario_col]
        .astype(str)
        .str.strip()
        .str.upper())

    df_rips[usuario_col] = df_rips[usuario_col].map(mapa_nombre).fillna(df_rips[usuario_col])

    return df_rips


def calcular_productividad_rips(df):
    """
    Calcula métricas de productividad de RIPS.
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

    total = len(df)

    por_usuario = None
    if usuario_col:
        por_usuario = aggregate_by_user(df, usuario_col, fecha_col, group_by_date=False)

    por_fecha = None
    if fecha_col:
        df_temp = df.copy()
        df_temp['FECHA'] = pd.to_datetime(df_temp[fecha_col]).dt.date
        por_fecha = df_temp.groupby('FECHA').size().reset_index(name='CANTIDAD')

    promedio_diario = 0
    if por_fecha is not None and not por_fecha.empty:
        promedio_diario = por_fecha['CANTIDAD'].mean()

    return {
        "total": total,
        "por_usuario": por_usuario,
        "por_fecha": por_fecha,
        "promedio_diario": promedio_diario
    }
