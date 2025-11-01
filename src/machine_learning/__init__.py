"""
机器学习模块
提供多种机器学习模型用于股票价格预测
"""

from .base_model import BaseMLModel
from .feature_engineering import FeatureEngine
from .ml_prediction_system import MLPredictionSystem

# 模型类
from .models.lstm_model import LSTMModel
from .models.random_forest_model import RandomForestModel
from .models.xgboost_model import XGBoostModel

__all__ = [
    'BaseMLModel',
    'FeatureEngine',
    'MLPredictionSystem',
    'LSTMModel',
    'RandomForestModel',
    'XGBoostModel'
]

__version__ = '1.0.0'
