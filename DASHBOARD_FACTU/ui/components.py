"""
Reusable UI Components
================================
Common Streamlit components for use throughout the dashboard.
"""

import streamlit as st

def show_metric_card(label, value, delta=None, delta_color="normal"):

    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def show_dataframe(df, title=None, width="stretch"):

    if title:
        st.subheader(title)

    if df is None or df.empty:
        st.info("No hay datos para mostrar.")
        return

    st.dataframe(df, width = width)

def show_success_message(message):
    """Show success message."""
    st.success(f"✅ {message}")


def show_error_message(message):
    """Show error message."""
    st.error(f"❌ {message}")


def show_warning_message(message):
    """Show warning message."""
    st.warning(f"⚠️ {message}")


def show_info_message(message):
    """Show info message."""
    st.info(f"ℹ️ {message}")


def create_download_button(df, filename, label="📥 Descargar datos"):
    """
    Create download button.
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

def create_excel_download_button(file_bytes, filename, label="📥 Descargar informe Excel"):
    """Create download button for Excel files."""
    if not file_bytes:
        return

    st.download_button(
        label=label,
        data=file_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )