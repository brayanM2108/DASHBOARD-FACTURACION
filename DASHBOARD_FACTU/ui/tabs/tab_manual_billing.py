"""
Manual Billing Tab
==================
UI orchestration for administrative process productivity.
"""

import os
import traceback

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
from ui.components import show_error_message, show_success_message, show_warning_message


ALL_OPTION = "Todos"


def _clear_processes_data():
    """Clear process data from session state and persisted parquet file."""
    st.session_state["administrative_processes_df"] = None

    process_file = FILES.get("ArchivoProcesos")
    if process_file and os.path.exists(process_file):
        os.remove(process_file)


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
                show_warning_message("La hoja esta vacia.")
                return

            st.success(f"Datos cargados: {len(raw_df):,} filas, {len(raw_df.columns)} columnas")
            st.write("Columnas cargadas:", list(raw_df.columns[:8]))

            processed_df = process_administrative_processes(raw_df)
            if processed_df is None or processed_df.empty:
                show_warning_message("No se pudieron procesar los datos.")
                return

            st.success(f"Datos procesados: {len(processed_df):,} registros validos")
            st.dataframe(processed_df.head(3), use_container_width=True)

            st.session_state["administrative_processes_df"] = processed_df
            persist_administrative_processes(processed_df)

            show_success_message(f"Sincronizacion exitosa: {len(processed_df):,} registros.")
            st.rerun()

        except Exception as exc:
            show_error_message(f"Error al sincronizar: {exc}")
            st.error("Posibles causas:")
            st.markdown(
                """
1. El Google Sheet no esta compartido publicamente
2. La URL de Google Sheets es invalida
3. El archivo no tiene la estructura esperada
                """
            )
            with st.expander("Ver detalles tecnicos"):
                st.code(traceback.format_exc())


def render_tab_manual_billing():
    """Render administrative processes tab."""
    st.header("Productividad de Procesos Administrativos")
    st.info("Sincroniza los datos para visualizar metricas y graficos.")

    if st.button("Sincronizar desde Google Sheets", key="btn_sync_sheets", use_container_width=True):
        _sync_processes()
        return

    processes_df = st.session_state.get("administrative_processes_df")
    if processes_df is None or processes_df.empty:
        st.info("No hay datos de procesos cargados. Usa el boton de sincronizacion.")
        return

    try:
        options = get_filter_options(processes_df)
    except Exception as exc:
        show_error_message(f"Datos invalidos de procesos: {exc}")

        with st.expander("Ver columnas disponibles"):
            st.write(list(processes_df.columns))
            st.dataframe(processes_df.head(3), use_container_width=True)

        if st.button("Limpiar datos y volver a sincronizar", key="btn_clear_procesos"):
            _clear_processes_data()
            show_success_message("Datos limpiados. Sincroniza nuevamente.")
            st.rerun()
        return

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Fecha inicio", key="manual_proc_start_date")
    with col2:
        end_date = st.date_input("Fecha fin", key="manual_proc_end_date")

    col3, col4 = st.columns(2)
    with col3:
        people = [ALL_OPTION] + options["people"]
        selected_person = st.selectbox("Persona", people, key="manual_proc_person")
    with col4:
        processes = [ALL_OPTION] + options["processes"]
        selected_process = st.selectbox("Proceso", processes, key="manual_proc_process")

    filtered_df = filter_administrative_processes(
        processes_df,
        start_date=start_date,
        end_date=end_date,
        person=selected_person if selected_person != ALL_OPTION else None,
        process=selected_process if selected_process != ALL_OPTION else None,
    )

    if filtered_df is None or filtered_df.empty:
        show_warning_message("No hay registros para los filtros seleccionados.")
        return

    # KPIs from service
    kpis = build_processes_kpis(filtered_df)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Registros", kpis["total_records"])
    with m2:
        st.metric("Total Cantidad", f"{kpis['total_quantity']:,.0f}")
    with m3:
        st.metric("Personas", kpis["unique_people"])
    with m4:
        st.metric("Tipos de Procesos", kpis["unique_processes"])

    # Chart datasets from service
    chart_data = build_chart_datasets(
        filtered_df,
        selected_person=selected_person,
        selected_process=selected_process,
    )

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Cantidad por Persona")
        bar_df = chart_data["bar_by_person"]
        fig1 = px.bar(
            bar_df,
            x="NOMBRE",
            y="CANTIDAD",
            color="CANTIDAD",
            color_continuous_scale="Blues",
        )
        fig1.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        pie_df = chart_data["pie_distribution"]
        if chart_data["pie_mode"] == "person":
            st.subheader("Distribucion por Persona")
            fig2 = px.pie(pie_df, values="CANTIDAD", names="NOMBRE", hole=0.4)
        else:
            st.subheader("Cantidad por Proceso")
            fig2 = px.pie(pie_df, values="CANTIDAD", names="PROCESO", hole=0.4)

        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Tendencia Temporal")
    trend_df = chart_data["time_trend"]
    fig3 = px.line(trend_df, x="FECHA", y="CANTIDAD", markers=True)
    st.plotly_chart(fig3, use_container_width=True)

