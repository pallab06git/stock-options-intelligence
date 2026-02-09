# © 2025 Pallab Basu Roy. All rights reserved.
# This source code is proprietary and confidential.
# Unauthorized copying, modification, or commercial use is strictly prohibited.
# Repository: https://github.com/pallab06/stock-options-intelligence

"""
SPY Stock Data Ingestion Module (TEST Mode)

Fetches SPY daily OHLC aggregate data from Polygon.io REST API.
Granularity: Daily bars (coarse-grained for testing, minimal API quota usage).

Usage:
    df = fetch(days_back=30)
    save(df, output_dir="data/stocks/2026-02-07")
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch(days_back: int = 30) -> pd.DataFrame:
    """
    Fetch SPY daily OHLC aggregate data from Polygon.io.

    Args:
        days_back: Number of days to look back from today (default: 30)

    Returns:
        pandas DataFrame with columns: timestamp, open, high, low, close, volume

    Raises:
        ValueError: If POLYGON_API_KEY environment variable is not set
        RuntimeError: If API rate limit is hit (HTTP 429)
        requests.HTTPError: If API request fails
    """
    api_key = os.environ.get("POLYGON_API_KEY")
    if not api_key:
        logger.error("POLYGON_API_KEY environment variable not set")
        raise ValueError("POLYGON_API_KEY environment variable is required")

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    # Format dates for API (YYYY-MM-DD)
    from_date = start_date.strftime("%Y-%m-%d")
    to_date = end_date.strftime("%Y-%m-%d")

    # Polygon.io aggregates endpoint for daily bars
    url = f"https://api.polygon.io/v2/aggs/ticker/SPY/range/1/day/{from_date}/{to_date}"

    params = {
        "adjusted": "true",
        "sort": "asc",
        "apiKey": api_key
    }

    logger.info(f"Fetching SPY daily data from {from_date} to {to_date}")

    try:
        response = requests.get(url, params=params, timeout=30)

        # Rate-limit guard: detect HTTP 429
        if response.status_code == 429:
            logger.error("Rate limit hit: HTTP 429 from Polygon")
            raise RuntimeError("Polygon API rate limit exceeded")

        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise

    try:
        data = response.json()
    except ValueError as e:
        logger.error(f"Malformed JSON response: {e}")
        raise

    # Empty API response guard
    if "results" not in data or not data["results"]:
        logger.warning(
            f"No stock data returned for SPY from {from_date} to {to_date}"
        )
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    results = data["results"]

    # Convert to DataFrame
    try:
        records = []
        for bar in results:
            records.append({
                "timestamp": datetime.fromtimestamp(bar["t"] / 1000),  # Convert ms to datetime
                "open": bar["o"],
                "high": bar["h"],
                "low": bar["l"],
                "close": bar["c"],
                "volume": bar["v"]
            })
        df = pd.DataFrame(records)
    except (KeyError, TypeError) as e:
        logger.error(f"Malformed API response structure: {e}")
        raise ValueError(f"API response missing required fields: {e}")

    # Empty DataFrame guard
    if df.empty:
        logger.warning("Constructed DataFrame is empty after normalization")
        return df

    logger.info(f"Successfully fetched {len(df)} rows of SPY data")

    return df


def save(df: pd.DataFrame, output_dir: str = None, overwrite: bool = False) -> bool:
    """
    Save DataFrame to CSV file with deterministic filename based on date range.

    Args:
        df: DataFrame with stock price data
        output_dir: Directory path to save CSV file (default: data/stocks/YYYY-MM-DD/)
        overwrite: If True, overwrite existing file; if False, skip if exists (default: False)

    Returns:
        bool: True if file was written, False if write was skipped

    Raises:
        ValueError: If DataFrame is missing required columns
    """
    # Empty-write protection
    if df.empty:
        logger.warning("DataFrame is empty, skipping file write")
        return False

    # Schema enforcement
    expected_columns = ["timestamp", "open", "high", "low", "close", "volume"]
    missing_columns = set(expected_columns) - set(df.columns)
    if missing_columns:
        logger.error(f"DataFrame missing required columns: {missing_columns}")
        raise ValueError(f"DataFrame missing required columns: {missing_columns}")

    # Enforce column order
    df = df[expected_columns]

    # Use date-based directory structure if not specified
    if output_dir is None:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        output_dir = f"data/stocks/{today}"

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate deterministic filename from DataFrame timestamps
    from_date = df["timestamp"].min().strftime("%Y-%m-%d")
    to_date = df["timestamp"].max().strftime("%Y-%m-%d")
    filename = f"spy_daily_{from_date}_{to_date}.csv"
    filepath = output_path / filename

    # Idempotency check
    if filepath.exists() and not overwrite:
        logger.warning(f"File already exists, skipped write: {filepath}")
        return False

    # Save to CSV
    df.to_csv(filepath, index=False)
    logger.info(f"Saved {len(df)} rows to: {filepath}")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch and save SPY daily stock price data"
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=30,
        help="Number of days to look back (default: 30)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for CSV file (default: data/stocks/YYYY-MM-DD/)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing file if it exists",
    )

    args = parser.parse_args()

    try:
        df = fetch(days_back=args.days_back)
        saved = save(df, output_dir=args.output_dir, overwrite=args.overwrite)

        if saved:
            print(f"✓ Successfully fetched and saved {len(df)} rows of SPY data")
        else:
            print(
                f"✓ Successfully fetched {len(df)} rows of SPY data "
                "(existing file, skipped write)"
            )
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
