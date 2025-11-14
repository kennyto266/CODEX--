"""Custom Indicator Model.

This module defines the CustomIndicator entity for storing user-created
technical indicators.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4


class ParameterDefinition(BaseModel):
    """參數定義模型。

    定義自定義指標的參數結構。
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "float",
                "default": 14.0,
                "min": 2.0,
                "max": 100.0,
                "description": "計算週期"
            }
        }
    )

    type: str = Field(
        ...,
        description="參數類型 (int|float|str|bool)"
    )
    default: Union[int, float, str, bool, None] = Field(
        default=None,
        description="默認值"
    )
    min: Optional[Union[int, float]] = Field(
        default=None,
        description="最小值 (可選)"
    )
    max: Optional[Union[int, float]] = Field(
        default=None,
        description="最大值 (可選)"
    )
    description: str = Field(
        default="",
        description="參數說明",
        max_length=200
    )

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """驗證參數類型。

        Args:
            v: 參數類型

        Returns:
            驗證後的類型

        Raises:
            ValueError: 類型不在允許範圍內
        """
        allowed_types = ['int', 'float', 'str', 'bool']
        if v not in allowed_types:
            raise ValueError(
                f"type must be one of: {', '.join(allowed_types)}"
            )
        return v

    @field_validator('min', 'max')
    @classmethod
    def validate_range(cls, v: Optional[Union[int, float]]) -> Optional[Union[int, float]]:
        """驗證範圍值。

        Args:
            v: 範圍值

        Returns:
            驗證後的值
        """
        if v is not None and not isinstance(v, (int, float)):
            raise ValueError("min and max must be numbers")
        return v


class OutputType(str):
    """輸出類型枚舉。

    定義指標輸出類型。
    """
    SINGLE = "single"
    SERIES = "series"
    MULTIPLE = "multiple"


class CustomIndicator(BaseModel):
    """自定義指標模型。

    存儲用戶創建的技術指標。
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "indicator_id": "a1b2c3d4-5678-90ab-cdef-123456789abc",
                "name": "自定義RSI變體",
                "description": "基於成交量的RSI指標",
                "code": "def custom_rsi(close, volume, period=14):\\n    # 實現自定義RSI邏輯\\n    return rsi_values",
                "parameters": {
                    "period": {
                        "type": "int",
                        "default": 14,
                        "min": 2,
                        "max": 100,
                        "description": "計算週期"
                    },
                    "volume_weighted": {
                        "type": "bool",
                        "default": True,
                        "description": "是否使用成交量加權"
                    }
                },
                "output_type": "series",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "is_valid": True,
                "validation_errors": []
            }
        },
        str_strip_whitespace=True,
        validate_assignment=True
    )

    indicator_id: UUID = Field(
        default_factory=uuid4,
        description="指標唯一標識符 (UUID格式)"
    )
    name: str = Field(
        ...,
        description="指標名稱",
        min_length=1,
        max_length=50
    )
    description: str = Field(
        default="",
        description="指標描述",
        max_length=500
    )
    code: str = Field(
        ...,
        description="Python代碼",
        min_length=100,
        max_length=10000
    )
    parameters: Dict[str, ParameterDefinition] = Field(
        default_factory=dict,
        description="參數定義"
    )
    output_type: OutputType = Field(
        default=OutputType.SERIES,
        description="輸出類型 (single|series|multiple)"
    )
    user_id: UUID = Field(
        ...,
        description="用戶ID (關聯到UserConfig)"
    )
    is_valid: bool = Field(
        default=False,
        description="代碼是否有效"
    )
    validation_errors: List[str] = Field(
        default_factory=list,
        description="驗證錯誤列表"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="創建時間"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="最後更新時間"
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """驗證指標名稱。

        Args:
            v: 指標名稱

        Returns:
            驗證後的名稱

        Raises:
            ValueError: 名稱長度不符合要求
        """
        if not isinstance(v, str) or len(v) < 1 or len(v) > 50:
            raise ValueError("Name must be 1-50 characters long")
        return v.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """驗證描述。

        Args:
            v: 描述文本

        Returns:
            驗證後的描述
        """
        if len(v) > 500:
            raise ValueError("Description must be less than 500 characters")
        return v.strip()

    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """驗證代碼。

        Args:
            v: Python代碼

        Returns:
            驗證後的代碼

        Raises:
            ValueError: 代碼長度不符合要求
        """
        if not isinstance(v, str):
            raise ValueError("Code must be a string")

        code_len = len(v)
        if code_len < 100:
            raise ValueError("Code must be at least 100 characters long")
        if code_len > 10000:
            raise ValueError("Code must be less than 10000 characters long")

        # 檢查基本的Python語法元素
        if 'def ' not in v and 'lambda ' not in v:
            raise ValueError("Code must contain a function definition")

        return v

    @field_validator('output_type')
    @classmethod
    def validate_output_type(cls, v: str) -> OutputType:
        """驗證輸出類型。

        Args:
            v: 輸出類型

        Returns:
            驗證後的類型

        Raises:
            ValueError: 類型不在允許範圍內
        """
        if v not in [OutputType.SINGLE, OutputType.SERIES, OutputType.MULTIPLE]:
            raise ValueError(
                f"output_type must be one of: {', '.join([OutputType.SINGLE, OutputType.SERIES, OutputType.MULTIPLE])}"
            )
        return OutputType(v)

    @field_validator('validation_errors')
    @classmethod
    def validate_validation_errors(cls, v: List[str]) -> List[str]:
        """驗證錯誤列表。

        Args:
            v: 錯誤列表

        Returns:
            驗證後的列表
        """
        # 確保所有元素都是字符串
        return [str(error) for error in v]

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """序列化為字典。

        覆蓋基類方法以處理UUID和datetime序列化。
        """
        data = super().model_dump(**kwargs)
        # 轉換UUID為字符串
        data['indicator_id'] = str(self.indicator_id)
        data['user_id'] = str(self.user_id)
        # 轉換datetime為ISO格式字符串
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典。

        Returns:
            包含指標數據的字典
        """
        return self.model_dump()

    def to_json(self) -> str:
        """轉換為JSON字符串。

        Returns:
            JSON格式的字符串
        """
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> 'CustomIndicator':
        """從JSON字符串創建實例。

        Args:
            json_str: JSON字符串

        Returns:
            CustomIndicator實例
        """
        return cls.model_validate_json(json_str)

    def update_timestamp(self) -> None:
        """更新時間戳。

        更新updated_at字段為當前時間。
        """
        self.updated_at = datetime.now()

    def set_validation_result(self, is_valid: bool, errors: List[str]) -> None:
        """設置驗證結果。

        Args:
            is_valid: 是否有效
            errors: 錯誤列表
        """
        self.is_valid = is_valid
        self.validation_errors = errors
        self.update_timestamp()

    def add_parameter(self, name: str, param_def: ParameterDefinition) -> None:
        """添加參數定義。

        Args:
            name: 參數名稱
            param_def: 參數定義
        """
        self.parameters[name] = param_def
        self.update_timestamp()

    def remove_parameter(self, name: str) -> None:
        """移除參數定義。

        Args:
            name: 參數名稱
        """
        if name in self.parameters:
            del self.parameters[name]
            self.update_timestamp()

    def get_parameter(self, name: str) -> Optional[ParameterDefinition]:
        """獲取參數定義。

        Args:
            name: 參數名稱

        Returns:
            參數定義或None
        """
        return self.parameters.get(name)

    def get_default_parameters(self) -> Dict[str, Any]:
        """獲取默認參數值。

        Returns:
            默認參數字典
        """
        defaults = {}
        for name, param_def in self.parameters.items():
            if param_def.default is not None:
                defaults[name] = param_def.default
        return defaults

    def get_parameter_schema(self) -> Dict[str, Any]:
        """獲取參數JSON Schema。

        用於前端表單生成。

        Returns:
            參數Schema字典
        """
        schema = {}
        for name, param_def in self.parameters.items():
            schema[name] = {
                'type': param_def.type,
                'default': param_def.default,
                'description': param_def.description
            }
            if param_def.min is not None:
                schema[name]['minimum'] = param_def.min
            if param_def.max is not None:
                schema[name]['maximum'] = param_def.max
        return schema

    def clone(self) -> 'CustomIndicator':
        """克隆指標。

        創建當前指標的副本，創建新的UUID。

        Returns:
            新的CustomIndicator實例
        """
        data = self.model_dump()
        data['indicator_id'] = uuid4()  # 新的UUID
        return CustomIndicator(**data)

    def is_valid_code(self) -> bool:
        """檢查代碼是否有效。

        Returns:
            True if valid, False otherwise
        """
        return self.is_valid and len(self.validation_errors) == 0

    def get_function_name(self) -> Optional[str]:
        """提取函數名稱。

        Returns:
            函數名稱或None
        """
        # 嘗試從代碼中提取函數名
        if 'def ' in self.code:
            # 查找 def 關鍵字後的第一個識別符
            lines = self.code.split('\n')
            for line in lines:
                if 'def ' in line:
                    parts = line.split('def ')[1].split('(')[0].strip()
                    if parts:
                        return parts
        return None

    def to_python_code(self) -> str:
        """生成可執行的Python代碼。

        Returns:
            Python代碼字符串
        """
        return self.code

    def validate_parameter_value(self, name: str, value: Any) -> bool:
        """驗證參數值。

        Args:
            name: 參數名稱
            value: 參數值

        Returns:
            True if valid, False otherwise
        """
        param_def = self.get_parameter(name)
        if not param_def:
            return False

        # 類型檢查
        expected_type = param_def.type
        if expected_type == 'int' and not isinstance(value, int):
            return False
        if expected_type == 'float' and not isinstance(value, (int, float)):
            return False
        if expected_type == 'str' and not isinstance(value, str):
            return False
        if expected_type == 'bool' and not isinstance(value, bool):
            return False

        # 範圍檢查
        if param_def.min is not None and value < param_def.min:
            return False
        if param_def.max is not None and value > param_def.max:
            return False

        return True
