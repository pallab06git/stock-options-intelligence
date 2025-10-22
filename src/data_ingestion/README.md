# Data Ingestion Module

## Overview

This module handles real-time and historical market data ingestion from various providers including Polygon.io, Finnhub, and Interactive Brokers.

## Components

### `polygon_listener.py`

Real-time SPY data listener service that continuously fetches minute-level aggregates from Polygon.io.

**Features**:
- Continuous data fetching with configurable intervals
- State management with Last Processed Indicator (LPI)
- Retry logic with exponential backoff
- Graceful shutdown handling
- Comprehensive logging

**Usage**:
```bash
python -m src.data_ingestion.polygon_listener
```

See [Polygon Listener Guide](../../docs/polygon_listener_guide.md) for detailed documentation.

### `market_data.py`

Abstract market data provider interface with implementations for multiple data sources.

**Providers**:
- Polygon.io
- Alpaca Markets
- Interactive Brokers (coming soon)

## Quick Start

1. **Set up environment**:
```bash
cp .env.example .env
# Add your POLYGON_API_KEY
```

2. **Run the listener**:
```bash
./scripts/run_listener.sh
```

3. **Monitor logs**:
```bash
tail -f logs/listener.log
```

## Data Flow

```
Market Data APIs → polygon_listener.py → State Management → Console/Logs
                                       ↓
                                  [Future: Database/S3]
```

## Configuration

Environment variables (`.env`):
- `POLYGON_API_KEY` - Polygon.io API key
- `FETCH_INTERVAL` - Fetch interval in seconds (default: 60)
- `LPI_FILE` - State file location (default: ./state/last_processed_index.json)
- `LOG_PATH` - Log directory (default: ./logs)

## Extension Points

The module is designed for easy extension:

1. **Add new providers**: Implement `MarketDataProvider` interface
2. **Add data sinks**: Implement functions to push data to databases or S3
3. **Add data processing**: Add transformation functions between fetch and storage

## Documentation

- [Polygon Listener Guide](../../docs/polygon_listener_guide.md) - Complete service documentation
- [Polygon Data Dictionary](../../docs/polygon_data_dictionary.md) - API data structure reference

## License

© 2025 Pallab Basu Roy. All rights reserved.
