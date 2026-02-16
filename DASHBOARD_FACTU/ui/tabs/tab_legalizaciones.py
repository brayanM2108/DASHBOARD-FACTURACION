"""
Pestaña de Legalizaciones
==========================
Interfaz para visualizar y analizar legalizaciones PPL y Convenios.
"""


import streamlit as st
from service.legalizaciones_service import filtrar_legalizaciones, calcular_productividad_legalizaciones
from ui.visualizations import plot_productivity_charts
from ui.components import show_dataframe, create_download_button, show_info_message


def render_tab_legalizacion(filtros):
    """
    Renderiza la pestaña de legalizaciones.

    Args:
        filtros (dict): Filtros aplicados (start_date, end_date, usuarios_seleccionados)
    """
    st.header("📋 Legalizaciones")

    # Crear sub-pestañas para PPL y Convenios
    tab_ppl, tab_convenios = st.tabs(["🏥 PPL", "🤝 Convenios"])

    with tab_ppl:
        render_ppl_section(filtros)

    with tab_convenios:
        render_convenios_section(filtros)


def render_ppl_section(filtros):
    """Renderiza la sección de PPL."""
    st.subheader("Legalizaciones PPL")

    df_ppl = st.session_state.get('df_ppl')

    if df_ppl is None or df_ppl.empty:
        show_info_message("No hay datos de legalizaciones PPL. Carga un archivo en la sección de carga.")
        return

    # Aplicar filtros
    df_filtered = filtrar_legalizaciones(
        df_ppl,
        filtros["start_date"],
        filtros["end_date"],
        filtros["usuarios_seleccionados"]
    )

    if df_filtered is None or df_filtered.empty:
        show_info_message("No hay datos que coincidan con los filtros seleccionados.")
        return

    # Calcular métricas
    metricas = calcular_productividad_legalizaciones(df_filtered, tipo="PPL")

    # Mostrar gráficos
    plot_productivity_charts(metricas, tipo="Legalizaciones PPL")

    # Mostrar tabla de datos
    with st.expander("📊 Ver datos detallados", expanded=False):
        show_dataframe(df_filtered, title="Datos de Legalizaciones PPL")
        create_download_button(df_filtered, "legalizaciones_ppl.csv")


def render_convenios_section(filtros):
    """Renderiza la sección de Convenios."""
    st.subheader("Legalizaciones Convenios")

    df_convenios = st.session_state.get('df_convenios')

    if df_convenios is None or df_convenios.empty:
        show_info_message("No hay datos de legalizaciones de Convenios. Carga un archivo en la sección de carga.")
        return

    # Aplicar filtros
    df_filtered = filtrar_legalizaciones(
        df_convenios,
        filtros["start_date"],
        filtros["end_date"],
        filtros["usuarios_seleccionados"]
    )

    if df_filtered is None or df_filtered.empty:
        show_info_message("No hay datos que coincidan con los filtros seleccionados.")
        return

    # Calcular métricas
    metricas = calcular_productividad_legalizaciones(df_filtered, tipo="Convenios")

    # Mostrar gráficos
    plot_productivity_charts(metricas, tipo="Legalizaciones Convenios")

    # Mostrar tabla de datos
    with st.expander("📊 Ver datos detallados", expanded=False):
        show_dataframe(df_filtered, title="Datos de Legalizaciones Convenios")
        create_download_button(df_filtered, "legalizaciones_convenios.csv")
"""
Pestaña de Legalizaciones
==========================
Interfaz para visualizar y analizar legalizaciones PPL y Convenios.
"""

import streamlit as st
from service.legalizaciones_service import filtrar_legalizaciones, calcular_productividad_legalizaciones
from ui.visualizations import plot_productivity_charts
from ui.components import show_dataframe, create_download_button, show_info_message


def render_tab_legalizacion(filtros):
    """
    Renderiza la pestaña de legalizaciones.

    Args:
        filtros (dict): Filtros aplicados (start_date, end_date, usuarios_seleccionados)
    """
    st.header("📋 Legalizaciones")

    # Crear sub-pestañas para PPL y Convenios
    tab_ppl, tab_convenios = st.tabs(["🏥 PPL", "🤝 Convenios"])

    with tab_ppl:
        render_ppl_section(filtros)

    with tab_convenios:
        render_convenios_section(filtros)


def render_ppl_section(filtros):
    """Renderiza la sección de PPL."""
    st.subheader("Legalizaciones PPL")

    df_ppl = st.session_state.get('df_ppl')

    if df_ppl is None or df_ppl.empty:
        show_info_message("No hay datos de legalizaciones PPL. Carga un archivo en la sección de carga.")
        return

    # Aplicar filtros
    df_filtered = filtrar_legalizaciones(
        df_ppl,
        filtros["start_date"],
        filtros["end_date"],
        filtros["usuarios_seleccionados"]
    )

    if df_filtered is None or df_filtered.empty:
        show_info_message("No hay datos que coincidan con los filtros seleccionados.")
        return

    # Calcular métricas
    metricas = calcular_productividad_legalizaciones(df_filtered, tipo="PPL")

    # Mostrar gráficos
    plot_productivity_charts(metricas, tipo="Legalizaciones PPL")

    # Mostrar tabla de datos
    with st.expander("📊 Ver datos detallados", expanded=False):
        show_dataframe(df_filtered, title="Datos de Legalizaciones PPL")
        create_download_button(df_filtered, "legalizaciones_ppl.csv")


def render_convenios_section(filtros):
    """Renderiza la sección de Convenios."""
    st.subheader("Legalizaciones Convenios")

    df_convenios = st.session_state.get('df_convenios')

    if df_convenios is None or df_convenios.empty:
        show_info_message("No hay datos de legalizaciones de Convenios. Carga un archivo en la sección de carga.")
        return

    # Aplicar filtros
    df_filtered = filtrar_legalizaciones(
        df_convenios,
        filtros["start_date"],
        filtros["end_date"],
        filtros["usuarios_seleccionados"]
    )

    if df_filtered is None or df_filtered.empty:
        show_info_message("No hay datos que coincidan con los filtros seleccionados.")
        return

    # Calcular métricas
    metricas = calcular_productividad_legalizaciones(df_filtered, tipo="Convenios")

    # Mostrar gráficos
    plot_productivity_charts(metricas, tipo="Legalizaciones Convenios")

    # Mostrar tabla de datos
    with st.expander("📊 Ver datos detallados", expanded=False):
        show_dataframe(df_filtered, title="Datos de Legalizaciones Convenios")
        create_download_button(df_filtered, "legalizaciones_convenios.csv")
