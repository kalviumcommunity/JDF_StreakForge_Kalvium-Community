"""Unit tests for the upload parsing, validation and profiling layer.

upload_utils holds no Streamlit UI calls, so every one of these runs in
milliseconds without a server or a browser.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import upload_utils as uu  # noqa: E402

CSV = b"member_id,city,visits\nMBR-1,Bangalore,10\nMBR-2,Chennai,4\nMBR-3,,0\n"
JSON = b'[{"member_id":"MBR-1","visits":10},{"member_id":"MBR-2","visits":4}]'


# ------------------------------------------------------------- format routing
def test_detects_csv():
    assert uu.detect_format("export.csv") == "csv"


def test_detects_json_case_insensitively():
    assert uu.detect_format("EXPORT.JSON") == "json"


def test_rejects_unsupported_extension():
    with pytest.raises(uu.UploadError, match="Unsupported file type"):
        uu.detect_format("report.xlsx")


def test_rejects_missing_extension():
    with pytest.raises(uu.UploadError):
        uu.detect_format("noextension")


# --------------------------------------------------------------------- parsing
def test_parses_csv_bytes():
    df = uu.parse_bytes("export.csv", CSV)
    assert df.shape == (3, 3)
    assert list(df.columns) == ["member_id", "city", "visits"]


def test_parses_json_bytes():
    df = uu.parse_bytes("export.json", JSON)
    assert df.shape == (2, 2)


def test_malformed_json_raises_friendly_error():
    with pytest.raises(uu.UploadError) as err:
        uu.parse_bytes("broken.json", b"{not valid json")
    assert "well-formed" in str(err.value)


def test_ragged_csv_raises_friendly_error():
    ragged = b"a,b\n1,2\n3,4,5,6\n"
    with pytest.raises(uu.UploadError, match="same\\s+number of columns"):
        uu.parse_bytes("ragged.csv", ragged)


def test_completely_empty_file_raises_friendly_error():
    with pytest.raises(uu.UploadError, match="empty"):
        uu.parse_bytes("empty.csv", b"")


# ------------------------------------------------------------------ validation
def test_valid_frame_passes():
    uu.validate(uu.parse_bytes("export.csv", CSV))  # must not raise


def test_headers_but_no_rows_rejected():
    with pytest.raises(uu.UploadError, match="no rows"):
        uu.validate(pd.DataFrame(columns=["a", "b"]))


def test_no_columns_rejected():
    with pytest.raises(uu.UploadError, match="no columns"):
        uu.validate(pd.DataFrame())


def test_all_null_frame_rejected():
    with pytest.raises(uu.UploadError, match="empty"):
        uu.validate(pd.DataFrame({"a": [None, None], "b": [None, None]}))


# ------------------------------------------------------------------- profiling
def test_overall_null_pct():
    df = uu.parse_bytes("export.csv", CSV)
    # 9 cells, 1 null (the blank city) -> 11.1%
    assert uu.overall_null_pct(df) == pytest.approx(11.1, abs=0.1)


def test_null_pct_is_zero_for_complete_frame():
    assert uu.overall_null_pct(pd.DataFrame({"a": [1, 2]})) == 0.0


def test_column_summary_shape_and_values():
    summary = uu.column_summary(uu.parse_bytes("export.csv", CSV))
    assert list(summary.columns) == [
        "Column", "Type", "Non-Null", "Null Count", "Null %"
    ]
    assert len(summary) == 3
    city = summary[summary["Column"] == "city"].iloc[0]
    assert city["Null Count"] == 1
    assert city["Non-Null"] == 2


def test_numeric_and_categorical_split():
    df = uu.parse_bytes("export.csv", CSV)
    assert uu.numeric_columns(df) == ["visits"]
    assert "city" in uu.categorical_columns(df)


# ---------------------------------------------------------------------- flags
def test_flags_empty_column():
    df = pd.DataFrame({"a": [1, 2], "blank": [None, None]})
    assert any("entirely empty" in f for f in uu.quality_flags(df))


def test_flags_duplicate_rows():
    df = pd.DataFrame({"a": [1, 1], "b": [2, 2]})
    assert any("duplicated" in f for f in uu.quality_flags(df))


def test_clean_frame_has_no_flags():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    assert uu.quality_flags(df) == []