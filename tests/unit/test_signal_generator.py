# © 2025 Pallab Basu Roy. All rights reserved.
# This source code is proprietary and confidential.
# Unauthorized copying, modification, or commercial use is strictly prohibited.
# Repository: https://github.com/pallab06/stock-options-intelligence

"""
Unit tests for signal generator
"""

import pytest

from src.signal_generator.generator import SignalGenerator


def test_generate_signal(mock_prediction, mock_market_data, mock_claude_analysis):  # type: ignore
    """Test signal generation with valid inputs"""
    generator = SignalGenerator()

    signal = generator.generate_signal(
        prediction=mock_prediction,
        market_data=mock_market_data,
        claude_analysis=mock_claude_analysis,
    )

    assert signal is not None
    assert signal.symbol == "SPY"
    assert signal.confidence == 0.75
    assert signal.direction == "up"
    assert signal.entry_price == 450.00


def test_generate_signal_low_confidence(mock_market_data, mock_claude_analysis):  # type: ignore
    """Test that low confidence predictions don't generate signals"""
    generator = SignalGenerator(confidence_threshold=0.7)

    low_conf_prediction = {
        "direction": "up",
        "confidence": 0.5,  # Below threshold
        "current_price": 450.00,
        "target_price": 453.00,
    }

    signal = generator.generate_signal(
        prediction=low_conf_prediction,
        market_data=mock_market_data,
        claude_analysis=mock_claude_analysis,
    )

    assert signal is None
