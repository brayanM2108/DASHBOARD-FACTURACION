"""
Productivity Dashboard - Main Application
==================================================
Author: Brayan Melo
Version: 2.0
=================================================
Streamlit Application Entry Point
"""

import streamlit as st
from config.settings import PAGE_CONFIG
from data.loaders import load_all_persisted_frames, load_billers_master
from ui.file_upload import render_file_upload_section
from ui.sidebar import render_state_data
from ui.tabs.tab_legalizations import render_tab_legalizations
from ui.tabs.tab_rips import render_tab_rips
from ui.tabs.tab_billing import render_tab_billing
from ui.tabs.tab_manual_billing import render_tab_manual_billing
from service.rips_service import map_document_to_name

def init_session_state():
    """Inicializa el estado de sesión con datos persistidos."""
    if 'initialized' not in st.session_state:
        data = load_all_persisted_frames()


        st.session_state["ppl_legalizations_df"] = data.get("ppl_legalizations")
        st.session_state["agreement_legalizations_df"] = data.get("agreement_legalizations")
        st.session_state["rips_df"] = data.get("rips")
        st.session_state["billing_df"] = data.get("billing")
        st.session_state["billers_df"] = data.get("billers")
        st.session_state["electronic_billing_df"] = data.get("electronic_billing")
        st.session_state["administrative_processes_df"] = data.get("administrative_processes")

        if st.session_state["billers_df"] is None:
            st.session_state["billers_df"] = load_billers_master()

        if st.session_state["rips_df"] is not None and st.session_state["billers_df"] is not None:
            st.session_state["rips_df"] = map_document_to_name(
                st.session_state["rips_df"],
                st.session_state["billers_df"],
            )

        st.session_state["initialized"] = True


def main():
    """Función principal de la aplicación."""
    st.set_page_config(**PAGE_CONFIG)

    init_session_state()

    st.title("📊 Dashboard de Productividad")
    render_state_data()

    tab_home, tab_legalizations, tab_rips, tab_billing, tab_manual_billing, tab_load = st.tabs([
        "🏠 Inicio",
        "📋 Legalizaciones",
        "📄 RIPS",
        "💰 Facturación",
        "🔧 Procesos Administrativos",
        "📂 Cargar Archivos"
    ])

    with tab_home:
        render_home()

    with tab_legalizations:
        render_tab_legalizations()

    with tab_rips:
        render_tab_rips()

    with tab_billing:
        render_tab_billing()

    with tab_manual_billing:
        render_tab_manual_billing()

    with tab_load:
        render_file_upload_section()


def render_home():
    """Renderiza la pestaña de inicio con resumen general."""
    st.header("🏠 Resumen General")

    # Mostrar estado de los datos cargados
    st.subheader("📁 Estado de Datos")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        df_ppl = st.session_state.get('ppl_legalizations_df')
        count_ppl = len(df_ppl) if df_ppl is not None else 0
        st.metric("Legalizaciones PPL", count_ppl)
        df_convenios = st.session_state.get('agreement_legalizations_df')
        count_conv = len(df_convenios) if df_convenios is not None else 0
        st.metric("Legalizaciones Convenios", count_conv)

    with col2:
        df_rips = st.session_state.get('rips_df')
        count_rips = len(df_rips) if df_rips is not None else 0
        st.metric("RIPS", count_rips)

        df_facturadores = st.session_state.get('billers_df')
        count_fact = len(df_facturadores) if df_facturadores is not None else 0
        st.metric("Facturadores", count_fact)

    with col3:
        df_facturacion = st.session_state.get('billing_df')
        count_facturacion = len(df_facturacion) if df_facturacion is not None else 0
        st.metric("Facturación", count_facturacion)

        df_fact_elec = st.session_state.get('electronic_billing_df')
        count_fact_elec = len(df_fact_elec) if df_fact_elec is not None else 0
        st.metric("Facturación Electrónica", count_fact_elec)

    with col4:
        df_procesos = st.session_state.get('administrative_processes_df')
        count_procesos = len(df_procesos) if df_procesos is not None else 0
        st.metric("Procesos Administrativos", count_procesos)

        if df_procesos is not None and not df_procesos.empty:
            total_cantidad = df_procesos['CANTIDAD'].sum() if 'CANTIDAD' in df_procesos.columns else 0

            try:
                total_cantidad = float(total_cantidad)
                st.metric("Total Cantidad Procesos", f"{total_cantidad:,.0f}")
            except (ValueError, TypeError):
                st.metric("Total Cantidad Procesos", "N/A")

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
