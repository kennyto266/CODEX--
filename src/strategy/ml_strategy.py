"""
机器学习策略 (T182)
机器学习模型集成策略
实现特征工程、模型训练、预测生成和在线学习

Author: Claude Code
Date: 2025-11-09
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
import warnings
warnings.filterwarnings('ignore')

# 机器学习库
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
import joblib

try:
    from core.base_strategy import IStrategy, Signal, SignalType
    from strategy.traits import StrategyTraits
except ImportError:
    from ..core.base_strategy import IStrategy, Signal, SignalType
    from .traits import StrategyTraits

logger = logging.getLogger(__name__)


class MLStrategy(IStrategy):
    """
    机器学习策略

    使用多种机器学习算法进行量化交易决策，
    包括特征工程、模型训练、预测生成和在线学习。

    核心功能：
    1. 自动特征工程和技术指标计算
    2. 多种ML算法支持（RF, GBM, LR, SVM等）
    3. 模型训练、验证和评估
    4. 实时预测和信号生成
    5. 在线学习和模型更新
    6. 特征重要性分析

    策略特点：
    - 数据驱动的决策
    - 自适应学习市场模式
    - 多算法集成
    - 实时模型更新
    """

    def __init__(
        self,
        model_type: str = 'random_forest',
        feature_window: int = 60,
        prediction_horizon: int = 5,
        retrain_frequency: int = 30,
        online_learning: bool = True,
        n_features: int = 50,
        use_ensemble: bool = True
    ):
        """
        初始化机器学习策略

        Args:
            model_type: 模型类型 ('random_forest', 'gradient_boosting', 'logistic', 'svm', 'ensemble')
            feature_window: 特征窗口期
            prediction_horizon: 预测时间跨度
            retrain_frequency: 重新训练频率（天）
            online_learning: 是否启用在线学习
            n_features: 特征数量
            use_ensemble: 是否使用模型集成
        """
        self.model_type = model_type
        self.feature_window = feature_window
        self.prediction_horizon = prediction_horizon
        self.retrain_frequency = retrain_frequency
        self.online_learning = online_learning
        self.n_features = n_features
        self.use_ensemble = use_ensemble

        # 模型存储
        self.model = None
        self.models = {} if use_ensemble else None
        self.scaler = StandardScaler()
        self.feature_selector = None
        self.label_encoder = LabelEncoder()

        # 数据存储
        self.historical_data = None
        self.features = None
        self.labels = None
        self.feature_names = []
        self.last_training_date = None

        # 性能指标
        self.model_accuracy = 0.0
        self.feature_importance = {}
        self.prediction_history = []

        # 特征工程
        self.technical_indicators = [
            'rsi', 'macd', 'bb_position', 'sma_ratio', 'ema_ratio',
            'stoch_k', 'stoch_d', 'williams_r', 'cci', 'atr_ratio',
            'adx', 'di_plus', 'di_minus', 'obv_change', 'mfi'
        ]

        # 特征标记
        self.traits = StrategyTraits(
            name=f"ML-{model_type}",
            timeframe="1D",
            机器学习=True,
            在线学习=True,
            特征工程=True
        )

    @property
    def strategy_name(self) -> str:
        return f"ML-{self.model_type}"

    @property
    def supported_symbols(self) -> List[str]:
        return ['0700.HK', '0388.HK', '1398.HK', '0939.HK', '3988.HK', '2318.HK']

    def _create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        创建机器学习特征

        Args:
            data: OHLCV数据

        Returns:
            特征DataFrame
        """
        df = data.copy()
        features = pd.DataFrame(index=df.index)

        try:
            price = df['Close'] if 'Close' in df.columns else df['close']
            volume = df['Volume'] if 'Volume' in df.columns else df['volume']

            # 价格特征
            features['returns'] = price.pct_change()
            features['log_returns'] = np.log(price / price.shift(1))
            features['high_low_ratio'] = df['High'] / df['Low']
            features['open_close_ratio'] = df['Open'] / df['Close']

            # 移动平均特征
            for window in [5, 10, 20, 50]:
                sma = price.rolling(window).mean()
                features[f'sma_{window}'] = price / sma
                features[f'sma_slope_{window}'] = sma.pct_change(5)

            # 指数移动平均特征
            for span in [12, 26]:
                ema = price.ewm(span=span).mean()
                features[f'ema_{span}'] = price / ema

            # 技术指标特征
            # RSI
            delta = price.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss.replace(0, 1e-10)
            features['rsi'] = 100 - (100 / (1 + rs))

            # MACD
            ema_12 = price.ewm(span=12).mean()
            ema_26 = price.ewm(span=26).mean()
            features['macd'] = ema_12 - ema_26
            features['macd_signal'] = features['macd'].ewm(span=9).mean()
            features['macd_histogram'] = features['macd'] - features['macd_signal']

            # 布林带
            sma_20 = price.rolling(20).mean()
            std_20 = price.rolling(20).std()
            features['bb_upper'] = sma_20 + (std_20 * 2)
            features['bb_lower'] = sma_20 - (std_20 * 2)
            features['bb_position'] = (price - sma_20) / (std_20 * 2)
            features['bb_width'] = (features['bb_upper'] - features['bb_lower']) / sma_20

            # 随机指标
            low_min = df['Low'].rolling(14).min()
            high_max = df['High'].rolling(14).max()
            features['stoch_k'] = 100 * (price - low_min) / (high_max - low_min)
            features['stoch_d'] = features['stoch_k'].rolling(3).mean()

            # Williams %R
            features['williams_r'] = -100 * (high_max - price) / (high_max - low_min)

            # CCI
            typical_price = (df['High'] + df['Low'] + price) / 3
            sma_tp = typical_price.rolling(20).mean()
            mad = typical_price.rolling(20).apply(lambda x: np.mean(np.abs(x - x.mean())))
            features['cci'] = (typical_price - sma_tp) / (0.015 * mad)

            # ATR
            tr1 = df['High'] - df['Low']
            tr2 = abs(df['High'] - price.shift(1))
            tr3 = abs(df['Low'] - price.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            features['atr'] = tr.rolling(14).mean()
            features['atr_ratio'] = features['atr'] / price

            # ADX
            dm_plus = np.where((df['High'] - df['High'].shift(1)) > (df['Low'].shift(1) - df['Low']),
                              np.maximum(df['High'] - df['High'].shift(1), 0), 0)
            dm_minus = np.where((df['Low'].shift(1) - df['Low']) > (df['High'] - df['High'].shift(1)),
                               np.maximum(df['Low'].shift(1) - df['Low'], 0), 0)
            tr_smooth = features['atr']
            di_plus = 100 * pd.Series(dm_plus).rolling(14).mean() / tr_smooth
            di_minus = 100 * pd.Series(dm_minus).rolling(14).mean() / tr_smooth
            features['adx'] = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
            features['di_plus'] = di_plus
            features['di_minus'] = di_minus

            # OBV
            obv = (volume * np.sign(price.diff())).cumsum()
            features['obv'] = obv
            features['obv_change'] = obv.pct_change()

            # MFI
            typical_price = (df['High'] + df['Low'] + price) / 3
            money_flow = typical_price * volume
            positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
            negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
            positive_mf = positive_flow.rolling(14).sum()
            negative_mf = negative_flow.rolling(14).sum()
            mfi_ratio = positive_mf / negative_mf.replace(0, 1e-10)
            features['mfi'] = 100 - (100 / (1 + mfi_ratio))

            # 统计特征
            features['price_volatility'] = features['returns'].rolling(20).std()
            features['volume_ma_ratio'] = volume / volume.rolling(20).mean()
            features['returns_skew'] = features['returns'].rolling(20).skew()
            features['returns_kurt'] = features['returns'].rolling(20).kurt()

            # 滞后特征
            for lag in [1, 2, 3, 5]:
                features[f'returns_lag_{lag}'] = features['returns'].shift(lag)
                features[f'volume_lag_{lag}'] = volume.pct_change().shift(lag)

            # 滚动统计特征
            features['returns_ma_5'] = features['returns'].rolling(5).mean()
            features['returns_ma_10'] = features['returns'].rolling(10).mean()
            features['returns_std_5'] = features['returns'].rolling(5).std()
            features['returns_std_10'] = features['returns'].rolling(10).std()

            # 去除无穷大和NaN值
            features = features.replace([np.inf, -np.inf], np.nan)
            features = features.fillna(method='ffill').fillna(0)

        except Exception as e:
            logger.error(f"特征创建失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return features

    def _create_labels(self, data: pd.DataFrame) -> pd.Series:
        """
        创建标签（目标变量）

        Args:
            data: OHLCV数据

        Returns:
            标签Series
        """
        price = data['Close'] if 'Close' in data.columns else data['close']

        # 计算未来收益率
        future_returns = price.shift(-self.prediction_horizon) / price - 1

        # 创建分类标签
        # 1: 上涨, 0: 下跌/横盘
        labels = np.where(future_returns > 0.02, 1, 0)  # 2%以上涨幅为买入信号

        return pd.Series(labels, index=data.index)

    def _prepare_training_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """
        准备训练数据

        Returns:
            特征和标签
        """
        if self.historical_data is None or len(self.historical_data) < self.feature_window + self.prediction_horizon:
            raise ValueError("历史数据不足")

        # 创建特征
        features = self._create_features(self.historical_data)

        # 创建标签
        labels = self._create_labels(self.historical_data)

        # 对齐特征和标签
        valid_index = features.dropna().index.intersection(labels.dropna().index)
        features = features.loc[valid_index]
        labels = labels.loc[valid_index]

        # 确保有足够的数据
        if len(features) < 100:
            raise ValueError("有效数据不足")

        return features, labels

    def _select_features(self, features: pd.DataFrame, labels: pd.Series) -> Tuple[pd.DataFrame, List[str]]:
        """
        特征选择

        Args:
            features: 原始特征
            labels: 标签

        Returns:
            选择的特征和特征名列表
        """
        try:
            from sklearn.feature_selection import SelectKBest, f_classif

            # 移除常数特征
            features_clean = features.loc[:, features.std() > 1e-8]

            # 特征选择
            if len(features_clean.columns) > self.n_features:
                selector = SelectKBest(score_func=f_classif, k=self.n_features)
                features_selected = selector.fit_transform(features_clean, labels)
                selected_features = features_clean.columns[selector.get_support()].tolist()
                features_df = pd.DataFrame(features_selected, index=features_clean.index, columns=selected_features)
            else:
                features_df = features_clean
                selected_features = features_clean.columns.tolist()

            return features_df, selected_features

        except Exception as e:
            logger.warning(f"特征选择失败: {e}，使用所有特征")
            return features, features.columns.tolist()

    def _initialize_model(self) -> Any:
        """
        初始化机器学习模型

        Returns:
            机器学习模型
        """
        if self.model_type == 'random_forest':
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'gradient_boosting':
            return GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42
            )
        elif self.model_type == 'logistic':
            return LogisticRegression(
                C=1.0,
                max_iter=1000,
                random_state=42
            )
        elif self.model_type == 'svm':
            return SVC(
                C=1.0,
                kernel='rbf',
                probability=True,
                random_state=42
            )
        else:
            return RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            )

    def _initialize_ensemble(self) -> Dict[str, Any]:
        """
        初始化模型集成

        Returns:
            模型字典
        """
        return {
            'rf': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
            'gb': GradientBoostingClassifier(n_estimators=100, random_state=42),
            'lr': LogisticRegression(C=1.0, max_iter=1000, random_state=42)
        }

    def train_model(self, features: pd.DataFrame, labels: pd.Series) -> None:
        """
        训练机器学习模型

        Args:
            features: 特征数据
            labels: 标签数据
        """
        try:
            # 特征选择
            features_selected, self.feature_names = self._select_features(features, labels)

            # 标准化特征
            features_scaled = self.scaler.fit_transform(features_selected)

            # 分割训练和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                features_scaled, labels, test_size=0.2, random_state=42, stratify=labels
            )

            if self.use_ensemble:
                # 训练集成模型
                self.models = self._initialize_ensemble()
                for name, model in self.models.items():
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                    accuracy = accuracy_score(y_test, y_pred)
                    logger.info(f"模型 {name} 准确率: {accuracy:.4f}")
            else:
                # 训练单模型
                self.model = self._initialize_model()
                self.model.fit(X_train, y_train)

                # 评估模型
                y_pred = self.model.predict(X_test)
                self.model_accuracy = accuracy_score(y_test, y_pred)

                # 打印分类报告
                logger.info(f"模型准确率: {self.model_accuracy:.4f}")
                logger.info(f"\n分类报告:\n{classification_report(y_test, y_pred)}")

                # 特征重要性
                if hasattr(self.model, 'feature_importances_'):
                    importance = self.model.feature_importances_
                    self.feature_importance = {
                        name: imp for name, imp in zip(self.feature_names, importance)
                    }

            self.last_training_date = datetime.now()
            logger.info("模型训练完成")

        except Exception as e:
            logger.error(f"模型训练失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def _make_prediction(self, features: pd.DataFrame) -> Tuple[int, float]:
        """
        进行预测

        Args:
            features: 特征数据

        Returns:
            (预测类别, 预测概率)
        """
        if self.use_ensemble and self.models:
            # 集成预测
            features_scaled = self.scaler.transform(features)
            predictions = []
            probabilities = []

            for name, model in self.models.items():
                pred = model.predict(features_scaled)[0]
                prob = model.predict_proba(features_scaled)[0]
                predictions.append(pred)
                probabilities.append(prob)

            # 投票
            final_pred = int(np.round(np.mean(predictions)))
            final_prob = np.mean(probabilities, axis=0)

            return final_pred, final_prob[1] if final_prob.shape[0] > 1 else 0.5

        elif self.model:
            # 单模型预测
            features_scaled = self.scaler.transform(features)
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]

            return int(prediction), probabilities[1] if len(probabilities) > 1 else 0.5

        else:
            return 0, 0.5

    def initialize(self, historical_data: pd.DataFrame, **kwargs) -> None:
        """
        初始化策略

        Args:
            historical_data: 历史数据
            **kwargs: 额外参数
        """
        try:
            self.historical_data = historical_data.copy()

            # 准备训练数据
            features, labels = self._prepare_training_data()

            # 训练模型
            self.train_model(features, labels)

            logger.info(f"机器学习策略初始化完成: {self.strategy_name}")

        except Exception as e:
            logger.error(f"策略初始化失败: {e}")
            raise

    def generate_signals(self, current_data: pd.DataFrame) -> List[Signal]:
        """
        生成机器学习信号

        Args:
            current_data: 当前市场数据

        Returns:
            信号列表
        """
        signals = []

        try:
            # 更新历史数据
            if self.historical_data is not None:
                self.historical_data = pd.concat([self.historical_data, current_data]).drop_duplicates()
                self.historical_data = self.historical_data.sort_index()
            else:
                self.historical_data = current_data.copy()

            # 检查是否需要重新训练
            if (self.last_training_date is None or
                (datetime.now() - self.last_training_date).days >= self.retrain_frequency):
                logger.info("开始重新训练模型")
                features, labels = self._prepare_training_data()
                self.train_model(features, labels)

            # 准备当前特征
            features = self._create_features(self.historical_data)

            # 获取最新的有效特征
            if self.feature_names:
                # 确保特征名对应
                available_features = [f for f in self.feature_names if f in features.columns]
                if available_features:
                    latest_features = features[available_features].iloc[-1:]
                    latest_features = latest_features.fillna(method='ffill').fillna(0)

                    # 进行预测
                    prediction, probability = self._make_prediction(latest_features)

                    # 根据预测和置信度生成信号
                    if probability > 0.6:  # 买入阈值
                        latest_data = current_data.iloc[-1]
                        signal = Signal(
                            symbol=latest_data.get('Symbol', 'UNKNOWN'),
                            timestamp=latest_data.name if isinstance(latest_data.name, pd.Timestamp) else pd.Timestamp.now(),
                            signal_type=SignalType.BUY,
                            confidence=float(probability),
                            reason=f"机器学习预测 - 上涨概率: {probability:.2f}",
                            price=float(latest_data['Close']),
                            metadata={
                                'model_type': self.model_type,
                                'prediction': prediction,
                                'probability': probability,
                                'model_accuracy': self.model_accuracy,
                                'feature_importance': dict(list(self.feature_importance.items())[:10])  # 前10个重要特征
                            }
                        )
                        signals.append(signal)

                    elif probability < 0.4:  # 卖出阈值
                        latest_data = current_data.iloc[-1]
                        signal = Signal(
                            symbol=latest_data.get('Symbol', 'UNKNOWN'),
                            timestamp=latest_data.name if isinstance(latest_data.name, pd.Timestamp) else pd.Timestamp.now(),
                            signal_type=SignalType.SELL,
                            confidence=float(1 - probability),
                            reason=f"机器学习预测 - 下跌概率: {1 - probability:.2f}",
                            price=float(latest_data['Close']),
                            metadata={
                                'model_type': self.model_type,
                                'prediction': prediction,
                                'probability': probability,
                                'model_accuracy': self.model_accuracy,
                                'feature_importance': dict(list(self.feature_importance.items())[:10])
                            }
                        )
                        signals.append(signal)

                    # 记录预测历史
                    self.prediction_history.append({
                        'timestamp': datetime.now(),
                        'prediction': prediction,
                        'probability': probability
                    })

                    # 保持历史长度
                    if len(self.prediction_history) > 1000:
                        self.prediction_history.pop(0)

        except Exception as e:
            logger.error(f"信号生成失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return signals

    def get_parameters(self) -> Dict[str, Any]:
        """获取策略参数"""
        return {
            'model_type': self.model_type,
            'feature_window': self.feature_window,
            'prediction_horizon': self.prediction_horizon,
            'retrain_frequency': self.retrain_frequency,
            'online_learning': self.online_learning,
            'n_features': self.n_features,
            'use_ensemble': self.use_ensemble,
            'model_accuracy': self.model_accuracy,
            'last_training_date': self.last_training_date.isoformat() if self.last_training_date else None
        }

    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """设置策略参数"""
        if 'model_type' in parameters:
            self.model_type = parameters['model_type']
        if 'feature_window' in parameters:
            self.feature_window = parameters['feature_window']
        if 'prediction_horizon' in parameters:
            self.prediction_horizon = parameters['prediction_horizon']
        if 'retrain_frequency' in parameters:
            self.retrain_frequency = parameters['retrain_frequency']
        if 'online_learning' in parameters:
            self.online_learning = parameters['online_learning']
        if 'n_features' in parameters:
            self.n_features = parameters['n_features']
        if 'use_ensemble' in parameters:
            self.use_ensemble = parameters['use_ensemble']

    def save_model(self, filepath: str) -> None:
        """
        保存模型

        Args:
            filepath: 模型保存路径
        """
        model_data = {
            'model': self.model,
            'models': self.models,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'feature_importance': self.feature_importance,
            'model_type': self.model_type,
            'model_accuracy': self.model_accuracy,
            'parameters': self.get_parameters()
        }
        joblib.dump(model_data, filepath)
        logger.info(f"模型已保存到: {filepath}")

    def load_model(self, filepath: str) -> None:
        """
        加载模型

        Args:
            filepath: 模型文件路径
        """
        model_data = joblib.load(filepath)
        self.model = model_data.get('model')
        self.models = model_data.get('models')
        self.scaler = model_data.get('scaler')
        self.feature_names = model_data.get('feature_names', [])
        self.feature_importance = model_data.get('feature_importance', {})
        self.model_type = model_data.get('model_type', 'random_forest')
        self.model_accuracy = model_data.get('model_accuracy', 0.0)
        logger.info(f"模型已从 {filepath} 加载")

    def get_ml_summary(self) -> Dict[str, Any]:
        """
        获取机器学习策略摘要

        Returns:
            包含ML模型信息的字典
        """
        return {
            'strategy_name': self.strategy_name,
            'model_type': self.model_type,
            'model_accuracy': self.model_accuracy,
            'feature_count': len(self.feature_names),
            'feature_names': self.feature_names[:20],  # 前20个特征
            'feature_importance': dict(sorted(self.feature_importance.items(),
                                             key=lambda x: x[1], reverse=True)[:10]),
            'last_training_date': self.last_training_date.isoformat() if self.last_training_date else None,
            'retrain_frequency': self.retrain_frequency,
            'use_ensemble': self.use_ensemble,
            'prediction_history_length': len(self.prediction_history),
            'recent_predictions': self.prediction_history[-10:] if self.prediction_history else []
        }


# 导出策略类
__all__ = ['MLStrategy']
