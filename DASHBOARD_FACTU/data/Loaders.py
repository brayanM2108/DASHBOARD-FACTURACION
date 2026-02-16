"""
Carga y guardado de datos
==========================
Funciones para cargar archivos desde diferentes fuentes y
guardar datos procesados en formato Parquet.
"""

import pandas as pd
from config.settings import FILES, FACTURADORES_FILE, FACTURADORES_SHEET
from utils.file_helpers import save_to_parquet, load_from_parquet, read_file_robust


def load_all_persisted_data():
    """
    Carga todos los archivos Parquet persistidos.

    Returns:
        dict: Diccionario con DataFrames cargados
    """
    return {
        "ppl": load_from_parquet(FILES["PPL"]),
        "convenios": load_from_parquet(FILES["Convenios"]),
        "rips": load_from_parquet(FILES["RIPS"]),
        "facturacion": load_from_parquet(FILES["Facturacion"]),
        "facturadores": load_from_parquet(FILES["Facturadores"]),
        "facturacion_electronica": load_from_parquet(FILES["FacturacionElectronica"])
    }


def save_all_data(data_dict):
    """
    Guarda todos los DataFrames en formato Parquet.

    Args:
        data_dict (dict): Diccionario con DataFrames a guardar
            Claves esperadas: 'ppl', 'convenios', 'rips', 'facturacion',
            'facturadores', 'facturacion_electronica'

    Returns:
        dict: Diccionario con resultado de cada operación (True/False)
    """
    results = {}

    if "ppl" in data_dict:
        results["ppl"] = save_to_parquet(data_dict["ppl"], FILES["PPL"])

    if "convenios" in data_dict:
        results["convenios"] = save_to_parquet(data_dict["convenios"], FILES["Convenios"])

    if "rips" in data_dict:
        results["rips"] = save_to_parquet(data_dict["rips"], FILES["RIPS"])

    if "facturacion" in data_dict:
        results["facturacion"] = save_to_parquet(data_dict["facturacion"], FILES["Facturacion"])

    if "facturadores" in data_dict:
        results["facturadores"] = save_to_parquet(data_dict["facturadores"], FILES["Facturadores"])

    if "facturacion_electronica" in data_dict:
        results["facturacion_electronica"] = save_to_parquet(
            data_dict["facturacion_electronica"],
            FILES["FacturacionElectronica"]
        )

    return results


def load_facturadores_master():
    """
    Carga el archivo maestro de facturadores.

    Returns:
        pd.DataFrame or None: DataFrame con facturadores o None si falla
    """
    try:
        df = pd.read_excel(FACTURADORES_FILE, sheet_name=FACTURADORES_SHEET)
        df.columns = df.columns.str.strip().str.upper()
        return df
    except Exception as e:
        print(f"Error al cargar archivo de facturadores: {e}")
        return None


def load_uploaded_file(file, column_marker):
    """
    Carga un archivo subido por el usuario.

    Args:
        file: Objeto de archivo de Streamlit
        column_marker (str): Marcador para detectar encabezados

    Returns:
        pd.DataFrame or None: DataFrame procesado o None si falla
    """
    df, header_row = read_file_robust(file, column_marker)
    return df
