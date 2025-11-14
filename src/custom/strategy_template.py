"""
策略模板系統
提供可視化策略編輯器和模板引擎
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """策略類型"""
    TECHNICAL = "technical"
    MACRO = "macro"
    REVERSION = "reversion"
    MOMENTUM = "momentum"
    MULTIFACTOR = "multifactor"
    CUSTOM = "custom"


class SignalType(Enum):
    """信號類型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"


@dataclass
class StrategyBlock:
    """策略構建塊"""
    id: str
    type: str  # indicator, filter, condition, action
    name: str
    config: Dict[str, Any]
    inputs: List[str] = None  # 輸入來源
    outputs: List[str] = None  # 輸出目標
    position: Dict[str, int] = None  # 位置信息 (x, y)

    def __post_init__(self):
        if self.inputs is None:
            self.inputs = []
        if self.outputs is None:
            self.outputs = []
        if self.position is None:
            self.position = {'x': 0, 'y': 0}


@dataclass
class StrategyTemplate:
    """策略模板"""
    id: str
    name: str
    description: str
    type: StrategyType
    version: str = "1.0.0"
    author: str = "User"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    blocks: List[StrategyBlock] = None
    connections: List[Dict[str, Any]] = None  # 塊之間的連接
    parameters: Dict[str, Any] = None  # 策略參數
    required_data: List[str] = None  # 需要的數據字段

    def __post_init__(self):
        if self.blocks is None:
            self.blocks = []
        if self.connections is None:
            self.connections = []
        if self.parameters is None:
            self.parameters = {}
        if self.required_data is None:
            self.required_data = ['open', 'high', 'low', 'close', 'volume']


class StrategyTemplateEngine:
    """策略模板引擎 - 管理策略模板的創建、編輯和執行"""

    def __init__(self):
        self.templates: Dict[str, StrategyTemplate] = {}
        self.code_generator = StrategyCodeGenerator()
        self._load_builtin_templates()

    def _load_builtin_templates(self):
        """加載內建模板"""
        # 移動平均策略模板
        ma_template = self.create_ma_template()
        self.templates[ma_template.id] = ma_template

        # RSI策略模板
        rsi_template = self.create_rsi_template()
        self.templates[rsi_template.id] = rsi_template

        # MACD策略模板
        macd_template = self.create_macd_template()
        self.templates[macd_template.id] = macd_template

        # 多因子策略模板
        multifactor_template = self.create_multifactor_template()
        self.templates[multifactor_template.id] = multifactor_template

    def create_ma_template(self) -> StrategyTemplate:
        """創建移動平均策略模板"""
        blocks = [
            StrategyBlock(
                id="sma_short",
                type="indicator",
                name="短週期移動平均",
                config={"period": 10, "column": "close"},
                position={'x': 100, 'y': 100}
            ),
            StrategyBlock(
                id="sma_long",
                type="indicator",
                name="長週期移動平均",
                config={"period": 20, "column": "close"},
                position={'x': 100, 'y': 200}
            ),
            StrategyBlock(
                id="crossover",
                type="condition",
                name="金叉/死叉",
                config={"condition": "sma_short > sma_long"},
                inputs=["sma_short", "sma_long"],
                outputs=["signal"],
                position={'x': 300, 'y': 150}
            ),
            StrategyBlock(
                id="buy_action",
                type="action",
                name="買入",
                config={"signal": "BUY"},
                inputs=["signal"],
                position={'x': 500, 'y': 100}
            ),
            StrategyBlock(
                id="sell_action",
                type="action",
                name="賣出",
                config={"signal": "SELL"},
                inputs=["signal"],
                position={'x': 500, 'y': 200}
            ),
        ]

        connections = [
            {"from": "sma_short", "to": "crossover"},
            {"from": "sma_long", "to": "crossover"},
            {"from": "crossover", "to": "buy_action"},
            {"from": "crossover", "to": "sell_action"},
        ]

        return StrategyTemplate(
            id="ma_crossover",
            name="移動平均交叉策略",
            description="基於短期和長期移動平均線交叉的趨勢跟隨策略",
            type=StrategyType.TECHNICAL,
            blocks=blocks,
            connections=connections,
            parameters={
                "initial_capital": 100000,
                "transaction_cost": 0.001,
            }
        )

    def create_rsi_template(self) -> StrategyTemplate:
        """創建RSI策略模板"""
        blocks = [
            StrategyBlock(
                id="rsi",
                type="indicator",
                name="RSI指標",
                config={"period": 14, "column": "close"},
                position={'x': 100, 'y': 150}
            ),
            StrategyBlock(
                id="oversold",
                type="condition",
                name="超賣條件",
                config={"condition": "rsi < 30"},
                inputs=["rsi"],
                outputs=["buy_signal"],
                position={'x': 300, 'y': 100}
            ),
            StrategyBlock(
                id="overbought",
                type="condition",
                name="超買條件",
                config={"condition": "rsi > 70"},
                inputs=["rsi"],
                outputs=["sell_signal"],
                position={'x': 300, 'y': 200}
            ),
            StrategyBlock(
                id="buy_action",
                type="action",
                name="買入",
                config={"signal": "BUY"},
                inputs=["buy_signal"],
                position={'x': 500, 'y': 100}
            ),
            StrategyBlock(
                id="sell_action",
                type="action",
                name="賣出",
                config={"signal": "SELL"},
                inputs=["sell_signal"],
                position={'x': 500, 'y': 200}
            ),
        ]

        return StrategyTemplate(
            id="rsi_mean_reversion",
            name="RSI均值回歸策略",
            description="基於RSI指標超買超賣的均值回歸策略",
            type=StrategyType.TECHNICAL,
            blocks=blocks,
            connections=[
                {"from": "rsi", "to": "oversold"},
                {"from": "rsi", "to": "overbought"},
                {"from": "oversold", "to": "buy_action"},
                {"from": "overbought", "to": "sell_action"},
            ],
        )

    def create_macd_template(self) -> StrategyTemplate:
        """創建MACD策略模板"""
        blocks = [
            StrategyBlock(
                id="macd",
                type="indicator",
                name="MACD指標",
                config={"fast": 12, "slow": 26, "signal": 9},
                position={'x': 100, 'y': 150}
            ),
            StrategyBlock(
                id="signal_cross",
                type="condition",
                name="信號線交叉",
                config={"condition": "macd_line > signal_line"},
                inputs=["macd_line", "signal_line"],
                outputs=["signal"],
                position={'x': 300, 'y': 150}
            ),
            StrategyBlock(
                id="buy_action",
                type="action",
                name="買入",
                config={"signal": "BUY"},
                inputs=["signal"],
                position={'x': 500, 'y': 100}
            ),
            StrategyBlock(
                id="sell_action",
                type="action",
                name="賣出",
                config={"signal": "SELL"},
                inputs=["signal"],
                position={'x': 500, 'y': 200}
            ),
        ]

        return StrategyTemplate(
            id="macd_strategy",
            name="MACD策略",
            description="基於MACD指標和信號線交叉的策略",
            type=StrategyType.TECHNICAL,
            blocks=blocks,
            connections=[
                {"from": "macd", "to": "signal_cross"},
                {"from": "signal_cross", "to": "buy_action"},
                {"from": "signal_cross", "to": "sell_action"},
            ],
        )

    def create_multifactor_template(self) -> StrategyTemplate:
        """創建多因子策略模板"""
        blocks = [
            StrategyBlock(
                id="sma",
                type="indicator",
                name="移動平均",
                config={"period": 20},
                position={'x': 100, 'y': 100}
            ),
            StrategyBlock(
                id="rsi",
                type="indicator",
                name="RSI",
                config={"period": 14},
                position={'x': 100, 'y': 200}
            ),
            StrategyBlock(
                id="volume_ma",
                type="indicator",
                name="成交量移動平均",
                config={"period": 20, "column": "volume"},
                position={'x': 100, 'y': 300}
            ),
            StrategyBlock(
                id="trend_filter",
                type="filter",
                name="趨勢過濾",
                config={"type": "and", "conditions": [
                    "close > sma",
                    "rsi > 30 and rsi < 70",
                    "volume > volume_ma"
                ]},
                inputs=["sma", "rsi", "volume_ma", "close", "volume"],
                position={'x': 300, 'y': 200}
            ),
            StrategyBlock(
                id="signal",
                type="condition",
                name="信號",
                config={"action": "trend_filter"},
                inputs=["trend_filter"],
                position={'x': 500, 'y': 200}
            ),
            StrategyBlock(
                id="action",
                type="action",
                name="交易",
                config={},
                inputs=["signal"],
                position={'x': 700, 'y': 200}
            ),
        ]

        return StrategyTemplate(
            id="multifactor_strategy",
            name="多因子策略",
            description="結合多個技術指標的多因子交易策略",
            type=StrategyType.MULTIFACTOR,
            blocks=blocks,
            connections=[
                {"from": "sma", "to": "trend_filter"},
                {"from": "rsi", "to": "trend_filter"},
                {"from": "volume_ma", "to": "trend_filter"},
                {"from": "trend_filter", "to": "signal"},
                {"from": "signal", "to": "action"},
            ],
        )

    def get_template(self, template_id: str) -> Optional[StrategyTemplate]:
        """獲取策略模板"""
        return self.templates.get(template_id)

    def list_templates(self) -> List[StrategyTemplate]:
        """列出所有模板"""
        return list(self.templates.values())

    def create_template(
        self,
        name: str,
        description: str,
        strategy_type: StrategyType,
        blocks: List[StrategyBlock],
        connections: List[Dict[str, Any]]
    ) -> StrategyTemplate:
        """創建自定義模板"""
        import uuid
        template_id = f"custom_{uuid.uuid4().hex[:8]}"

        template = StrategyTemplate(
            id=template_id,
            name=name,
            description=description,
            type=strategy_type,
            blocks=blocks,
            connections=connections
        )

        self.templates[template_id] = template
        return template

    def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        blocks: Optional[List[StrategyBlock]] = None,
        connections: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """更新模板"""
        if template_id not in self.templates:
            return False

        template = self.templates[template_id]

        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if blocks is not None:
            template.blocks = blocks
        if connections is not None:
            template.connections = connections

        return True

    def delete_template(self, template_id: str) -> bool:
        """刪除模板"""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False

    def export_template(self, template_id: str) -> str:
        """導出模板為JSON"""
        template = self.get_template(template_id)
        if template is None:
            raise ValueError(f"Template {template_id} not found")

        return json.dumps(asdict(template), indent=2, ensure_ascii=False)

    def import_template(self, template_json: str) -> StrategyTemplate:
        """從JSON導入模板"""
        data = json.loads(template_json)
        template = StrategyTemplate(**data)
        self.templates[template.id] = template
        return template

    def generate_code(self, template_id: str) -> str:
        """生成可執行的策略代碼"""
        template = self.get_template(template_id)
        if template is None:
            raise ValueError(f"Template {template_id} not found")

        return self.code_generator.generate(template)

    def validate_template(self, template: StrategyTemplate) -> List[str]:
        """驗證模板結構"""
        errors = []

        # 檢查塊的依賴
        block_ids = {b.id for b in template.blocks}
        for conn in template.connections:
            if conn.get('from') not in block_ids:
                errors.append(f"Connection from unknown block: {conn.get('from')}")
            if conn.get('to') not in block_ids:
                errors.append(f"Connection to unknown block: {conn.get('to')}")

        # 檢查輸入輸出
        for block in template.blocks:
            for input_name in block.inputs:
                if not any(input_name in [b.id for b in template.blocks]):
                    errors.append(f"Block {block.id} references unknown input: {input_name}")

        return errors


class StrategyCodeGenerator:
    """策略代碼生成器 - 將視覺化策略轉換為可執行代碼"""

    def __init__(self):
        self.indicator_registry = {
            'sma': 'simple_moving_average',
            'ema': 'exponential_moving_average',
            'rsi': 'rsi',
            'macd': 'macd',
            'bollinger': 'bollinger_bands',
            'atr': 'atr',
        }

    def generate(self, template: StrategyTemplate) -> str:
        """
        生成策略代碼

        Args:
            template: 策略模板

        Returns:
            可執行的Python代碼
        """
        code = f"""# {template.name}
# Generated from strategy template: {template.id}

import pandas as pd
import numpy as np

def execute_strategy(data):
    '''
    執行策略邏輯

    Args:
        data: 包含OHLCV數據的DataFrame

    Returns:
        交易信號DataFrame
    '''
    signals = pd.DataFrame(index=data.index)
    signals['signal'] = 0  # 0: hold, 1: buy, -1: sell
"""

        # 按依賴順序排序塊
        sorted_blocks = self._topological_sort(template)

        # 生成每個塊的代碼
        for block in sorted_blocks:
            if block.type == "indicator":
                code += f"\n    # {block.name}\n"
                code += self._generate_indicator_code(block)
            elif block.type == "filter":
                code += f"\n    # {block.name}\n"
                code += self._generate_filter_code(block)
            elif block.type == "condition":
                code += f"\n    # {block.name}\n"
                code += self._generate_condition_code(block)

        # 生成最終信號
        code += "\n    return signals\n"

        return code

    def _topological_sort(self, template: StrategyTemplate) -> List[StrategyBlock]:
        """對塊進行拓撲排序"""
        # 簡化版本：按類型排序
        type_order = {
            'indicator': 0,
            'filter': 1,
            'condition': 2,
            'action': 3,
        }
        return sorted(template.blocks, key=lambda b: type_order.get(b.type, 99))

    def _generate_indicator_code(self, block: StrategyBlock) -> str:
        """生成指標計算代碼"""
        config = block.config
        var_name = block.id

        if 'period' in config:
            period = config['period']
            column = config.get('column', 'close')
            return f"    {var_name} = data['{column}'].rolling(window={period}).mean()\n"
        elif 'fast' in config and 'slow' in config:
            fast = config['fast']
            slow = config['slow']
            signal = config.get('signal', 9)
            return f"""    ema_fast = data['close'].ewm(span={fast}).mean()
    ema_slow = data['close'].ewm(span={slow}).mean()
    {var_name} = ema_fast - ema_slow
"""
        else:
            return f"    # Unknown indicator configuration: {config}\n"

    def _generate_filter_code(self, block: StrategyBlock) -> str:
        """生成過濾器代碼"""
        config = block.config
        var_name = block.id

        if 'type' in config and config['type'] == 'and':
            conditions = config.get('conditions', [])
            condition_str = ' and '.join(conditions)
            return f"    {var_name} = {condition_str}\n"
        else:
            return f"    # Filter: {var_name}\n"

    def _generate_condition_code(self, block: StrategyBlock) -> str:
        """生成條件代碼"""
        config = block.config
        var_name = block.id

        if 'condition' in config:
            condition = config['condition']
            return f"    if {condition}:\n        signals.loc[data.index, 'signal'] = 1\n    elif {condition.replace('>', '<').replace('<', '>').replace('and', 'or')}:\n        signals.loc[data.index, 'signal'] = -1\n"
        elif 'action' in config:
            action = config['action']
            return f"    if {action}:\n        signals.loc[data.index, 'signal'] = 1\n"
        else:
            return f"    # Condition: {var_name}\n"


# 導出
__all__ = [
    'StrategyTemplate',
    'StrategyBlock',
    'StrategyType',
    'SignalType',
    'StrategyTemplateEngine',
    'StrategyCodeGenerator',
]
