"""
XGBoost模型
梯度提升决策树算法
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score, classification_report
import logging
from typing import Dict, List, Optional, Tuple, Any
import joblib

from ..base_model import BaseMLModel

logger = logging.getLogger(__name__)


class XGBoostModel(BaseMLModel):
    """XGBoost模型"""

    def __init__(self, name: str = "XGBoost", task_type: str = 'regression',
                 n_estimators: int = 100, max_depth: int = 6,
                 learning_rate: float = 0.1, subsample: float = 1.0,
                 colsample_bytree: float = 1.0, random_state: int = 42):
        """
        初始化XGBoost模型

        Args:
            name: 模型名称
            task_type: 任务类型 ('regression' 或 'classification')
            n_estimators: 树的数量
            max_depth: 树的最大深度
            learning_rate: 学习率
            subsample: 样本采样率
            colsample_bytree: 特征采样率
            random_state: 随机种子
        """
        super().__init__(name, 'xgboost')

        self.task_type = task_type
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state

        self.model_params = {
            'task_type': task_type,
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'learning_rate': learning_rate,
            'subsample': subsample,
            'colsample_bytree': colsample_bytree,
            'random_state': random_state
        }

        self.feature_names_ = []

    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        准备XGBoost特征数据

        Args:
            data: 原始股票数据

        Returns:
            特征数据框
        """
        # 确保只使用数值特征
        numeric_df = data.select_dtypes(include=[np.number])

        # 移除包含NaN的行
        numeric_df = numeric_df.dropna()

        return numeric_df

    def _build_model(self) -> xgb.XGBRegressor | xgb.XGBClassifier:
        """
        构建XGBoost模型

        Returns:
            XGBoost模型
        """
        if self.task_type == 'regression':
            return xgb.XGBRegressor(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                learning_rate=self.learning_rate,
                subsample=self.subsample,
                colsample_bytree=self.colsample_bytree,
                random_state=self.random_state,
                n_jobs=-1,
                verbosity=0
            )
        else:
            return xgb.XGBClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                learning_rate=self.learning_rate,
                subsample=self.subsample,
                colsample_bytree=self.colsample_bytree,
                random_state=self.random_state,
                n_jobs=-1,
                verbosity=0
            )

    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        训练XGBoost模型

        Args:
            X: 特征数据
            y: 目标变量

        Returns:
            训练结果
        """
        try:
            # 数据验证
            if not self.validate_data(X, y):
                raise ValueError("数据验证失败")

            # 保存特征名称
            self.feature_names = list(X.columns)
            self.feature_names_ = self.feature_names

            # 处理缺失值
            X = X.fillna(X.mean())
            y = y.fillna(y.mean())

            # 构建模型
            self.model = self._build_model()

            # 训练模型
            logger.info(f"开始训练XGBoost模型 (n_estimators={self.n_estimators})")
            self.model.fit(X, y)

            self.is_trained = True
            self.last_trained = pd.Timestamp.now()

            # 计算训练指标
            y_train_pred = self.model.predict(X)

            if self.task_type == 'regression':
                train_mse = mean_squared_error(y, y_train_pred)
                train_mae = mean_absolute_error(y, y_train_pred)
                train_rmse = np.sqrt(train_mse)

                self.training_history = {
                    'train_mse': train_mse,
                    'train_mae': train_mae,
                    'train_rmse': train_rmse
                }

                logger.info(f"XGBoost训练完成 - Train MSE: {train_mse:.6f}, MAE: {train_mae:.6f}")

                return {
                    'status': 'success',
                    'train_mse': train_mse,
                    'train_mae': train_mae,
                    'train_rmse': train_rmse,
                    'n_features': len(self.feature_names),
                    'n_estimators': self.n_estimators
                }
            else:
                train_acc = accuracy_score(y, y_train_pred)

                self.training_history = {
                    'train_accuracy': train_acc
                }

                logger.info(f"XGBoost训练完成 - Train Accuracy: {train_acc:.4f}")

                return {
                    'status': 'success',
                    'train_accuracy': train_acc,
                    'n_features': len(self.feature_names),
                    'n_estimators': self.n_estimators
                }

        except Exception as e:
            logger.error(f"XGBoost训练失败: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        XGBoost预测

        Args:
            X: 特征数据

        Returns:
            预测结果
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")

        try:
            # 处理缺失值
            X = X.fillna(X.mean())

            # 确保特征顺序一致
            X = X.reindex(columns=self.feature_names, fill_value=0)

            return self.model.predict(X)

        except Exception as e:
            logger.error(f"XGBoost预测失败: {e}")
            return np.array([])

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        预测概率 (仅分类任务)

        Args:
            X: 特征数据

        Returns:
            预测概率
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")

        if self.task_type != 'classification':
            raise ValueError("概率预测仅适用于分类任务")

        try:
            # 处理缺失值
            X = X.fillna(X.mean())

            # 确保特征顺序一致
            X = X.reindex(columns=self.feature_names, fill_value=0)

            return self.model.predict_proba(X)

        except Exception as e:
            logger.error(f"XGBoost概率预测失败: {e}")
            return np.array([])

    def get_feature_importance(self) -> Dict[str, float]:
        """
        获取特征重要性

        Returns:
            特征重要性字典
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")

        try:
            importance = self.model.feature_importances_
            feature_importance = dict(zip(self.feature_names, importance))

            # 按重要性排序
            sorted_importance = dict(sorted(
                feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            ))

            logger.info("已获取特征重要性")
            return sorted_importance

        except Exception as e:
            logger.error(f"获取特征重要性失败: {e}")
            return {}

    def get_top_features(self, n: int = 10) -> List[Tuple[str, float]]:
        """
        获取最重要的N个特征

        Args:
            n: 特征数量

        Returns:
            最重要的特征列表
        """
        importance = self.get_feature_importance()
        return list(importance.items())[:n]

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """
        评估模型性能

        Args:
            X_test: 测试特征
            y_test: 测试目标

        Returns:
            评估结果
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")

        try:
            # 预测
            y_pred = self.predict(X_test)

            if self.task_type == 'regression':
                mse = mean_squared_error(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                rmse = np.sqrt(mse)

                results = {
                    'mse': mse,
                    'mae': mae,
                    'rmse': rmse
                }
            else:
                accuracy = accuracy_score(y_test, y_pred)

                results = {
                    'accuracy': accuracy
                }

                # 分类报告
                if len(np.unique(y_test)) > 1:
                    report = classification_report(y_test, y_pred, output_dict=True)
                    results['classification_report'] = report

            logger.info(f"模型评估完成: {results}")
            return results

        except Exception as e:
            logger.error(f"模型评估失败: {e}")
            return {}

    def plot_feature_importance(self, top_n: int = 20, save_path: Optional[str] = None):
        """
        绘制特征重要性图表

        Args:
            top_n: 显示前N个特征
            save_path: 保存路径
        """
        try:
            import matplotlib.pyplot as plt

            importance = self.get_feature_importance()
            top_features = list(importance.items())[:top_n]

            features, importance_values = zip(*top_features)

            plt.figure(figsize=(10, 8))
            plt.barh(range(len(features)), importance_values)
            plt.yticks(range(len(features)), features)
            plt.xlabel('Feature Importance')
            plt.title(f'{self.name} - Top {top_n} Feature Importance')
            plt.tight_layout()

            if save_path:
                plt.savefig(save_path)
                logger.info(f"特征重要性图表已保存到 {save_path}")
            else:
                plt.show()

        except ImportError:
            logger.error("matplotlib未安装，无法绘制图表")
        except Exception as e:
            logger.error(f"绘制特征重要性失败: {e}")

    def plot_tree(self, tree_index: int = 0, save_path: Optional[str] = None):
        """
        绘制决策树

        Args:
            tree_index: 树索引
            save_path: 保存路径
        """
        try:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(20, 10))
            xgb.plot_tree(self.model, num_trees=tree_index, ax=ax)

            if save_path:
                plt.savefig(save_path)
                logger.info(f"决策树已保存到 {save_path}")
            else:
                plt.show()

        except ImportError:
            logger.error("matplotlib未安装，无法绘制图表")
        except Exception as e:
            logger.error(f"绘制决策树失败: {e}")

    def get_model_params(self) -> Dict[str, Any]:
        """
        获取模型参数

        Returns:
            模型参数字典
        """
        return {
            **self.model_params,
            'n_features': len(self.feature_names) if self.feature_names else 0,
            'is_trained': self.is_trained
        }
