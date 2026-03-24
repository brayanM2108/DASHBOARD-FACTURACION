"""
Date Handling Tools
=================================
Auxiliary functions for working with dates in the dashboard.
"""

import pandas as pd
import datetime


def parse_date_column(df, column_name):
    """
    Convert a column to datetime format.
    """
    if column_name not in df.columns:
        return df

    df[column_name] = pd.to_datetime(df[column_name], errors='coerce')
    return df


def filter_by_date_range(df, date_column, start_date, end_date):
    """
    Filter a DataFrame by date range.
    """
    if date_column not in df.columns:
        return df

    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')

    df = df.dropna(subset=[date_column])

    mask = (df[date_column].dt.date >= start_date) & (df[date_column].dt.date <= end_date)
    return df[mask]


def get_default_date_range(days_back=30):
    """
    It obtains a default date range.
    """
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days_back)
    return start_date, end_date
