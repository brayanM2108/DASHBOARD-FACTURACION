"""
Filtros y barra lateral
========================
Componentes de filtrado para el dashboard.
"""

import streamlit as st

from utils.date_helpers import get_default_date_range
from service import obtener_lista_facturadores


def render_sidebar():
    """
    Renderiza la barra lateral con filtros globales.

    Returns:
        dict: Diccionario con valores de filtros seleccionados
    """
    with st.sidebar:
        st.header("🎛️ Filtros Globales")

        # Filtro de fechas
        st.subheader("📅 Rango de Fechas")
        start_date_default, end_date_default = get_default_date_range(30)

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Desde",
                value=start_date_default,
                key="filter_start_date"
            )
        with col2:
            end_date = st.date_input(
                "Hasta",
                value=end_date_default,
                key="filter_end_date"
            )

        # Filtro de usuarios
        st.subheader("👥 Facturadores")

        df_facturadores = st.session_state.get('df_facturadores')
        lista_facturadores = obtener_lista_facturadores(df_facturadores)

        if lista_facturadores:
            usuarios_seleccionados = st.multiselect(
                "Seleccionar facturadores",
                options=lista_facturadores,
                default=lista_facturadores,
                key="filter_usuarios"
            )
        else:
            usuarios_seleccionados = []
            st.info("No hay facturadores disponibles. Carga el archivo maestro.")

        # Botón para aplicar filtros
        aplicar_filtros = st.button("🔄 Aplicar Filtros", use_container_width=True)

        return {
            "start_date": start_date,
            "end_date": end_date,
            "usuarios_seleccionados": usuarios_seleccionados,
            "aplicar_filtros": aplicar_filtros
        }


def render_date_filter(key_prefix=""):
    """
    Renderiza un filtro de fechas independiente.

    Args:
        key_prefix (str): Prefijo para las keys de Streamlit

    Returns:
        tuple: (start_date, end_date)
    """
    start_date_default, end_date_default = get_default_date_range(30)

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Desde",
            value=start_date_default,
            key=f"{key_prefix}_start_date"
        )
    with col2:
        end_date = st.date_input(
            "Hasta",
            value=end_date_default,
            key=f"{key_prefix}_end_date"
        )

    return start_date, end_date


def render_user_filter(df_facturadores, key_prefix=""):
    """
    Renderiza un filtro de usuarios independiente.

    Args:
        df_facturadores (pd.DataFrame): DataFrame de facturadores
        key_prefix (str): Prefijo para las keys de Streamlit

    Returns:
        list: Lista de usuarios seleccionados
    """
    lista_facturadores = obtener_lista_facturadores(df_facturadores)

    if not lista_facturadores:
        st.info("No hay facturadores disponibles.")
        return []

    usuarios_seleccionados = st.multiselect(
        "Seleccionar facturadores",
        options=lista_facturadores,
        default=lista_facturadores,
        key=f"{key_prefix}_usuarios"
    )

    return usuarios_seleccionados

def render_state_data(key_prefix=""):
    """
    Renderiza el estado de los datos cargados en la barra lateral.

    Args:
        key_prefix (str): Prefijo para las keys (no usado actualmente)

    Returns:
        dict: Diccionario con el estado de cada dataset (True si tiene datos)
    """
    # --- BARRA LATERAL (FILTROS GLOBALES) ---
    st.sidebar.header("📊 Estado de Datos")

    estado = {}

    # Muestra el estado de carga de cada dataset en la barra lateral
    for nombre, key in [("PPL", "df_ppl"), ("Convenios", "df_convenios"),
                        ("RIPS", "df_rips"), ("Facturación", "df_facturacion")]:
        df = st.session_state.get(key)
        if df is not None and not df.empty:
            st.sidebar.success(f"✅ {nombre}: {len(df):,} registros")
            estado[key] = True
        else:
            st.sidebar.warning(f"⚠️ {nombre}: Sin datos")
            estado[key] = False

    st.sidebar.markdown("---")
    return estado
