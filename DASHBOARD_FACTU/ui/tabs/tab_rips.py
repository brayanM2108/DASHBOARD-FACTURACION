"""
RIPS Tab
================
Interface for viewing and analyzing RIPS productivity.
"""

import pandas as pd
import streamlit as st

from config.settings import COLUMN_NAMES
from data.validators import find_first_column_variant
from service.rips_service import calculate_rips_productivity, filter_rips
from ui.components import create_download_button, show_dataframe, show_info_message
from ui.visualizations import plot_productivity_charts

def _safe_min_date(df: pd.DataFrame, date_col: str | None) -> pd.Timestamp:
    if date_col and date_col in df.columns:
        min_value = pd.to_datetime(df[date_col], errors="coerce").min()
        if pd.notna(min_value):
            return min_value
    return pd.Timestamp.now()

ALL_OPTION = "All"

def _safe_max_date(df: pd.DataFrame, date_col: str | None) -> pd.Timestamp:
    if date_col and date_col in df.columns:
        max_value = pd.to_datetime(df[date_col], errors="coerce").max()
        if pd.notna(max_value):
            return max_value
    return pd.Timestamp.now()


def _build_user_options(df: pd.DataFrame) -> tuple[list[str], str | None]:
    user_col = find_first_column_variant(df, COLUMN_NAMES["usuario"])
    if user_col is None or user_col not in df.columns:
        return [ALL_OPTION], None

    users = sorted(df[user_col].dropna().astype(str).unique().tolist())
    return [ALL_OPTION] + users, user_col


def render_tab_rips():
    """Render RIPS tab with independent filters."""
    st.header("📄 RIPS")

    df_rips = st.session_state.get('rips_df')

    if df_rips is None or df_rips.empty:
        show_info_message("No hay datos de RIPS. Carga un archivo en la sección de carga.")
        return
    date_col = find_first_column_variant(df_rips, COLUMN_NAMES["fecha"])

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start date",
            value=_safe_min_date(df_rips, date_col),
            key="rips_start_date",
        )
    with col2:
        end_date = st.date_input(
            "End date",
            value=_safe_max_date(df_rips, date_col),
            key="rips_end_date",
        )

    user_options, _ = _build_user_options(df_rips)
    selected_user = st.selectbox("User", user_options, key="rips_user")
    selected_users = None if selected_user == ALL_OPTION else [selected_user]

    filtered_df = filter_rips(
        df_rips,
        start_date,
        end_date,
        selected_users,
    )

    if filtered_df is None or filtered_df.empty:
        show_info_message("No hay datos que coincidan con los filtros seleccionados.")
        return

    metrics = calculate_rips_productivity(filtered_df)
    plot_productivity_charts(metrics, tipo="RIPS")

    with st.expander("📊 Ver datos detallados", expanded=False):
        show_dataframe(filtered_df, title="Datos de RIPS")
        create_download_button(filtered_df, "rips.csv")
