"""
Pestaña de Facturación
=======================
Interfaz para visualizar y analizar facturación.
"""

import streamlit as st
from service.facturador_service import filtrar_facturacion, calcular_productividad_facturacion
from ui.visualizations import plot_productivity_charts
from ui.components import show_dataframe, create_download_button, show_info_message


def render_tab_facturacion(filtros):
    """
    Renderiza la pestaña de facturación.

    Args:
        filtros (dict): Filtros aplicados (start_date, end_date, usuarios_seleccionados)
    """
    st.header("Facturación")

    # Crear sub-pestañas
    tab_fact, tab_fact_elec = st.tabs(["📑 Facturación", "🧾 Facturación Electrónica"])

    with tab_fact:
        render_facturacion_section(filtros)

    with tab_fact_elec:
        render_facturacion_electronica_section(filtros)


def render_facturacion_section(filtros):
    """Renderiza la sección de facturación."""
    st.subheader("Facturación General")

    df_facturacion = st.session_state.get('df_facturacion')

    if df_facturacion is None or df_facturacion.empty:
        show_info_message("No hay datos de facturación. Carga un archivo en la sección de carga.")
        return

    # Aplicar filtros
    df_filtered = filtrar_facturacion(
        df_facturacion,
        filtros["start_date"],
        filtros["end_date"],
        filtros["usuarios_seleccionados"]
    )

    if df_filtered is None or df_filtered.empty:
        show_info_message("No hay datos que coincidan con los filtros seleccionados.")
        return

    # Calcular métricas
    metricas = calcular_productividad_facturacion(df_filtered)

    # Mostrar gráficos
    plot_productivity_charts(metricas, tipo="Facturación")

    # Mostrar tabla de datos
    with st.expander("📊 Ver datos detallados", expanded=False):
        show_dataframe(df_filtered, title="Datos de Facturación")
        create_download_button(df_filtered, "facturacion.csv")


def render_facturacion_electronica_section(filtros):
    """Renderiza la sección de facturación electrónica."""
    st.subheader("Facturación Electrónica")

    df_fact_elec = st.session_state.get('df_facturacion_electronica')

    if df_fact_elec is None or df_fact_elec.empty:
        show_info_message("No hay datos de facturación electrónica. Carga un archivo en la sección de carga.")
        return

    # Mostrar información básica
    st.metric("Total Registros", len(df_fact_elec))

    # Mostrar tabla de datos
    with st.expander("📊 Ver datos detallados", expanded=False):
        show_dataframe(df_fact_elec, title="Datos de Facturación Electrónica")
        create_download_button(df_fact_elec, "facturacion_electronica.csv")
