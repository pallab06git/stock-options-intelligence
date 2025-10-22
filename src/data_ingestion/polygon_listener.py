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
import traceback
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
MAX_CONSECUTIVE_EMPTY_RESPONSES = 3  # Shutdown after this many empty responses

# Global flags
shutdown_requested = False
consecutive_empty_responses = 0


class SensitiveDataFilter(logging.Filter):
    """Filter to prevent API keys from being logged"""

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter out sensitive data from log records

        Args:
            record: Log record to filter

        Returns:
            True to allow logging, False to block
        """
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            # Mask API key if present
            if POLYGON_API_KEY and POLYGON_API_KEY in msg:
                record.msg = msg.replace(POLYGON_API_KEY, "***REDACTED***")
            # Mask apiKey parameter in URLs
            record.msg = str(record.msg).replace(f"apiKey={POLYGON_API_KEY}", "apiKey=***REDACTED***")
        return True


def setup_logging() -> logging.Logger:
    """
    Set up logging configuration with file and console handlers
    Includes sensitive data filtering

    Returns:
        Configured logger instance
    """
    LOG_PATH.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("polygon_listener")
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    logger.handlers = []

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s"
    )

    # File handler
    file_handler = logging.FileHandler(LOG_PATH / "listener.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(SensitiveDataFilter())

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(SensitiveDataFilter())

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


def graceful_shutdown(exit_code: int = 0, message: str = "") -> None:
    """
    Perform graceful shutdown with logging

    Args:
        exit_code: Exit code (0 = success, non-zero = error)
        message: Optional shutdown message
    """
    logger.info("=" * 80)
    if message:
        if exit_code == 0:
            logger.info(f"✅ {message}")
        else:
            logger.error(f"❌ {message}")
    logger.info("🛑 Polygon.io SPY Listener Service Stopped")
    logger.info(f"Exit Code: {exit_code}")
    logger.info("=" * 80)
    sys.exit(exit_code)


def load_lpi() -> Optional[int]:
    """
    Load the Last Processed Indicator from state file

    Returns:
        Last processed timestamp in milliseconds, or None if not exists

    Raises:
        Exception: Re-raises critical errors after logging
    """
    try:
        if not LPI_FILE.exists():
            logger.info("No LPI file found. Starting fresh.")
            return None

        with open(LPI_FILE, "r") as f:
            data = json.load(f)
            timestamp = data.get("last_processed_timestamp")
            if timestamp:
                logger.info(f"Loaded LPI: {timestamp} ({epoch_to_iso(timestamp)})")
            return timestamp

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in LPI file: {e}")
        logger.info("Starting fresh due to corrupted LPI file")
        return None

    except PermissionError as e:
        logger.error(f"Permission denied reading LPI file: {e}")
        logger.error(f"Function: load_lpi, Line: {traceback.extract_tb(e.__traceback__)[-1].lineno}")
        graceful_shutdown(1, "Permission error accessing state file")

    except Exception as e:
        logger.error(f"Unexpected error loading LPI: {e}")
        logger.error(f"Function: load_lpi, Line: {traceback.extract_tb(e.__traceback__)[-1].lineno}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        graceful_shutdown(1, "Critical error loading state file")


def update_lpi(timestamp: int) -> None:
    """
    Update the Last Processed Indicator in state file

    Args:
        timestamp: Unix timestamp in milliseconds

    Raises:
        Exception: Re-raises critical errors after logging
    """
    try:
        LPI_FILE.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "last_processed_timestamp": timestamp,
            "last_processed_iso": epoch_to_iso(timestamp),
            "updated_at": datetime.utcnow().isoformat(),
        }

        with open(LPI_FILE, "w") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Updated LPI to: {timestamp} ({epoch_to_iso(timestamp)})")

    except PermissionError as e:
        logger.error(f"Permission denied writing LPI file: {e}")
        logger.error(f"Function: update_lpi, Line: {traceback.extract_tb(e.__traceback__)[-1].lineno}")
        graceful_shutdown(1, "Permission error writing state file")

    except Exception as e:
        logger.error(f"Error updating LPI file: {e}")
        logger.error(f"Function: update_lpi, Line: {traceback.extract_tb(e.__traceback__)[-1].lineno}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Don't shutdown on LPI update errors, just warn
        logger.warning("Continuing without updating LPI. State may be inconsistent.")


def epoch_to_iso(timestamp_ms: int) -> str:
    """
    Convert Unix timestamp (milliseconds) to ISO 8601 format

    Args:
        timestamp_ms: Unix timestamp in milliseconds

    Returns:
        ISO 8601 formatted datetime string
    """
    try:
        return datetime.utcfromtimestamp(timestamp_ms / 1000).isoformat() + "Z"
    except Exception as e:
        logger.error(f"Error converting epoch to ISO: {e}")
        logger.error(f"Function: epoch_to_iso, Line: {traceback.extract_tb(e.__traceback__)[-1].lineno}")
        return "INVALID_TIMESTAMP"


def mask_api_key(url: str) -> str:
    """
    Mask API key in URL for safe logging

    Args:
        url: URL potentially containing API key

    Returns:
        URL with masked API key
    """
    if POLYGON_API_KEY and POLYGON_API_KEY in url:
        return url.replace(POLYGON_API_KEY, "***REDACTED***")
    return url


def fetch_data(from_time: int, to_time: int, retry_count: int = 0) -> Optional[Dict[str, Any]]:
    """
    Fetch SPY aggregates data from Polygon.io API with retry logic

    Args:
        from_time: Start timestamp (milliseconds)
        to_time: End timestamp (milliseconds)
        retry_count: Current retry attempt number

    Returns:
        API response data dict, or None if failed after max retries
    """
    try:
        if not POLYGON_API_KEY:
            logger.error("POLYGON_API_KEY not found in environment variables")
            graceful_shutdown(1, "Missing required API key configuration")

        # Convert milliseconds to date strings (YYYY-MM-DD)
        from_date = datetime.utcfromtimestamp(from_time / 1000).strftime("%Y-%m-%d")
        to_date = datetime.utcfromtimestamp(to_time / 1000).strftime("%Y-%m-%d")

        url = f"{POLYGON_BASE_URL}/{TICKER}/range/{MULTIPLIER}/{TIMESPAN}/{from_date}/{to_date}"
        params = {
            "apiKey": POLYGON_API_KEY,
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000,
        }

        # Log with masked URL
        safe_url = mask_api_key(url)
        logger.info(f"Fetching data from {from_date} to {to_date}... URL: {safe_url}")

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
                logger.error("Max retries reached for rate limiting")
                graceful_shutdown(1, "Max retries exceeded due to rate limiting")

        # Check for authentication errors
        if response.status_code == 401:
            logger.error("Authentication failed. Invalid API key.")
            graceful_shutdown(1, "API authentication failed - check your API key")

        # Check for forbidden
        if response.status_code == 403:
            logger.error("Access forbidden. API key may not have required permissions.")
            graceful_shutdown(1, "API access forbidden - check API key permissions")

        response.raise_for_status()
        data = response.json()

        # Log response metadata (without sensitive data)
        results_count = data.get("resultsCount", 0)
        logger.info(f"Received {results_count} records from Polygon.io")

        return data

    except requests.exceptions.Timeout as e:
        logger.error(f"Request timed out: {e}")
        logger.error(f"Function: fetch_data, Line: {traceback.extract_tb(e.__traceback__)[-1].lineno}")
        if retry_count < MAX_RETRIES:
            backoff = min(INITIAL_BACKOFF * (2 ** retry_count), MAX_BACKOFF)
            logger.info(f"Retrying in {backoff} seconds... (Attempt {retry_count + 1}/{MAX_RETRIES})")
            time.sleep(backoff)
            return fetch_data(from_time, to_time, retry_count + 1)
        else:
            logger.error("Max retries reached for timeout")
            graceful_shutdown(1, "Max retries exceeded due to timeouts")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        logger.error(f"Function: fetch_data, Line: {traceback.extract_tb(e.__traceback__)[-1].lineno}")
        if retry_count < MAX_RETRIES:
            backoff = min(INITIAL_BACKOFF * (2 ** retry_count), MAX_BACKOFF)
            logger.info(f"Retrying in {backoff} seconds... (Attempt {retry_count + 1}/{MAX_RETRIES})")
            time.sleep(backoff)
            return fetch_data(from_time, to_time, retry_count + 1)
        else:
            logger.error("Max retries reached for request errors")
            graceful_shutdown(1, "Max retries exceeded due to network errors")

    except Exception as e:
        logger.error(f"Unexpected error during fetch: {e}")
        logger.error(f"Function: fetch_data, Line: {traceback.extract_tb(e.__traceback__)[-1].lineno}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        graceful_shutdown(1, "Unexpected error during data fetch")


def process_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process raw records by converting timestamps and enriching data

    Args:
        records: List of raw record dictionaries from Polygon.io

    Returns:
        List of processed record dictionaries with ISO timestamps
    """
    processed = []

    try:
        for record in records:
            try:
                # Convert timestamp to ISO format
                timestamp_ms = record.get("t")
                if timestamp_ms is None:
                    logger.warning("Record missing timestamp, skipping")
                    continue

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
                logger.error(f"Error processing individual record: {e}")
                logger.error(f"Function: process_records, Line: {traceback.extract_tb(e.__traceback__)[-1].lineno}")
                # Continue processing other records
                continue

    except Exception as e:
        logger.error(f"Critical error in process_records: {e}")
        logger.error(f"Function: process_records, Line: {traceback.extract_tb(e.__traceback__)[-1].lineno}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        graceful_shutdown(1, "Critical error processing records")

    return processed


def print_records(records: List[Dict[str, Any]]) -> None:
    """
    Print formatted records to console (no sensitive data)

    Args:
        records: List of processed record dictionaries
    """
    if not records:
        return

    try:
        print("\n" + "=" * 80)
        print(f"📊 NEW SPY DATA - {len(records)} records")
        print("=" * 80)

        for record in records:
            print(json.dumps(record, indent=2))
            print("-" * 80)

        print("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"Error printing records: {e}")
        logger.error(f"Function: print_records, Line: {traceback.extract_tb(e.__traceback__)[-1].lineno}")
        # Non-critical, continue execution


def calculate_time_range(last_timestamp: Optional[int]) -> tuple[int, int]:
    """
    Calculate the time range for the next data fetch

    Args:
        last_timestamp: Last processed timestamp in milliseconds, or None

    Returns:
        Tuple of (from_time, to_time) in milliseconds
    """
    try:
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

    except Exception as e:
        logger.error(f"Error calculating time range: {e}")
        logger.error(f"Function: calculate_time_range, Line: {traceback.extract_tb(e.__traceback__)[-1].lineno}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        graceful_shutdown(1, "Critical error in time calculation")


def main() -> None:
    """
    Main listener loop with comprehensive error handling
    """
    global shutdown_requested, consecutive_empty_responses

    try:
        logger.info("=" * 80)
        logger.info("🚀 Polygon.io SPY Listener Service Starting")
        logger.info("=" * 80)
        logger.info(f"Ticker: {TICKER}")
        logger.info(f"Fetch Interval: {FETCH_INTERVAL} seconds")
        logger.info(f"LPI File: {LPI_FILE}")
        logger.info(f"Log Path: {LOG_PATH / 'listener.log'}")
        logger.info(f"Max Consecutive Empty Responses: {MAX_CONSECUTIVE_EMPTY_RESPONSES}")
        logger.info("=" * 80)

        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Validate API key (without logging it)
        if not POLYGON_API_KEY:
            logger.error("❌ POLYGON_API_KEY not found in environment variables")
            logger.error("Please set POLYGON_API_KEY in your .env file")
            graceful_shutdown(1, "Missing required API key configuration")

        logger.info("✅ API key validated (masked for security)")

        while not shutdown_requested:
            try:
                # Load last processed timestamp
                last_timestamp = load_lpi()

                # Calculate time range
                from_time, to_time = calculate_time_range(last_timestamp)

                # Fetch data
                data = fetch_data(from_time, to_time)

                if data is None:
                    logger.warning("Failed to fetch data after retries")
                    graceful_shutdown(1, "Data fetch failed after all retry attempts")

                # Extract results
                results = data.get("results", [])

                if not results:
                    consecutive_empty_responses += 1
                    if last_timestamp:
                        iso_time = epoch_to_iso(last_timestamp)
                        print(f"✅ No new data since {iso_time}")
                        logger.info(f"No new records. Last processed: {iso_time}")
                    else:
                        print("✅ No data available in the requested time range")
                        logger.info("No data available")

                    # Check if we should shutdown due to too many empty responses
                    if consecutive_empty_responses >= MAX_CONSECUTIVE_EMPTY_RESPONSES:
                        logger.warning(
                            f"Received {consecutive_empty_responses} consecutive empty responses"
                        )
                        graceful_shutdown(
                            0,
                            f"Graceful shutdown after {MAX_CONSECUTIVE_EMPTY_RESPONSES} empty responses"
                        )
                else:
                    # Reset counter on successful data fetch
                    consecutive_empty_responses = 0

                    # Filter records newer than last timestamp
                    if last_timestamp:
                        results = [r for r in results if r.get("t") > last_timestamp]

                    if results:
                        # Process records
                        processed_records = process_records(results)

                        if not processed_records:
                            logger.warning("No records after processing")
                        else:
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

            except Exception as e:
                logger.error(f"Error in main loop iteration: {e}")
                logger.error(f"Function: main, Line: {traceback.extract_tb(e.__traceback__)[-1].lineno}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                graceful_shutdown(1, "Critical error in main loop")

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        graceful_shutdown(0, "Shutdown requested by user")

    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        logger.error(f"Function: main, Line: {traceback.extract_tb(e.__traceback__)[-1].lineno}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        graceful_shutdown(1, "Unexpected critical error")


if __name__ == "__main__":
    main()
