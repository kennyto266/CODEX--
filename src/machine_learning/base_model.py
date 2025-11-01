"""
机器学习模型基类
定义所有ML模型的基础接口和方法
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import pickle
import joblib

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseMLModel(ABC):
    """机器学习模型基类"""

    def __init__(self, name: str, model_type: str):
        """
        初始化模型

        Args:
            name: 模型名称
            model_type: 模型类型 (如: 'lstm', 'rf', 'xgboost')
        """
        self.name = name
        self.model_type = model_type
        self.model = None
        self.is_trained = False
        self.training_history = {}
        self.feature_names = []
        self.model_params = {}
        self.created_at = datetime.now()
        self.last_trained = None

    @abstractmethod
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        准备特征数据

        Args:
            data: 原始股票数据

        Returns:
            特征数据框
        """
        pass

    @abstractmethod
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        训练模型

        Args:
            X: 特征数据
            y: 目标变量

        Returns:
            训练结果字典
        """
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        预测

        Args:
            X: 特征数据

        Returns:
            预测结果
        """
        pass

    @abstractmethod
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        预测概率 (如果支持)

        Args:
            X: 特征数据

        Returns:
            预测概率
        """
        pass

    def validate_data(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> bool:
        """
        验证数据质量

        Args:
            X: 特征数据
            y: 目标变量

        Returns:
            数据是否有效
        """
        try:
            # 检查空值
            if X.isnull().any().any():
                logger.warning(f"模型 {self.name} 输入数据包含空值")
                return False

            # 检查无穷大值
            if np.isinf(X.select_dtypes(include=[np.number])).any().any():
                logger.warning(f"模型 {self.name} 输入数据包含无穷大值")
                return False

            # 检查数据量
            if len(X) < 10:
                logger.warning(f"模型 {self.name} 数据量不足: {len(X)}")
                return False

            # 如果有目标变量，检查一致性
            if y is not None and len(X) != len(y):
                logger.error(f"模型 {self.name} 特征和目标变量长度不一致")
                return False

            return True

        except Exception as e:
            logger.error(f"模型 {self.name} 数据验证出错: {e}")
            return False

    def save_model(self, filepath: str) -> bool:
        """
        保存模型

        Args:
            filepath: 保存路径

        Returns:
            是否保存成功
        """
        try:
            model_data = {
                'name': self.name,
                'model_type': self.model_type,
                'model': self.model,
                'is_trained': self.is_trained,
                'training_history': self.training_history,
                'feature_names': self.feature_names,
                'model_params': self.model_params,
                'created_at': self.created_at,
                'last_trained': self.last_trained
            }

            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)

            logger.info(f"模型 {self.name} 已保存到 {filepath}")
            return True

        except Exception as e:
            logger.error(f"模型 {self.name} 保存失败: {e}")
            return False

    def load_model(self, filepath: str) -> bool:
        """
        加载模型

        Args:
            filepath: 模型文件路径

        Returns:
            是否加载成功
        """
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)

            self.name = model_data['name']
            self.model_type = model_data['model_type']
            self.model = model_data['model']
            self.is_trained = model_data['is_trained']
            self.training_history = model_data['training_history']
            self.feature_names = model_data['feature_names']
            self.model_params = model_data['model_params']
            self.created_at = model_data['created_at']
            self.last_trained = model_data['last_trained']

            logger.info(f"模型 {self.name} 已从 {filepath} 加载")
            return True

        except Exception as e:
            logger.error(f"模型 {self.name} 加载失败: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        return {
            'name': self.name,
            'type': self.model_type,
            'is_trained': self.is_trained,
            'feature_count': len(self.feature_names),
            'feature_names': self.feature_names,
            'created_at': self.created_at.isoformat(),
            'last_trained': self.last_trained.isoformat() if self.last_trained else None,
            'training_history': self.training_history
        }

    def __str__(self) -> str:
        return f"Model(name={self.name}, type={self.model_type}, trained={self.is_trained})"

    def __repr__(self) -> str:
        return self.__str__()
