"""
Lógica de negocio - Facturadores
=================================
Funciones específicas para gestionar información de facturadores.
"""

import pandas as pd
import streamlit as st
from data.loaders import load_facturadores_master


def obtener_lista_facturadores(df_facturadores=None):
    """
    Obtiene la lista de facturadores disponibles de todos los datasets cargados.

    Args:
        df_facturadores (pd.DataFrame): DataFrame de facturadores (opcional, no se usa)

    Returns:
        list: Lista de nombres de facturadores únicos de todos los datasets
    """
    # Recolecta todos los usuarios únicos de todos los datasets cargados
    facturadores_total = []

    for df_name in ['df_ppl', 'df_convenios', 'df_rips', 'df_facturacion']:
        df_temp = st.session_state.get(df_name)
        if df_temp is not None and not df_temp.empty:
            col_u = 'USUARIO' if 'USUARIO' in df_temp.columns else 'Usuario'
            if col_u in df_temp.columns:
                facturadores_total.extend(df_temp[col_u].dropna().unique())

    if not facturadores_total:
        return []

    return sorted(list(set(facturadores_total)))



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

    # Buscar en columna NOMBRE o USUARIO
    columna_busqueda = None
    if "NOMBRE" in df_facturadores.columns:
        columna_busqueda = "NOMBRE"
    elif "USUARIO" in df_facturadores.columns:
        columna_busqueda = "USUARIO"

    if columna_busqueda is None:
        return None

    facturador = df_facturadores[df_facturadores[columna_busqueda] == usuario]

    if facturador.empty:
        return None

    return facturador.iloc[0].to_dict()
