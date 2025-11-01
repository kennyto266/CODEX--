"""
LSTM深度学习模型
用于时间序列预测
"""

import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.regularizers import l2
import logging
from typing import Dict, List, Optional, Tuple, Any
import joblib
from sklearn.preprocessing import MinMaxScaler

from ..base_model import BaseMLModel

logger = logging.getLogger(__name__)


class LSTMModel(BaseMLModel):
    """LSTM神经网络模型"""

    def __init__(self, name: str = "LSTM", sequence_length: int = 60,
                 lstm_units: List[int] = [50, 50], dropout_rate: float = 0.2,
                 learning_rate: float = 0.001, epochs: int = 100,
                 batch_size: int = 32):
        """
        初始化LSTM模型

        Args:
            name: 模型名称
            sequence_length: 序列长度 (时间步)
            lstm_units: LSTM层神经元数量列表
            dropout_rate: Dropout比例
            learning_rate: 学习率
            epochs: 训练轮数
            batch_size: 批次大小
        """
        super().__init__(name, 'lstm')

        self.sequence_length = sequence_length
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size

        self.model_params = {
            'sequence_length': sequence_length,
            'lstm_units': lstm_units,
            'dropout_rate': dropout_rate,
            'learning_rate': learning_rate,
            'epochs': epochs,
            'batch_size': batch_size
        }

        self.scaler_X = MinMaxScaler()
        self.scaler_y = MinMaxScaler()

    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        准备LSTM特征数据

        Args:
            data: 原始股票数据

        Returns:
            特征数据框
        """
        # 这里应该使用FeatureEngine创建特征
        # 简化实现，直接返回数值列
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        return data[numeric_cols].copy()

    def _create_sequences(self, X: np.ndarray, y: np.ndarray,
                         sequence_length: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        创建LSTM序列数据

        Args:
            X: 特征数据
            y: 目标数据
            sequence_length: 序列长度

        Returns:
            X序列, y序列
        """
        sequences_X = []
        sequences_y = []

        for i in range(len(X) - sequence_length + 1):
            sequences_X.append(X[i:i + sequence_length])
            sequences_y.append(y[i + sequence_length - 1])

        return np.array(sequences_X), np.array(sequences_y)

    def _build_model(self, input_shape: Tuple[int, int]) -> tf.keras.Model:
        """
        构建LSTM模型

        Args:
            input_shape: 输入形状 (时间步, 特征数)

        Returns:
            Keras模型
        """
        model = Sequential()

        # 第一层LSTM
        model.add(LSTM(
            self.lstm_units[0],
            return_sequences=len(self.lstm_units) > 1,
            input_shape=input_shape,
            kernel_regularizer=l2(0.001)
        ))
        model.add(BatchNormalization())
        model.add(Dropout(self.dropout_rate))

        # 中间LSTM层
        for i in range(1, len(self.lstm_units)):
            model.add(LSTM(
                self.lstm_units[i],
                return_sequences=i < len(self.lstm_units) - 1,
                kernel_regularizer=l2(0.001)
            ))
            model.add(BatchNormalization())
            model.add(Dropout(self.dropout_rate))

        # 全连接层
        model.add(Dense(25, activation='relu'))
        model.add(Dropout(self.dropout_rate / 2))
        model.add(Dense(1, activation='linear'))

        # 编译模型
        optimizer = Adam(learning_rate=self.learning_rate)
        model.compile(
            optimizer=optimizer,
            loss='mse',
            metrics=['mae']
        )

        return model

    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        训练LSTM模型

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

            # 处理缺失值
            X = X.fillna(X.mean())
            y = y.fillna(y.mean())

            # 标准化
            X_scaled = self.scaler_X.fit_transform(X)
            y_scaled = self.scaler_y.fit_transform(y.values.reshape(-1, 1)).flatten()

            # 创建序列
            X_seq, y_seq = self._create_sequences(
                X_scaled, y_scaled, self.sequence_length
            )

            if len(X_seq) == 0:
                raise ValueError(f"数据量不足，无法创建序列 (需要 {self.sequence_length})")

            # 构建模型
            self.model = self._build_model((X_seq.shape[1], X_seq.shape[2]))

            # 回调函数
            callbacks = [
                EarlyStopping(
                    monitor='val_loss',
                    patience=15,
                    restore_best_weights=True,
                    verbose=1
                ),
                ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=10,
                    min_lr=1e-6,
                    verbose=1
                )
            ]

            # 训练模型
            history = self.model.fit(
                X_seq, y_seq,
                epochs=self.epochs,
                batch_size=self.batch_size,
                validation_split=0.2,
                callbacks=callbacks,
                verbose=1
            )

            self.is_trained = True
            self.last_trained = pd.Timestamp.now()

            # 保存训练历史
            self.training_history = {
                'loss': history.history['loss'],
                'val_loss': history.history['val_loss'],
                'mae': history.history['mae'],
                'val_mae': history.history['val_mae']
            }

            # 计算最终指标
            final_loss = min(history.history['val_loss'])
            final_mae = min(history.history['val_mae'])

            logger.info(f"LSTM模型训练完成 - Val Loss: {final_loss:.4f}, Val MAE: {final_mae:.4f}")

            return {
                'status': 'success',
                'final_loss': final_loss,
                'final_mae': final_mae,
                'epochs_trained': len(history.history['loss']),
                'train_samples': len(X_seq)
            }

        except Exception as e:
            logger.error(f"LSTM训练失败: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        LSTM预测

        Args:
            X: 特征数据

        Returns:
            预测结果
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")

        try:
            # 标准化
            X_scaled = self.scaler_X.transform(X)

            # 创建序列
            X_seq, _ = self._create_sequences(
                X_scaled, np.zeros(len(X_scaled)), self.sequence_length
            )

            if len(X_seq) == 0:
                logger.warning("预测数据不足，返回空预测")
                return np.array([])

            # 预测
            y_pred_scaled = self.model.predict(X_seq, verbose=0)

            # 反标准化
            y_pred = self.scaler_y.inverse_transform(y_pred_scaled).flatten()

            return y_pred

        except Exception as e:
            logger.error(f"LSTM预测失败: {e}")
            return np.array([])

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        LSTM不提供概率预测，抛出异常

        Args:
            X: 特征数据

        Returns:
            不支持
        """
        raise NotImplementedError("LSTM模型不提供概率预测")

    def predict_sequence(self, X: pd.DataFrame, steps: int = 5) -> np.ndarray:
        """
        多步预测

        Args:
            X: 特征数据
            steps: 预测步数

        Returns:
            多步预测结果
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")

        predictions = []

        # 获取最后的序列
        X_scaled = self.scaler_X.transform(X)
        current_seq = X_scaled[-self.sequence_length:].reshape(1, self.sequence_length, -1)

        for _ in range(steps):
            # 预测下一步
            next_pred_scaled = self.model.predict(current_seq, verbose=0)
            next_pred = self.scaler_y.inverse_transform(next_pred_scaled)[0, 0]

            predictions.append(next_pred)

            # 更新序列 (简化实现)
            break

        return np.array(predictions)

    def get_feature_importance(self) -> Dict[str, float]:
        """
        获取特征重要性 (LSTM无法直接提供特征重要性)

        Returns:
            空字典
        """
        logger.warning("LSTM模型不支持特征重要性分析")
        return {}

    def save_model(self, filepath: str) -> bool:
        """
        保存LSTM模型

        Args:
            filepath: 保存路径

        Returns:
            是否保存成功
        """
        try:
            # 保存模型架构和权重
            if self.is_trained:
                self.model.save(f"{filepath}_keras_model")

            # 保存其他属性
            model_data = {
                'name': self.name,
                'model_type': self.model_type,
                'is_trained': self.is_trained,
                'training_history': self.training_history,
                'model_params': self.model_params,
                'scaler_X': self.scaler_X,
                'scaler_y': self.scaler_y,
                'created_at': self.created_at,
                'last_trained': self.last_trained
            }

            with open(f"{filepath}_data.pkl", 'wb') as f:
                joblib.dump(model_data, f)

            logger.info(f"LSTM模型已保存到 {filepath}")
            return True

        except Exception as e:
            logger.error(f"LSTM模型保存失败: {e}")
            return False

    def load_model(self, filepath: str) -> bool:
        """
        加载LSTM模型

        Args:
            filepath: 模型文件路径

        Returns:
            是否加载成功
        """
        try:
            # 加载其他属性
            with open(f"{filepath}_data.pkl", 'rb') as f:
                model_data = joblib.load(f)

            self.name = model_data['name']
            self.model_type = model_data['model_type']
            self.is_trained = model_data['is_trained']
            self.training_history = model_data['training_history']
            self.model_params = model_data['model_params']
            self.scaler_X = model_data['scaler_X']
            self.scaler_y = model_data['scaler_y']
            self.created_at = model_data['created_at']
            self.last_trained = model_data['last_trained']

            # 加载Keras模型
            if self.is_trained:
                self.model = tf.keras.models.load_model(f"{filepath}_keras_model")

            logger.info(f"LSTM模型已从 {filepath} 加载")
            return True

        except Exception as e:
            logger.error(f"LSTM模型加载失败: {e}")
            return False
