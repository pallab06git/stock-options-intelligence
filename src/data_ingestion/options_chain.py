# © 2025 Pallab Basu Roy. All rights reserved.
# This source code is proprietary and confidential.
# Unauthorized copying, modification, or commercial use is strictly prohibited.
# Repository: https://github.com/pallab06/stock-options-intelligence

"""
SPY Options Chain Data Ingestion Module (TEST Mode)

Fetches SPY options contracts from Polygon.io REST API.
Granularity: Options contract metadata (strike, expiration, type).

Usage:
    df = fetch(symbol="SPY", expiration_date="2026-02-14")
    save(df, output_dir="data/options/2026-02-09")
"""

import os
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch(
    symbol: str = "SPY",
    expiration_date: str | None = None,
    contract_type: str | None = None,
) -> pd.DataFrame:
    """
    Fetch SPY options contracts from Polygon.io.

    Args:
        symbol: Underlying ticker symbol (default: "SPY")
        expiration_date: Expiration date filter in YYYY-MM-DD format (optional)
        contract_type: Option type filter - "call" or "put" (optional)

    Returns:
        pandas DataFrame with columns: contract_symbol, underlying_symbol,
        expiration_date, strike_price, option_type

    Raises:
        ValueError: If POLYGON_API_KEY environment variable is not set
        RuntimeError: If API rate limit is hit (HTTP 429)
        requests.HTTPError: If API request fails
    """
    api_key = os.environ.get("POLYGON_API_KEY")
    if not api_key:
        logger.error("POLYGON_API_KEY environment variable not set")
        raise ValueError("POLYGON_API_KEY environment variable is required")

    # Polygon.io options contracts endpoint
    url = "https://api.polygon.io/v3/reference/options/contracts"

    params = {
        "underlying_ticker": symbol,
        "apiKey": api_key
    }

    if expiration_date:
        params["expiration_date"] = expiration_date

    if contract_type:
        params["contract_type"] = contract_type

    logger.info(
        f"Fetching options chain: symbol={symbol}, "
        f"expiration={expiration_date or 'ALL'}, "
        f"type={contract_type or 'ALL'}"
    )

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
            f"No options data returned for {symbol} "
            f"(expiration={expiration_date or 'ALL'}, "
            f"type={contract_type or 'ALL'})"
        )
        return pd.DataFrame(columns=[
            "contract_symbol",
            "underlying_symbol",
            "expiration_date",
            "strike_price",
            "option_type"
        ])

    results = data["results"]

    # Convert to DataFrame
    try:
        records = []
        for contract in results:
            records.append({
                "contract_symbol": contract["ticker"],
                "underlying_symbol": contract["underlying_ticker"],
                "expiration_date": contract["expiration_date"],
                "strike_price": contract["strike_price"],
                "option_type": contract["contract_type"]
            })
        df = pd.DataFrame(records)
    except (KeyError, TypeError) as e:
        logger.error(f"Malformed API response structure: {e}")
        raise ValueError(f"API response missing required fields: {e}")

    # Empty DataFrame guard
    if df.empty:
        logger.warning("Constructed DataFrame is empty after normalization")
        return df

    logger.info(f"Successfully fetched {len(df)} option contracts")

    return df


def save(df: pd.DataFrame, output_dir: str = None, overwrite: bool = False) -> bool:
    """
    Save DataFrame to CSV file with deterministic filename based on parameters.

    Args:
        df: DataFrame with options chain data
        output_dir: Directory path to save CSV file (default: data/options/YYYY-MM-DD/)
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
    expected_columns = [
        "contract_symbol",
        "underlying_symbol",
        "expiration_date",
        "strike_price",
        "option_type"
    ]
    missing_columns = set(expected_columns) - set(df.columns)
    if missing_columns:
        logger.error(f"DataFrame missing required columns: {missing_columns}")
        raise ValueError(f"DataFrame missing required columns: {missing_columns}")

    # Enforce column order
    df = df[expected_columns]

    # Use date-based directory structure if not specified
    if output_dir is None:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        output_dir = f"data/options/{today}"

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate deterministic filename from DataFrame properties
    # Extract symbol from underlying_symbol column
    symbol = df["underlying_symbol"].iloc[0] if not df.empty else "SPY"

    # Determine expiration (single date or ALL)
    unique_expirations = df["expiration_date"].nunique()
    if unique_expirations == 1:
        expiration_str = df["expiration_date"].iloc[0]
    else:
        expiration_str = "ALL"

    # Determine contract type (single type or ALL)
    unique_types = df["option_type"].nunique()
    if unique_types == 1:
        type_str = df["option_type"].iloc[0]
    else:
        type_str = "ALL"

    filename = f"{symbol.lower()}_options_{expiration_str}_{type_str}.csv"
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
        description="Fetch and save SPY options chain data"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="SPY",
        help="Underlying ticker symbol (default: SPY)",
    )
    parser.add_argument(
        "--expiration-date",
        type=str,
        default=None,
        help="Expiration date filter in YYYY-MM-DD format (optional)",
    )
    parser.add_argument(
        "--contract-type",
        type=str,
        default=None,
        choices=["call", "put"],
        help="Option type filter: call or put (optional)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for CSV file (default: data/options/YYYY-MM-DD/)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing file if it exists",
    )

    args = parser.parse_args()

    try:
        df = fetch(
            symbol=args.symbol,
            expiration_date=args.expiration_date,
            contract_type=args.contract_type
        )
        saved = save(df, output_dir=args.output_dir, overwrite=args.overwrite)

        if saved:
            print(f"✓ Successfully fetched and saved {len(df)} option contracts")
        else:
            print(
                f"✓ Successfully fetched {len(df)} option contracts "
                "(existing file, skipped write)"
            )
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
