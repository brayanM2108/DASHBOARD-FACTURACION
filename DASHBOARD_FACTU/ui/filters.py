"""
Filtros y barra lateral
========================
Componentes de filtrado para el dashboard.
"""

import streamlit as st

from utils.date_helpers import get_default_date_range
from service import obtener_lista_facturadores


def render_date_filter(key_prefix=""):
    """
    Renderiza un filtro de fechas independiente.

    Args:
        key_prefix (str): Prefijo para las keys de Streamlit

    Returns:
        tuple: (start_date, end_date)
    """
    start_date_default, end_date_default = get_default_date_range(30)

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Desde",
            value=start_date_default,
            key=f"{key_prefix}_start_date"
        )
    with col2:
        end_date = st.date_input(
            "Hasta",
            value=end_date_default,
            key=f"{key_prefix}_end_date"
        )

    return start_date, end_date


def render_user_filter(df_facturadores, key_prefix=""):
    """
    Renderiza un filtro de usuarios independiente.

    Args:
        df_facturadores (pd.DataFrame): DataFrame de facturadores
        key_prefix (str): Prefijo para las keys de Streamlit

    Returns:
        list: Lista de usuarios seleccionados
    """
    lista_facturadores = obtener_lista_facturadores(df_facturadores)

    if not lista_facturadores:
        st.info("No hay facturadores disponibles.")
        return ['Todos']

    usuarios_seleccionados = st.multiselect(
        "Seleccionar Facturador",
        options=['Todos'] + lista_facturadores,
        default=['Todos'],
        key=f"{key_prefix}_usuarios"
    )

    return usuarios_seleccionados

