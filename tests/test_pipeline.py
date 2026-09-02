"""Unit tests for the automated data pipeline."""

import json
from pathlib import Path
import pandas as pd
import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pipeline as pl


@pytest.fixture
def sample_raw_csv(tmp_path):
    csv_content = (
        "customer_id,order_id,amount,segment\n"
        "C-1,O-1,100.0,Gold\n"
        "C-2,O-2,50.0,Silver\n"
        ",O-3,20.0,Gold\n"
        "C-4,O-4,-10.0,Bronze\n"
        "C-5,O-5,0,Silver\n"
        "C-6,O-6,200.0,Gold\n"
    )
    file_path = tmp_path / "raw_test.csv"
    file_path.write_text(csv_content)
    return str(file_path)


@pytest.fixture
def sample_config_file(tmp_path, sample_raw_csv):
    out_dir = str(tmp_path / "config_output")
    config = {
        "input": sample_raw_csv,
        "output": out_dir
    }
    config_file = tmp_path / "test_config.json"
    config_file.write_text(json.dumps(config))
    return str(config_file), out_dir


def test_ingest_valid_csv(sample_raw_csv):
    df = pl.ingest(sample_raw_csv)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 6
    assert list(df.columns) == ["customer_id", "order_id", "amount", "segment"]


def test_ingest_missing_file():
    with pytest.raises(FileNotFoundError):
        pl.ingest("non_existent_file.csv")


def test_clean_filters_nulls_and_non_positive_amounts(sample_raw_csv):
    raw = pl.ingest(sample_raw_csv)
    cleaned = pl.clean(raw)
    
    assert len(cleaned) == 3
    assert set(cleaned["customer_id"]) == {"C-1", "C-2", "C-6"}
    assert (cleaned["amount"] > 0).all()
    assert cleaned["customer_id"].notna().all()


def test_aggregate_metrics(sample_raw_csv):
    raw = pl.ingest(sample_raw_csv)
    cleaned = pl.clean(raw)
    agg = pl.aggregate(cleaned)
    
    assert isinstance(agg, pd.DataFrame)
    assert list(agg.columns) == ["segment", "revenue", "orders"]
    
    gold_row = agg[agg["segment"] == "Gold"].iloc[0]
    assert gold_row["revenue"] == 300.0
    assert gold_row["orders"] == 2
    
    silver_row = agg[agg["segment"] == "Silver"].iloc[0]
    assert silver_row["revenue"] == 50.0
    assert silver_row["orders"] == 1


def test_output_creates_csv_files(tmp_path, sample_raw_csv):
    raw = pl.ingest(sample_raw_csv)
    cleaned = pl.clean(raw)
    agg = pl.aggregate(cleaned)
    
    out_dir = str(tmp_path / "out_test")
    cleaned_path, agg_path = pl.output(cleaned, agg, out_dir)
    
    assert Path(cleaned_path).exists()
    assert Path(agg_path).exists()
    
    df_c = pd.read_csv(cleaned_path)
    df_a = pd.read_csv(agg_path)
    
    assert len(df_c) == 3
    assert len(df_a) == 2


def test_run_pipeline_end_to_end(tmp_path, sample_raw_csv):
    out_dir = str(tmp_path / "e2e_output")
    cleaned, agg = pl.run_pipeline(sample_raw_csv, out_dir)
    
    assert len(cleaned) == 3
    assert len(agg) == 2
    assert (Path(out_dir) / "cleaned.csv").exists()
    assert (Path(out_dir) / "aggregated.csv").exists()


def test_config_loading(sample_config_file):
    config_path, expected_out = sample_config_file
    config = pl.load_config(config_path)
    
    assert "input" in config
    assert config["output"] == expected_out
