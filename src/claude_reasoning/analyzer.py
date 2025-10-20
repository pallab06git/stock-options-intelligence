# © 2025 Pallab Basu Roy. All rights reserved.
# This source code is proprietary and confidential.
# Unauthorized copying, modification, or commercial use is strictly prohibited.
# Repository: https://github.com/pallab06/stock-options-intelligence

"""
Claude AI reasoning module for analyzing trading signals
"""

import os
from typing import Any, Dict

from anthropic import Anthropic


class ClaudeAnalyzer:
    """Claude AI analyzer for trading signals"""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
        self.client = Anthropic(api_key=self.api_key)

    def analyze_signal(
        self, prediction_data: Dict[str, Any], market_context: Dict[str, Any]
    ) -> str:
        """
        Analyze trading signal using Claude AI

        Args:
            prediction_data: Model predictions and confidence
            market_context: Current market conditions and indicators

        Returns:
            Analysis text with rationale and risk assessment
        """
        prompt = self._build_analysis_prompt(prediction_data, market_context)

        message = self.client.messages.create(
            model=self.model, max_tokens=1024, messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text if message.content else ""

    def _build_analysis_prompt(
        self, prediction_data: Dict[str, Any], market_context: Dict[str, Any]
    ) -> str:
        """Build prompt for Claude analysis"""
        return f"""
        Analyze this SPY options trading signal:

        Predicted Direction: {prediction_data.get('direction', 'N/A')}
        Confidence: {prediction_data.get('confidence', 0):.2f}
        Current Price: ${prediction_data.get('current_price', 0):.2f}
        Target Price: ${prediction_data.get('target_price', 0):.2f}

        Market Context:
        VIX: {market_context.get('vix', 'N/A')}
        Volume: {market_context.get('volume', 'N/A')}
        Trend: {market_context.get('trend', 'N/A')}

        Provide:
        1. Risk assessment (high/medium/low)
        2. Key factors driving this prediction
        3. Potential catalysts or risks to watch
        4. Recommended position sizing (as % of portfolio)
        5. Stop-loss recommendation

        Be concise and actionable.
        """

    def generate_market_commentary(self, market_data: Dict[str, Any]) -> str:
        """Generate general market commentary"""
        prompt = f"""
        Provide a brief market commentary for SPY based on:

        Current Price: ${market_data.get('price', 0):.2f}
        Daily Change: {market_data.get('change_percent', 0):.2f}%
        Volume: {market_data.get('volume', 0):,}
        VIX: {market_data.get('vix', 0):.2f}

        Focus on:
        1. Overall market sentiment
        2. Key support/resistance levels
        3. Notable patterns or anomalies

        Keep it under 100 words.
        """

        message = self.client.messages.create(
            model=self.model, max_tokens=512, messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text if message.content else ""
