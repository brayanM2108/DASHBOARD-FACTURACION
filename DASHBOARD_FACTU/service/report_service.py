"""
Business logic - Report Service
================================
Builds structured report data for each module.
Consumed by excel_exporter.py to generate downloadable Excel files.
"""

import pandas as pd

from service.billing_electronic_service import calculate_billing_productivity
from service.legalizations_service import calculate_legalizations_productivity
from service.manual_billing_service import build_chart_datasets, build_processes_kpis, get_summary_by_person, get_summary_by_process
from service.rips_service import calculate_rips_productivity


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _calculate_variation(current: float, previous: float) -> float | None:
    """
    Percentage variation between two periods.
    Returns None when the previous value is zero or unavailable.
    """
    if previous is None or previous == 0:
        return None
    return ((current - previous) / previous) * 100


def _build_variation_block(current_total: float, previous_total: float) -> dict:
    """Return a standardized variation block for the executive summary."""
    variation = _calculate_variation(current_total, previous_total)
    return {
        "current_total": current_total,
        "previous_total": previous_total,
        "variation_pct": variation,
    }


def _top5_by_user(by_user_df: pd.DataFrame | None) -> pd.DataFrame | None:
    """Return the top 5 users by COUNT from a by_user dataframe."""
    if by_user_df is None or by_user_df.empty:
        return None
    if "COUNT" not in by_user_df.columns:
        return None
    return (
        by_user_df
        .sort_values("COUNT", ascending=False)
        .head(5)
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# Billing report
# ---------------------------------------------------------------------------

def build_billing_report(
        df_current: pd.DataFrame,
        df_previous: pd.DataFrame | None = None,
        by_user_df: pd.DataFrame | None = None,
) -> dict:
    """
    Build billing report data.

    Args:
        df_current: Filtered billing dataframe for the current period.
        df_previous: Filtered billing dataframe for the previous period (optional).
        by_user_df: Optional pre-aggregated productivity by user dataframe.

    Returns:
        dict with keys: executive_summary, by_user, by_date
    """
    metrics_current = calculate_billing_productivity(df_current)
    metrics_previous = calculate_billing_productivity(df_previous) if df_previous is not None else None

    by_user_current = by_user_df if by_user_df is not None else metrics_current["by_user"]

    previous_total = metrics_previous["total"] if metrics_previous else 0
    previous_daily_avg = metrics_previous["daily_average"] if metrics_previous else 0
    user_col = by_user_current.columns[0] if by_user_current is not None and not by_user_current.empty else "USUARIO"
    executive_summary = {
        "total": metrics_current["total"],
        "daily_average": metrics_current["daily_average"],
        "top5_by_user": _top5_by_user(by_user_current),
        "variation": _build_variation_block(metrics_current["total"], previous_total),
        "variation_daily_avg": _build_variation_block(
            metrics_current["daily_average"], previous_daily_avg
        ),
    }

    return {
        "executive_summary": executive_summary,
        "by_user": by_user_current,
        "by_date": metrics_current["by_date"],
        "by_date_records": (
            metrics_current["by_date_dual"][["DATE", "REGISTROS"]]
            if metrics_current.get("by_date_dual") is not None
            else None
        ),
        "by_user_records": (
            metrics_current["by_user_dual"][[user_col, "REGISTROS"]]
            if metrics_current.get("by_user_dual") is not None
            else None
        ),
    }


# ---------------------------------------------------------------------------
# RIPS report
# ---------------------------------------------------------------------------

def build_rips_report(
        df_current: pd.DataFrame,
        df_previous: pd.DataFrame | None = None,
) -> dict:
    """
    Build RIPS report data.

    Args:
        df_current: Filtered RIPS dataframe for the current period.
        df_previous: Filtered RIPS dataframe for the previous period (optional).

    Returns:
        dict with keys: executive_summary, by_user, by_date
    """
    metrics_current = calculate_rips_productivity(df_current)
    metrics_previous = calculate_rips_productivity(df_previous) if df_previous is not None else None

    previous_total = metrics_previous["total"] if metrics_previous else 0
    previous_daily_avg = metrics_previous["daily_average"] if metrics_previous else 0

    executive_summary = {
        "total": metrics_current["total"],
        "daily_average": metrics_current["daily_average"],
        "top5_by_user": _top5_by_user(metrics_current["by_user"]),
        "variation": _build_variation_block(metrics_current["total"], previous_total),
        "variation_daily_avg": _build_variation_block(
            metrics_current["daily_average"], previous_daily_avg
        ),
    }

    return {
        "executive_summary": executive_summary,
        "by_user": metrics_current["by_user"],
        "by_date": metrics_current["by_date"],
    }


# ---------------------------------------------------------------------------
# Legalizations report (PPL + Agreements together)
# ---------------------------------------------------------------------------

def build_legalizations_report(
        ppl_current: pd.DataFrame,
        agreements_current: pd.DataFrame,
        ppl_previous: pd.DataFrame | None = None,
        agreements_previous: pd.DataFrame | None = None,
) -> dict:
    """
    Build legalizations report data combining PPL and Agreements.

    Args:
        ppl_current: Filtered PPL dataframe for the current period.
        agreements_current: Filtered Agreements dataframe for the current period.
        ppl_previous: PPL dataframe for the previous period (optional).
        agreements_previous: Agreements dataframe for the previous period (optional).

    Returns:
        dict with keys: executive_summary, ppl, agreements
        - ppl / agreements each contain: metrics, by_user, by_date, top5_by_user
    """
    ppl_metrics = calculate_legalizations_productivity(ppl_current, category="PPL")
    agreements_metrics = calculate_legalizations_productivity(agreements_current, category="Convenios")

    ppl_previous_metrics = (
        calculate_legalizations_productivity(ppl_previous, category="PPL")
        if ppl_previous is not None else None
    )
    agreements_previous_metrics = (
        calculate_legalizations_productivity(agreements_previous, category="Convenios")
        if agreements_previous is not None else None
    )

    total_current = ppl_metrics["total"] + agreements_metrics["total"]
    total_previous = (
            (ppl_previous_metrics["total"] if ppl_previous_metrics else 0)
            + (agreements_previous_metrics["total"] if agreements_previous_metrics else 0)
    )

    # Weighted daily average across both categories
    ppl_avg = ppl_metrics["daily_average"] or 0
    agreements_avg = agreements_metrics["daily_average"] or 0
    global_daily_avg = (ppl_avg + agreements_avg) / 2 if (ppl_avg + agreements_avg) > 0 else 0

    ppl_prev_avg = ppl_previous_metrics["daily_average"] if ppl_previous_metrics else 0
    agreements_prev_avg = agreements_previous_metrics["daily_average"] if agreements_previous_metrics else 0
    previous_daily_avg = (ppl_prev_avg + agreements_prev_avg) / 2

    executive_summary = {
        "total": total_current,
        "daily_average": global_daily_avg,
        "ppl_total": ppl_metrics["total"],
        "agreements_total": agreements_metrics["total"],
        "variation": _build_variation_block(total_current, total_previous),
        "variation_daily_avg": _build_variation_block(global_daily_avg, previous_daily_avg),
    }

    return {
        "executive_summary": executive_summary,
        "ppl": {
            "metrics": ppl_metrics,
            "by_user": ppl_metrics["by_user"],
            "by_date": ppl_metrics["by_date"],
            "top5_by_user": _top5_by_user(ppl_metrics["by_user"]),
        },
        "agreements": {
            "metrics": agreements_metrics,
            "by_user": agreements_metrics["by_user"],
            "by_date": agreements_metrics["by_date"],
            "top5_by_user": _top5_by_user(agreements_metrics["by_user"]),
        },
    }


# ---------------------------------------------------------------------------
# Administrative processes report
# ---------------------------------------------------------------------------

def build_processes_report(
        df_current: pd.DataFrame,
        df_previous: pd.DataFrame | None = None,
        selected_person: str | None = None,
        selected_process: str | None = None,
) -> dict:
    """
    Build administrative processes report data.

    Args:
        df_current: Filtered processes dataframe for the current period.
        df_previous: Filtered processes dataframe for the previous period (optional).
        selected_person: Active person filter (for chart datasets).
        selected_process: Active process filter (for chart datasets).

    Returns:
        dict with keys: executive_summary, by_person, by_process, chart_datasets
    """
    kpis_current = build_processes_kpis(df_current)
    kpis_previous = build_processes_kpis(df_previous) if df_previous is not None else None

    previous_records = kpis_previous["total_records"] if kpis_previous else 0
    previous_quantity = kpis_previous["total_quantity"] if kpis_previous else 0

    executive_summary = {
        "total_records": kpis_current["total_records"],
        "total_quantity": kpis_current["total_quantity"],
        "unique_people": kpis_current["unique_people"],
        "unique_processes": kpis_current["unique_processes"],
        "variation_records": _build_variation_block(
            kpis_current["total_records"], previous_records
        ),
        "variation_quantity": _build_variation_block(
            kpis_current["total_quantity"], previous_quantity
        ),
    }

    chart_datasets = build_chart_datasets(
        df_current,
        selected_person=selected_person,
        selected_process=selected_process,
    )

    return {
        "executive_summary": executive_summary,
        "by_person": get_summary_by_person(df_current),
        "by_process": get_summary_by_process(df_current),
        "chart_datasets": chart_datasets,
    }