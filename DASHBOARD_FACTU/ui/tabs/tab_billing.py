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
from ui.visualizations import plot_bar_chart, plot_productivity_charts

from service.report_service import build_billing_report
from utils.excel_exporter import export_billing_report
from ui.components import (
    create_excel_download_button,
    show_info_message, create_download_button, show_dataframe,
)

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
            "Fecha Inicio",
            value=_safe_min_date(billing_df, date_col),
            key="billing_start_date",
        )
    with col2:
        end_date = st.date_input(
            "Fecha Fin",
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
        selected_users=usuarios_seleccionados,
    )

    if filtered_billing_df is None or filtered_billing_df.empty:
        show_info_message("No hay datos que coincidan con los filtros seleccionados.")
        return

    # Build user mapping first so Excel report can reuse the same by-user dataset.
    result = get_billing_with_user(filtered_billing_df, e_billing_df, billers_df)

    # Base dataframe for time metrics/charts. Defaults to date-filtered billing.
    productivity_base_df: pd.DataFrame = filtered_billing_df

    report_by_user_df = None
    if not result["error"]:
        mapped_df = result.get("billing_with_user_df")
        if isinstance(mapped_df, pd.DataFrame):
            productivity_base_df = mapped_df
        report_by_user_df = result.get("billing_by_user_df")
        usuario_col_tmp = result.get("user_column")
        if usuarios_seleccionados:
            if usuario_col_tmp and usuario_col_tmp in productivity_base_df.columns:
                productivity_base_df = productivity_base_df[
                    productivity_base_df[usuario_col_tmp].isin(usuarios_seleccionados)
                ]
            if (
                report_by_user_df is not None
                and usuario_col_tmp
                and usuario_col_tmp in report_by_user_df.columns
            ):
                report_by_user_df = report_by_user_df[
                    report_by_user_df[usuario_col_tmp].isin(usuarios_seleccionados)
                ]

    period_label = f"{start_date} - {end_date}"
    billing_report = build_billing_report(
        df_current=productivity_base_df,
        df_previous=None,
        by_user_df=report_by_user_df,
    )
    billing_excel = export_billing_report(billing_report, period_label=period_label)

    create_excel_download_button(
        billing_excel,
        filename=f"billing_productivity_{start_date}_{end_date}.xlsx",
        label="📥 Descargar informe de productividad (Excel)",
    )

    st.subheader("📈 Facturación por Usuario")

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

        df_plot = billing_by_user_df.copy()

        if 'NOMBRE' in df_plot.columns:
            df_plot['LABEL_USUARIO'] = df_plot['NOMBRE'].fillna(df_plot[usuario_col]).astype(str)
            df_plot['LABEL_USUARIO'] = df_plot['LABEL_USUARIO'].replace(['nan', 'None', ''], df_plot[usuario_col].astype(str))
        else:
            df_plot['LABEL_USUARIO'] = df_plot[usuario_col].astype(str)

            plot_bar_chart(
                df_plot,
                x_col='LABEL_USUARIO',
                y_col='COUNT',
                title="Facturación por Usuario"
            )
            st.dataframe(billing_by_user_df, width = "stretch")

    metrics = calculate_billing_productivity(productivity_base_df)
    metrics_for_summary = dict(metrics)
    metrics_for_summary["by_user"] = None
    plot_productivity_charts(metrics_for_summary, tipo="Facturacion")


    with st.expander("📊 Ver datos detallados", expanded=False):
        show_dataframe(filtered_billing_df, title="Datos de facturacion")
        create_download_button(filtered_billing_df, "facturacion.csv")
