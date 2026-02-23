"""
Lógica de negocio - Facturación
================================
Funciones específicas para el procesamiento y análisis de facturación.
"""

import pandas as pd
from data.processors import process_facturacion, merge_with_facturadores, aggregate_by_user, filtrar_por_facturadores
from data.validators import validate_facturacion, find_column_variant
from config.settings import COLUMN_NAMES
from utils.date_helpers import filter_by_date_range


def procesar_facturacion(df, df_facturadores=None):
    """
    Procesa el DataFrame de facturación.
    """
    is_valid, message = validate_facturacion(df)
    if not is_valid:
        return {"error": message, "df_facturacion": None}

    df_facturacion = process_facturacion(df)

    if df_facturadores is not None and df_facturacion is not None:
        usuario_col = find_column_variant(df_facturacion, COLUMN_NAMES["usuario"])
        if usuario_col:
            df_facturacion = merge_with_facturadores(df_facturacion, df_facturadores, usuario_col)

    return {
        "df_facturacion": df_facturacion,
        "error": None
    }


def filtrar_facturacion(df, start_date, end_date, usuarios_seleccionados=None):
    """
    Filtra facturación por fecha y usuarios.
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


def obtener_facturacion_con_usuario(df_facturacion, df_fact_elec, df_facturadores=None):
    """
    Cruza facturación con facturación electrónica para obtener el usuario.
    Filtra solo usuarios que están en el archivo de facturadores.
    """
    from data.processors import merge_facturacion_with_electronica

    if df_facturacion is None or df_facturacion.empty:
        return {"df_with_usuario": None, "df_por_usuario": None, "usuario_col": None, "error": "No hay datos de facturación"}

    if df_fact_elec is None or df_fact_elec.empty:
        return {"df_with_usuario": None, "df_por_usuario": None, "usuario_col": None, "error": "No hay datos de facturación electrónica"}

    # Hacer el cruce
    df_with_usuario = merge_facturacion_with_electronica(df_facturacion, df_fact_elec)

    usuario_col = find_column_variant(df_with_usuario, COLUMN_NAMES["usuario"])

    if usuario_col is None or usuario_col not in df_with_usuario.columns:
        return {"df_with_usuario": None, "df_por_usuario": None, "usuario_col": None, "error": "No se pudo determinar el usuario"}

    # Filtrar registros con usuario asignado
    df_with_usuario_valid = df_with_usuario[df_with_usuario[usuario_col].notna()].copy()

    if df_with_usuario_valid.empty:
        return {"df_with_usuario": None, "df_por_usuario": None, "usuario_col": None, "error": "No se encontraron coincidencias"}

    # Filtrar por facturadores DESPUÉS del merge (comparar por NOMBRE)
    if df_facturadores is not None and not df_facturadores.empty:
        df_with_usuario_valid = filtrar_por_facturadores(
            df_with_usuario_valid,
            df_facturadores,
            usuario_col,
            'NOMBRE'
        )

    if df_with_usuario_valid.empty:
        return {"df_with_usuario": None, "df_por_usuario": None, "usuario_col": None, "error": "No hay usuarios válidos del área"}

    # Agrupar por usuario
    df_por_usuario = df_with_usuario_valid.groupby(usuario_col).size().reset_index(name='CANTIDAD')

    # Combinar con facturadores para obtener información adicional
    if df_facturadores is not None and not df_facturadores.empty:
        df_por_usuario = merge_with_facturadores(df_por_usuario, df_facturadores, usuario_col)

    df_por_usuario = df_por_usuario.sort_values('CANTIDAD', ascending=False)

    return {
        "df_with_usuario": df_with_usuario_valid,
        "df_por_usuario": df_por_usuario,
        "usuario_col": usuario_col,
        "error": None
    }


def calcular_productividad_facturacion(df):
    """
    Calcula métricas de productividad de facturación.
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
