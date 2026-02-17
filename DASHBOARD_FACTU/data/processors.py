"""
Procesamiento de datos
=======================
Funciones para transformar y limpiar datos cargados.
"""

import pandas as pd
from config.settings import (
    ESTADOS_VALIDOS_LEGALIZACIONES,
    ESTADOS_VALIDOS_RIPS,
    ESTADOS_VALIDOS_FACTURACION_ELECTRONICA,
    CONVENIO_PPL
)
from utils.date_helpers import parse_date_column


def process_legalizaciones(df, estado_column="ESTADO", fecha_column="FECHA_REAL", convenio_column="CONVENIO"):
    """
    Procesa el DataFrame de legalizaciones.

    Args:
        df (pd.DataFrame): DataFrame de legalizaciones
        estado_column (str): Nombre de columna de estado
        fecha_column (str): Nombre de columna de fecha
        convenio_column (str): Nombre de columna de convenio

    Returns:
        tuple: (df_ppl, df_convenios) - DataFrames separados
    """
    if df is None or df.empty:
        return None, None

    # Convertir fecha
    df = parse_date_column(df, fecha_column)

    # Normalizar y filtrar por estado válido
    if estado_column in df.columns:
        # Normalizar valores de estado a mayúsculas
        df[estado_column] = df[estado_column].astype(str).str.strip().str.upper()
        df = df[df[estado_column].isin(ESTADOS_VALIDOS_LEGALIZACIONES)]

    # Separar PPL y Convenios
    df_ppl = None
    df_convenios = None

    if convenio_column in df.columns:
        df_ppl = df[df[convenio_column] == CONVENIO_PPL].copy()
        df_convenios = df[df[convenio_column] != CONVENIO_PPL].copy()

    return df_ppl, df_convenios


def process_rips(df, estado_column="ESTADO", fecha_column="FECHA_REAL"):
    """
    Procesa el DataFrame de RIPS.

    Args:
        df (pd.DataFrame): DataFrame de RIPS
        estado_column (str): Nombre de columna de estado
        fecha_column (str): Nombre de columna de fecha

    Returns:
        pd.DataFrame: DataFrame procesado
    """
    if df is None or df.empty:
        return None

    # Convertir fecha
    df = parse_date_column(df, fecha_column)

    # Normalizar y filtrar por estado válido
    if estado_column in df.columns:
        df[estado_column] = df[estado_column].astype(str).str.strip().str.upper()
        df = df[df[estado_column].isin(ESTADOS_VALIDOS_RIPS)]

    return df


def process_facturacion(df, fecha_column="FECHA_FACTURA"):
    """
    Procesa el DataFrame de facturación.

    Args:
        df (pd.DataFrame): DataFrame de facturación
        fecha_column (str): Nombre de columna de fecha

    Returns:
        pd.DataFrame: DataFrame procesado
    """
    if df is None or df.empty:
        return None

    # Convertir fecha
    df = parse_date_column(df, fecha_column)

    return df


def process_facturacion_electronica(df, estado_column="ESTADO", fecha_column="FECHA RADICACIÓN"):
    """
    Procesa el DataFrame de facturación electrónica.

    Args:
        df (pd.DataFrame): DataFrame de facturación electrónica
        estado_column (str): Nombre de columna de estado
        fecha_column (str): Nombre de columna de fecha

    Returns:
        pd.DataFrame: DataFrame procesado
    """
    if df is None or df.empty:
        return None

    # Convertir fecha
    df = parse_date_column(df, fecha_column)

    # Normalizar y filtrar por estado válido
    if estado_column in df.columns:
        df[estado_column] = df[estado_column].astype(str).str.strip().str.upper()
        df = df[df[estado_column].isin(ESTADOS_VALIDOS_FACTURACION_ELECTRONICA)]

    return df


def merge_with_facturadores(df, df_facturadores, usuario_column="USUARIO"):
    """
    Combina un DataFrame con información de facturadores.

    Args:
        df (pd.DataFrame): DataFrame principal
        df_facturadores (pd.DataFrame): DataFrame de facturadores
        usuario_column (str): Nombre de columna de usuario

    Returns:
        pd.DataFrame: DataFrame combinado con información de facturadores
    """
    if df is None or df.empty or df_facturadores is None or df_facturadores.empty:
        return df

    if usuario_column not in df.columns or "USUARIO" not in df_facturadores.columns:
        return df

    # Realizar merge
    df_merged = pd.merge(
        df,
        df_facturadores,
        left_on=usuario_column,
        right_on="USUARIO",
        how="left"
    )

    return df_merged


def aggregate_by_user(df, usuario_column="USUARIO", date_column=None, group_by_date=False):
    """
    Agrupa datos por usuario y opcionalmente por fecha.

    Args:
        df (pd.DataFrame): DataFrame a agregar
        usuario_column (str): Nombre de columna de usuario
        date_column (str): Nombre de columna de fecha (opcional)
        group_by_date (bool): Si True, agrupa también por fecha

    Returns:
        pd.DataFrame: DataFrame agregado
    """
    if df is None or df.empty or usuario_column not in df.columns:
        return None

    if group_by_date and date_column and date_column in df.columns:
        # Agregar columna de fecha (solo día)
        df['FECHA'] = df[date_column].dt.date
        agg_df = df.groupby([usuario_column, 'FECHA']).size().reset_index(name='CANTIDAD')
    else:
        agg_df = df.groupby(usuario_column).size().reset_index(name='CANTIDAD')

    return agg_df
