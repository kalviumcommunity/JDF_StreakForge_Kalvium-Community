"""Parsing, validation and profiling for user-uploaded datasets.

Everything here is a plain function over bytes or a DataFrame — no Streamlit UI
calls — so the whole module can be unit-tested without a browser or a server.
app.py owns the widgets; this file owns the logic.
"""

from __future__ import annotations

import io

import pandas as pd
import streamlit as st

SUPPORTED_EXTENSIONS = (".csv", ".json")
PREVIEW_ROWS = 10


class UploadError(Exception):
    """Raised with a message written for a business user, not a developer."""


# ------------------------------------------------------------------ parsing --
def detect_format(filename: str) -> str:
    """Return 'csv' or 'json' from the filename, or raise UploadError."""
    lowered = (filename or "").lower()
    for ext in SUPPORTED_EXTENSIONS:
        if lowered.endswith(ext):
            return ext.lstrip(".")
    raise UploadError(
        "Unsupported file type. Please upload a .csv or .json file."
    )


def parse_bytes(filename: str, data: bytes) -> pd.DataFrame:
    """Turn raw uploaded bytes into a DataFrame.

    Takes bytes rather than the uploader object so tests can pass literals and
    so the caching layer has something hashable to key on.
    """
    kind = detect_format(filename)
    buffer = io.BytesIO(data)
    # Order matters: EmptyDataError and ParserError both subclass ValueError,
    # so the specific handlers must come first or they are unreachable.
    try:
        if kind == "csv":
            return pd.read_csv(buffer)
        return pd.read_json(buffer)
    except pd.errors.EmptyDataError as exc:
        raise UploadError(
            "This file is empty — there are no rows and no headers to read."
        ) from exc
    except pd.errors.ParserError as exc:
        raise UploadError(
            "Could not read this file. The rows do not all have the same "
            "number of columns — check for stray commas or a broken export."
        ) from exc
    except UnicodeDecodeError as exc:
        raise UploadError(
            "This file is not readable as text. If it is an Excel file, "
            "export it as CSV first."
        ) from exc
    except ValueError as exc:
        # Catch-all for malformed JSON and anything else pandas rejects.
        raise UploadError(
            "Could not read this file. Check that it is a well-formed "
            f"{kind.upper()} file and try again."
        ) from exc


# The uploader hands back the same bytes on every rerun, so hashing them means
# a 9 MB file is parsed once per session instead of once per widget click.
@st.cache_data(show_spinner="Reading your file…")
def load_dataframe(filename: str, data: bytes) -> pd.DataFrame:
    return parse_bytes(filename, data)


# --------------------------------------------------------------- validation --
def validate(df: pd.DataFrame) -> None:
    """Raise UploadError if the parsed file is unusable. Silent when fine."""
    if df is None or df.shape[1] == 0:
        raise UploadError(
            "This file has no columns. Check that the first row contains "
            "column headers."
        )
    if len(df) == 0:
        raise UploadError(
            "This file has headers but no rows. Check the export and try again."
        )
    if df.isnull().all().all():
        raise UploadError(
            "Every cell in this file is empty. Check the export settings."
        )


# ---------------------------------------------------------------- profiling --
def overall_null_pct(df: pd.DataFrame) -> float:
    """Share of all cells in the table that are null."""
    total_cells = df.shape[0] * df.shape[1]
    if total_cells == 0:
        return 0.0
    return round(df.isnull().sum().sum() / total_cells * 100, 1)


def column_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-column type and completeness — the data-quality check at a glance."""
    return pd.DataFrame(
        {
            "Column": df.columns,
            "Type": df.dtypes.astype(str).values,
            "Non-Null": df.notnull().sum().values,
            "Null Count": df.isnull().sum().values,
            "Null %": (df.isnull().sum() / len(df) * 100).round(1).values,
        }
    )


def numeric_columns(df: pd.DataFrame) -> list:
    return df.select_dtypes(include="number").columns.tolist()


def categorical_columns(df: pd.DataFrame) -> list:
    return df.select_dtypes(exclude="number").columns.tolist()


def quality_flags(df: pd.DataFrame) -> list:
    """Non-fatal warnings worth surfacing above the preview.

    These do not stop the upload — they are the things an analyst would want
    flagged before they trust a number they read off the table.
    """
    flags = []

    empty_cols = [c for c in df.columns if df[c].isnull().all()]
    if empty_cols:
        flags.append(
            f"{len(empty_cols)} column(s) are entirely empty: "
            + ", ".join(map(str, empty_cols[:5]))
            + ("…" if len(empty_cols) > 5 else "")
        )

    sparse = [c for c in df.columns if 0 < df[c].isnull().mean() and
              df[c].isnull().mean() > 0.5 and c not in empty_cols]
    if sparse:
        flags.append(
            f"{len(sparse)} column(s) are more than half null: "
            + ", ".join(map(str, sparse[:5]))
            + ("…" if len(sparse) > 5 else "")
        )

    dupes = int(df.duplicated().sum())
    if dupes:
        flags.append(f"{dupes:,} fully duplicated row(s) found.")

    unnamed = [c for c in df.columns if str(c).startswith("Unnamed:")]
    if unnamed:
        flags.append(
            f"{len(unnamed)} column(s) have no header — the file may have been "
            "exported with an index column."
        )

    return flags
