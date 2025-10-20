# © 2025 Pallab Basu Roy. All rights reserved.
# This source code is proprietary and confidential.
# Unauthorized copying, modification, or commercial use is strictly prohibited.
# Repository: https://github.com/pallab06/stock-options-intelligence

"""
Market data fetcher for SPY options data from various providers
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel


class OptionData(BaseModel):
    """Options data model"""

    symbol: str
    underlying_price: float
    strike: float
    expiration: datetime
    option_type: str  # 'call' or 'put'
    bid: float
    ask: float
    last: float
    volume: int
    open_interest: int
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    timestamp: datetime


class MarketDataProvider(ABC):
    """Abstract base class for market data providers"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def fetch_options_chain(
        self, symbol: str, expiration_date: Optional[str] = None
    ) -> List[OptionData]:
        """Fetch options chain for a given symbol"""
        pass

    @abstractmethod
    def fetch_underlying_price(self, symbol: str) -> float:
        """Fetch current price of underlying asset"""
        pass


class PolygonDataProvider(MarketDataProvider):
    """Polygon.io market data provider"""

    BASE_URL = "https://api.polygon.io"

    def fetch_options_chain(
        self, symbol: str, expiration_date: Optional[str] = None
    ) -> List[OptionData]:
        """Fetch options chain from Polygon.io"""
        # TODO: Implement Polygon.io API integration
        raise NotImplementedError("Polygon.io integration pending")

    def fetch_underlying_price(self, symbol: str) -> float:
        """Fetch current price from Polygon.io"""
        # TODO: Implement price fetching
        raise NotImplementedError("Price fetching pending")


class AlpacaDataProvider(MarketDataProvider):
    """Alpaca market data provider"""

    BASE_URL = "https://data.alpaca.markets"

    def fetch_options_chain(
        self, symbol: str, expiration_date: Optional[str] = None
    ) -> List[OptionData]:
        """Fetch options chain from Alpaca"""
        # TODO: Implement Alpaca API integration
        raise NotImplementedError("Alpaca integration pending")

    def fetch_underlying_price(self, symbol: str) -> float:
        """Fetch current price from Alpaca"""
        # TODO: Implement price fetching
        raise NotImplementedError("Price fetching pending")


def get_market_data_provider() -> MarketDataProvider:
    """Factory function to get configured market data provider"""
    provider = os.getenv("MARKET_DATA_PROVIDER", "polygon").lower()
    api_key = os.getenv("MARKET_DATA_API_KEY", "")

    if provider == "polygon":
        return PolygonDataProvider(api_key)
    elif provider == "alpaca":
        return AlpacaDataProvider(api_key)
    else:
        raise ValueError(f"Unknown market data provider: {provider}")
