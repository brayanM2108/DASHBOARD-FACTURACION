"""
Validación de datos
===================
Funciones para verificar la integridad y validez de los datos.
"""

import pandas as pd
from config.settings import COLUMN_NAMES


def validate_required_columns(df, required_columns):
    """
    Valida que un DataFrame tenga las columnas requeridas.

    Args:
        df (pd.DataFrame): DataFrame a validar
        required_columns (list): Lista de columnas requeridas

    Returns:
        tuple: (is_valid, missing_columns)
    """
    if df is None or df.empty:
        return False, required_columns

    missing = [col for col in required_columns if col not in df.columns]
    return len(missing) == 0, missing


def find_column_variant(df, column_variants):
    """
    Busca una columna entre múltiples variantes de nombres.

    Args:
        df (pd.DataFrame): DataFrame donde buscar
        column_variants (list): Lista de posibles nombres de columna

    Returns:
        str or None: Nombre de la columna encontrada o None
    """
    if df is None or df.empty:
        return None

    for variant in column_variants:
        if variant in df.columns:
            return variant

    return None


def validate_legalizaciones(df):
    """
    Valida que un DataFrame de legalizaciones tenga la estructura correcta.

    Returns:
        tuple: (is_valid, message)
    """
    required = ["ESTADO", "CONVENIO"]
    usuario_col = find_column_variant(df, COLUMN_NAMES["usuario"])
    fecha_col = find_column_variant(df, COLUMN_NAMES["fecha"])

    if usuario_col is None or fecha_col is None:
        return False, "Faltan columnas de USUARIO o FECHA"

    is_valid, missing = validate_required_columns(df, required)
    if not is_valid:
        return False, f"Faltan columnas: {', '.join(missing)}"

    return True, "Validación exitosa"


def validate_rips(df):
    """
    Valida que un DataFrame de RIPS tenga la estructura correcta.

    Returns:
        tuple: (is_valid, message)
    """
    required = ["ESTADO"]
    usuario_col = find_column_variant(df, COLUMN_NAMES["usuario"])
    fecha_col = find_column_variant(df, COLUMN_NAMES["fecha"])

    if usuario_col is None or fecha_col is None:
        return False, "Faltan columnas de USUARIO o FECHA"

    is_valid, missing = validate_required_columns(df, required)
    if not is_valid:
        return False, f"Faltan columnas: {', '.join(missing)}"

    return True, "Validación exitosa"


def validate_facturacion(df):
    """
    Valida que un DataFrame de facturación tenga la estructura correcta.

    Returns:
        tuple: (is_valid, message)
    """
    # Buscar columna NRO_LEGALIACION o similar
    if "NRO_LEGALIACION" not in df.columns and "NRO_LEGALIZACION" not in df.columns:
        return False, "Falta columna NRO_LEGALIACION o NRO_LEGALIZACION"

    return True, "Validación exitosa"


def validate_facturacion_electronica(df):
    """
    Valida que un DataFrame de facturación electrónica tenga la estructura correcta.

    Returns:
        tuple: (is_valid, message)
    """
    required = ["ESTADO"]
    usuario_col = find_column_variant(df, COLUMN_NAMES["usuario"])
    fecha_col = find_column_variant(df, COLUMN_NAMES["fecha"])

    if usuario_col is None or fecha_col is None:
        return False, "Faltan columnas de USUARIO o FECHA"

    is_valid, missing = validate_required_columns(df, required)
    if not is_valid:
        return False, f"Faltan columnas: {', '.join(missing)}"

    return True, "Validación exitosa"
