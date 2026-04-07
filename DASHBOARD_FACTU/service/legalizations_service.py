"""
Business logic - Legalizations
==============================
Functions for legalizations processing and productivity analytics.
"""

import pandas as pd

from config import COLUMN_NAMES_LEGALIZATIONS
from data.processors import (
    aggregate_records_by_user,
    filter_by_billers ,
    merge_with_billers,
    split_legalizations

)
from data.validators import (
    find_first_column_variant,
    validate_legalizations_dataframe,
)
from config.settings import COLUMN_NAMES
from utils.date_helpers import filter_by_date_range

ERROR_VALIDATION_FAILED = "Legalizations validation failed"

def _build_error_result(message):
    """Standard error payload for legalizations processing."""
    return {
        "ppl_df": None,
        "agreements_df": None,
        "error": message,
    }

def _empty_productivity_metrics():
    """Standard metrics payload when input data is empty."""
    return {
        "total": 0,
        "by_user": None,
        "by_date": None,
        "daily_average": 0,
    }

def _is_user_filter_active(selected_users):
    """Return True when a specific user filter is active."""
    return (
            selected_users
            and "All" not in selected_users
            and "Todos" not in selected_users
            and len(selected_users) > 0
    )

def process_legalizations(df, billers_df=None):
    """
    Validate and process legalizations dataframe into PPL and agreements datasets.
    """
    is_valid, message = validate_legalizations_dataframe(df)
    if not is_valid:
        return _build_error_result(f"{ERROR_VALIDATION_FAILED}: {message}")

    ppl_df, agreements_df = split_legalizations(df)

    if billers_df is not None:
        biller_document_col = "USUARIO_QUE_LEGALIZO"

        if ppl_df is not None and biller_document_col in ppl_df.columns:
            ppl_df = filter_by_billers(ppl_df, billers_df, biller_document_col, "DOCUMENTO")

        if agreements_df is not None and biller_document_col in agreements_df.columns:
            agreements_df = filter_by_billers(
                agreements_df,
                billers_df,
                biller_document_col,
                "DOCUMENTO",
            )

    if billers_df is not None:
        ppl_user_col = (
            find_first_column_variant(ppl_df, COLUMN_NAMES["usuario"])
            if ppl_df is not None
            else None
        )
        if ppl_user_col:
            ppl_df = merge_with_billers(ppl_df, billers_df, ppl_user_col)

        agreements_user_col = (
            find_first_column_variant(agreements_df, COLUMN_NAMES["usuario"])
            if agreements_df is not None
            else None
        )
        if agreements_user_col:
            agreements_df = merge_with_billers(agreements_df, billers_df, agreements_user_col)

    return {
        "ppl_df": ppl_df,
        "agreements_df": agreements_df,
        "error": None,
    }


def filter_legalizations(df, start_date, end_date, selected_users=None):
    """Filter legalizations by date range and optional user selection."""
    if df is None or df.empty:
        return df

    date_col = find_first_column_variant(df, COLUMN_NAMES_LEGALIZATIONS["fecha"])
    if date_col is None:
        return df

    filtered_df = filter_by_date_range(df, date_col, start_date, end_date)

    if _is_user_filter_active(selected_users):
        user_col = find_first_column_variant(filtered_df, COLUMN_NAMES_LEGALIZATIONS["usuario"])
        if user_col and user_col in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[user_col].isin(selected_users)]

    return filtered_df


def calculate_legalizations_productivity(df, category="PPL"):
    """Calculate productivity metrics for legalizations."""
    if df is None or df.empty:
        result = _empty_productivity_metrics()
        result["category"] = category
        return result

    user_col = find_first_column_variant(df, COLUMN_NAMES["usuario"])
    date_col = find_first_column_variant(df, COLUMN_NAMES_LEGALIZATIONS["fecha"])

    total = len(df)

    by_user = None
    if user_col:
        by_user = aggregate_records_by_user(df, user_col, date_col, group_by_date=False)

    by_date = None
    if date_col:
        temp_df = df.copy()
        temp_df["DATE"] = pd.to_datetime(temp_df[date_col]).dt.date
        by_date = temp_df.groupby("DATE").size().reset_index(name="COUNT")

    daily_average = 0
    if by_date is not None and not by_date.empty:
        daily_average = by_date["COUNT"].mean()

    return {
        "total": total,
        "by_user": by_user,
        "by_date": by_date,
        "daily_average": daily_average,
        "category": category,
    }
