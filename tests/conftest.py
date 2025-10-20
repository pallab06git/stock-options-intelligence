# © 2025 Pallab Basu Roy. All rights reserved.
# This source code is proprietary and confidential.
# Unauthorized copying, modification, or commercial use is strictly prohibited.
# Repository: https://github.com/pallab06/stock-options-intelligence

"""
Pytest configuration and fixtures
"""

from datetime import datetime
from typing import Dict

import pytest


@pytest.fixture
def mock_market_data() -> Dict[str, float]:
    """Mock market data for testing"""
    return {
        "symbol": "SPY",
        "price": 450.00,
        "volume": 75000000,
        "change_percent": 0.5,
        "vix": 15.5,
    }


@pytest.fixture
def mock_option_data() -> Dict[str, float]:
    """Mock options data for testing"""
    return {
        "strike": 450,
        "type": "call",
        "bid": 2.50,
        "ask": 2.55,
        "last": 2.52,
        "volume": 10000,
        "open_interest": 50000,
        "iv": 0.15,
        "delta": 0.5,
        "gamma": 0.05,
        "theta": -0.02,
        "vega": 0.1,
    }


@pytest.fixture
def mock_prediction() -> Dict[str, float]:
    """Mock ML prediction for testing"""
    return {
        "direction": "up",
        "confidence": 0.75,
        "current_price": 450.00,
        "target_price": 453.00,
    }


@pytest.fixture
def mock_claude_analysis() -> str:
    """Mock Claude analysis for testing"""
    return """
    Risk Assessment: Medium

    Key Factors:
    - Strong upward momentum
    - High volume confirming trend
    - Low volatility environment

    Position Sizing: 3-4% of portfolio
    Stop Loss: $448.50
    """
