"""
Visualizations and Graphs
===========================
Functions for creating graphs with Plotly and Matplotlib.
"""

import streamlit as st
import plotly.express as px

def plot_bar_chart(df, x_col, y_col, title, color=None, sortable=True, sort_key=None):
    """
    Create a bar chart with Plotly.
    """
    if df is None or df.empty:
        st.info("No hay datos para graficar.")
        return

    df_plot = df.copy()

    if sortable:
        col1, col2 = st.columns([3, 1])
        with col2:
            sort_key_suffix = f"_{sort_key}" if sort_key else ""
            orden = st.selectbox(
                "Ordenar por:",
                options=["Sin ordenar", "Mayor a Menor", "Menor a Mayor"],
                key=f"sort_bar{sort_key_suffix}"
            )

            if orden == "Mayor a Menor":
                df_plot = df_plot.sort_values(by=y_col, ascending=False)
            elif orden == "Menor a Mayor":
                df_plot = df_plot.sort_values(by=y_col, ascending=True)

    df_plot[x_col] = df_plot[x_col].astype(str)

    fig = px.bar(
        df_plot,
        x=x_col,
        y=y_col,
        title=title,
        color=color,
        text=y_col
    )

    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis_tickangle=-45,
        showlegend=True if color else False,
        xaxis_type='category'
    )

    st.plotly_chart(fig, use_container_width = "stretch")


def plot_line_chart(df, x_col, y_col, title, color=None, sortable=True, sort_key=None):
    """
    Create a line graph with Plotly.
    """
    if df is None or df.empty:
        st.info("No hay datos para graficar.")
        return

    df_plot = df.copy()

    if sortable:
        col1, col2 = st.columns([3, 1])
        with col2:
            sort_key_suffix = f"_{sort_key}" if sort_key else ""
            orden = st.selectbox(
                "Ordenar por:",
                options=["Por Fecha", "Mayor a Menor", "Menor a Mayor"],
                key=f"sort_line{sort_key_suffix}"
            )

            if orden == "Mayor a Menor":
                df_plot = df_plot.sort_values(by=y_col, ascending=False)
            elif orden == "Menor a Mayor":
                df_plot = df_plot.sort_values(by=y_col, ascending=True)
            else:  # Por Fecha
                df_plot = df_plot.sort_values(by=x_col)

    fig = px.line(
        df_plot,
        x=x_col,
        y=y_col,
        title=title,
        color=color,
        markers=True
    )

    fig.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig, use_container_width = "stretch")


def plot_metrics_summary(metrics):
    """
    It displays a summary of metrics in cards.
    """
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Registros", f"{metrics.get('total', 0):,}")

    with col2:
        promedio = metrics.get('daily_average', 0)
        st.metric("Promedio Diario", f"{promedio:.2f}")


def plot_productivity_charts(metrics, tipo="Productividad"):
    """
    Displays productivity graphs (by user and by date).
    """
    st.subheader(f"📊 Análisis de {tipo}")

    plot_metrics_summary(metrics)

    if metrics.get('by_user') is not None and not metrics['by_user'].empty:
        st.markdown("### Por Usuario")
        plot_bar_chart(
            metrics['by_user'],
            x_col=metrics['by_user'].columns[0],
            y_col='COUNT',
            title=f"{tipo} por Usuario",
            sortable=True,
            sort_key=f"{tipo}_usuario"
        )

    if metrics.get('by_date') is not None and not metrics['by_date'].empty:
        st.markdown("### Por Fecha")
        plot_line_chart(
            metrics['by_date'],
            x_col='DATE',
            y_col='COUNT',
            title=f"{tipo} por Fecha",
            sortable=True,
            sort_key=f"{tipo}_fecha"
        )
