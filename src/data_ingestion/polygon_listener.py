# © 2025 Pallab Basu Roy. All rights reserved.
# This source code is proprietary and confidential.
# Unauthorized copying, modification, or commercial use is strictly prohibited.
# Repository: https://github.com/pallab06/stock-options-intelligence

"""
Polygon.io Real-Time SPY Data Listener Service

Continuously fetches minute-level SPY aggregates from Polygon.io,
maintains processing state, and handles data with retry logic.
"""

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "60"))  # seconds
DATA_PATH = Path(os.getenv("DATA_PATH", "./data"))
LOG_PATH = Path(os.getenv("LOG_PATH", "./logs"))
LPI_FILE = Path(os.getenv("LPI_FILE", "./state/last_processed_index.json"))

# API Configuration
POLYGON_BASE_URL = "https://api.polygon.io/v2/aggs/ticker"
TICKER = "SPY"
TIMESPAN = "minute"
MULTIPLIER = 1

# Retry Configuration
MAX_RETRIES = 5
INITIAL_BACKOFF = 1  # seconds
MAX_BACKOFF = 60  # seconds

# Global flag for graceful shutdown
shutdown_requested = False


def setup_logging() -> logging.Logger:
    """
    Set up logging configuration with file and console handlers

    Returns:
        Configured logger instance
    """
    LOG_PATH.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("polygon_listener")
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    logger.handlers = []

    # File handler
    file_handler = logging.FileHandler(LOG_PATH / "listener.log")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()


def signal_handler(signum: int, frame: Any) -> None:
    """
    Handle shutdown signals (Ctrl+C, SIGTERM)

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    global shutdown_requested
    logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
    shutdown_requested = True


def load_lpi() -> Optional[int]:
    """
    Load the Last Processed Indicator from state file

    Returns:
        Last processed timestamp in milliseconds, or None if not exists
    """
    if not LPI_FILE.exists():
        logger.info("No LPI file found. Starting fresh.")
        return None

    try:
        with open(LPI_FILE, "r") as f:
            data = json.load(f)
            timestamp = data.get("last_processed_timestamp")
            if timestamp:
                logger.info(
                    f"Loaded LPI: {timestamp} ({epoch_to_iso(timestamp)})"
                )
            return timestamp
    except json.JSONDecodeError as e:
        logger.error(f"Error reading LPI file: {e}. Starting fresh.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading LPI: {e}")
        return None


def update_lpi(timestamp: int) -> None:
    """
    Update the Last Processed Indicator in state file

    Args:
        timestamp: Unix timestamp in milliseconds
    """
    LPI_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        data = {
            "last_processed_timestamp": timestamp,
            "last_processed_iso": epoch_to_iso(timestamp),
            "updated_at": datetime.utcnow().isoformat(),
        }

        with open(LPI_FILE, "w") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Updated LPI to: {timestamp} ({epoch_to_iso(timestamp)})")
    except Exception as e:
        logger.error(f"Error updating LPI file: {e}")


def epoch_to_iso(timestamp_ms: int) -> str:
    """
    Convert Unix timestamp (milliseconds) to ISO 8601 format

    Args:
        timestamp_ms: Unix timestamp in milliseconds

    Returns:
        ISO 8601 formatted datetime string
    """
    return datetime.utcfromtimestamp(timestamp_ms / 1000).isoformat() + "Z"


def iso_to_epoch(iso_string: str) -> int:
    """
    Convert ISO 8601 datetime string to Unix timestamp (milliseconds)

    Args:
        iso_string: ISO 8601 formatted datetime string

    Returns:
        Unix timestamp in milliseconds
    """
    dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)


def fetch_data(from_time: int, to_time: int, retry_count: int = 0) -> Optional[Dict[str, Any]]:
    """
    Fetch SPY aggregates data from Polygon.io API with retry logic

    Args:
        from_time: Start timestamp (milliseconds)
        to_time: End timestamp (milliseconds)
        retry_count: Current retry attempt number

    Returns:
        API response data dict, or None if failed
    """
    if not POLYGON_API_KEY:
        logger.error("POLYGON_API_KEY not found in environment variables")
        return None

    # Convert milliseconds to date strings (YYYY-MM-DD)
    from_date = datetime.utcfromtimestamp(from_time / 1000).strftime("%Y-%m-%d")
    to_date = datetime.utcfromtimestamp(to_time / 1000).strftime("%Y-%m-%d")

    url = f"{POLYGON_BASE_URL}/{TICKER}/range/{MULTIPLIER}/{TIMESPAN}/{from_date}/{to_date}"
    params = {
        "apiKey": POLYGON_API_KEY,
        "adjusted": "true",
        "sort": "asc",
        "limit": 50000,  # Maximum results per request
    }

    try:
        logger.info(f"Fetching data from {from_date} to {to_date}...")
        response = requests.get(url, params=params, timeout=30)

        # Check for rate limiting
        if response.status_code == 429:
            logger.warning("Rate limit exceeded. Implementing backoff...")
            if retry_count < MAX_RETRIES:
                backoff = min(INITIAL_BACKOFF * (2 ** retry_count), MAX_BACKOFF)
                logger.info(f"Retrying in {backoff} seconds... (Attempt {retry_count + 1}/{MAX_RETRIES})")
                time.sleep(backoff)
                return fetch_data(from_time, to_time, retry_count + 1)
            else:
                logger.error("Max retries reached. Giving up.")
                return None

        response.raise_for_status()
        data = response.json()

        # Log response metadata
        results_count = data.get("resultsCount", 0)
        logger.info(f"Received {results_count} records from Polygon.io")

        return data

    except requests.exceptions.Timeout:
        logger.error("Request timed out")
        if retry_count < MAX_RETRIES:
            backoff = min(INITIAL_BACKOFF * (2 ** retry_count), MAX_BACKOFF)
            logger.info(f"Retrying in {backoff} seconds...")
            time.sleep(backoff)
            return fetch_data(from_time, to_time, retry_count + 1)
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        if retry_count < MAX_RETRIES:
            backoff = min(INITIAL_BACKOFF * (2 ** retry_count), MAX_BACKOFF)
            logger.info(f"Retrying in {backoff} seconds...")
            time.sleep(backoff)
            return fetch_data(from_time, to_time, retry_count + 1)
        return None

    except Exception as e:
        logger.error(f"Unexpected error during fetch: {e}")
        return None


def process_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process raw records by converting timestamps and enriching data

    Args:
        records: List of raw record dictionaries from Polygon.io

    Returns:
        List of processed record dictionaries with ISO timestamps
    """
    processed = []

    for record in records:
        try:
            # Convert timestamp to ISO format
            timestamp_ms = record.get("t")
            iso_timestamp = epoch_to_iso(timestamp_ms)

            # Create enriched record
            processed_record = {
                "timestamp_iso": iso_timestamp,
                "timestamp_epoch": timestamp_ms,
                "ticker": TICKER,
                "open": record.get("o"),
                "high": record.get("h"),
                "low": record.get("l"),
                "close": record.get("c"),
                "volume": record.get("v"),
                "vwap": record.get("vw"),
                "transactions": record.get("n"),
            }

            processed.append(processed_record)

        except Exception as e:
            logger.error(f"Error processing record: {e}")
            logger.debug(f"Problematic record: {record}")
            continue

    return processed


def print_records(records: List[Dict[str, Any]]) -> None:
    """
    Print formatted records to console

    Args:
        records: List of processed record dictionaries
    """
    if not records:
        return

    print("\n" + "=" * 80)
    print(f"📊 NEW SPY DATA - {len(records)} records")
    print("=" * 80)

    for record in records:
        print(json.dumps(record, indent=2))
        print("-" * 80)

    print("=" * 80 + "\n")


def calculate_time_range(last_timestamp: Optional[int]) -> tuple[int, int]:
    """
    Calculate the time range for the next data fetch

    Args:
        last_timestamp: Last processed timestamp in milliseconds, or None

    Returns:
        Tuple of (from_time, to_time) in milliseconds
    """
    now = datetime.utcnow()
    to_time = int(now.timestamp() * 1000)

    if last_timestamp is None:
        # If no LPI, fetch last 24 hours
        from_time = int((now - timedelta(hours=24)).timestamp() * 1000)
        logger.info("No previous data. Fetching last 24 hours.")
    else:
        # Fetch from last timestamp + 1 minute
        from_time = last_timestamp + (60 * 1000)

    return from_time, to_time


def main() -> None:
    """
    Main listener loop
    """
    global shutdown_requested

    logger.info("=" * 80)
    logger.info("🚀 Polygon.io SPY Listener Service Starting")
    logger.info("=" * 80)
    logger.info(f"Ticker: {TICKER}")
    logger.info(f"Fetch Interval: {FETCH_INTERVAL} seconds")
    logger.info(f"LPI File: {LPI_FILE}")
    logger.info(f"Log Path: {LOG_PATH / 'listener.log'}")
    logger.info("=" * 80)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Validate API key
    if not POLYGON_API_KEY:
        logger.error("❌ POLYGON_API_KEY not found in environment variables")
        logger.error("Please set POLYGON_API_KEY in your .env file")
        sys.exit(1)

    try:
        while not shutdown_requested:
            # Load last processed timestamp
            last_timestamp = load_lpi()

            # Calculate time range
            from_time, to_time = calculate_time_range(last_timestamp)

            # Fetch data
            data = fetch_data(from_time, to_time)

            if data is None:
                logger.warning("Failed to fetch data. Waiting before retry...")
                time.sleep(FETCH_INTERVAL)
                continue

            # Extract results
            results = data.get("results", [])

            if not results:
                if last_timestamp:
                    iso_time = epoch_to_iso(last_timestamp)
                    print(f"✅ No new data since {iso_time}")
                    logger.info(f"No new records. Last processed: {iso_time}")
                else:
                    print("✅ No data available in the requested time range")
                    logger.info("No data available")
            else:
                # Filter records newer than last timestamp
                if last_timestamp:
                    results = [r for r in results if r.get("t") > last_timestamp]

                if results:
                    # Process records
                    processed_records = process_records(results)

                    # Print to console
                    print_records(processed_records)

                    # Update LPI with the latest timestamp
                    latest_timestamp = max(r.get("t") for r in results)
                    update_lpi(latest_timestamp)

                    logger.info(
                        f"✅ Processed {len(processed_records)} new records. "
                        f"Latest: {epoch_to_iso(latest_timestamp)}"
                    )
                else:
                    if last_timestamp:
                        iso_time = epoch_to_iso(last_timestamp)
                        print(f"✅ No new data since {iso_time}")
                        logger.info(f"No new records after filtering. Last processed: {iso_time}")

            # Wait before next fetch
            if not shutdown_requested:
                logger.info(f"⏳ Waiting {FETCH_INTERVAL} seconds until next fetch...")
                time.sleep(FETCH_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
    finally:
        logger.info("=" * 80)
        logger.info("🛑 Polygon.io SPY Listener Service Stopped")
        logger.info("=" * 80)


if __name__ == "__main__":
    main()
