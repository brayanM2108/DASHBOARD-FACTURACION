"""
Dashboard de Productividad - Aplicación Principal
==================================================
Punto de entrada de la aplicación Streamlit.
"""

import streamlit as st
from config.settings import PAGE_CONFIG
from data.loaders import load_all_persisted_data, load_facturadores_master
from ui.filters import render_sidebar, render_state_data
from ui.file_upload import render_file_upload_section
from ui.tabs.tab_legalizaciones import render_tab_legalizacion
from ui.tabs.tab_rips import render_tab_rips
from ui.tabs.tab_facturacion import render_tab_facturacion


def init_session_state():
    """Inicializa el estado de sesión con datos persistidos."""
    if 'initialized' not in st.session_state:
        # Cargar datos persistidos
        data = load_all_persisted_data()

        st.session_state['df_ppl'] = data.get('ppl')
        st.session_state['df_convenios'] = data.get('convenios')
        st.session_state['df_rips'] = data.get('rips')
        st.session_state['df_facturacion'] = data.get('facturacion')
        st.session_state['df_facturadores'] = data.get('facturadores')
        st.session_state['df_facturacion_electronica'] = data.get('facturacion_electronica')

        # Cargar facturadores maestro si no hay datos
        if st.session_state['df_facturadores'] is None:
            st.session_state['df_facturadores'] = load_facturadores_master()

        st.session_state['initialized'] = True


def main():
    """Función principal de la aplicación."""
    # Configurar página
    st.set_page_config(**PAGE_CONFIG)

    # Inicializar estado
    init_session_state()

    # Título principal
    st.title("📊 Dashboard de Productividad")
    render_state_data()
    # Renderizar sidebar con filtros
    filtros = render_sidebar()

    # Mostrar estado de datos en sidebar


    # Crear pestañas principales
    tab_inicio, tab_legalizaciones, tab_rips, tab_facturacion, tab_carga = st.tabs([
        "🏠 Inicio",
        "📋 Legalizaciones",
        "📄 RIPS",
        "💰 Facturación",
        "📂 Cargar Archivos"
    ])

    with tab_inicio:
        render_inicio()

    with tab_legalizaciones:
        render_tab_legalizacion(filtros)

    with tab_rips:
        render_tab_rips(filtros)

    with tab_facturacion:
        render_tab_facturacion(filtros)

    with tab_carga:
        render_file_upload_section()


def render_inicio():
    """Renderiza la pestaña de inicio con resumen general."""
    st.header("🏠 Resumen General")

    # Mostrar estado de los datos cargados
    st.subheader("📁 Estado de Datos")

    col1, col2, col3 = st.columns(3)

    with col1:
        df_ppl = st.session_state.get('df_ppl')
        count_ppl = len(df_ppl) if df_ppl is not None else 0
        st.metric("Legalizaciones PPL", count_ppl)
        df_convenios = st.session_state.get('df_convenios')
        count_conv = len(df_convenios) if df_convenios is not None else 0
        st.metric("Legalizaciones Convenios", count_conv)

    with col2:
        df_rips = st.session_state.get('df_rips')
        count_rips = len(df_rips) if df_rips is not None else 0
        st.metric("RIPS", count_rips)

        df_facturadores = st.session_state.get('df_facturadores')
        count_fact = len(df_facturadores) if df_facturadores is not None else 0
        st.metric("Facturadores", count_fact)

    with col3:
        df_facturacion = st.session_state.get('df_facturacion')
        count_facturacion = len(df_facturacion) if df_facturacion is not None else 0
        st.metric("Facturación", count_facturacion)

        df_fact_elec = st.session_state.get('df_facturacion_electronica')
        count_fact_elec = len(df_fact_elec) if df_fact_elec is not None else 0
        st.metric("Facturación Electrónica", count_fact_elec)

    # Instrucciones
    st.markdown("---")
    st.subheader("📖 Instrucciones")
    st.markdown("""
    1. **Cargar Archivos**: Ve a la pestaña "📂 Cargar Archivos" para subir tus datos.
    2. **Filtrar**: Usa la barra lateral para filtrar por fechas y facturadores.
    3. **Analizar**: Navega por las pestañas para ver métricas y gráficos.
    4. **Exportar**: Descarga los datos filtrados en formato CSV.
    """)


if __name__ == "__main__":
    main()
