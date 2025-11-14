"""Optimization Result Model.

This module defines the OptimizationResult entity for storing parameter
optimization results and performance metrics.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4


class DateRange(BaseModel):
    """日期範圍模型。

    存儲優化的日期範圍。
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start": "2020-01-01",
                "end": "2023-12-31"
            }
        }
    )

    start: date = Field(
        ...,
        description="開始日期 (YYYY-MM-DD格式)"
    )
    end: date = Field(
        ...,
        description="結束日期 (YYYY-MM-DD格式)"
    )

    @field_validator('end')
    @classmethod
    def validate_date_order(cls, v: date, info) -> date:
        """驗證日期順序。

        Args:
            v: 結束日期
            info: 字段信息

        Returns:
            驗證後的結束日期

        Raises:
            ValueError: 結束日期早於開始日期
        """
        if 'start' in info.data and v <= info.data['start']:
            raise ValueError("End date must be after start date")
        return v

    def to_dict(self) -> Dict[str, str]:
        """轉換為字典。

        Returns:
            字典格式的日期
        """
        return {
            'start': self.start.isoformat(),
            'end': self.end.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'DateRange':
        """從字典創建實例。

        Args:
            data: 字典數據

        Returns:
            DateRange實例
        """
        return cls(
            start=date.fromisoformat(data['start']),
            end=date.fromisoformat(data['end'])
        )


class OptimizationMetrics(BaseModel):
    """優化指標模型。

    存儲策略優化的性能指標。
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_return": 25.5,
                "annualized_return": 8.2,
                "sharpe_ratio": 1.5,
                "sortino_ratio": 2.1,
                "max_drawdown": -6.8,
                "win_rate": 68.0,
                "profit_factor": 1.8,
                "trade_count": 150,
                "avg_trade_return": 0.17,
                "volatility": 12.3
            }
        }
    )

    total_return: float = Field(
        ...,
        description="總收益率 (百分比)",
        ge=-100.0,
        le=1000.0
    )
    annualized_return: float = Field(
        ...,
        description="年化收益率 (百分比)",
        ge=-100.0,
        le=1000.0
    )
    sharpe_ratio: float = Field(
        ...,
        description="夏普比率",
        ge=-10.0,
        le=10.0
    )
    sortino_ratio: float = Field(
        ...,
        description="Sortino比率",
        ge=-10.0,
        le=10.0
    )
    max_drawdown: float = Field(
        ...,
        description="最大回撤 (百分比)",
        le=0.0
    )
    win_rate: float = Field(
        ...,
        description="勝率 (百分比)",
        ge=0.0,
        le=100.0
    )
    profit_factor: float = Field(
        ...,
        description="盈虧比",
        ge=0.0
    )
    trade_count: int = Field(
        ...,
        description="交易次數",
        ge=0
    )
    avg_trade_return: float = Field(
        ...,
        description="平均交易收益率 (百分比)",
        ge=-100.0,
        le=1000.0
    )
    volatility: float = Field(
        ...,
        description="波動率 (百分比)",
        ge=0.0
    )


class OptimizationResult(BaseModel):
    """優化結果模型。

    存儲參數優化的結果和性能指標。
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "result_id": "a1b2c3d4-5678-90ab-cdef-123456789abc",
                "strategy_type": "KDJ",
                "symbol": "0700.HK",
                "date_range": {
                    "start": "2020-01-01",
                    "end": "2023-12-31"
                },
                "parameters": {
                    "k_period": 9,
                    "d_period": 3,
                    "oversold": 20,
                    "overbought": 80
                },
                "metrics": {
                    "total_return": 25.5,
                    "annualized_return": 8.2,
                    "sharpe_ratio": 1.5,
                    "sortino_ratio": 2.1,
                    "max_drawdown": -6.8,
                    "win_rate": 68.0,
                    "profit_factor": 1.8,
                    "trade_count": 150,
                    "avg_trade_return": 0.17,
                    "volatility": 12.3
                },
                "execution_time_ms": 1250,
                "memory_usage_mb": 256.5,
                "worker_count": 8,
                "user_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        },
        str_strip_whitespace=True,
        validate_assignment=True
    )

    result_id: UUID = Field(
        default_factory=uuid4,
        description="優化結果唯一標識符 (UUID格式)"
    )
    strategy_type: str = Field(
        ...,
        description="策略類型"
    )
    symbol: str = Field(
        ...,
        description="股票代碼",
        min_length=5,
        max_length=10
    )
    date_range: DateRange = Field(
        ...,
        description="優化日期範圍"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="優化參數組合"
    )
    metrics: OptimizationMetrics = Field(
        ...,
        description="性能指標"
    )
    execution_time_ms: int = Field(
        ...,
        description="執行時間 (毫秒)",
        gt=0
    )
    memory_usage_mb: float = Field(
        ...,
        description="內存使用 (MB)",
        gt=0.0
    )
    worker_count: int = Field(
        default=1,
        description="並行工作數",
        ge=1
    )
    user_id: UUID = Field(
        ...,
        description="用戶ID (關聯到UserConfig)"
    )
    template_id: Optional[UUID] = Field(
        default=None,
        description="關聯的策略模板ID (可選)"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="創建時間"
    )

    @field_validator('strategy_type')
    @classmethod
    def validate_strategy_type(cls, v: str) -> str:
        """驗證策略類型。

        Args:
            v: 策略類型

        Returns:
            驗證後的策略類型

        Raises:
            ValueError: 策略類型不在允許範圍內
        """
        allowed_types = [
            'MA', 'RSI', 'MACD', 'KDJ', 'CCI',
            'ADX', 'ATR', 'OBV', 'Ichimoku', 'SAR',
            'Bollinger', 'Stochastic', 'WilliamsR', 'Custom'
        ]
        if v not in allowed_types:
            raise ValueError(
                f"strategy_type must be one of: {', '.join(allowed_types)}"
            )
        return v

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """驗證股票代碼。

        Args:
            v: 股票代碼

        Returns:
            驗證後的代碼

        Raises:
            ValueError: 代碼格式不符合要求
        """
        if not isinstance(v, str) or len(v) < 5 or len(v) > 10:
            raise ValueError("Symbol must be 5-10 characters long")
        return v

    @field_validator('parameters')
    @classmethod
    def validate_parameters(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """驗證參數。

        Args:
            v: 參數字典

        Returns:
            驗證後的參數

        Raises:
            ValueError: 參數驗證失敗
        """
        if not isinstance(v, dict):
            raise ValueError("Parameters must be a dictionary")

        # 檢查參數名稱
        for key in v.keys():
            if not isinstance(key, str) or not key:
                raise ValueError(
                    f"Parameter key {key} must be a non-empty string"
                )

        return v

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """序列化為字典。

        覆蓋基類方法以處理UUID和datetime序列化。
        """
        data = super().model_dump(**kwargs)
        # 轉換UUID為字符串
        data['result_id'] = str(self.result_id)
        data['user_id'] = str(self.user_id)
        if self.template_id is not None:
            data['template_id'] = str(self.template_id)
        # 轉換datetime為ISO格式字符串
        data['created_at'] = self.created_at.isoformat()
        # 轉換date為ISO格式字符串
        data['date_range'] = self.date_range.to_dict()
        return data

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典。

        Returns:
            包含優化結果的字典
        """
        return self.model_dump()

    def to_json(self) -> str:
        """轉換為JSON字符串。

        Returns:
            JSON格式的字符串
        """
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> 'OptimizationResult':
        """從JSON字符串創建實例。

        Args:
            json_str: JSON字符串

        Returns:
            OptimizationResult實例
        """
        return cls.model_validate_json(json_str)

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """獲取參數值。

        Args:
            key: 參數名稱
            default: 默認值

        Returns:
            參數值或默認值
        """
        return self.parameters.get(key, default)

    def get_metric(self, key: str, default: float = 0.0) -> float:
        """獲取指標值。

        Args:
            key: 指標名稱
            default: 默認值

        Returns:
            指標值或默認值
        """
        return getattr(self.metrics, key, default)

    def is_better_than(self, other: 'OptimizationResult',
                      primary_metric: str = 'sharpe_ratio') -> bool:
        """比較兩個優化結果。

        Args:
            other: 另一個優化結果
            primary_metric: 主要比較指標

        Returns:
            True if this result is better, False otherwise

        Raises:
            ValueError: 指標名稱無效
        """
        if not hasattr(self.metrics, primary_metric):
            raise ValueError(f"Unknown metric: {primary_metric}")

        self_value = getattr(self.metrics, primary_metric)
        other_value = getattr(other.metrics, primary_metric)

        # 對於回撤等負值越小越好的指標
        if primary_metric == 'max_drawdown':
            return self_value > other_value

        # 其他指標越大越好
        return self_value > other_value

    def get_performance_score(self) -> float:
        """計算綜合性能得分。

        使用加權方式計算綜合得分。

        Returns:
            綜合性能得分 (0-100)
        """
        score = 0.0

        # 夏普比率 (30%)
        score += min(max(self.metrics.sharpe_ratio / 3.0, 0), 1) * 30

        # 總收益率 (25%)
        score += min(max(self.metrics.total_return / 50, 0), 1) * 25

        # 勝率 (20%)
        score += (self.metrics.win_rate / 100.0) * 20

        # 盈虧比 (15%)
        score += min(max(self.metrics.profit_factor / 2.0, 0), 1) * 15

        # 交易次數 (10%) - 適中最好
        trade_score = 1.0 - abs(self.metrics.trade_count - 100) / 200.0
        score += max(min(trade_score, 1.0), 0) * 10

        return score

    def get_summary(self) -> Dict[str, Any]:
        """獲取結果摘要。

        Returns:
            包含關鍵指標的摘要字典
        """
        return {
            'result_id': str(self.result_id),
            'strategy_type': self.strategy_type,
            'symbol': self.symbol,
            'total_return': self.metrics.total_return,
            'sharpe_ratio': self.metrics.sharpe_ratio,
            'max_drawdown': self.metrics.max_drawdown,
            'win_rate': self.metrics.win_rate,
            'trade_count': self.metrics.trade_count,
            'performance_score': self.get_performance_score(),
            'execution_time_ms': self.execution_time_ms,
            'created_at': self.created_at.isoformat()
        }
