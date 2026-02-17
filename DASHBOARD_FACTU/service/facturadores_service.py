"""
Lógica de negocio - Facturadores
=================================
Funciones específicas para gestionar información de facturadores.
"""

import pandas as pd
from data.loaders import load_facturadores_master


def obtener_lista_facturadores(df_facturadores=None):
    """
    Obtiene la lista de facturadores disponibles.

    Args:
        df_facturadores (pd.DataFrame): DataFrame de facturadores (opcional)

    Returns:
        list: Lista de nombres de facturadores
    """
    if df_facturadores is None:
        df_facturadores = load_facturadores_master()

    if df_facturadores is None or df_facturadores.empty:
        return []

    if "USUARIO" in df_facturadores.columns:
        return sorted(df_facturadores["USUARIO"].dropna().unique().tolist())

    return []


def obtener_info_facturador(usuario, df_facturadores=None):
    """
    Obtiene información detallada de un facturador.

    Args:
        usuario (str): Nombre del usuario
        df_facturadores (pd.DataFrame): DataFrame de facturadores (opcional)

    Returns:
        dict or None: Información del facturador o None si no existe
    """
    if df_facturadores is None:
        df_facturadores = load_facturadores_master()

    if df_facturadores is None or df_facturadores.empty:
        return None

    if "USUARIO" not in df_facturadores.columns:
        return None

    facturador = df_facturadores[df_facturadores["USUARIO"] == usuario]

    if facturador.empty:
        return None

    return facturador.iloc[0].to_dict()
