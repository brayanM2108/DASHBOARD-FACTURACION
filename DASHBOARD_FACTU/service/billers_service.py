"""
Business logic - Billers
========================
Functions to manage biller-related information.
"""

from data.loaders import load_billers_master

USER_LOOKUP_COLUMNS = "NOMBRE"

DEFAULT_SESSION_DATASET_KEYS = (
    "ppl_legalizations_df",
    "agreement_legalizations_df",
    "rips_df",
    "billing_df",
)

def _normalize_text(value):
    """Normalize text values for robust comparisons."""
    return str(value).strip().upper()


def _extract_unique_users_from_dataframes(dataframes):
    """Collect unique users from provided dataframes."""
    users = set()

    for df in dataframes:
        if df is None or df.empty:
            continue

        selected_col = USER_LOOKUP_COLUMNS if USER_LOOKUP_COLUMNS in df.columns else None
        if selected_col is None:
            continue

        normalized_values = (
            df[selected_col]
            .dropna()
            .astype(str)
            .map(_normalize_text)
            .tolist()
        )
        users.update(normalized_values)

    return sorted(users)


def _extract_unique_users_from_master(billers_df):
    """Collect unique users directly from billers master dataframe."""
    if billers_df is None or billers_df.empty:
        return []

    selected_col = USER_LOOKUP_COLUMNS if USER_LOOKUP_COLUMNS in billers_df.columns else None
    if selected_col is None:
        return []

    return sorted(
        billers_df[selected_col]
        .dropna()
        .astype(str)
        .map(_normalize_text)
        .unique()
        .tolist()
    )

def get_billers_list(billers_df=None, dataframes=None, session_state=None):
    """
    Return available billers list.
    """
    if dataframes is not None:
        return _extract_unique_users_from_dataframes(dataframes)

    if billers_df is not None:
        return _extract_unique_users_from_master(billers_df)

    if session_state is not None:
        dataset_frames = [session_state.get(key) for key in DEFAULT_SESSION_DATASET_KEYS]
        return _extract_unique_users_from_dataframes(dataset_frames)

    return []

def get_biller_info(user, billers_df=None):
    """
    Return detailed biller information by user name/identifier.
    """
    if user is None:
        return None

    if billers_df is None:
        billers_df = load_billers_master()

    if billers_df is None or billers_df.empty:
        return None

    lookup_col = USER_LOOKUP_COLUMNS if USER_LOOKUP_COLUMNS else None
    if lookup_col is None:
        return None

    user_norm = _normalize_text(user)
    matches = billers_df[
        billers_df[lookup_col].astype(str).map(_normalize_text) == user_norm
        ]

    if matches.empty:
        return None

    return matches.iloc[0].to_dict()
