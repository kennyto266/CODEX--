"""Layout Config Model.

This module defines the LayoutConfig entity for storing user interface
layout configurations.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4


class GridConfig(BaseModel):
    """網格配置模型。

    定義界面網格的尺寸和結構。
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "width": 12,
                "height": 8,
                "cell_width": 100,
                "cell_height": 80
            }
        }
    )

    width: int = Field(
        ...,
        description="網格寬度 (列數)",
        ge=1,
        le=50
    )
    height: int = Field(
        ...,
        description="網格高度 (行數)",
        ge=1,
        le=50
    )
    cell_width: int = Field(
        ...,
        description="單元格寬度 (像素)",
        ge=10,
        le=500
    )
    cell_height: int = Field(
        ...,
        description="單元格高度 (像素)",
        ge=10,
        le=500
    )


class WidgetConfig(BaseModel):
    """組件配置模型。

    定義單個界面組件的位置和配置。
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "widget-1",
                "type": "price-chart",
                "x": 0,
                "y": 0,
                "w": 6,
                "h": 4,
                "config": {
                    "symbol": "0700.HK",
                    "timeframe": "1d",
                    "show_volume": True
                }
            }
        }
    )

    id: str = Field(
        ...,
        description="組件ID",
        min_length=1,
        max_length=50
    )
    type: str = Field(
        ...,
        description="組件類型"
    )
    x: int = Field(
        ...,
        description="X座標 (列)",
        ge=0
    )
    y: int = Field(
        ...,
        description="Y座標 (行)",
        ge=0
    )
    w: int = Field(
        ...,
        description="寬度 (列數)",
        ge=1,
        le=50
    )
    h: int = Field(
        ...,
        description="高度 (行數)",
        ge=1,
        le=50
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="組件配置參數"
    )

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """驗證組件類型。

        Args:
            v: 組件類型

        Returns:
            驗證後的類型

        Raises:
            ValueError: 類型不在允許範圍內
        """
        allowed_types = [
            'price-chart', 'performance-chart', 'heatmap',
            'scatter', 'config-panel', 'toolbar', 'watchlist',
            'news-feed', 'order-book', 'trade-history'
        ]
        if v not in allowed_types:
            raise ValueError(
                f"type must be one of: {', '.join(allowed_types)}"
            )
        return v

    @field_validator('w', 'h')
    @classmethod
    def validate_size(cls, v: int, info) -> int:
        """驗證組件尺寸。

        Args:
            v: 尺寸值
            info: 字段信息

        Returns:
            驗證後的尺寸

        Raises:
            ValueError: 尺寸不符合要求
        """
        if v < 1:
            raise ValueError("Width and height must be at least 1")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典。

        Returns:
            組件配置字典
        """
        return self.model_dump()


class ThemeConfig(BaseModel):
    """主題配置模型。

    定義界面主題的視覺設定。
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mode": "dark",
                "primary_color": "#3b82f6",
                "background_color": "#1f2937",
                "text_color": "#f9fafb",
                "font_family": "Inter",
                "font_size": 14
            }
        }
    )

    mode: str = Field(
        default="light",
        description="主題模式 (dark 或 light)"
    )
    primary_color: str = Field(
        default="#3b82f6",
        description="主色調 (HEX格式)"
    )
    background_color: str = Field(
        default="#ffffff",
        description="背景色 (HEX格式)"
    )
    text_color: str = Field(
        default="#000000",
        description="文字色 (HEX格式)"
    )
    font_family: str = Field(
        default="Arial",
        description="字體家族",
        max_length=50
    )
    font_size: int = Field(
        default=14,
        description="字體大小 (px)",
        ge=10,
        le=24
    )

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """驗證主題模式。

        Args:
            v: 主題模式

        Returns:
            驗證後的模式

        Raises:
            ValueError: 模式不在允許範圍內
        """
        if v not in ['dark', 'light']:
            raise ValueError("mode must be either 'dark' or 'light'")
        return v

    @field_validator('primary_color', 'background_color', 'text_color')
    @classmethod
    def validate_color(cls, v: str) -> str:
        """驗證顏色值。

        Args:
            v: 顏色值

        Returns:
            驗證後的顏色

        Raises:
            ValueError: 顏色格式不正確
        """
        import re
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError("Color must be in HEX format (e.g., #ffffff)")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典。

        Returns:
            主題配置字典
        """
        return self.model_dump()


class LayoutData(BaseModel):
    """布局數據模型。

    存儲完整的界面布局信息。
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "grid": {
                    "width": 12,
                    "height": 8,
                    "cell_width": 100,
                    "cell_height": 80
                },
                "widgets": [
                    {
                        "id": "widget-1",
                        "type": "price-chart",
                        "x": 0,
                        "y": 0,
                        "w": 6,
                        "h": 4,
                        "config": {
                            "symbol": "0700.HK",
                            "timeframe": "1d"
                        }
                    }
                ]
            }
        }
    )

    grid: GridConfig = Field(
        ...,
        description="網格配置"
    )
    widgets: List[WidgetConfig] = Field(
        default_factory=list,
        description="組件列表",
        max_length=20
    )

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典。

        Returns:
            布局數據字典
        """
        return self.model_dump()


class LayoutConfig(BaseModel):
    """布局配置模型。

    保存用戶的界面布局設置。
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "config_id": "a1b2c3d4-5678-90ab-cdef-123456789abc",
                "name": "我的工作區",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "layout_data": {
                    "grid": {
                        "width": 12,
                        "height": 8,
                        "cell_width": 100,
                        "cell_height": 80
                    },
                    "widgets": [
                        {
                            "id": "widget-1",
                            "type": "price-chart",
                            "x": 0,
                            "y": 0,
                            "w": 6,
                            "h": 4,
                            "config": {
                                "symbol": "0700.HK",
                                "timeframe": "1d"
                            }
                        }
                    ]
                },
                "theme": {
                    "mode": "dark",
                    "primary_color": "#3b82f6",
                    "background_color": "#1f2937",
                    "text_color": "#f9fafb",
                    "font_family": "Inter",
                    "font_size": 14
                },
                "is_default": True
            }
        },
        str_strip_whitespace=True,
        validate_assignment=True
    )

    config_id: UUID = Field(
        default_factory=uuid4,
        description="配置唯一標識符 (UUID格式)"
    )
    name: str = Field(
        ...,
        description="布局名稱",
        min_length=1,
        max_length=50
    )
    user_id: UUID = Field(
        ...,
        description="用戶ID (關聯到UserConfig)"
    )
    layout_data: LayoutData = Field(
        ...,
        description="布局數據"
    )
    theme: ThemeConfig = Field(
        default_factory=ThemeConfig,
        description="主題配置"
    )
    is_default: bool = Field(
        default=False,
        description="是否為默認布局"
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
        """驗證布局名稱。

        Args:
            v: 布局名稱

        Returns:
            驗證後的名稱

        Raises:
            ValueError: 名稱長度不符合要求
        """
        if not isinstance(v, str) or len(v) < 1 or len(v) > 50:
            raise ValueError("Name must be 1-50 characters long")
        return v.strip()

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """序列化為字典。

        覆蓋基類方法以處理UUID和datetime序列化。
        """
        data = super().model_dump(**kwargs)
        # 轉換UUID為字符串
        data['config_id'] = str(self.config_id)
        data['user_id'] = str(self.user_id)
        # 轉換datetime為ISO格式字符串
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典。

        Returns:
            包含布局配置的字典
        """
        return self.model_dump()

    def to_json(self) -> str:
        """轉換為JSON字符串。

        Returns:
            JSON格式的字符串
        """
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> 'LayoutConfig':
        """從JSON字符串創建實例。

        Args:
            json_str: JSON字符串

        Returns:
            LayoutConfig實例
        """
        return cls.model_validate_json(json_str)

    def update_timestamp(self) -> None:
        """更新時間戳。

        更新updated_at字段為當前時間。
        """
        self.updated_at = datetime.now()

    def add_widget(self, widget: WidgetConfig) -> None:
        """添加組件。

        Args:
            widget: 組件配置
        """
        # 檢查是否已存在相同ID的組件
        if any(w.id == widget.id for w in self.layout_data.widgets):
            raise ValueError(f"Widget with id {widget.id} already exists")

        self.layout_data.widgets.append(widget)
        self.update_timestamp()

    def remove_widget(self, widget_id: str) -> None:
        """移除組件。

        Args:
            widget_id: 組件ID
        """
        self.layout_data.widgets = [
            w for w in self.layout_data.widgets if w.id != widget_id
        ]
        self.update_timestamp()

    def get_widget(self, widget_id: str) -> Optional[WidgetConfig]:
        """獲取的件。

        Args:
            widget_id: 組件ID

        Returns:
            組件配置或None
        """
        for widget in self.layout_data.widgets:
            if widget.id == widget_id:
                return widget
        return None

    def update_widget(self, widget_id: str, updates: Dict[str, Any]) -> None:
        """更新組件。

        Args:
            widget_id: 組件ID
            updates: 更新內容
        """
        widget = self.get_widget(widget_id)
        if widget:
            for key, value in updates.items():
                if hasattr(widget, key):
                    setattr(widget, key, value)
            self.update_timestamp()

    def set_as_default(self) -> None:
        """設為默認布局。

        將此布局設置為用戶的默認布局。
        """
        self.is_default = True
        self.update_timestamp()

    def clone(self) -> 'LayoutConfig':
        """克隆布局配置。

        創建當前布局的副本，創建新的UUID和ID。

        Returns:
            新的LayoutConfig實例
        """
        data = self.model_dump()
        data['config_id'] = uuid4()  # 新的UUID

        # 為所有組件生成新的ID
        for widget in data['layout_data']['widgets']:
            widget['id'] = f"widget-{uuid4()}"

        return LayoutConfig(**data)

    def is_valid(self) -> bool:
        """檢查布局是否有效。

        Returns:
            True if valid, False otherwise
        """
        return (
            self.name and
            self.user_id and
            self.config_id and
            len(self.layout_data.widgets) > 0
        )

    def get_widget_count(self) -> int:
        """獲取的件數量。

        Returns:
            組件總數
        """
        return len(self.layout_data.widgets)

    def get_widgets_by_type(self, widget_type: str) -> List[WidgetConfig]:
        """按類型獲取的件。

        Args:
            widget_type: 組件類型

        Returns:
            匹配的組件列表
        """
        return [
            w for w in self.layout_data.widgets
            if w.type == widget_type
        ]

    def get_layout_bounds(self) -> Dict[str, int]:
        """獲取布局邊界。

        計算布局中所有組件的最大邊界。

        Returns:
            邊界字典 {x, y, w, h, max_x, max_y}
        """
        if not self.layout_data.widgets:
            return {
                'x': 0, 'y': 0, 'w': 0, 'h': 0,
                'max_x': 0, 'max_y': 0
            }

        max_x = max(w.x + w.w for w in self.layout_data.widgets)
        max_y = max(w.y + w.h for w in self.layout_data.widgets)

        return {
            'x': 0,
            'y': 0,
            'w': max_x,
            'h': max_y,
            'max_x': max_x,
            'max_y': max_y
        }

    def check_collisions(self) -> List[Dict[str, Any]]:
        """檢查組件碰撞。

        檢查是否有組件重疊。

        Returns:
            碰撞組件對的列表
        """
        collisions = []
        widgets = self.layout_data.widgets

        for i, w1 in enumerate(widgets):
            for w2 in widgets[i+1:]:
                # 檢查是否重疊
                if not (w1.x + w1.w <= w2.x or w2.x + w2.w <= w1.x or
                        w1.y + w1.h <= w2.y or w2.y + w2.h <= w1.y):
                    collisions.append({
                        'widget1': w1.id,
                        'widget2': w2.id
                    })

        return collisions
