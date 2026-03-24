"""
Business logic - Manual Billing / Administrative Processes
==========================================================
Service functions for filtering and aggregating administrative process data.
"""

import pandas as pd

REQUIRED_COLUMNS = ("FECHA", "NOMBRE", "PROCESO", "CANTIDAD")

ERROR_INPUT_NONE = "Input dataframe cannot be None."
ERROR_MISSING_COLUMNS = "Missing required columns: {columns}"


def _validate_required_columns(df: pd.DataFrame) -> None:
    """Validate required columns for service operations."""
    if df is None:
        raise ValueError(ERROR_INPUT_NONE)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(ERROR_MISSING_COLUMNS.format(columns=", ".join(missing)))


def _normalize_operational_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return safe copy with normalized FECHA and CANTIDAD."""
    result_df = df.copy()
    result_df["FECHA"] = pd.to_datetime(result_df["FECHA"], errors="coerce")
    result_df["CANTIDAD"] = pd.to_numeric(result_df["CANTIDAD"], errors="coerce")
    result_df = result_df.dropna(subset=["FECHA"])
    return result_df


def get_filtered_data(
        df: pd.DataFrame,
        start_date=None,
        end_date=None,
        person=None,
        process=None,
) -> pd.DataFrame:
    """Filter data by date range, person, and process."""
    _validate_required_columns(df)
    filtered_df = _normalize_operational_columns(df)

    if start_date:
        filtered_df = filtered_df[filtered_df["FECHA"] >= pd.Timestamp(start_date)]
    if end_date:
        filtered_df = filtered_df[filtered_df["FECHA"] <= pd.Timestamp(end_date)]
    if person:
        filtered_df = filtered_df[filtered_df["NOMBRE"] == person]
    if process:
        filtered_df = filtered_df[filtered_df["PROCESO"] == process]

    return filtered_df


def get_summary_by_person(df: pd.DataFrame) -> pd.DataFrame:
    """Return aggregated summary by person."""
    _validate_required_columns(df)
    normalized_df = _normalize_operational_columns(df)

    return (
        normalized_df
        .groupby("NOMBRE")
        .agg({"CANTIDAD": "sum", "PROCESO": "count"})
        .reset_index()
        .rename(columns={"PROCESO": "TOTAL_PROCESSES"})
    )


def get_summary_by_process(df: pd.DataFrame) -> pd.DataFrame:
    """Return aggregated summary by process type."""
    _validate_required_columns(df)
    normalized_df = _normalize_operational_columns(df)

    return (
        normalized_df
        .groupby("PROCESO")
        .agg({"CANTIDAD": "sum", "NOMBRE": "count"})
        .reset_index()
        .rename(columns={"NOMBRE": "PEOPLE"})
    )


def build_processes_kpis(df: pd.DataFrame) -> dict:
    """Build main KPI metrics from filtered dataframe."""
    _validate_required_columns(df)

    if df.empty:
        return {
            "total_records": 0,
            "total_quantity": 0.0,
            "unique_people": 0,
            "unique_processes": 0,
        }

    normalized_df = _normalize_operational_columns(df)

    return {
        "total_records": len(normalized_df),
        "total_quantity": float(normalized_df["CANTIDAD"].fillna(0).sum()),
        "unique_people": int(normalized_df["NOMBRE"].nunique()),
        "unique_processes": int(normalized_df["PROCESO"].nunique()),
    }


def build_chart_datasets(df: pd.DataFrame, selected_person=None, selected_process=None) -> dict:
    """Build datasets for charts (bar, pie, trend)."""
    _validate_required_columns(df)

    if df.empty:
        empty_df = pd.DataFrame()
        return {
            "bar_by_person": empty_df,
            "pie_distribution": empty_df,
            "pie_mode": "process",
            "time_trend": empty_df,
        }

    normalized_df = _normalize_operational_columns(df)

    bar_by_person = normalized_df.groupby("NOMBRE")["CANTIDAD"].sum().reset_index()

    show_person_distribution = (
            selected_process is not None
            and selected_process not in ("Todos", "All")
            and (selected_person is None or selected_person in ("Todos", "All"))
    )

    if show_person_distribution:
        pie_distribution = normalized_df.groupby("NOMBRE")["CANTIDAD"].sum().reset_index()
        pie_mode = "person"
    else:
        pie_distribution = normalized_df.groupby("PROCESO")["CANTIDAD"].sum().reset_index()
        pie_mode = "process"

    time_trend = normalized_df.groupby("FECHA")["CANTIDAD"].sum().reset_index()

    return {
        "bar_by_person": bar_by_person,
        "pie_distribution": pie_distribution,
        "pie_mode": pie_mode,
        "time_trend": time_trend,
    }

def filter_administrative_processes(
        df: pd.DataFrame,
        start_date=None,
        end_date=None,
        person=None,
        process=None,
) -> pd.DataFrame:
    """Compatibility alias expected by UI modules."""
    return get_filtered_data(
        df=df,
        start_date=start_date,
        end_date=end_date,
        person=person,
        process=process,
    )

def get_filter_options(df: pd.DataFrame) -> dict:
    """Return available people and process options for UI filters."""
    _validate_required_columns(df)
    normalized_df = _normalize_operational_columns(df)

    people = sorted(normalized_df["NOMBRE"].dropna().astype(str).unique().tolist())
    processes = sorted(normalized_df["PROCESO"].dropna().astype(str).unique().tolist())

    return {
        "people": people,
        "processes": processes,
    }