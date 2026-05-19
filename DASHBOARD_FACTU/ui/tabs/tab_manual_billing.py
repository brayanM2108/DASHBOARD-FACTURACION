"""
Manual Billing Tab
==================
UI orchestration for administrative process productivity.
"""

import os
import traceback
import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import FILES, PROCESOS_SHEET_URL
from data.loaders import load_google_sheet_csv, persist_administrative_processes
from data.processors import process_administrative_processes
from service.manual_billing_service import (
    build_chart_datasets,
    build_processes_kpis,
    filter_administrative_processes,
    get_filter_options,
)
from service.report_service import build_processes_report_cached
from utils.excel_exporter import export_processes_report_cached
from ui.components import (
    create_download_button,
    create_excel_download_button,
    show_error_message,
    show_success_message,
    show_warning_message,
)
from ui.filters import render_date_filter_with_bounds, render_single_select

ALL_OPTION = "Todos"


# ---------------------------
# Helpers
# ---------------------------
def _safe_date_str(d):
    """Return ISO string for date-like objects, empty string for None."""
    if d is None:
        return ""
    try:
        # date, datetime, pandas Timestamp all have isoformat
        return d.isoformat()
    except Exception:
        return str(d)


def _sanitize_filename(name: str) -> str:
    """Replace characters that may break filenames."""
    return (
        str(name)
        .replace(":", "-")
        .replace("/", "-")
        .replace("\\", "-")
        .replace(" ", "_")
    )


# ---------------------------
# Local actions
# ---------------------------
def _clear_processes_data():
    """Clear process data from session state and persisted parquet file."""
    st.session_state["administrative_processes_df"] = None

    process_file = FILES.get("ArchivoProcesos")
    if process_file and os.path.exists(process_file):
        os.remove(process_file)
    st.cache_data.clear()


def _sync_processes():
    """
    Sync workflow:
    - Load raw Google Sheet data from loaders
    - Process and validate from processors
    - Persist from loaders
    - Store in session state
    """
    with st.spinner("Sincronizando datos desde Google Sheets..."):
        try:
            if not PROCESOS_SHEET_URL:
                show_error_message("No hay URL configurada para Google Sheets.")
                return

            raw_df = load_google_sheet_csv(PROCESOS_SHEET_URL)
            if raw_df is None or raw_df.empty:
                show_warning_message("La hoja está vacía.")
                return

            st.success(f"Datos cargados: {len(raw_df):,} filas, {len(raw_df.columns)} columnas")
            st.write("Columnas cargadas:", list(raw_df.columns[:8]))

            processed_df = process_administrative_processes(raw_df)
            if processed_df is None or processed_df.empty:
                show_warning_message("No se pudieron procesar los datos.")
                return

            st.success(f"Datos procesados: {len(processed_df):,} registros válidos")
            st.dataframe(processed_df.head(3), width= "stretch" )

            st.session_state["administrative_processes_df"] = processed_df
            persist_administrative_processes(processed_df)
            st.cache_data.clear()

            show_success_message(f"Sincronización exitosa: {len(processed_df):,} registros.")
            st.rerun()

        except Exception as exc:
            show_error_message(f"Error al sincronizar: {exc}")
            st.error("Posibles causas:")
            st.markdown(
                """
                1. El Google Sheet no está compartido públicamente
                2. La URL de Google Sheets es inválida
                3. El archivo no tiene la estructura esperada
                """
            )
            with st.expander("Ver detalles técnicos"):
                st.code(traceback.format_exc())


# ---------------------------
# Main renderer
# ---------------------------
def render_tab_manual_billing():
    """Render administrative processes tab."""
    st.header("Productividad de Procesos Administrativos")
    st.info("Sincroniza los datos para visualizar métricas y gráficos.")

    # Sync button (no width param)
    if st.button("Sincronizar desde Google Sheets", key="btn_sync_sheets"):
        _sync_processes()
        return

    processes_df = st.session_state.get("administrative_processes_df")
    if processes_df is None or processes_df.empty:
        st.info("No hay datos de procesos cargados. Usa el botón de sincronización.")
        return

    # --- Options for selectboxes (people/processes) ---
    try:
        options = get_filter_options(processes_df)
    except Exception as exc:
        show_error_message(f"Error al obtener opciones de filtro: {exc}")
        st.write("Columnas disponibles:", list(processes_df.columns))
        return

    # --- Filters: separate start and end date inputs defaulted to data min/max (fallback to today) ---
    try:
        if "FECHA" in processes_df.columns:
            fe = pd.to_datetime(processes_df["FECHA"], errors="coerce").dropna()
            if not fe.empty:
                min_date = fe.min().date()
                max_date = fe.max().date()
            else:
                today = pd.to_datetime("today").date()
                min_date = today
                max_date = today
        else:
            today = pd.to_datetime("today").date()
            min_date = today
            max_date = today
    except Exception:
        today = pd.to_datetime("today").date()
        min_date = today
        max_date = today

    # Two separate date inputs (start / end)
    start_date, end_date = render_date_filter_with_bounds(
        min_date,
        max_date,
        key_prefix="manual_proc",
        label_start="Fecha inicio",
        label_end="Fecha fin",
    )

    # Ensure end_date is not before start_date
    if start_date is not None and end_date is not None and end_date < start_date:
        show_warning_message("La fecha fin es anterior a la fecha inicio. Ajustando fecha fin al valor de inicio.")
        end_date = start_date
        st.session_state["manual_proc_end_date"] = end_date

    # Person / process filters
    col3, col4 = st.columns(2)
    with col3:
        people = [ALL_OPTION] + options.get("people", [])
        selected_person = render_single_select("Persona", people, key="manual_proc_person")
    with col4:
        processes = [ALL_OPTION] + options.get("processes", [])
        selected_process = render_single_select("Proceso", processes, key="manual_proc_process")

    # Apply filters
    try:
        filtered_df = filter_administrative_processes(
            processes_df,
            start_date=start_date,
            end_date=end_date,
            person=selected_person if selected_person != ALL_OPTION else None,
            process=selected_process if selected_process != ALL_OPTION else None,
        )
    except Exception as exc:
        show_error_message(f"Error aplicando filtros: {exc}")
        return

    safe_start = _safe_date_str(start_date)
    safe_end = _safe_date_str(end_date)
    period_label = f"{safe_start} - {safe_end}" if (safe_start or safe_end) else "Período no especificado"

    try:
        processes_report = build_processes_report_cached(
            df_current=filtered_df,
            df_previous=None,
            selected_person=selected_person if selected_person != ALL_OPTION else None,
            selected_process=selected_process if selected_process != ALL_OPTION else None,
        )
        processes_excel = export_processes_report_cached(processes_report, period_label=period_label)
        filename_suffix = f"{selected_person}" if selected_person else ""
        filename = f"INFORME_PRODUCTIVIDAD_PROCESOSMANUALES_{filename_suffix}.xlsx"
        create_excel_download_button(
            processes_excel,
            filename=filename,
            label="Descargar informe de productividad (Excel)",
        )
    except Exception as exc:
        show_error_message(f"Error generando o exportando el informe: {exc}")


    try:
        kpis = build_processes_kpis(filtered_df)
    except Exception as exc:
        show_error_message(f"Error calculando KPIs: {exc}")
        return

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Registros", kpis.get("total_records", 0))
    with m2:
        # protect formatting if value missing
        total_qty = kpis.get("total_quantity", 0.0)
        try:
            st.metric("Total Cantidad", f"{total_qty:,.0f}")
        except Exception:
            st.metric("Total Cantidad", total_qty)
    with m3:
        st.metric("Personas", kpis.get("unique_people", 0))
    with m4:
        st.metric("Tipos de Procesos", kpis.get("unique_processes", 0))

    # Chart datasets from service
    try:
        chart_data = build_chart_datasets(
            filtered_df,
            selected_person=selected_person,
            selected_process=selected_process,
        )
    except Exception as exc:
        show_error_message(f"Error construyendo datasets para gráficos: {exc}")
        return

    # Top row: left wide column (bar chart), right narrow column (pie + download stacked)
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Cantidad por Persona")
        bar_df = chart_data.get("bar_by_person")
        if bar_df is None or bar_df.empty:
            st.info("No hay datos para el gráfico de barras.")
        else:
            try:
                fig1 = px.bar(
                    bar_df,
                    x="NOMBRE",
                    y="CANTIDAD",
                    color="CANTIDAD",
                    color_continuous_scale="Blues",
                )
                fig1.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig1, width = "stretch")
            except Exception as exc:
                show_warning_message(f"Error generando gráfico de barras: {exc}")

    with col_right:
        pie_df = chart_data.get("pie_distribution")
        try:
            if pie_df is None or pie_df.empty:
                st.info("No hay datos para el gráfico de torta.")
            else:
                if chart_data.get("pie_mode") == "person":
                    st.subheader("Distribución por Persona")
                    fig2 = px.pie(pie_df, values="CANTIDAD", names="NOMBRE", hole=0.4)
                else:
                    st.subheader("Cantidad por Proceso")
                    fig2 = px.pie(pie_df, values="CANTIDAD", names="PROCESO", hole=0.4)

                st.plotly_chart(fig2, width = "stretch")
        except Exception as exc:
            show_warning_message(f"Error generando gráfico de torta: {exc}")



    st.subheader("Tendencia Temporal")
    trend_df = chart_data.get("time_trend")
    if trend_df is None or trend_df.empty:
        st.info("No hay datos para la tendencia temporal.")
    else:
        try:
            fig3 = px.line(trend_df, x="FECHA", y="CANTIDAD", markers=True)
            st.plotly_chart(fig3, width = "stretch")
        except Exception as exc:
            show_warning_message(f"Error generando gráfico de tendencia: {exc}")

