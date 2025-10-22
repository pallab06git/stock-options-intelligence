# Polygon.io SPY Listener Service Guide

## Overview

The Polygon.io SPY Listener is a continuous data ingestion service that fetches minute-level SPY (S&P 500 ETF) aggregates data from Polygon.io and maintains processing state for incremental updates.

## Features

- ✅ **Real-Time Data Fetching**: Continuously fetches minute-level SPY data
- ✅ **State Management**: Maintains Last Processed Indicator (LPI) to track progress
- ✅ **Incremental Processing**: Only fetches new data since last run
- ✅ **Retry Logic**: Exponential backoff for API failures and rate limits
- ✅ **Error Handling**: Comprehensive error handling and logging
- ✅ **Graceful Shutdown**: Handles Ctrl+C and SIGTERM signals
- ✅ **Extensible Design**: Modular functions ready for database/S3 integration
- ✅ **Timestamp Conversion**: Converts Unix epochs to ISO 8601 format
- ✅ **Console Output**: Formatted JSON output for monitoring
- ✅ **File Logging**: Detailed logs saved to `./logs/listener.log`

## Architecture

### Data Flow

```
┌─────────────────┐
│  Polygon.io API │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  fetch_data()   │ ← Retry logic with exponential backoff
└────────┬────────┘
         │
         v
┌─────────────────┐
│ process_records │ ← Convert timestamps, enrich data
└────────┬────────┘
         │
         v
┌─────────────────┐
│  print_records  │ ← Console output
└────────┬────────┘
         │
         v
┌─────────────────┐
│   update_lpi    │ ← Save state to /state/last_processed_index.json
└─────────────────┘
```

### Modular Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `fetch_data(from_time, to_time)` | Fetch data from Polygon.io API | `Dict` or `None` |
| `process_records(records)` | Convert timestamps and enrich data | `List[Dict]` |
| `update_lpi(timestamp)` | Save last processed timestamp | `None` |
| `load_lpi()` | Load last processed timestamp | `int` or `None` |
| `calculate_time_range(last_timestamp)` | Determine fetch window | `Tuple[int, int]` |
| `epoch_to_iso(timestamp_ms)` | Convert epoch to ISO 8601 | `str` |
| `main()` | Main service loop | `None` |

## Installation

### Prerequisites

```bash
# Ensure you have Python 3.11+ installed
python --version

# Install dependencies
pip install requests python-dotenv
```

### Configuration

1. **Copy environment template**:
```bash
cp .env.example .env
```

2. **Add your Polygon.io API key**:
```bash
# Edit .env
POLYGON_API_KEY=your_polygon_api_key_here
FETCH_INTERVAL=60
DATA_PATH=./data
LOG_PATH=./logs
LPI_FILE=./state/last_processed_index.json
```

3. **Create required directories**:
```bash
mkdir -p logs state data
```

## Usage

### Running the Listener

#### Option 1: Using the convenience script
```bash
./scripts/run_listener.sh
```

#### Option 2: Direct Python execution
```bash
# Activate virtual environment
source venv/bin/activate

# Run the listener
python -m src.data_ingestion.polygon_listener
```

#### Option 3: As a module
```python
from src.data_ingestion.polygon_listener import main

if __name__ == "__main__":
    main()
```

### Stopping the Service

Press `Ctrl+C` for graceful shutdown:

```
^C2025-10-21 23:00:00 - INFO - Received signal 2. Initiating graceful shutdown...
================================================================================
🛑 Polygon.io SPY Listener Service Stopped
================================================================================
```

## Output Examples

### First Run (No LPI)

```
================================================================================
🚀 Polygon.io SPY Listener Service Starting
================================================================================
Ticker: SPY
Fetch Interval: 60 seconds
LPI File: ./state/last_processed_index.json
Log Path: ./logs/listener.log
================================================================================
2025-10-21 10:00:00 - INFO - No LPI file found. Starting fresh.
2025-10-21 10:00:00 - INFO - No previous data. Fetching last 24 hours.
2025-10-21 10:00:00 - INFO - Fetching data from 2025-10-20 to 2025-10-21...
2025-10-21 10:00:02 - INFO - Received 1440 records from Polygon.io

================================================================================
📊 NEW SPY DATA - 1440 records
================================================================================
{
  "timestamp_iso": "2025-10-20T14:30:00Z",
  "timestamp_epoch": 1729434600000,
  "ticker": "SPY",
  "open": 450.25,
  "high": 450.50,
  "low": 450.20,
  "close": 450.45,
  "volume": 125000,
  "vwap": 450.35,
  "transactions": 1250
}
--------------------------------------------------------------------------------
...
================================================================================

2025-10-21 10:00:02 - INFO - ✅ Processed 1440 new records. Latest: 2025-10-21T09:59:00Z
2025-10-21 10:00:02 - INFO - ⏳ Waiting 60 seconds until next fetch...
```

### Subsequent Run (With LPI)

```
2025-10-21 10:01:02 - INFO - Loaded LPI: 1729501140000 (2025-10-21T09:59:00Z)
2025-10-21 10:01:02 - INFO - Fetching data from 2025-10-21 to 2025-10-21...
2025-10-21 10:01:03 - INFO - Received 2 records from Polygon.io

================================================================================
📊 NEW SPY DATA - 2 records
================================================================================
{
  "timestamp_iso": "2025-10-21T10:00:00Z",
  "timestamp_epoch": 1729501200000,
  "ticker": "SPY",
  "open": 450.50,
  "high": 450.75,
  "low": 450.45,
  "close": 450.70,
  "volume": 98000,
  "vwap": 450.62,
  "transactions": 980
}
--------------------------------------------------------------------------------
...
```

### No New Data

```
2025-10-21 10:02:02 - INFO - Loaded LPI: 1729501260000 (2025-10-21T10:01:00Z)
2025-10-21 10:02:02 - INFO - Fetching data from 2025-10-21 to 2025-10-21...
2025-10-21 10:02:03 - INFO - Received 0 records from Polygon.io
✅ No new data since 2025-10-21T10:01:00Z
2025-10-21 10:02:03 - INFO - No new records. Last processed: 2025-10-21T10:01:00Z
2025-10-21 10:02:03 - INFO - ⏳ Waiting 60 seconds until next fetch...
```

## State Management

### LPI File Format

The Last Processed Indicator is stored in JSON format:

```json
{
  "last_processed_timestamp": 1729501260000,
  "last_processed_iso": "2025-10-21T10:01:00Z",
  "updated_at": "2025-10-21T10:02:03.123456"
}
```

**Location**: `./state/last_processed_index.json` (configurable via `LPI_FILE` env var)

### State Recovery

If the LPI file is missing or corrupted:
- Service automatically starts fresh
- Fetches last 24 hours of data
- Creates new LPI file

To reset state:
```bash
rm ./state/last_processed_index.json
```

## Error Handling & Retry Logic

### Exponential Backoff

The service implements exponential backoff for failures:

| Retry | Backoff Time |
|-------|--------------|
| 1 | 1 second |
| 2 | 2 seconds |
| 3 | 4 seconds |
| 4 | 8 seconds |
| 5 | 16 seconds |
| Max | 60 seconds |

### Error Scenarios

#### Rate Limiting (HTTP 429)
```
2025-10-21 10:00:00 - WARNING - Rate limit exceeded. Implementing backoff...
2025-10-21 10:00:00 - INFO - Retrying in 1 seconds... (Attempt 1/5)
```

#### Timeout
```
2025-10-21 10:00:00 - ERROR - Request timed out
2025-10-21 10:00:00 - INFO - Retrying in 2 seconds...
```

#### API Error
```
2025-10-21 10:00:00 - ERROR - Request error: 500 Server Error
2025-10-21 10:00:00 - INFO - Retrying in 4 seconds...
```

#### Max Retries Reached
```
2025-10-21 10:00:00 - ERROR - Max retries reached. Giving up.
2025-10-21 10:00:00 - WARNING - Failed to fetch data. Waiting before retry...
```

## Logging

### Log File Location

`./logs/listener.log` (configurable via `LOG_PATH` env var)

### Log Format

```
2025-10-21 10:00:00,123 - polygon_listener - INFO - Message here
```

### Log Levels

- **INFO**: Normal operation, fetch results, state updates
- **WARNING**: Rate limits, retries, non-critical issues
- **ERROR**: API errors, file I/O errors, unexpected failures
- **DEBUG**: Detailed debugging information (enable with `LOG_LEVEL=DEBUG`)

## Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `POLYGON_API_KEY` | Polygon.io API key | - | ✅ Yes |
| `FETCH_INTERVAL` | Seconds between fetches | `60` | No |
| `DATA_PATH` | Data storage path | `./data` | No |
| `LOG_PATH` | Log file directory | `./logs` | No |
| `LPI_FILE` | LPI state file path | `./state/last_processed_index.json` | No |

### Customization

Modify these constants in `polygon_listener.py`:

```python
# API Configuration
TICKER = "SPY"  # Change to other tickers (requires API plan)
TIMESPAN = "minute"  # Options: minute, hour, day, week, month
MULTIPLIER = 1  # Aggregate window multiplier

# Retry Configuration
MAX_RETRIES = 5  # Maximum retry attempts
INITIAL_BACKOFF = 1  # Initial backoff in seconds
MAX_BACKOFF = 60  # Maximum backoff in seconds
```

## Extension Points

### Database Integration

Add this function to push data to PostgreSQL:

```python
def save_to_database(records: List[Dict[str, Any]]) -> None:
    """Save processed records to PostgreSQL"""
    # TODO: Implement database insertion
    # Use SQLAlchemy or psycopg2
    # Bulk insert for efficiency
    pass

# In main() after process_records():
processed_records = process_records(results)
save_to_database(processed_records)  # Add this line
```

### S3 Integration

Add this function to push data to S3:

```python
import boto3
from datetime import datetime

def save_to_s3(records: List[Dict[str, Any]]) -> None:
    """Save processed records to S3"""
    s3 = boto3.client('s3')
    bucket = os.getenv('S3_BUCKET')

    # Create partitioned path
    date = datetime.utcnow().strftime('%Y/%m/%d')
    key = f"spy-data/{date}/spy_{int(time.time())}.json"

    # Upload
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(records, indent=2)
    )

# In main() after process_records():
save_to_s3(processed_records)  # Add this line
```

### Real-Time Processing

Add this function for real-time analysis:

```python
def analyze_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Perform real-time analysis on new records"""
    if not records:
        return {}

    # Calculate statistics
    prices = [r['close'] for r in records]
    volumes = [r['volume'] for r in records]

    return {
        'avg_price': sum(prices) / len(prices),
        'total_volume': sum(volumes),
        'price_range': max(prices) - min(prices),
        'record_count': len(records)
    }

# In main() after process_records():
analysis = analyze_records(processed_records)
logger.info(f"Analysis: {analysis}")
```

## Production Deployment

### Systemd Service (Linux)

Create `/etc/systemd/system/polygon-listener.service`:

```ini
[Unit]
Description=Polygon.io SPY Listener Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/stock-options-intelligence
ExecStart=/path/to/venv/bin/python -m src.data_ingestion.polygon_listener
Restart=always
RestartSec=10
Environment="POLYGON_API_KEY=your_key"

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable polygon-listener
sudo systemctl start polygon-listener
sudo systemctl status polygon-listener
```

### Docker Deployment

Add to `docker-compose.yml`:

```yaml
services:
  polygon-listener:
    build: .
    command: python -m src.data_ingestion.polygon_listener
    environment:
      - POLYGON_API_KEY=${POLYGON_API_KEY}
      - FETCH_INTERVAL=60
    volumes:
      - ./logs:/app/logs
      - ./state:/app/state
    restart: unless-stopped
```

### Monitoring

Use Prometheus metrics (future enhancement):

```python
from prometheus_client import Counter, Histogram

records_processed = Counter('spy_records_processed', 'Total SPY records processed')
fetch_latency = Histogram('spy_fetch_latency_seconds', 'API fetch latency')

# In process_records():
records_processed.inc(len(records))

# In fetch_data():
with fetch_latency.time():
    response = requests.get(url, params=params, timeout=30)
```

## Troubleshooting

### Issue: "POLYGON_API_KEY not found"

**Solution**: Ensure `.env` file exists and contains `POLYGON_API_KEY=your_key`

```bash
# Check if .env exists
ls -la .env

# If not, create from template
cp .env.example .env

# Edit and add your key
nano .env
```

### Issue: Rate limit errors

**Solution**: Increase `FETCH_INTERVAL` or upgrade Polygon.io plan

```bash
# In .env
FETCH_INTERVAL=120  # Fetch every 2 minutes instead
```

### Issue: No data returned

**Possible causes**:
- Market is closed (check market hours)
- Weekend or holiday
- Future timestamp requested

**Solution**: Service will show "No new data since..." message. This is normal.

### Issue: Permission denied on /state/

**Solution**: Ensure directories have write permissions

```bash
mkdir -p logs state data
chmod 755 logs state data
```

## API Reference

### Polygon.io Endpoint

```
GET https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}
```

**Parameters**:
- `ticker`: Stock symbol (e.g., SPY)
- `multiplier`: Aggregate window size
- `timespan`: minute, hour, day, week, month
- `from`: Start date (YYYY-MM-DD)
- `to`: End date (YYYY-MM-DD)
- `apiKey`: Your API key (query parameter)

**Response**: See [Polygon Data Dictionary](./polygon_data_dictionary.md)

## Performance

### Resource Usage

- **Memory**: ~50-100 MB
- **CPU**: <1% average
- **Network**: ~1-5 KB per minute fetch
- **Disk I/O**: Minimal (only logs and LPI updates)

### Optimization Tips

1. **Batch Processing**: Increase `FETCH_INTERVAL` for less frequent checks
2. **Filtering**: Add filters for specific time ranges or conditions
3. **Async Processing**: Use `asyncio` for concurrent operations
4. **Database Buffering**: Batch insert multiple records at once

## License

© 2025 Pallab Basu Roy. All rights reserved.

---

**Last Updated**: 2025-10-21
**Version**: 1.0.0
**Author**: Pallab Basu Roy
