# © 2025 Pallab Basu Roy. All rights reserved.
# This source code is proprietary and confidential.
# Unauthorized copying, modification, or commercial use is strictly prohibited.
# Repository: https://github.com/pallab06/stock-options-intelligence

"""
Trading signal generator
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class TradingSignal(BaseModel):
    """Trading signal model"""

    timestamp: datetime
    symbol: str
    signal_type: str  # 'call' or 'put'
    direction: str  # 'up', 'down', 'neutral'
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    position_size: float  # as % of portfolio
    risk_reward_ratio: float
    time_horizon: str  # 'intraday', 'weekly', 'monthly'
    rationale: str
    risk_level: str  # 'low', 'medium', 'high'
    model_version: str


class SignalGenerator:
    """Generate trading signals from predictions and analysis"""

    def __init__(self, max_position_size: float = 0.05, confidence_threshold: float = 0.7):
        self.max_position_size = max_position_size
        self.confidence_threshold = confidence_threshold

    def generate_signal(
        self,
        prediction: Dict[str, float],
        market_data: Dict[str, float],
        claude_analysis: str,
    ) -> Optional[TradingSignal]:
        """
        Generate trading signal from prediction and analysis

        Args:
            prediction: Model prediction with confidence
            market_data: Current market data
            claude_analysis: Claude AI analysis text

        Returns:
            TradingSignal if confidence meets threshold, None otherwise
        """
        confidence = prediction.get("confidence", 0.0)

        if confidence < self.confidence_threshold:
            return None

        direction = prediction.get("direction", "neutral")
        current_price = market_data.get("price", 0.0)

        # Calculate entry, target, and stop-loss levels
        entry_price = current_price
        target_price = self._calculate_target(current_price, direction, confidence)
        stop_loss = self._calculate_stop_loss(current_price, direction)

        # Calculate position sizing based on confidence
        position_size = self._calculate_position_size(confidence)

        # Calculate risk/reward
        risk = abs(entry_price - stop_loss)
        reward = abs(target_price - entry_price)
        risk_reward_ratio = reward / risk if risk > 0 else 0

        return TradingSignal(
            timestamp=datetime.now(),
            symbol="SPY",
            signal_type="call" if direction == "up" else "put",
            direction=direction,
            confidence=confidence,
            entry_price=entry_price,
            target_price=target_price,
            stop_loss=stop_loss,
            position_size=position_size,
            risk_reward_ratio=risk_reward_ratio,
            time_horizon="intraday",
            rationale=claude_analysis,
            risk_level=self._assess_risk_level(confidence, risk_reward_ratio),
            model_version="v1.0.0",
        )

    def _calculate_target(self, price: float, direction: str, confidence: float) -> float:
        """Calculate target price based on direction and confidence"""
        move_percent = 0.01 * confidence  # 0.7 confidence = 0.7% move

        if direction == "up":
            return price * (1 + move_percent)
        elif direction == "down":
            return price * (1 - move_percent)
        else:
            return price

    def _calculate_stop_loss(self, price: float, direction: str) -> float:
        """Calculate stop-loss price"""
        stop_percent = 0.005  # 0.5% stop loss

        if direction == "up":
            return price * (1 - stop_percent)
        elif direction == "down":
            return price * (1 + stop_percent)
        else:
            return price

    def _calculate_position_size(self, confidence: float) -> float:
        """Calculate position size based on confidence"""
        # Scale position size with confidence
        base_size = self.max_position_size
        return base_size * confidence

    def _assess_risk_level(self, confidence: float, risk_reward: float) -> str:
        """Assess overall risk level of signal"""
        if confidence > 0.8 and risk_reward > 2.0:
            return "low"
        elif confidence > 0.6 and risk_reward > 1.5:
            return "medium"
        else:
            return "high"

    def filter_signals(
        self, signals: List[TradingSignal], min_risk_reward: float = 1.5
    ) -> List[TradingSignal]:
        """Filter signals based on criteria"""
        return [s for s in signals if s.risk_reward_ratio >= min_risk_reward]
