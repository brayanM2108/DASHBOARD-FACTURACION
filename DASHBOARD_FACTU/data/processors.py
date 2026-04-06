"""
Data processing
===============
Functions to transform and clean loaded datasets.
"""

import pandas as pd
from config.settings import (
    VALID_STATES_LEGALIZATIONS,
    VALID_STATES_RIPS,
    VALID_STATES_INVOICING_ELECTRONIC,
    PPL_NAME
)
from utils.date_helpers import parse_date_column

REQUIRED_PROCESS_COLUMNS = ("FECHA", "NOMBRE", "DOCUMENTO", "PROCESO", "CANTIDAD")
PROCESS_TEXT_COLUMNS = ("NOMBRE", "DOCUMENTO", "PROCESO")

ERROR_MISSING_PROCESS_COLUMNS = (
    "Missing required columns: {missing}. Available columns: {available}"
)

COMPARISON_MODE_DOCUMENT = "DOCUMENTO"
COMPARISON_MODE_NAME = "NOMBRE"

def _normalize_text_series(series: pd.Series) -> pd.Series:
    """Normalize text values for stable matching."""
    return series.astype(str).str.strip().str.upper()


def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize dataframe column names to uppercase without extra spaces."""
    df_copy = df.copy()
    df_copy.columns = df_copy.columns.astype(str).str.strip().str.upper()
    return df_copy


def _normalize_object_columns_in_place(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize all object columns (trim + uppercase)."""
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = _normalize_text_series(df[col])
    return df

def _ensure_required_columns(df: pd.DataFrame, required_columns: tuple[str, ...]) -> None:
    """Raise ValueError when required columns are missing."""
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(
            ERROR_MISSING_PROCESS_COLUMNS.format(
                missing=", ".join(missing),
                available=", ".join(df.columns.tolist()),
            )
        )

def split_legalizations(
        df: pd.DataFrame,
        state_column: str = "ESTADO",
        date_column: str = "FECHA LEGALIZACION",
        agreement_column: str = "CONVENIO",
):
    """
    Process legalizations dataframe and split into PPL and agreements.
    Returns: (ppl_df, agreements_df)
    """
    if df is None or df.empty:
        return None, None

    result_df = df.copy()
    result_df = parse_date_column(result_df, date_column)

    if state_column in result_df.columns:
        result_df[state_column] = _normalize_text_series(result_df[state_column])
        result_df = result_df[result_df[state_column].isin(VALID_STATES_LEGALIZATIONS)]

    if agreement_column not in result_df.columns:
        return None, None

    ppl_df = result_df[result_df[agreement_column] == PPL_NAME].copy()
    agreements_df = result_df[result_df[agreement_column] != PPL_NAME].copy()
    return ppl_df, agreements_df

def process_rips_data(df: pd.DataFrame,state_column: str = "ESTADO",date_column: str = "FECHA_REAL",
):
    """Process RIPS dataframe."""
    if df is None or df.empty:
        return None

    result_df = df.copy()
    result_df = parse_date_column(result_df, date_column)

    if state_column in result_df.columns:
        result_df[state_column] = _normalize_text_series(result_df[state_column])
        result_df = result_df[result_df[state_column].isin(VALID_STATES_RIPS)]

    return result_df

def process_billing_data(
        df: pd.DataFrame,
        date_column: str = "FECHA_FACTURA",
):
    """Process billing dataframe."""
    if df is None or df.empty:
        return None

    result_df = df.copy()
    result_df = parse_date_column(result_df, date_column)
    return result_df

def process_electronic_billing_data(
        df: pd.DataFrame,
        state_column: str = "ESTADO",
        date_column: str = "FECHA RADICACIÓN",
):
    """Process electronic billing dataframe."""
    if df is None or df.empty:
        return None

    result_df = df.copy()
    result_df = parse_date_column(result_df, date_column)

    if state_column in result_df.columns:
        result_df[state_column] = _normalize_text_series(result_df[state_column])
        result_df = result_df[result_df[state_column].isin(VALID_STATES_INVOICING_ELECTRONIC)]

    return result_df

def merge_with_billers(
        df: pd.DataFrame,
        billers_df: pd.DataFrame,
        user_column: str = "USUARIO",
):
    """Left-merge dataframe with billers master info."""
    if df is None or df.empty or billers_df is None or billers_df.empty:
        return df

    if user_column not in df.columns or "USUARIO" not in billers_df.columns:
        return df

    return pd.merge(df,
                    billers_df,
                    left_on=user_column,
                    right_on="USUARIO"
                    , how="left")

def merge_billing_with_electronic_billing(
        billing_df: pd.DataFrame,
        electronic_billing_df: pd.DataFrame,
):
    """
    Assign user to billing records by matching:
    billing.NRO_FACTURACLI -> electronic_billing.FACTURA
    """
    if billing_df is None or billing_df.empty:
        return billing_df

    if electronic_billing_df is None or electronic_billing_df.empty:
        return billing_df

    result_df = billing_df.copy()
    normalized_e_billing_df = electronic_billing_df.copy()

    _normalize_object_columns_in_place(result_df)
    _normalize_object_columns_in_place(normalized_e_billing_df)

    state_col = "ESTADO" if "ESTADO" in normalized_e_billing_df.columns else "Estado"
    if state_col in normalized_e_billing_df.columns:
        active_e_billing_df = normalized_e_billing_df[
            normalized_e_billing_df[state_col] == "ACTIVO"
            ].copy()
    else:
        active_e_billing_df = normalized_e_billing_df.copy()

    if "FACTURA" in active_e_billing_df.columns and "USUARIO" in active_e_billing_df.columns:
        user_map = (
            active_e_billing_df
            .dropna(subset=["FACTURA", "USUARIO"])
            .drop_duplicates(subset=["FACTURA"])
            .set_index("FACTURA")["USUARIO"]
        )

        if "NRO_FACTURACLI" in result_df.columns:
            result_df["USUARIO"] = result_df["NRO_FACTURACLI"].map(user_map)

    return result_df

def process_administrative_processes(df: pd.DataFrame):
    """
    Process administrative processes dataframe (e.g., Google Sheets source).
    Normalizes columns, validates structure, converts types, and cleans rows.
    """
    if df is None or df.empty:
        return None

    result_df = df.copy()

    # Detect whether first row contains actual headers.
    first_row_upper = result_df.iloc[0].astype(str).str.upper()
    if "FECHA" in first_row_upper.values or "NOMBRE" in first_row_upper.values:
        result_df.columns = result_df.iloc[0].astype(str).str.strip().str.upper()
        result_df = result_df.iloc[1:].reset_index(drop=True)
    else:
        result_df = _normalize_column_names(result_df)

    _ensure_required_columns(result_df, REQUIRED_PROCESS_COLUMNS)

    result_df = result_df.dropna(how="all")
    result_df["FECHA"] = pd.to_datetime(result_df["FECHA"], errors="coerce")
    result_df["CANTIDAD"] = pd.to_numeric(result_df["CANTIDAD"], errors="coerce")
    result_df = result_df.dropna(subset=["FECHA", "NOMBRE", "CANTIDAD"])

    for col in PROCESS_TEXT_COLUMNS:
        if col in result_df.columns:
            result_df[col] = result_df[col].astype(str).str.strip()

    return result_df

def aggregate_records_by_user(
        df: pd.DataFrame,
        user_column: str = "USUARIO",
        date_column: str | None = None,
        group_by_date: bool = False,
):
    """Aggregate records by user, optionally by date."""
    if df is None or df.empty or user_column not in df.columns:
        return None

    result_df = df.copy()

    if group_by_date and date_column and date_column in result_df.columns:
        result_df["DATE"] = pd.to_datetime(result_df[date_column], errors="coerce").dt.date
        agg_df = result_df.groupby([user_column, "DATE"]).size().reset_index(name="COUNT")
    else:
        agg_df = result_df.groupby(user_column).size().reset_index(name="COUNT")

    return agg_df

def filter_by_billers(
        df: pd.DataFrame,
        billers_df: pd.DataFrame,
        user_column: str,
        comparison_mode: str = COMPARISON_MODE_DOCUMENT,
):
    """
    Keep only rows where user value exists in billers master comparison column.
    comparison_mode: 'DOCUMENTO' or 'NOMBRE'
    """
    if df is None or df.empty:
        return df
    if billers_df is None or billers_df.empty:
        return df
    if user_column is None or user_column not in df.columns:
        return df
    if comparison_mode not in billers_df.columns:
        return df

    valid_values = (
        billers_df[comparison_mode]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
        .unique()
        .tolist()
    )

    result_df = df.copy()
    result_df["_user_norm"] = _normalize_text_series(result_df[user_column])
    filtered_df = result_df[result_df["_user_norm"].isin(valid_values)].copy()
    filtered_df = filtered_df.drop(columns=["_user_norm"])

    return filtered_df
