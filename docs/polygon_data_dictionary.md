# Polygon.io Data Dictionary

## Aggregates (Bars) Endpoint

This document describes the data structure returned by Polygon.io's Aggregates (Bars) API endpoint for stock market data.

**Endpoint**: `/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}`

**Example Ticker**: SPY (SPDR S&P 500 ETF Trust)

---

## Response Structure

### Top-Level Fields

| Field Name | Data Type | Description | Example | Notes |
|------------|-----------|-------------|---------|-------|
| `ticker` | String | The stock ticker symbol | `"SPY"` | Uppercase ticker symbol for the requested security |
| `results_count` | Integer | Total number of aggregate results returned | `1774` | Represents the count of bars/candles in the response |
| `adjusted` | Boolean | Whether the results are adjusted for splits and dividends | `true` | `true` = adjusted, `false` = unadjusted |
| `results` | Array[Object] | Array of aggregate bar data objects | See below | Contains OHLCV data for each time period |

---

## Results Array Fields

Each object in the `results` array represents a single bar/candle for a specific time period and contains the following fields:

### OHLCV Data Fields

| Field Name | Data Type | Description | Example | Notes |
|------------|-----------|-------------|---------|-------|
| `v` | Integer/Float | **Volume** - The trading volume during the aggregate window | `2758` | Number of shares traded |
| `vw` | Float | **Volume Weighted Average Price (VWAP)** | `666.79` | Average price weighted by volume; calculated as: (Σ(price × volume)) / Σ(volume) |
| `o` | Float | **Open** - Price at the start of the aggregate window | `666.89` | Opening price for the period |
| `c` | Float | **Close** - Price at the end of the aggregate window | `667.01` | Closing price for the period |
| `h` | Float | **High** - Highest price during the aggregate window | `667.01` | Maximum price reached during the period |
| `l` | Float | **Low** - Lowest price during the aggregate window | `666.72` | Minimum price reached during the period |
| `t` | Integer | **Timestamp** - Unix timestamp (milliseconds) for the start of the aggregate window | `1760601600000` | Milliseconds since Unix epoch (Jan 1, 1970) |
| `n` | Integer | **Number of transactions** - Count of individual trades during the aggregate window | `108` | Total number of trades executed during this period |

---

## Field Descriptions with Examples

### Volume (`v`)
- **Purpose**: Indicates market activity and liquidity
- **Use Case**: High volume often indicates strong interest; useful for confirming price movements
- **Example**: `2758` shares traded during this 1-minute period

### Volume Weighted Average Price (`vw`)
- **Purpose**: Provides a more accurate average price that considers volume at each price level
- **Use Case**: Trading algorithms and institutional traders use VWAP as a benchmark
- **Example**: `666.79` - the average price considering volume distribution

### Open (`o`)
- **Purpose**: First traded price in the time period
- **Use Case**: Identifies the starting point for price action analysis
- **Example**: `666.89` - SPY opened at this price for the period

### Close (`c`)
- **Purpose**: Last traded price in the time period
- **Use Case**: Most commonly used price for technical analysis and charting
- **Example**: `667.01` - SPY closed at this price for the period
- **Note**: For the current/latest incomplete bar, this represents the most recent trade price

### High (`h`)
- **Purpose**: Peak price reached during the period
- **Use Case**: Used to identify resistance levels and calculate trading ranges
- **Example**: `667.01` - highest price reached during this period

### Low (`l`)
- **Purpose**: Lowest price reached during the period
- **Use Case**: Used to identify support levels and calculate trading ranges
- **Example**: `666.72` - lowest price reached during this period

### Timestamp (`t`)
- **Purpose**: Identifies when the aggregate window starts
- **Format**: Unix timestamp in milliseconds (UTC)
- **Example**: `1760601600000` milliseconds
- **Human Readable**: October 16, 2025, 00:00:00 UTC
- **Conversion**: Divide by 1000 to get Unix timestamp in seconds

### Number of Transactions (`n`)
- **Purpose**: Indicates trading activity granularity
- **Use Case**: Higher transaction counts can indicate genuine price movements vs. low-liquidity price swings
- **Example**: `108` individual trades occurred during this period

---

## Data Types Summary

| Field | Python Type | SQL Type | Notes |
|-------|-------------|----------|-------|
| `ticker` | `str` | `VARCHAR(10)` | Ticker symbol |
| `results_count` | `int` | `INTEGER` | Result count |
| `adjusted` | `bool` | `BOOLEAN` | Adjustment flag |
| `v` | `int` or `float` | `BIGINT` or `NUMERIC` | Volume |
| `vw` | `float` | `NUMERIC(10,2)` | VWAP |
| `o` | `float` | `NUMERIC(10,2)` | Open price |
| `c` | `float` | `NUMERIC(10,2)` | Close price |
| `h` | `float` | `NUMERIC(10,2)` | High price |
| `l` | `float` | `NUMERIC(10,2)` | Low price |
| `t` | `int` | `BIGINT` | Unix timestamp (ms) |
| `n` | `int` | `INTEGER` | Trade count |

---

## Sample Response

```json
{
  "ticker": "SPY",
  "results_count": 1774,
  "adjusted": true,
  "results": [
    {
      "v": 2758,           // Volume: 2,758 shares traded
      "vw": 666.79,        // VWAP: $666.79
      "o": 666.89,         // Open: $666.89
      "c": 667.01,         // Close: $667.01
      "h": 667.01,         // High: $667.01
      "l": 666.72,         // Low: $666.72
      "t": 1760601600000,  // Timestamp: Oct 16, 2025, 00:00:00 UTC
      "n": 108             // Number of trades: 108
    }
  ]
}
```

---

## Usage in Trading Systems

### Price Analysis
- **Trend Detection**: Compare multiple `c` (close) values over time
- **Range Analysis**: Calculate `h - l` to measure volatility
- **Gap Detection**: Compare current `o` with previous `c`

### Volume Analysis
- **Liquidity Assessment**: Monitor `v` for sufficient trading activity
- **Volume Confirmation**: High `v` + price movement = strong signal
- **Transaction Density**: Use `n` to assess market participation

### Execution Benchmarking
- **VWAP Strategy**: Compare execution prices against `vw`
- **Slippage Analysis**: Measure difference between target and actual prices

### Risk Management
- **Support/Resistance**: Use `h` and `l` for stop-loss placement
- **Volatility Calculation**: Calculate Average True Range (ATR) using OHLC data

---

## Time Period Considerations

The aggregate window size depends on your API request parameters:
- **1 minute**: Each bar represents 1 minute of trading
- **5 minutes**: Each bar represents 5 minutes of trading
- **1 hour**: Each bar represents 1 hour of trading
- **1 day**: Each bar represents 1 full trading day

The `t` (timestamp) always represents the **start** of the aggregate window.

---

## Adjusted vs. Unadjusted Data

### Adjusted (`adjusted: true`)
- Prices are modified to account for:
  - Stock splits (e.g., 2-for-1 split)
  - Dividends distributions
  - Corporate actions
- **Use Case**: Long-term historical analysis, backtesting strategies
- **Example**: A 2-for-1 split would halve all historical prices

### Unadjusted (`adjusted: false`)
- Raw prices as they traded at that time
- **Use Case**: Intraday trading, real-time analysis
- **Example**: Shows actual traded prices without retroactive adjustments

---

## API Rate Limits & Best Practices

1. **Rate Limits**: Check Polygon.io documentation for your plan's limits
2. **Caching**: Store frequently accessed data locally to reduce API calls
3. **Pagination**: Use `limit` parameter for large date ranges
4. **Error Handling**: Implement retry logic with exponential backoff
5. **Data Validation**: Always validate field presence and data types

---

## Related Endpoints

- **Quotes**: `/v3/quotes/{ticker}` - Bid/ask spread data
- **Trades**: `/v3/trades/{ticker}` - Individual trade tick data
- **Options Chain**: `/v3/snapshot/options/{underlyingAsset}` - Options contract data
- **Daily Open/Close**: `/v1/open-close/{ticker}/{date}` - Daily OHLCV summary

---

## References

- [Polygon.io API Documentation](https://polygon.io/docs/stocks/get_v2_aggs_ticker__stocksticker__range__multiplier___timespan___from___to)
- [Unix Timestamp Converter](https://www.unixtimestamp.com/)
- [VWAP Calculation](https://www.investopedia.com/terms/v/vwap.asp)

---

**Last Updated**: 2025-10-21
**API Version**: v2
**Document Version**: 1.0
