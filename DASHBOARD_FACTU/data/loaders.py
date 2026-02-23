"""
Carga y guardado de datos
==========================
Funciones para cargar archivos desde diferentes fuentes y
guardar datos procesados en formato Parquet.
"""

import pandas as pd
import streamlit as st
import io
import os
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
        "facturacion_electronica": load_from_parquet(FILES["FacturacionElectronica"]),
        "procesos": load_from_parquet(FILES["ArchivoProcesos"])
    }


def save_all_data(data_dict):
    """
    Guarda todos los DataFrames en formato Parquet.

    Args:
        data_dict (dict): Diccionario con DataFrames a guardar
            Claves esperadas: 'ppl', 'convenios', 'rips', 'facturacion',
            'facturadores', 'facturacion_electronica', 'procesos'

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

    if "procesos" in data_dict:
        results["procesos"] = save_to_parquet(data_dict["procesos"], FILES["ArchivoProcesos"])

    return results


def load_facturadores_master():
    """
    Carga el archivo maestro de facturadores.
    Intenta primero desde Streamlit Secrets (producción),
    luego desde archivo local (desarrollo).

    Returns:
        pd.DataFrame or None: DataFrame con facturadores o None si falla
    """
    # Intentar cargar desde Streamlit Secrets (producción)
    df = _load_facturadores_from_secrets()
    if df is not None:
        return df

    # Intentar cargar desde archivo local (desarrollo)
    df = _load_facturadores_from_file()
    return df


def _load_facturadores_from_secrets():
    """
    Carga facturadores desde Streamlit Secrets (para producción/deploy).

    Returns:
        pd.DataFrame or None
    """
    try:
        if "facturadores" in st.secrets and "data" in st.secrets["facturadores"]:
            csv_data = st.secrets["facturadores"]["data"]
            df = pd.read_csv(io.StringIO(csv_data))
            df.columns = df.columns.str.strip().str.upper()
            return df
    except Exception as e:
        print(f"No se pudo cargar facturadores desde secrets: {e}")

    return None


def _load_facturadores_from_file():
    """
    Carga facturadores desde archivo Excel local (para desarrollo).

    Returns:
        pd.DataFrame or None
    """
    try:
        df = pd.read_excel(FACTURADORES_FILE, sheet_name=FACTURADORES_SHEET)
        df.columns = df.columns.str.strip().str.upper()
        return df
    except Exception as e:
        print(f"No se pudo cargar facturadores desde archivo: {e}")

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


def load_procesos(file_or_url):
    """
     Carga datos de procesos administrativos desde Excel o Google Sheets

     Args:
         file_or_url: Archivo subido o URL de Google Sheets

     Returns:
         pd.DataFrame: DataFrame con los datos de procesos
     """
    try:
        # Si es una URL de Google Sheets
        if isinstance(file_or_url, str) and 'docs.google.com/spreadsheets' in file_or_url:
            # Convertir URL de Google Sheets a formato exportable
            if '/edit' in file_or_url:
                sheet_id = file_or_url.split('/d/')[1].split('/')[0]
                url_export = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx'
            else:
                url_export = file_or_url

            df = pd.read_excel(url_export)
        else:
            # Es un archivo subido
            df = pd.read_excel(file_or_url)

        # Normalizar nombres de columnas
        df.columns = df.columns.str.strip().str.upper()

        # Validar columnas requeridas
        columnas_requeridas = ['FECHA', 'NOMBRE', 'DOCUMENTO', 'PROCESO', 'CANTIDAD']
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]

        if columnas_faltantes:
            raise ValueError(f"Faltan las siguientes columnas: {', '.join(columnas_faltantes)}")

        # Convertir fecha al formato correcto
        df['FECHA'] = pd.to_datetime(df['FECHA'], format='%d/%m/%Y', errors='coerce')

        # Convertir cantidad a numérico
        df['CANTIDAD'] = pd.to_numeric(df['CANTIDAD'], errors='coerce')

        # Eliminar filas con valores nulos en columnas críticas
        df = df.dropna(subset=['FECHA', 'NOMBRE', 'CANTIDAD'])

        return df

    except Exception as e:
        raise ValueError(f"Error al cargar archivo de procesos: {str(e)}")

