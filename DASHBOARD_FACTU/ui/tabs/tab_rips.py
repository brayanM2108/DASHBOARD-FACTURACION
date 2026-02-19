"""
Pestaña de RIPS
================
Interfaz para visualizar y analizar RIPS.
"""
import pandas as pd
import streamlit as st
from service.rips_service import filtrar_rips, calcular_productividad_rips
from ui.visualizations import plot_productivity_charts
from ui.components import show_dataframe, create_download_button, show_info_message


def render_tab_rips():
    """Renderiza la pestaña de RIPS con filtros independientes."""
    st.header("📄 RIPS")

    df_rips = st.session_state.get('df_rips')

    if df_rips is None or df_rips.empty:
        show_info_message("No hay datos de RIPS. Carga un archivo en la sección de carga.")
        return

    # Filtros específicos para RIPS
    col1, col2 = st.columns(2)
    with col1:
        try:
            fecha_min = df_rips['FECHA'].min()
            if pd.isna(fecha_min):
                fecha_min = pd.Timestamp.now()
        except:
            fecha_min = pd.Timestamp.now()
        fecha_inicio = st.date_input("Fecha inicio", value=fecha_min, key="rips_fecha_inicio")

    with col2:
        try:
            fecha_max = df_rips['FECHA'].max()
            if pd.isna(fecha_max):
                fecha_max = pd.Timestamp.now()
        except:
            fecha_max = pd.Timestamp.now()
        fecha_fin = st.date_input("Fecha fin", value=fecha_max, key="rips_fecha_fin")


        # Filtro por usuario (ya viene con el nombre del facturador después del cruce)
        usuario_col = None
        for col_name in ['USUARIO FACTURÓ', 'USUARIO FACTURO', 'USUARIO', 'FACTURADOR']:
            if col_name in df_rips.columns:
                usuario_col = col_name
                break

        if usuario_col:
            usuarios = ['Todos'] + sorted(df_rips[usuario_col].dropna().unique().tolist())
            usuario_sel = st.selectbox("Usuario", usuarios, key="rips_usuario")
        else:
            usuario_sel = 'Todos'


    usuarios_seleccionados = None if usuario_sel == 'Todos' else [usuario_sel]

    # Aplicar filtros
    df_filtered = filtrar_rips(
        df_rips,
        fecha_inicio,
        fecha_fin,
        usuarios_seleccionados
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
