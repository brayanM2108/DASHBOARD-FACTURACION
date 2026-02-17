"""
Utilidades para manejo de fechas
=================================
Funciones auxiliares para trabajar con fechas en el dashboard.
"""

import pandas as pd
import datetime


def parse_date_column(df, column_name):
    """
    Convierte una columna a formato datetime.

    Args:
        df (pd.DataFrame): DataFrame con la columna
        column_name (str): Nombre de la columna

    Returns:
        pd.DataFrame: DataFrame con columna convertida
    """
    if column_name not in df.columns:
        return df

    df[column_name] = pd.to_datetime(df[column_name], errors='coerce')
    return df


def filter_by_date_range(df, date_column, start_date, end_date):
    """
    Filtra un DataFrame por rango de fechas.

    Args:
        df (pd.DataFrame): DataFrame a filtrar
        date_column (str): Nombre de la columna de fecha
        start_date (datetime.date): Fecha inicial
        end_date (datetime.date): Fecha final

    Returns:
        pd.DataFrame: DataFrame filtrado
    """
    if date_column not in df.columns:
        return df

    # Asegurar que la columna sea datetime
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')

    # Eliminar filas con fechas inválidas
    df = df.dropna(subset=[date_column])

    # Filtrar por rango
    mask = (df[date_column].dt.date >= start_date) & (df[date_column].dt.date <= end_date)
    return df[mask]


def get_default_date_range(days_back=30):
    """
    Obtiene un rango de fechas por defecto.

    Args:
        days_back (int): Número de días hacia atrás desde hoy

    Returns:
        tuple: (start_date, end_date)
    """
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days_back)
    return start_date, end_date
