"""
Pestaña de Facturación
=======================
Interfaz para visualizar y analizar facturación.
"""

import streamlit as st

from data.processors import merge_with_facturadores
from service.facturador_service import filtrar_facturacion, calcular_productividad_facturacion
from ui.visualizations import plot_productivity_charts
from ui.components import show_dataframe, create_download_button, show_info_message
from ui.visualizations import plot_bar_chart

def render_tab_facturacion(filtros):
    """
    Renderiza la pestaña de facturación.

    Args:
        filtros (dict): Filtros aplicados (start_date, end_date, usuarios_seleccionados)
    """
    st.header("Facturación")


    render_facturacion_section(filtros)


def render_facturacion_section(filtros):

    df_facturacion = st.session_state.get('df_facturacion')
    df_facturadores = st.session_state.get('df_facturadores')
    df_fact_elec = st.session_state.get('df_facturacion_electronica')

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

    st.subheader("📈 Facturación por Usuario")

    # Verificar que exista facturación electrónica para hacer el cruce
    if df_fact_elec is None or df_fact_elec.empty:
        st.warning("No hay datos de facturación electrónica. Carga el archivo para poder identificar usuarios.")
    else:
        from data.processors import merge_facturacion_with_electronica
        from data.validators import find_column_variant
        from config.settings import COLUMN_NAMES

        # Hacer el cruce con facturación electrónica para obtener el USUARIO
        df_with_usuario = merge_facturacion_with_electronica(df_filtered, df_fact_elec)

        # Encontrar la columna de usuario dinámicamente
        usuario_col = find_column_variant(df_with_usuario, COLUMN_NAMES["usuario"])

        if usuario_col is None or usuario_col not in df_with_usuario.columns:
            st.warning(
                "No se pudo determinar el usuario. Verifica que el cruce con facturación electrónica sea correcto.")
        else:
            # Filtrar registros que tienen usuario asignado
            df_with_usuario_valid = df_with_usuario[df_with_usuario[usuario_col].notna()].copy()

            if df_with_usuario_valid.empty:
                st.warning("No se encontraron coincidencias entre facturación y facturación electrónica.")
            else:
                # Agrupar por columna de usuario
                df_por_usuario = df_with_usuario_valid.groupby(usuario_col).size().reset_index(name='CANTIDAD')

                # Combinar con facturadores para obtener nombres
                if df_facturadores is not None and not df_facturadores.empty:
                    df_por_usuario = merge_with_facturadores(
                        df_por_usuario,
                        df_facturadores=df_facturadores,
                        usuario_column=usuario_col
                    )

                # Ordenar descendente
                df_por_usuario = df_por_usuario.sort_values('CANTIDAD', ascending=False)

                # Determinar columna de nombre
                nombre_col = 'NOMBRE' if 'NOMBRE' in df_por_usuario.columns else usuario_col

                # Mostrar gráfico
                plot_bar_chart(
                    df_por_usuario,
                    x_col=nombre_col,
                    y_col='CANTIDAD',
                    title="Facturación por Usuario"
                )


    # Calcular métricas
    metricas = calcular_productividad_facturacion(df_filtered)

    # Mostrar gráficos
    plot_productivity_charts(metricas, tipo="Facturación")

    # Mostrar tabla
    st.dataframe(df_por_usuario, use_container_width=True)


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
