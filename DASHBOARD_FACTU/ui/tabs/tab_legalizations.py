"""
Legalizations tab
=================
UI to visualize and analyze PPL and agreements legalizations.
"""

import pandas as pd
import streamlit as st

from config.settings import COLUMN_NAMES
from data.validators import find_first_column_variant
from service.legalizations_service import (
    calculate_legalizations_productivity,
    filter_legalizations,
)
from ui.components import create_download_button, show_dataframe, show_info_message
from ui.visualizations import plot_productivity_charts

ALL_OPTION = "All"


def _safe_min_date(df: pd.DataFrame, date_col: str | None) -> pd.Timestamp:
    if date_col and date_col in df.columns:
        min_value = pd.to_datetime(df[date_col], errors="coerce").min()
        if pd.notna(min_value):
            return min_value
    return pd.Timestamp.now()


def _safe_max_date(df: pd.DataFrame, date_col: str | None) -> pd.Timestamp:
    if date_col and date_col in df.columns:
        max_value = pd.to_datetime(df[date_col], errors="coerce").max()
        if pd.notna(max_value):
            return max_value
    return pd.Timestamp.now()


def _build_user_options(df: pd.DataFrame) -> list[str]:
    user_col = find_first_column_variant(df, COLUMN_NAMES["usuario"])
    if user_col is None or user_col not in df.columns:
        return [ALL_OPTION]

    unique_users = df[user_col].dropna().astype(str).tolist()
    return [ALL_OPTION] + sorted(set(unique_users))


def render_tab_legalizations():
    """Render legalizations tab with PPL and agreements sub-tabs."""

    st.header("📋 Legalizaciones")

    # Crear sub-pestañas para PPL y Convenios
    tab_ppl, tab_convenios = st.tabs(["🏥 PPL", "🤝 Convenios"])

    with tab_ppl:
        render_ppl_section()

    with tab_convenios:
        render_agreements_section()

def render_ppl_section():
    """Render the PPL section with independent filters."""
    st.subheader("Legalizaciones PPL")

    ppl_df =  st.session_state.get("ppl_legalizations_df")

    if ppl_df is None or ppl_df.empty:
        show_info_message("No hay datos de legalizaciones PPL. Carga un archivo en la sección de carga.")
        return

    date_col = find_first_column_variant(ppl_df, COLUMN_NAMES["fecha"])



    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start date",
            value=_safe_min_date(ppl_df, date_col),
            key="ppl_start_date",
        )
    with col2:
        end_date = st.date_input(
            "End date",
            value=_safe_max_date(ppl_df, date_col),
            key="ppl_end_date",
        )

    users = _build_user_options(ppl_df)
    selected_user = st.selectbox("USUARIO", users, key="ppl_user")
    selected_users = None if selected_user == ALL_OPTION else [selected_user]

    filtered_df = filter_legalizations(
        ppl_df,
        start_date,
        end_date,
        selected_users,
    )

    if filtered_df is None or filtered_df.empty:
        show_info_message("No hay datos que coincidan con los filtros seleccionados.")
        return

    metrics = calculate_legalizations_productivity(filtered_df)
    plot_productivity_charts(metrics, tipo="Legalizaciones PPL")

    with st.expander("📊 Ver datos detallados", expanded=False):
        show_dataframe(filtered_df, title="Datos de Legalizaciones PPL")
        create_download_button(filtered_df, "legalizaciones_ppl.csv")


def render_agreements_section():
    """Render agreements section with independent filters."""
    st.subheader("Legalizaciones Convenios")

    agreements_df = st.session_state.get("agreement_legalizations_df")

    if agreements_df is None or agreements_df.empty:
        show_info_message("No hay datos de legalizaciones de Convenios. Carga un archivo en la sección de carga.")
        return

    date_col = find_first_column_variant(agreements_df, COLUMN_NAMES["fecha"])

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start date",
            value=_safe_min_date(agreements_df, date_col),
            key="agreements_start_date",
        )
    with col2:
        end_date = st.date_input(
            "End date",
            value=_safe_max_date(agreements_df, date_col),
            key="agreements_end_date",
        )

    users = _build_user_options(agreements_df)
    selected_user = st.selectbox("User", users, key="agreements_user")
    selected_users = None if selected_user == ALL_OPTION else [selected_user]

    filtered_df = filter_legalizations(
        agreements_df,
        start_date,
        end_date,
        selected_users,
    )

    if filtered_df is None or filtered_df.empty:
        show_info_message("No hay datos que coincidan con los filtros seleccionados.")
        return

    metrics = calculate_legalizations_productivity(filtered_df)

    plot_productivity_charts(metrics, tipo="Legalizaciones Convenios")

    # Mostrar tabla de datos
    with st.expander("📊 Ver datos detallados", expanded=False):
        show_dataframe(filtered_df, title="Datos de Legalizaciones Convenios")
        create_download_button(filtered_df, "legalizaciones_convenios.csv")
