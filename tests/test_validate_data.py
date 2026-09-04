"""Tests for validate_data.py - the CI schema/quality gate.

Each test builds a tiny schema + CSV in a tmp directory and asserts the
validator exits 0 on good data and 1 on each class of schema drift.
"""

import json

import pandas as pd
import pytest

import validate_data

MINI_SCHEMA = {
    "dataset": "data.csv",
    "min_rows": 3,
    "primary_key": "customer_id",
    "allow_extra_columns": False,
    "columns": {
        "customer_id": {"dtype": "string", "required": True, "unique": True,
                        "max_null_pct": 0},
        "amount": {"dtype": "float", "required": True, "min": 0, "max_null_pct": 0},
        "date": {"dtype": "datetime", "required": True, "max_null_pct": 0},
        "segment": {"dtype": "string", "required": True,
                    "allowed": ["Premium", "Standard"], "max_null_pct": 0},
    },
}

VALID_ROWS = [
    {"customer_id": "C1", "amount": 150.0, "date": "2024-01-02", "segment": "Premium"},
    {"customer_id": "C2", "amount": 75.5, "date": "2024-01-03", "segment": "Standard"},
    {"customer_id": "C3", "amount": 200.0, "date": "2024-01-04", "segment": "Premium"},
]


def _write(tmp_path, schema, rows):
    df = pd.DataFrame(rows)
    csv_path = tmp_path / "data.csv"
    df.to_csv(csv_path, index=False)
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    report_path = tmp_path / "report.json"
    return csv_path, schema_path, report_path


def _run(tmp_path, schema, rows):
    csv_path, schema_path, report_path = _write(tmp_path, schema, rows)
    code = validate_data.main(
        [str(csv_path), "--schema", str(schema_path), "--report", str(report_path)]
    )
    return code, report_path


def test_all_checks_pass(tmp_path):
    code, report_path = _run(tmp_path, MINI_SCHEMA, VALID_ROWS)
    assert code == 0
    report = json.loads(report_path.read_text())
    assert report["status"] == "PASS"
    assert report["summary"]["failed"] == 0


def test_missing_required_column_fails(tmp_path):
    schema = json.loads(json.dumps(MINI_SCHEMA))
    rows = [{k: v for k, v in r.items() if k != "amount"} for r in VALID_ROWS]
    code, report_path = _run(tmp_path, schema, rows)
    assert code == 1
    report = json.loads(report_path.read_text())
    required = [c for c in report["checks"] if c["check"] == "Required columns"][0]
    assert required["status"] == "FAIL"
    assert any("Missing required columns: amount" in e for e in required["errors"])


def test_unexpected_column_fails(tmp_path):
    schema = json.loads(json.dumps(MINI_SCHEMA))
    rows = [dict(r, cust_id=r["customer_id"]) for r in VALID_ROWS]
    code, _ = _run(tmp_path, schema, rows)
    assert code == 1


def test_rename_hint_reported(tmp_path):
    schema = json.loads(json.dumps(MINI_SCHEMA))
    rows = [
        {("cust_id" if k == "customer_id" else k): v for k, v in r.items()}
        for r in VALID_ROWS
    ]
    code, report_path = _run(tmp_path, schema, rows)
    assert code == 1
    report = json.loads(report_path.read_text())
    required = [c for c in report["checks"] if c["check"] == "Required columns"][0]
    assert any("Possible rename detected" in e for e in required["errors"])


def test_wrong_dtype_fails(tmp_path):
    schema = json.loads(json.dumps(MINI_SCHEMA))
    rows = [dict(r, amount=f"{r['amount']} INR") for r in VALID_ROWS]
    code, report_path = _run(tmp_path, schema, rows)
    assert code == 1
    report = json.loads(report_path.read_text())
    dtypes = [c for c in report["checks"] if c["check"] == "Data types"][0]
    assert any("expected dtype 'float'" in e for e in dtypes["errors"])


def test_row_count_below_minimum_fails(tmp_path):
    schema = json.loads(json.dumps(MINI_SCHEMA))
    code, report_path = _run(tmp_path, schema, VALID_ROWS[:2])
    assert code == 1
    report = json.loads(report_path.read_text())
    rows_check = [c for c in report["checks"] if c["check"] == "Minimum row count"][0]
    assert any("below minimum 3" in e for e in rows_check["errors"])


def test_fully_null_column_fails(tmp_path):
    schema = json.loads(json.dumps(MINI_SCHEMA))
    rows = [dict(r, segment=None) for r in VALID_ROWS]
    code, report_path = _run(tmp_path, schema, rows)
    assert code == 1
    report = json.loads(report_path.read_text())
    nulls = [c for c in report["checks"] if c["check"] == "Null quality"][0]
    assert any("Fully null columns: segment" in e for e in nulls["errors"])


def test_duplicate_primary_key_fails(tmp_path):
    schema = json.loads(json.dumps(MINI_SCHEMA))
    rows = [dict(r, customer_id="C1") for r in VALID_ROWS]
    code, report_path = _run(tmp_path, schema, rows)
    assert code == 1
    report = json.loads(report_path.read_text())
    pk = [c for c in report["checks"] if c["check"] == "Primary key uniqueness"][0]
    assert any("duplicate" in e for e in pk["errors"])


def test_out_of_domain_value_fails(tmp_path):
    schema = json.loads(json.dumps(MINI_SCHEMA))
    rows = [dict(r, segment="Enterprise") for r in VALID_ROWS[:1]] + VALID_ROWS[1:]
    code, report_path = _run(tmp_path, schema, rows)
    assert code == 1
    report = json.loads(report_path.read_text())
    domain = [c for c in report["checks"] if c["check"] == "Domain / range"][0]
    assert any("outside allowed set" in e for e in domain["errors"])


def test_missing_dataset_file_exits_1(tmp_path):
    schema = json.loads(json.dumps(MINI_SCHEMA))
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    code = validate_data.main(
        [str(tmp_path / "nope.csv"), "--schema", str(schema_path),
         "--report", str(tmp_path / "report.json")]
    )
    assert code == 1
