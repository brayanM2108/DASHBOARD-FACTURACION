"""
Pestaña de RIPS
================
Interfaz para visualizar y analizar RIPS.
"""

import streamlit as st
from service.rips_service import filtrar_rips, calcular_productividad_rips
from ui.visualizations import plot_productivity_charts
from ui.components import show_dataframe, create_download_button, show_info_message


def render_tab_rips(filtros):
    """
    Renderiza la pestaña de RIPS.

    Args:
        filtros (dict): Filtros aplicados (start_date, end_date, usuarios_seleccionados)
    """
    st.header("📄 RIPS")

    df_rips = st.session_state.get('df_rips')

    if df_rips is None or df_rips.empty:
        show_info_message("No hay datos de RIPS. Carga un archivo en la sección de carga.")
        return

    # Aplicar filtros
    df_filtered = filtrar_rips(
        df_rips,
        filtros["start_date"],
        filtros["end_date"],
        filtros["usuarios_seleccionados"]
    )

    if df_filtered is None or df_filtered.empty:
        show_info_message("No hay datos que coincidan con los filtros seleccionados.")
        return

    # Calcular métricas
    metricas = calcular_productividad_rips(df_filtered)

    # Mostrar gráficos
    plot_productivity_charts(metricas, tipo="RIPS")

    # Mostrar tabla de datos
    with st.expander("📊 Ver datos detallados", expanded=False):
        show_dataframe(df_filtered, title="Datos de RIPS")
        create_download_button(df_filtered, "rips.csv")
