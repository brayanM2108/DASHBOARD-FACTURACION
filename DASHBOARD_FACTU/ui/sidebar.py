# Panel lateral con estado de datos y funciones útiles.

import streamlit as st
import pandas as  pd

def _mostrar_estado_datos():
    """Muestra el estado de los datos cargados con indicadores visuales."""

    datos_estado = [
        ('PPL', 'df_ppl'),
        ('Convenios', 'df_convenios'),
        ('RIPS', 'df_rips'),
        ('Facturación', 'df_facturacion'),
        ('Facturadores', 'df_facturadores'),
        ('Fact. Electrónica', 'df_facturacion_electronica'),
        ('Procesos', 'df_procesos')
    ]

    for nombre, key in datos_estado:
        df = st.session_state.get(key)

        if df is not None and not df.empty:
            st.success(f"✅ {nombre}: {len(df)} registros")
        else:
            st.warning(f"⚠️ {nombre}: Sin datos")


def render_state_data():
    """Panel lateral con estado de datos y funciones útiles."""

    with st.sidebar:
        st.header("📊 Estado de Datos")

        # Estado actual (ya lo tienes)
        _mostrar_estado_datos()

        st.divider()

        # 1. Resumen rápido
        _mostrar_resumen_rapido()

        st.divider()

        # 2. Acciones rápidas
        _mostrar_acciones_rapidas()

        st.divider()

        # 3. Última actualización
        _mostrar_ultima_actualizacion()


def _mostrar_resumen_rapido():
    """Muestra métricas resumidas de productividad."""
    st.subheader("📈 Resumen Rápido")

    df_ppl = st.session_state.get('df_ppl')
    df_convenios = st.session_state.get('df_convenios')
    df_rips = st.session_state.get('df_rips')
    df_procesos = st.session_state.get('df_procesos')
    total_legalizaciones = 0
    if df_ppl is not None:
        total_legalizaciones += len(df_ppl)
    if df_convenios is not None:
        total_legalizaciones += len(df_convenios)

    st.metric("Total Legalizaciones", total_legalizaciones)

    if df_procesos is not None:
        st.metric("Total Procesos", len(df_procesos))


def _mostrar_acciones_rapidas():
    """Botones de acciones rápidas."""
    st.subheader("⚡ Acciones Rápidas")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Recargar", help="Recarga todos los datos"):
            _recargar_datos()

    with col2:
        if st.button("🗑️ Limpiar", help="Limpia todos los datos"):
            _limpiar_datos()

def _mostrar_ultima_actualizacion():
    """Muestra cuándo se actualizaron los datos."""
    st.subheader("🕐 Última Actualización")

    ultima = st.session_state.get('ultima_actualizacion')
    if ultima:
        st.caption(f"📅 {ultima}")
    else:
        st.caption("Sin información")


def _recargar_datos():
    """Recarga datos desde archivos persistidos."""
    from data.loaders import load_all_persisted_data

    data = load_all_persisted_data()
    st.session_state['df_ppl'] = data.get('ppl')
    st.session_state['df_convenios'] = data.get('convenios')
    st.session_state['df_rips'] = data.get('rips')
    st.session_state['ultima_actualizacion'] = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
    st.rerun()


def _limpiar_datos():
    """Limpia todos los datos del session_state."""
    keys = ['df_ppl', 'df_convenios', 'df_rips', 'df_facturacion', 'df_facturadores']
    for key in keys:
        st.session_state[key] = None
    st.rerun()