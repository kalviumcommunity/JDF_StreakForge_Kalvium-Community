"""Automated data schema & quality validation for StreakForge.

Runs a declarative contract (schema.json) against a processed CSV and fails
the CI pipeline with exit code 1 when any check fails. Kept separate from the
GitHub Actions workflow so the validation logic stays maintainable and testable.

Usage:
    python validate_data.py data/processed/member_behaviour_summary.csv \
        --schema schema.json [--report validation_report.json]

Exit codes:
    0  -> all checks passed
    1  -> validation failed (schema drift, bad dtypes, nulls, etc.)
    2  -> usage error (missing/argument errors, missing files)
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


# --------------------------------------------------------------- dtype helpers ---
def is_string_dtype(series: pd.Series) -> bool:
    return pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)


def is_float_dtype(series: pd.Series) -> bool:
    # float64 columns, and object columns of pure floats (e.g. round-tripped CSV)
    if pd.api.types.is_float_dtype(series):
        return True
    if is_string_dtype(series):
        converted = pd.to_numeric(series.dropna(), errors="coerce")
        return converted.notna().all() and not converted.empty
    return False


def is_int_dtype(series: pd.Series) -> bool:
    return pd.api.types.is_integer_dtype(series)


def is_bool_dtype(series: pd.Series) -> bool:
    return pd.api.types.is_bool_dtype(series)


def is_datetime_dtype(series: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    # object column holding parseable dates is acceptable
    if is_string_dtype(series):
        parsed = pd.to_datetime(series.dropna(), errors="coerce", dayfirst=True, format="mixed")
        return parsed.notna().all() and not parsed.empty
    return False


DTYPE_CHECKS = {
    "string": is_string_dtype,
    "float": is_float_dtype,
    "int": is_int_dtype,
    "bool": is_bool_dtype,
    "datetime": is_datetime_dtype,
}

# ------------------------------------------------------------------ helpers ----
def load_schema(schema_path: Path) -> dict:
    with open(schema_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _null_pct(series: pd.Series) -> float:
    if len(series) == 0:
        return 100.0
    return float(series.isnull().sum()) / len(series) * 100.0


# --------------------------------------------------------------- checks -------
def check_required_columns(df: pd.DataFrame, schema: dict) -> list:
    """Required columns present; no unexpected columns when the contract is strict."""
    errors = []
    expected = list(schema["columns"].keys())
    missing = [c for c in expected if c not in df.columns]

    if missing:
        errors.append("Missing required columns: " + ", ".join(missing))

    if not schema.get("allow_extra_columns", False):
        unexpected = [c for c in df.columns if c not in expected]
        if unexpected:
            errors.append("Unexpected columns (schema drift): " + ", ".join(unexpected))

    if missing and not schema.get("allow_extra_columns", False):
        unexpected = [c for c in df.columns if c not in expected]
        if unexpected:
            errors.append(
                "Possible rename detected: '" + "', '".join(missing)
                + "' missing while '" + "', '".join(unexpected)
                + "' appeared"
            )
    return errors


def check_dtypes(df: pd.DataFrame, schema: dict) -> list:
    errors = []
    for col, spec in schema["columns"].items():
        if col not in df.columns:
            continue
        expected = spec.get("dtype")
        if not expected or expected not in DTYPE_CHECKS:
            continue
        if not DTYPE_CHECKS[expected](df[col]):
            errors.append(
                f"Column '{col}' expected dtype '{expected}' but got '{df[col].dtype}'"
            )
    return errors


def check_row_count(df: pd.DataFrame, schema: dict) -> list:
    errors = []
    min_rows = schema.get("min_rows", 0)
    if len(df) < min_rows:
        errors.append(
            f"Row count {len(df)} below minimum {min_rows} (possible truncated output)"
        )
    return errors


def check_null_quality(df: pd.DataFrame, schema: dict) -> list:
    errors = []
    fully_null = [c for c in df.columns if df[c].isnull().all()]
    if fully_null:
        errors.append("Fully null columns: " + ", ".join(fully_null))

    for col, spec in schema["columns"].items():
        if col not in df.columns:
            continue
        limit = spec.get("max_null_pct", 0)
        actual = _null_pct(df[col])
        if actual > limit:
            errors.append(
                f"Column '{col}' has {actual:.2f}% nulls, exceeding max {limit}%"
            )
    return errors


def check_primary_key(df: pd.DataFrame, schema: dict) -> list:
    errors = []
    pk = schema.get("primary_key")
    if pk and pk in df.columns:
        dupes = int(df[pk].duplicated().sum())
        if dupes:
            errors.append(
                f"Primary key '{pk}' has {dupes} duplicate value(s); expected unique"
            )
    return errors


def check_domain(df: pd.DataFrame, schema: dict) -> list:
    errors = []
    for col, spec in schema["columns"].items():
        if col not in df.columns:
            continue
        series = df[col]
        non_null = series.dropna()

        allowed = spec.get("allowed")
        if allowed:
            normalized = non_null.astype(str).str.strip()
            offenders = normalized[~normalized.isin(allowed)]
            if not offenders.empty:
                samples = sorted(offenders.unique().tolist())[:10]
                errors.append(
                    f"Column '{col}' has {len(offenders)} value(s) outside allowed set: "
                    + ", ".join(repr(s) for s in samples)
                )

        if "min" in spec and non_null.dtype.kind in "iuf":
            below = int((non_null < spec["min"]).sum())
            if below:
                errors.append(
                    f"Column '{col}' has {below} value(s) below minimum {spec['min']}"
                )
        if "max" in spec and non_null.dtype.kind in "iuf":
            above = int((non_null > spec["max"]).sum())
            if above:
                errors.append(
                    f"Column '{col}' has {above} value(s) above maximum {spec['max']}"
                )
    return errors


# -------------------------------------------------------------- orchestrator ----
CHECKS = [
    ("Required columns", check_required_columns),
    ("Data types", check_dtypes),
    ("Minimum row count", check_row_count),
    ("Null quality", check_null_quality),
    ("Primary key uniqueness", check_primary_key),
    ("Domain / range", check_domain),
]


def run_checks(df: pd.DataFrame, schema: dict) -> dict:
    """Run every check, print PASS/ERROR lines, and return a result dict."""
    results = []
    passed = 0
    failed = 0

    for name, fn in CHECKS:
        errors = fn(df, schema)
        ok = not errors
        if ok:
            passed += 1
            print(f"PASS: {name}")
        else:
            failed += 1
            print(f"FAIL: {name}")
            for e in errors:
                print(f"  ERROR: {e}")
        results.append({"check": name, "status": "PASS" if ok else "FAIL",
                        "errors": errors})

    return {"results": results, "passed": passed, "failed": failed}


def validate(csv_path: Path, schema: dict, report_path: Path | None = None) -> int:
    print("=" * 78)
    print(f"Validating: {csv_path}")
    print(f"Contract:  {schema.get('description', 'schema.json')}")
    print("=" * 78)

    if not csv_path.exists():
        print(f"ERROR: dataset not found at {csv_path}")
        return 1

    df = pd.read_csv(csv_path)
    print(f"Dataset: {len(df)} rows x {df.shape[1]} columns\n")

    result = run_checks(df, schema)

    summary = {
        "dataset": str(csv_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "checks": result["results"],
        "summary": {"total": result["passed"] + result["failed"],
                    "passed": result["passed"],
                    "failed": result["failed"]},
        "status": "PASS" if result["failed"] == 0 else "FAIL",
    }

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
        print(f"\nReport written to {report_path}")

    print("\n" + "=" * 78)
    if result["failed"]:
        print(f"VALIDATION FAILED: {result['passed']} passed, {result['failed']} failed")
        print("=" * 78)
        return 1

    print(f"ALL CHECKS PASSED ({result['passed']}/{result['passed'] + result['failed']})")
    print("=" * 78)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="?", help="CSV file to validate")
    parser.add_argument("--schema", default="schema.json", help="schema contract JSON")
    parser.add_argument("--report", default="validation_report.json",
                        help="where to write the JSON report")
    args = parser.parse_args(argv)

    schema_path = Path(args.schema)
    if not schema_path.exists():
        print(f"ERROR: schema file not found at {schema_path}")
        return 2

    schema = load_schema(schema_path)
    csv_path = Path(args.csv) if args.csv else Path(schema["dataset"])

    return validate(csv_path, schema, Path(args.report))


if __name__ == "__main__":
    sys.exit(main())
