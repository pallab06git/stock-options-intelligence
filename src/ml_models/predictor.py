# © 2025 Pallab Basu Roy. All rights reserved.
# This source code is proprietary and confidential.
# Unauthorized copying, modification, or commercial use is strictly prohibited.
# Repository: https://github.com/pallab06/stock-options-intelligence

"""
ML prediction models for SPY options
"""

import os
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBClassifier


class DirectionPredictor:
    """Predict SPY movement direction (up/down/neutral)"""

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or os.getenv("MODEL_PATH", "./models")
        self.model: XGBClassifier | None = None
        self.feature_names: list[str] = []

    def train(
        self, X: pd.DataFrame, y: pd.Series, n_splits: int = 5
    ) -> Tuple[XGBClassifier, list[float]]:
        """
        Train direction prediction model with time-series cross-validation

        Args:
            X: Feature dataframe
            y: Target labels (0=down, 1=neutral, 2=up)
            n_splits: Number of CV splits

        Returns:
            Trained model and validation scores
        """
        self.feature_names = list(X.columns)

        # Time-series cross-validation
        tscv = TimeSeriesSplit(n_splits=n_splits)

        model = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            objective="multi:softmax",
            num_class=3,
            random_state=42,
        )

        # Cross-validation
        scores = []
        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            model.fit(X_train, y_train)
            score = model.score(X_val, y_val)
            scores.append(score)

        # Train on full dataset
        model.fit(X, y)
        self.model = model

        return model, scores

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict direction for given features"""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probability distribution for each class"""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        return self.model.predict_proba(X)

    def save_model(self, filename: str = "direction_model.json") -> None:
        """Save model to disk"""
        if self.model is None:
            raise ValueError("No model to save")

        filepath = os.path.join(self.model_path, filename)
        self.model.save_model(filepath)

    def load_model(self, filename: str = "direction_model.json") -> None:
        """Load model from disk"""
        filepath = os.path.join(self.model_path, filename)
        self.model = XGBClassifier()
        self.model.load_model(filepath)

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores"""
        if self.model is None or not self.feature_names:
            return {}

        importance = self.model.feature_importances_
        return dict(zip(self.feature_names, importance))
