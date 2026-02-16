"""
Componentes reutilizables de UI
================================
Componentes comunes de Streamlit para usar en todo el dashboard.
"""

import streamlit as st
import pandas as pd


def show_metric_card(label, value, delta=None, delta_color="normal"):
    """
    Muestra una tarjeta de métrica.

    Args:
        label (str): Etiqueta de la métrica
        value (str/int/float): Valor de la métrica
        delta (str/int/float): Cambio/delta (opcional)
        delta_color (str): Color del delta ("normal", "inverse", "off")
    """
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def show_dataframe(df, title=None, use_container_width=True):
    """
    Muestra un DataFrame con título opcional.

    Args:
        df (pd.DataFrame): DataFrame a mostrar
        title (str): Título opcional
        use_container_width (bool): Si debe usar el ancho completo del contenedor
    """
    if title:
        st.subheader(title)

    if df is None or df.empty:
        st.info("No hay datos para mostrar.")
        return

    st.dataframe(df, use_container_width=use_container_width)


def show_success_message(message):
    """Muestra un mensaje de éxito."""
    st.success(f"✅ {message}")


def show_error_message(message):
    """Muestra un mensaje de error."""
    st.error(f"❌ {message}")


def show_warning_message(message):
    """Muestra un mensaje de advertencia."""
    st.warning(f"⚠️ {message}")


def show_info_message(message):
    """Muestra un mensaje informativo."""
    st.info(f"ℹ️ {message}")


def create_download_button(df, filename, label="📥 Descargar datos"):
    """
    Crea un botón para descargar un DataFrame como CSV.

    Args:
        df (pd.DataFrame): DataFrame a descargar
        filename (str): Nombre del archivo
        label (str): Texto del botón
    """
    if df is None or df.empty:
        return

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime='text/csv'
    )
