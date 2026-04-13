"""
Filters and sidebar helpers
===========================
Reusable filtering components for the dashboard UI.
"""

import streamlit as st

from utils.date_helpers import get_default_date_range
from service.billers_service import get_billers_list


def render_date_filter(key_prefix=""):
    """
    Render an independent date range filter.
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
    Render an independent biller/user filter.
    """
    billers_list = get_billers_list(df_facturadores)

    if not billers_list:
        st.info("No hay facturadores disponibles.")
        return ['Todos']

    selected_users = st.multiselect(
        "Seleccionar Facturador",
        options=['Todos'] + billers_list,
        default=['Todos'],
        key=f"{key_prefix}_usuarios"
    )

    return selected_users

