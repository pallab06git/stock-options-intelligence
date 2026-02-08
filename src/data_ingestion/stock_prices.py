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
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error("Request timed out after 30 seconds")
        raise
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            logger.error("Rate limit exceeded (HTTP 429)")
        else:
            logger.error(f"HTTP error occurred: {e}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise

    data = response.json()

    # Handle empty or missing results
    if "results" not in data or not data["results"]:
        logger.warning(f"No results returned from API (likely non-trading days or invalid date range)")
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    results = data["results"]
    logger.info(f"Received {len(results)} daily bars")

    # Convert to DataFrame
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
    logger.info(f"Successfully processed {len(df)} rows")

    return df


def save(df: pd.DataFrame, output_dir: str = None) -> None:
    """
    Save DataFrame to CSV file with timestamp in filename.

    Args:
        df: DataFrame with stock price data
        output_dir: Directory path to save CSV file (default: data/stocks/YYYY-MM-DD/)

    Returns:
        None
    """
    if df.empty:
        logger.warning("DataFrame is empty, skipping save")
        return

    # Use date-based directory structure if not specified
    if output_dir is None:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        output_dir = f"data/stocks/{today}"

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"spy_daily_{timestamp}.csv"
    filepath = output_path / filename

    # Save to CSV
    df.to_csv(filepath, index=False)
    logger.info(f"Saved {len(df)} rows to {filepath}")
