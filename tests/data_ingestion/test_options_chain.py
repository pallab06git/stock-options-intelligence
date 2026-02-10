"""
Contract tests for options_chain ingestion.

These tests define the expected behavior of the options_chain.fetch()
and options_chain.save() functions. They intentionally avoid implementation
details and focus on correctness, stability, and failure semantics.
"""


def test_fetch_returns_dataframe():
    """fetch() must always return a pandas DataFrame"""


def test_fetch_returns_expected_schema(monkeypatch):
    """fetch() must return a DataFrame with the required schema columns"""

    import pandas as pd
    from src.data_ingestion import options_chain

    # Mock environment variable
    monkeypatch.setenv("POLYGON_API_KEY", "test_key")

    # Mock requests.get to return empty results
    class MockResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"results": []}

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(options_chain.requests, "get", mock_get)

    df = options_chain.fetch(symbol="SPY")

    assert isinstance(df, pd.DataFrame)

    expected_columns = [
        "contract_symbol",
        "underlying_symbol",
        "expiration_date",
        "strike_price",
        "option_type",
    ]

    assert list(df.columns) == expected_columns


def test_fetch_empty_response_returns_empty_dataframe():
    """fetch() must return an empty DataFrame with correct schema when API returns no results"""


def test_fetch_missing_api_key_raises_value_error():
    """fetch() must raise ValueError if POLYGON_API_KEY is not set"""


def test_fetch_rate_limit_raises_runtime_error(monkeypatch):
    """fetch() must raise RuntimeError on HTTP 429 responses"""

    from src.data_ingestion import options_chain

    monkeypatch.setenv("POLYGON_API_KEY", "test_key")

    class MockResponse:
        status_code = 429

        def raise_for_status(self):
            pass

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(options_chain.requests, "get", mock_get)

    try:
        options_chain.fetch(symbol="SPY")
        assert False, "Expected RuntimeError on HTTP 429"
    except RuntimeError:
        pass


def test_fetch_http_error_propagates():
    """fetch() must raise requests.HTTPError on non-429 HTTP errors"""


def test_fetch_malformed_json_raises_value_error():
    """fetch() must raise ValueError when API returns malformed JSON"""


def test_fetch_missing_required_fields_raises_value_error(monkeypatch):
    """fetch() must raise ValueError if required fields are missing in API response"""

    from src.data_ingestion import options_chain

    monkeypatch.setenv("POLYGON_API_KEY", "test_key")

    # Missing 'strike_price' and 'contract_type'
    class MockResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {
                "results": [
                    {
                        "ticker": "SPY260214C00500000",
                        "underlying_ticker": "SPY",
                        "expiration_date": "2026-02-14"
                        # intentionally missing fields
                    }
                ]
            }

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(options_chain.requests, "get", mock_get)

    try:
        options_chain.fetch(symbol="SPY")
        assert False, "Expected ValueError due to missing required fields"
    except ValueError:
        pass

def test_fetch_is_deterministic_given_same_response():
    """fetch() must return identical DataFrames given identical API responses"""


def test_save_writes_file_when_not_exists():
    """save() must write file and return True when file does not exist"""


def test_save_skips_when_file_exists_and_overwrite_false():
    """save() must skip write and return False when file exists and overwrite=False"""


def test_save_overwrites_when_overwrite_true():
    """save() must overwrite existing file when overwrite=True"""


def test_save_empty_dataframe_is_noop():
    """save() must not write file and return False for empty DataFrames"""


def test_save_missing_required_columns_raises_value_error():
    """save() must raise ValueError if DataFrame schema is invalid"""
