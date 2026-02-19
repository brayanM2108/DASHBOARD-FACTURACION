"""
Pestaña de Legalizaciones
==========================
Interfaz para visualizar y analizar legalizaciones PPL y Convenios.
"""

import streamlit as st
import pandas as pd
from service.legalizaciones_service import filtrar_legalizaciones, calcular_productividad_legalizaciones
from ui.visualizations import plot_productivity_charts
from ui.components import show_dataframe, create_download_button, show_info_message

def render_tab_legalizacion():
    """
    Renderiza la pestaña de legalizaciones.

    Args:
        filtros (dict): Filtros aplicados (start_date, end_date, usuarios_seleccionados)
    """
    st.header("📋 Legalizaciones")

    # Crear sub-pestañas para PPL y Convenios
    tab_ppl, tab_convenios = st.tabs(["🏥 PPL", "🤝 Convenios"])

    with tab_ppl:
        render_ppl_section()

    with tab_convenios:
        render_convenios_section()

def render_ppl_section():
    """Renderiza la sección de PPL."""
    st.subheader("Legalizaciones PPL")

    df_ppl = st.session_state.get('df_ppl')

    if df_ppl is None or df_ppl.empty:
        show_info_message("No hay datos de legalizaciones PPL. Carga un archivo en la sección de carga.")
        return

        # Crear sub-pestañas para PPL y Convenios
    tab_ppl, tab_convenios = st.tabs(["🏥 PPL", "🤝 Convenios"])

    with tab_ppl:
        render_ppl_section()

    with tab_convenios:
        render_convenios_section()
"""
Pestaña de Legalizaciones
==========================
Interfaz para visualizar y analizar legalizaciones PPL y Convenios.
"""



def render_tab_legalizacion():
    """
    Renderiza la pestaña de legalizaciones.

    Args:
        filtros (dict): Filtros aplicados (start_date, end_date, usuarios_seleccionados)
    """
    st.header("📋 Legalizaciones")

    # Crear sub-pestañas para PPL y Convenios
    tab_ppl, tab_convenios = st.tabs(["🏥 PPL", "🤝 Convenios"])

    with tab_ppl:
        render_ppl_section()

    with tab_convenios:
        render_convenios_section()


def render_ppl_section():
    """Renderiza la sección de PPL con filtros independientes."""
    st.subheader("Legalizaciones PPL")

    df_ppl = st.session_state.get('df_ppl')

    if df_ppl is None or df_ppl.empty:
        show_info_message("No hay datos de legalizaciones PPL. Carga un archivo en la sección de carga.")
        return

    # Filtros específicos para PPL
    col1, col2 = st.columns(2)
    with col1:
        try:
            fecha_min = df_ppl['FECHA'].min()
            if pd.isna(fecha_min):
                fecha_min = pd.Timestamp.now()
        except:
            fecha_min = pd.Timestamp.now()
        fecha_inicio = st.date_input("Fecha inicio", value=fecha_min, key="ppl_fecha_inicio")

    with col2:
        try:
            fecha_max = df_ppl['FECHA'].max()
            if pd.isna(fecha_max):
                fecha_max = pd.Timestamp.now()
        except:
            fecha_max = pd.Timestamp.now()
        fecha_fin = st.date_input("Fecha fin", value=fecha_max, key="ppl_fecha_fin")

    # Filtro por usuario (ajusta el nombre de la columna según tu DataFrame)
    usuarios = ['Todos'] + sorted(df_ppl['USUARIO'].unique().tolist()) if 'USUARIO' in df_ppl.columns else ['Todos']
    usuario_sel = st.selectbox("Usuario", usuarios, key="ppl_usuario")

    usuarios_seleccionados = None if usuario_sel == 'Todos' else [usuario_sel]

    # Aplicar filtros
    df_filtered = filtrar_legalizaciones(
        df_ppl,
        fecha_inicio,
        fecha_fin,
        usuarios_seleccionados
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


def render_convenios_section():
    """Renderiza la sección de Convenios con filtros independientes."""
    st.subheader("Legalizaciones Convenios")

    df_convenios = st.session_state.get('df_convenios')

    if df_convenios is None or df_convenios.empty:
        show_info_message("No hay datos de legalizaciones de Convenios. Carga un archivo en la sección de carga.")
        return

    # Filtros específicos para Convenios
    col1, col2 = st.columns(2)
    with col1:
        try:
            fecha_min = df_convenios['FECHA'].min()
            if pd.isna(fecha_min):
                fecha_min = pd.Timestamp.now()
        except:
            fecha_min = pd.Timestamp.now()
        fecha_inicio = st.date_input("Fecha inicio", value=fecha_min, key="convenios_fecha_inicio")

    with col2:
        try:
            fecha_max = df_convenios['FECHA'].max()
            if pd.isna(fecha_max):
                fecha_max = pd.Timestamp.now()
        except:
            fecha_max = pd.Timestamp.now()
        fecha_fin = st.date_input("Fecha fin", value=fecha_max, key="convenios_fecha_fin")

    # Filtro por usuario
    usuarios = ['Todos'] + sorted(df_convenios['USUARIO'].unique().tolist()) if 'USUARIO' in df_convenios.columns else ['Todos']
    usuario_sel = st.selectbox("Usuario", usuarios, key="convenios_usuario")

    usuarios_seleccionados = None if usuario_sel == 'Todos' else [usuario_sel]

    # Aplicar filtros
    df_filtered = filtrar_legalizaciones(
        df_convenios,
        fecha_inicio,
        fecha_fin,
        usuarios_seleccionados
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
