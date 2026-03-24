"""
Billing tab
===========
UI to visualize and analyze billing productivity.
"""

import streamlit as st
import pandas as pd

from config.settings import COLUMN_NAMES
from data.validators import find_first_column_variant
from service.billing_service import (
    calculate_billing_productivity,
    filter_billing,
    get_billing_with_user,
)
from ui.components import create_download_button, show_dataframe, show_info_message
from ui.visualizations import plot_bar_chart, plot_productivity_charts


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

def render_tab_billing():
    """Render the billing tab."""
    st.header("Facturación")
    render_billing_section()


def render_billing_section():
    """Render billing section with independent filters."""

    billing_df = st.session_state.get("billing_df")
    billers_df = st.session_state.get("billers_df")
    e_billing_df = st.session_state.get("electronic_billing_df")

    if billing_df is None or billing_df.empty:
        show_info_message("No hay datos de facturación. Carga un archivo en la sección de carga.")
        return

    date_col = find_first_column_variant(billing_df, COLUMN_NAMES["fecha"])

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start date",
            value=_safe_min_date(billing_df, date_col),
            key="billing_start_date",
        )
    with col2:
        end_date = st.date_input(
            "End date",
            value=_safe_max_date(billing_df, date_col),
            key="billing_end_date",
        )

    usuarios_lista = ['Todos']
    if e_billing_df is not None and not e_billing_df.empty:
        e_user_col = find_first_column_variant(e_billing_df, COLUMN_NAMES["usuario"])
        if e_user_col and e_user_col in e_billing_df.columns:
            usuarios_unicos = e_billing_df[e_user_col].dropna().unique().tolist()
            usuarios_lista = ['Todos'] + sorted(usuarios_unicos)

    usuario_sel = st.selectbox("Usuario", usuarios_lista, key="facturacion_usuario")
    usuarios_seleccionados = None if usuario_sel == 'Todos' else [usuario_sel]

    filtered_billing_df = filter_billing(
        billing_df,
        start_date,
        end_date,
        selected_users=None,
    )

    if filtered_billing_df is None or filtered_billing_df.empty:
        show_info_message("No hay datos que coincidan con los filtros seleccionados.")
        return

    st.subheader("📈 Facturación por Usuario")

    result = get_billing_with_user(filtered_billing_df, e_billing_df, billers_df)

    if result["error"]:
        st.warning(result["error"])
    else:
        billing_by_user_df = result["billing_by_user_df"]
        usuario_col = result["user_column"]

        if usuarios_seleccionados:
            billing_by_user_df = billing_by_user_df[
                billing_by_user_df[usuario_col].isin(usuarios_seleccionados)
            ]

        if not billing_by_user_df.empty:
            nombre_col = 'NOMBRE' if 'NOMBRE' in billing_by_user_df.columns else usuario_col

            plot_bar_chart(
                billing_by_user_df,
                x_col=nombre_col,
                y_col='COUNT',
                title="Facturación por Usuario"
            )
            st.dataframe(billing_by_user_df, use_container_width = "stretch")

    metrics = calculate_billing_productivity(filtered_billing_df)
    plot_productivity_charts(metrics, tipo="Facturacion")


    with st.expander("📊 Ver datos detallados", expanded=False):
        show_dataframe(filtered_billing_df, title="Datos de Facturación")
        create_download_button(filtered_billing_df, "facturacion.csv")
