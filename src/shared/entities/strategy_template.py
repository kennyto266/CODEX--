"""Strategy Template Model.

This module defines the StrategyTemplate entity for storing user-created
custom trading strategy configurations.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4


class PerformanceMetrics(BaseModel):
    """策略性能指標。

    存儲策略的關鍵性能數據。
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_return": 15.5,
                "sharpe_ratio": 1.2,
                "max_drawdown": -5.2,
                "win_rate": 65.0,
                "trade_count": 120,
                "avg_holding_days": 3.5
            }
        }
    )

    total_return: float = Field(
        ...,
        description="總收益率 (百分比)",
        ge=-100.0,
        le=1000.0
    )
    sharpe_ratio: float = Field(
        ...,
        description="夏普比率",
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
    trade_count: int = Field(
        ...,
        description="交易次數",
        ge=0
    )
    avg_holding_days: float = Field(
        ...,
        description="平均持倉天數",
        ge=0.0
    )


class StrategyTemplate(BaseModel):
    """策略模板模型。

    保存用戶創建的自定義策略配置。
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "template_id": "a1b2c3d4-5678-90ab-cdef-123456789abc",
                "name": "MA交叉策略",
                "strategy_type": "MA",
                "parameters": {
                    "fast_period": 10,
                    "slow_period": 20,
                    "threshold": 0.02
                },
                "performance": {
                    "total_return": 15.5,
                    "sharpe_ratio": 1.2,
                    "max_drawdown": -5.2,
                    "win_rate": 65.0,
                    "trade_count": 120,
                    "avg_holding_days": 3.5
                },
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "is_public": False,
                "tags": ["趨勢", "移動平均", "短線"]
            }
        },
        str_strip_whitespace=True,
        validate_assignment=True
    )

    template_id: UUID = Field(
        default_factory=uuid4,
        description="策略模板唯一標識符 (UUID格式)"
    )
    name: str = Field(
        ...,
        description="策略名稱",
        min_length=1,
        max_length=100
    )
    strategy_type: str = Field(
        ...,
        description="策略類型"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="策略參數"
    )
    performance: Optional[PerformanceMetrics] = Field(
        default=None,
        description="策略性能指標"
    )
    user_id: UUID = Field(
        ...,
        description="用戶ID (關聯到UserConfig)"
    )
    is_public: bool = Field(
        default=False,
        description="是否公開策略"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="策略標籤",
        max_length=20
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="創建時間"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="最後更新時間"
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

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """驗證標籤。

        Args:
            v: 標籤列表

        Returns:
            驗證後的標籤列表

        Raises:
            ValueError: 標籤長度不符合要求
        """
        for tag in v:
            if not isinstance(tag, str) or len(tag) < 1 or len(tag) > 30:
                raise ValueError(
                    f"Tag {tag} must be 1-30 characters long"
                )
        return v

    @field_validator('parameters')
    @classmethod
    def validate_parameters(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """驗證策略參數。

        Args:
            v: 參數字典

        Returns:
            驗證後的參數

        Raises:
            ValueError: 參數驗證失敗
        """
        # 基本參數驗證，具體驗證應根據strategy_type進行
        if not isinstance(v, dict):
            raise ValueError("Parameters must be a dictionary")

        # 檢查參數名稱是否合法
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
        data['template_id'] = str(self.template_id)
        data['user_id'] = str(self.user_id)
        # 轉換datetime為ISO格式字符串
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典。

        Returns:
            包含策略模板數據的字典
        """
        return self.model_dump()

    def to_json(self) -> str:
        """轉換為JSON字符串。

        Returns:
            JSON格式的字符串
        """
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> 'StrategyTemplate':
        """從JSON字符串創建實例。

        Args:
            json_str: JSON字符串

        Returns:
            StrategyTemplate實例
        """
        return cls.model_validate_json(json_str)

    def update_timestamp(self) -> None:
        """更新時間戳。

        更新updated_at字段為當前時間。
        """
        self.updated_at = datetime.now()

    def set_performance(self, performance: PerformanceMetrics) -> None:
        """設置性能指標。

        Args:
            performance: 性能指標對象
        """
        self.performance = performance
        self.update_timestamp()

    def add_tag(self, tag: str) -> None:
        """添加標籤。

        Args:
            tag: 標籤名稱
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.update_timestamp()

    def remove_tag(self, tag: str) -> None:
        """移除標籤。

        Args:
            tag: 標籤名稱
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.update_timestamp()

    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """更新策略參數。

        Args:
            parameters: 新的參數字典
        """
        self.parameters.update(parameters)
        self.update_timestamp()

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """獲取參數值。

        Args:
            key: 參數名稱
            default: 默認值

        Returns:
            參數值或默認值
        """
        return self.parameters.get(key, default)

    def clone(self) -> 'StrategyTemplate':
        """克隆策略模板。

        創建當前模板的副本，創建新的UUID。

        Returns:
            新的StrategyTemplate實例
        """
        data = self.model_dump()
        data['template_id'] = uuid4()  # 新的UUID
        return StrategyTemplate(**data)

    def is_valid(self) -> bool:
        """檢查模板是否有效。

        Returns:
            True if valid, False otherwise
        """
        return bool(
            self.name and
            self.strategy_type and
            self.user_id and
            self.template_id
        )

    def get_performance_summary(self) -> Optional[Dict[str, Any]]:
        """獲取性能摘要。

        Returns:
            性能指標字典，如果沒有性能數據則返回None
        """
        if self.performance:
            return {
                'total_return': self.performance.total_return,
                'sharpe_ratio': self.performance.sharpe_ratio,
                'max_drawdown': self.performance.max_drawdown,
                'win_rate': self.performance.win_rate
            }
        return None
