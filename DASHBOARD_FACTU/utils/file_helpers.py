"""
Utilidades para manejo de archivos
===================================
Funciones auxiliares para leer, escribir y manipular archivos.
"""

import pandas as pd
import os


def save_to_parquet(df, filepath):
    """
    Guarda un DataFrame en formato Parquet.

    Args:
        df (pd.DataFrame): DataFrame a guardar
        filepath (str): Ruta del archivo

    Returns:
        bool: True si se guardó exitosamente, False en caso contrario
    """
    if df is None or df.empty:
        return False

    try:
        df.astype(str).to_parquet(filepath, index=False)
        return True
    except Exception as e:
        print(f"Error al guardar {filepath}: {e}")
        return False


def load_from_parquet(filepath):
    """
    Carga un DataFrame desde un archivo Parquet.

    Args:
        filepath (str): Ruta del archivo

    Returns:
        pd.DataFrame or None: DataFrame cargado o None si no existe
    """
    if not os.path.exists(filepath):
        return None

    try:
        return pd.read_parquet(filepath)
    except Exception as e:
        print(f"Error al cargar {filepath}: {e}")
        return None


def detect_header_row(df_raw, column_marker):
    """
    Detecta la fila de encabezados en un DataFrame.

    Busca una fila que contenga el marcador especificado para
    identificar dónde comienzan los encabezados reales.

    Args:
        df_raw (pd.DataFrame): DataFrame sin procesar
        column_marker (str): Texto marcador de la columna (ej: "ID_LEGALIZACION")

    Returns:
        int or None: Índice de la fila de encabezados o None si no se encuentra
    """
    for i, row in df_raw.iterrows():
        row_str = row.astype(str).str.strip().str.upper()
        if row_str.str.startswith(column_marker.upper()).any():
            return i
    return None


def normalize_column_names(df):
    """
    Normaliza los nombres de las columnas de un DataFrame.

    Elimina espacios, saltos de línea y convierte a mayúsculas.

    Args:
        df (pd.DataFrame): DataFrame a normalizar

    Returns:
        pd.DataFrame: DataFrame con columnas normalizadas
    """
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.replace('\n', ' ')
        .str.upper()
    )
    return df


def read_file_robust(file, column_marker):
    """
    Lee un archivo de forma robusta detectando automáticamente los encabezados.

    Args:
        file: Objeto de archivo de Streamlit
        column_marker (str): Marcador para detectar encabezados

    Returns:
        tuple: (df, header_row) o (None, None) si falla
    """
    try:
        # Leer archivo sin asumir encabezados
        if file.name.endswith('.csv'):
            df_raw = pd.read_csv(file, header=None)
        else:
            df_raw = pd.read_excel(file, header=None)

        # Detectar fila de encabezados
        header_row = detect_header_row(df_raw, column_marker)

        if header_row is None:
            return None, None

        # Releer con encabezados correctos
        file.seek(0)  # Reiniciar cursor del archivo
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, header=header_row)
        else:
            df = pd.read_excel(file, header=header_row)

        # Normalizar columnas
        df = normalize_column_names(df)

        return df, header_row

    except Exception as e:
        print(f"Error al leer archivo: {e}")
        return None, None
