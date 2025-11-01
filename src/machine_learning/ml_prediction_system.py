"""
机器学习预测系统
集成多种ML模型，提供统一的预测接口
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from .base_model import BaseMLModel
from .feature_engineering import FeatureEngine
from .models.lstm_model import LSTMModel
from .models.random_forest_model import RandomForestModel
from .models.xgboost_model import XGBoostModel

logger = logging.getLogger(__name__)


class MLPredictionSystem:
    """机器学习预测系统"""

    def __init__(self, models: Optional[List[str]] = None):
        """
        初始化ML预测系统

        Args:
            models: 要使用的模型列表 (如: ['lstm', 'rf', 'xgboost'])
        """
        # 默认模型
        if models is None:
            models = ['rf', 'xgboost']  # 默认使用随机森林和XGBoost

        self.models = {}
        self.feature_engine = FeatureEngine()
        self.model_names = models
        self.training_history = {}
        self.prediction_cache = {}

        # 初始化模型
        self._initialize_models(models)

        logger.info(f"ML预测系统已初始化，模型: {models}")

    def _initialize_models(self, model_names: List[str]):
        """
        初始化指定模型

        Args:
            model_names: 模型名称列表
        """
        for name in model_names:
            if name.lower() == 'lstm':
                self.models['lstm'] = LSTMModel()
            elif name.lower() == 'rf':
                self.models['rf'] = RandomForestModel()
            elif name.lower() == 'xgboost':
                self.models['xgboost'] = XGBoostModel()
            else:
                logger.warning(f"未知模型类型: {name}")

    def prepare_data(self, data: pd.DataFrame, target_type: str = 'next_return',
                    periods: int = 1) -> Tuple[pd.DataFrame, pd.Series]:
        """
        准备训练数据

        Args:
            data: 原始股票数据
            target_type: 目标类型
            periods: 预测周期

        Returns:
            特征数据, 目标数据
        """
        try:
            # 创建特征
            features = self.feature_engine.create_all_features(data)

            # 创建目标变量
            target = self.feature_engine.create_target(
                data, target_type=target_type, periods=periods
            )

            # 对齐特征和目标
            min_len = min(len(features), len(target))
            features = features.iloc[:min_len]
            target = target.iloc[:min_len]

            # 移除包含NaN的行
            valid_idx = ~(features.isnull().any(axis=1) | target.isnull())
            features = features[valid_idx]
            target = target[valid_idx]

            logger.info(f"数据准备完成 - 特征: {features.shape}, 目标: {len(target)}")

            return features, target

        except Exception as e:
            logger.error(f"数据准备失败: {e}")
            raise

    def train_all_models(self, data: pd.DataFrame, target_type: str = 'next_return',
                        periods: int = 1, test_size: float = 0.2) -> Dict[str, Dict[str, Any]]:
        """
        训练所有模型

        Args:
            data: 原始股票数据
            target_type: 目标类型
            periods: 预测周期
            test_size: 测试集比例

        Returns:
            训练结果字典
        """
        try:
            # 准备数据
            X, y = self.prepare_data(data, target_type, periods)

            # 分割数据
            split_idx = int(len(X) * (1 - test_size))
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

            results = {}

            # 训练每个模型
            for model_name, model in self.models.items():
                logger.info(f"开始训练模型: {model_name}")

                try:
                    # 训练
                    train_result = model.train(X_train, y_train)

                    # 评估
                    if len(X_test) > 0 and len(y_test) > 0:
                        eval_result = model.evaluate(X_test, y_test)
                        train_result.update(eval_result)

                    # 获取特征重要性 (如果有)
                    if hasattr(model, 'get_feature_importance'):
                        try:
                            importance = model.get_feature_importance()
                            train_result['top_features'] = dict(list(importance.items())[:10])
                        except:
                            pass

                    results[model_name] = train_result
                    logger.info(f"模型 {model_name} 训练完成")

                except Exception as e:
                    logger.error(f"模型 {model_name} 训练失败: {e}")
                    results[model_name] = {'status': 'error', 'error': str(e)}

            # 保存训练历史
            self.training_history = {
                'timestamp': datetime.now().isoformat(),
                'data_shape': data.shape,
                'feature_count': len(X.columns),
                'results': results
            }

            return results

        except Exception as e:
            logger.error(f"训练所有模型失败: {e}")
            return {}

    def predict(self, data: pd.DataFrame, model_name: Optional[str] = None,
               ensemble_method: str = 'average') -> Dict[str, np.ndarray]:
        """
        预测

        Args:
            data: 股票数据
            model_name: 指定模型名称，如果为None则使用所有模型
            ensemble_method: 集成方法 ('average', 'weighted')

        Returns:
            预测结果字典
        """
        try:
            # 准备特征
            features = self.feature_engine.create_all_features(data)

            # 移除原始数据列
            columns_to_remove = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
            features = features.drop(columns=columns_to_remove, errors='ignore')

            # 填充NaN
            features = features.fillna(features.mean())

            predictions = {}

            # 单模型预测
            if model_name:
                if model_name not in self.models:
                    raise ValueError(f"模型 {model_name} 不存在")
                model = self.models[model_name]
                if model.is_trained:
                    pred = model.predict(features)
                    predictions[model_name] = pred
                else:
                    logger.warning(f"模型 {model_name} 尚未训练")
            else:
                # 多模型预测
                for name, model in self.models.items():
                    if model.is_trained:
                        try:
                            pred = model.predict(features)
                            predictions[name] = pred
                        except Exception as e:
                            logger.error(f"模型 {name} 预测失败: {e}")

            # 集成预测
            if len(predictions) > 1:
                if ensemble_method == 'average':
                    predictions['ensemble'] = np.mean(
                        list(predictions.values()), axis=0
                    )
                elif ensemble_method == 'weighted':
                    # 简化的加权平均 (实际应该基于模型性能)
                    weights = np.ones(len(predictions)) / len(predictions)
                    ensemble = np.zeros(len(list(predictions.values())[0]))
                    for i, (name, pred) in enumerate(predictions.items()):
                        if name != 'ensemble':
                            ensemble += weights[i] * pred
                    predictions['ensemble'] = ensemble

            return predictions

        except Exception as e:
            logger.error(f"预测失败: {e}")
            return {}

    def predict_probability(self, data: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        预测概率 (仅适用于分类模型)

        Args:
            data: 股票数据

        Returns:
            概率预测字典
        """
        try:
            features = self.feature_engine.create_all_features(data)
            features = features.drop(columns=['open', 'high', 'low', 'close', 'volume', 'timestamp'], errors='ignore')
            features = features.fillna(features.mean())

            probabilities = {}

            for name, model in self.models.items():
                if model.is_trained and hasattr(model, 'predict_proba'):
                    try:
                        prob = model.predict_proba(features)
                        probabilities[name] = prob
                    except Exception as e:
                        logger.error(f"模型 {name} 概率预测失败: {e}")

            return probabilities

        except Exception as e:
            logger.error(f"概率预测失败: {e}")
            return {}

    def generate_signals(self, data: pd.DataFrame, threshold: float = 0.02,
                        model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        基于预测生成交易信号

        Args:
            data: 股票数据
            threshold: 信号阈值
            model_name: 指定模型

        Returns:
            交易信号字典
        """
        try:
            # 预测
            predictions = self.predict(data, model_name=model_name)

            if not predictions:
                return {'signal': 'HOLD', 'confidence': 0, 'prediction': 0}

            # 使用集成预测或指定模型预测
            pred_key = model_name if model_name else 'ensemble'
            if pred_key not in predictions:
                pred_key = list(predictions.keys())[0]

            pred_values = predictions[pred_key]

            # 生成信号
            latest_pred = pred_values[-1] if len(pred_values) > 0 else 0

            if latest_pred > threshold:
                signal = 'BUY'
                confidence = min(latest_pred / threshold, 1.0)
            elif latest_pred < -threshold:
                signal = 'SELL'
                confidence = min(abs(latest_pred) / threshold, 1.0)
            else:
                signal = 'HOLD'
                confidence = 1.0 - (abs(latest_pred) / threshold)

            return {
                'signal': signal,
                'confidence': float(confidence),
                'prediction': float(latest_pred),
                'threshold': threshold,
                'model_used': pred_key
            }

        except Exception as e:
            logger.error(f"生成交易信号失败: {e}")
            return {
                'signal': 'HOLD',
                'confidence': 0,
                'prediction': 0,
                'error': str(e)
            }

    def backtest_strategy(self, data: pd.DataFrame, start_date: str,
                         end_date: str, initial_capital: float = 100000) -> Dict[str, Any]:
        """
        回测ML策略

        Args:
            data: 股票数据
            start_date: 开始日期
            end_date: 结束日期
            initial_capital: 初始资金

        Returns:
            回测结果
        """
        try:
            # 筛选日期范围
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            mask = (data['timestamp'] >= start_date) & (data['timestamp'] <= end_date)
            backtest_data = data[mask].copy()

            if len(backtest_data) < 100:
                raise ValueError("回测数据不足")

            # 训练模型
            train_results = self.train_all_models(backtest_data)

            # 逐日回测
            portfolio = {
                'cash': initial_capital,
                'shares': 0,
                'value': initial_capital,
                'trades': [],
                'equity_curve': []
            }

            for i in range(50, len(backtest_data)):  # 留出足够的数据用于特征计算
                current_data = backtest_data.iloc[:i+1]

                # 生成信号
                signal_info = self.generate_signals(current_data, threshold=0.01)

                # 执行交易 (简化实现)
                current_price = current_data['close'].iloc[-1]

                if signal_info['signal'] == 'BUY' and portfolio['cash'] > current_price:
                    # 买入
                    shares_to_buy = int(portfolio['cash'] / current_price * 0.1)  # 每次用10%资金
                    if shares_to_buy > 0:
                        cost = shares_to_buy * current_price
                        portfolio['cash'] -= cost
                        portfolio['shares'] += shares_to_buy
                        portfolio['trades'].append({
                            'date': current_data['timestamp'].iloc[-1],
                            'action': 'BUY',
                            'shares': shares_to_buy,
                            'price': current_price,
                            'cost': cost
                        })

                elif signal_info['signal'] == 'SELL' and portfolio['shares'] > 0:
                    # 卖出
                    shares_to_sell = int(portfolio['shares'] * 0.1)  # 每次卖出10%
                    if shares_to_sell > 0:
                        revenue = shares_to_sell * current_price
                        portfolio['cash'] += revenue
                        portfolio['shares'] -= shares_to_sell
                        portfolio['trades'].append({
                            'date': current_data['timestamp'].iloc[-1],
                            'action': 'SELL',
                            'shares': shares_to_sell,
                            'price': current_price,
                            'revenue': revenue
                        })

                # 计算总价值
                portfolio['value'] = portfolio['cash'] + portfolio['shares'] * current_price
                portfolio['equity_curve'].append({
                    'date': current_data['timestamp'].iloc[-1],
                    'value': portfolio['value']
                })

            # 计算绩效指标
            equity_values = [p['value'] for p in portfolio['equity_curve']]
            returns = np.diff(equity_values) / equity_values[:-1]

            total_return = (equity_values[-1] - initial_capital) / initial_capital
            volatility = np.std(returns) * np.sqrt(252) if len(returns) > 0 else 0
            sharpe_ratio = (np.mean(returns) * 252) / volatility if volatility > 0 else 0

            # 计算最大回撤
            peak = np.maximum.accumulate(equity_values)
            drawdown = (peak - equity_values) / peak
            max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0

            results = {
                'total_return': total_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'total_trades': len(portfolio['trades']),
                'final_value': portfolio['value'],
                'initial_capital': initial_capital,
                'equity_curve': portfolio['equity_curve'],
                'trades': portfolio['trades'],
                'train_results': train_results
            }

            logger.info(f"回测完成 - 总收益: {total_return:.2%}, 夏普比率: {sharpe_ratio:.2f}")

            return results

        except Exception as e:
            logger.error(f"回测失败: {e}")
            return {}

    def get_model_info(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有模型信息

        Returns:
            模型信息字典
        """
        info = {}
        for name, model in self.models.items():
            try:
                info[name] = model.get_info()
            except Exception as e:
                info[name] = {'error': str(e)}

        return info

    def save_models(self, directory: str):
        """
        保存所有模型

        Args:
            directory: 保存目录
        """
        import os
        os.makedirs(directory, exist_ok=True)

        for name, model in self.models.items():
            model_path = os.path.join(directory, f"{name}_model.pkl")
            model.save_model(model_path)

        logger.info(f"所有模型已保存到 {directory}")

    def load_models(self, directory: str):
        """
        加载所有模型

        Args:
            directory: 模型目录
        """
        import os

        for name in self.model_names:
            if name.lower() in ['lstm', 'rf', 'xgboost']:
                model_path = os.path.join(directory, f"{name.lower()}_model.pkl")

                if os.path.exists(model_path):
                    # 重新创建模型实例
                    if name.lower() == 'lstm':
                        self.models[name.lower()] = LSTMModel()
                    elif name.lower() == 'rf':
                        self.models[name.lower()] = RandomForestModel()
                    elif name.lower() == 'xgboost':
                        self.models[name.lower()] = XGBoostModel()

                    self.models[name.lower()].load_model(model_path)

        logger.info(f"模型已从 {directory} 加载")

    def __str__(self) -> str:
        return f"MLPredictionSystem(models={list(self.models.keys())}, trained={sum(1 for m in self.models.values() if m.is_trained)})"
