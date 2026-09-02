"""Automated Data Ingestion, Cleaning, Aggregation, and Output Pipeline.

This pipeline ingests raw data files, cleans and validates records,
computes segment-level aggregations, and outputs processed datasets.
It supports parameters via CLI arguments or JSON configuration files,
logs all stages with timestamps, and is scheduled via GitHub Actions.
"""

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

# ---------------------------------------------------------------- Logging Setup ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# --------------------------------------------------------------- Pipeline Stages ----
def ingest(path: str) -> pd.DataFrame:
    """Ingest raw dataset from the given file path.
    
    Args:
        path: Path to the input file (CSV or JSON).
        
    Returns:
        pd.DataFrame: Ingested raw data.
    """
    logger.info("Ingesting: " + str(path))
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found at: {path}")

    if file_path.suffix.lower() == ".json":
        df = pd.read_json(file_path)
    else:
        df = pd.read_csv(file_path)

    logger.info("Rows ingested: " + str(len(df)))
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean raw DataFrame by removing missing values and invalid records.
    
    Supports standard e-commerce schemas (customer_id, amount) as well as
    StreakForge member/subscription data schemas (member_id, amount_paid_inr).
    
    Args:
        df: Ingested raw DataFrame.
        
    Returns:
        pd.DataFrame: Cleaned DataFrame.
    """
    logger.info("Cleaning...")
    initial = len(df)
    cleaned_df = df.copy()

    # Case 1: Standard e-commerce schema (customer_id, amount)
    if "customer_id" in cleaned_df.columns and "amount" in cleaned_df.columns:
        cleaned_df = cleaned_df.dropna(subset=["customer_id", "amount"])
        cleaned_df["amount"] = pd.to_numeric(cleaned_df["amount"], errors="coerce")
        cleaned_df = cleaned_df.dropna(subset=["amount"])
        cleaned_df = cleaned_df[cleaned_df["amount"] > 0]

    # Case 2: StreakForge / Gym subscription schema (member_id, amount_paid_inr)
    elif "member_id" in cleaned_df.columns and "amount_paid_inr" in cleaned_df.columns:
        cleaned_df = cleaned_df.dropna(subset=["member_id", "amount_paid_inr"])
        cleaned_df["amount_paid_inr"] = pd.to_numeric(cleaned_df["amount_paid_inr"], errors="coerce")
        cleaned_df = cleaned_df.dropna(subset=["amount_paid_inr"])
        cleaned_df = cleaned_df[cleaned_df["amount_paid_inr"] > 0]

    # Case 3: Generic dataset fallback
    else:
        # Drop rows where all elements are NaN
        cleaned_df = cleaned_df.dropna(how="all")
        # If numeric columns exist, ensure at least one positive value
        num_cols = cleaned_df.select_dtypes(include="number").columns
        if len(num_cols) > 0:
            primary_num = num_cols[0]
            cleaned_df[primary_num] = pd.to_numeric(cleaned_df[primary_num], errors="coerce")
            cleaned_df = cleaned_df.dropna(subset=[primary_num])
            cleaned_df = cleaned_df[cleaned_df[primary_num] > 0]

    logger.info("Cleaned: " + str(initial) + " -> " + str(len(cleaned_df)))
    return cleaned_df


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate cleaned dataset by segment to compute business metrics.
    
    Args:
        df: Cleaned DataFrame.
        
    Returns:
        pd.DataFrame: Aggregated summary DataFrame.
    """
    logger.info("Aggregating...")

    if df.empty:
        logger.warning("Empty DataFrame provided for aggregation.")
        return pd.DataFrame(columns=["segment", "revenue", "orders"])

    # Case 1: Standard segment + amount schema
    if "segment" in df.columns and "amount" in df.columns:
        order_col = "order_id" if "order_id" in df.columns else ("customer_id" if "customer_id" in df.columns else df.columns[0])
        agg = df.groupby("segment").agg(
            revenue=("amount", "sum"),
            orders=(order_col, "count")
        ).reset_index()

    # Case 2: StreakForge subscription schema (membership_type / plan_type + amount_paid_inr)
    elif ("membership_type" in df.columns or "plan_type" in df.columns) and "amount_paid_inr" in df.columns:
        seg_col = "membership_type" if "membership_type" in df.columns else "plan_type"
        id_col = "renewal_id" if "renewal_id" in df.columns else ("member_id" if "member_id" in df.columns else df.columns[0])
        agg = df.groupby(seg_col).agg(
            revenue=("amount_paid_inr", "sum"),
            orders=(id_col, "count")
        ).reset_index()
        agg = agg.rename(columns={seg_col: "segment"})

    # Case 3: Generic fallback - group by first non-numeric column
    else:
        cat_cols = df.select_dtypes(exclude="number").columns
        num_cols = df.select_dtypes(include="number").columns
        
        group_col = cat_cols[0] if len(cat_cols) > 0 else df.columns[0]
        val_col = num_cols[0] if len(num_cols) > 0 else df.columns[-1]
        
        agg = df.groupby(group_col).agg(
            revenue=(val_col, "sum"),
            orders=(df.columns[0], "count")
        ).reset_index()
        agg = agg.rename(columns={group_col: "segment"})

    logger.info("Segments: " + str(len(agg)))
    return agg


def output(df: pd.DataFrame, agg: pd.DataFrame, out_dir: str) -> Tuple[str, str]:
    """Write cleaned and aggregated datasets to output directory.
    
    Args:
        df: Cleaned DataFrame.
        agg: Aggregated DataFrame.
        out_dir: Destination folder path.
        
    Returns:
        Tuple[str, str]: Paths to the written cleaned and aggregated CSV files.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    cleaned_file = out_path / "cleaned.csv"
    aggregated_file = out_path / "aggregated.csv"

    df.to_csv(cleaned_file, index=False)
    agg.to_csv(aggregated_file, index=False)

    logger.info("Output written to: " + str(out_dir))
    logger.info("Pipeline complete")
    return str(cleaned_file), str(aggregated_file)


# -------------------------------------------------------------- Execution Flow ----
def load_config(config_path: str) -> dict:
    """Load configuration settings from a JSON file.
    
    Args:
        config_path: Path to configuration file.
        
    Returns:
        dict: Configuration dictionary.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found at: {config_path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_pipeline(input_path: str, output_dir: str = "output") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Execute complete end-to-end pipeline: ingest -> clean -> aggregate -> output.
    
    Args:
        input_path: Path to input data file.
        output_dir: Destination output directory.
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (cleaned_df, aggregated_df)
    """
    raw = ingest(input_path)
    cleaned_df = clean(raw)
    aggregated_df = aggregate(cleaned_df)
    output(cleaned_df, aggregated_df, output_dir)
    return cleaned_df, aggregated_df


def main():
    """Parse CLI arguments or config and trigger pipeline execution."""
    parser = argparse.ArgumentParser(
        description="Run automated data ingestion, cleaning, aggregation, and export pipeline."
    )
    parser.add_argument(
        "--input", "-i",
        help="Path to the input CSV/JSON file to process."
    )
    parser.add_argument(
        "--output", "-o",
        default="output",
        help="Destination directory for output CSVs (default: output)."
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to an optional JSON configuration file containing input/output paths."
    )

    args = parser.parse_args()

    input_path = args.input
    output_dir = args.output

    # Load from config file if provided
    if args.config:
        logger.info("Loading configuration from: " + str(args.config))
        config = load_config(args.config)
        if not input_path and "input" in config:
            input_path = config["input"]
        if args.output == "output" and "output" in config:
            output_dir = config["output"]

    if not input_path:
        parser.error("Input file path must be specified via --input argument or --config file.")

    run_pipeline(input_path=input_path, output_dir=output_dir)


if __name__ == "__main__":
    main()
