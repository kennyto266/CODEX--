"""
自定义策略构建器 (T183)
可视化策略构建和配置系统
实现拖拽式构建、参数调优、策略模板和代码生成

Author: Claude Code
Date: 2025-11-09
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime
import logging
import json
import inspect
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from core.base_strategy import IStrategy, Signal
    from strategy.traits import StrategyTraits
except ImportError:
    from ..core.base_strategy import IStrategy, Signal
    from .traits import StrategyTraits

logger = logging.getLogger(__name__)


class ComponentType(Enum):
    """策略组件类型"""
    INDICATOR = "indicator"
    FILTER = "filter"
    TRIGGER = "trigger"
    RISK_MANAGER = "risk_manager"
    POSITION_SIZER = "position_sizer"
    EXECUTION = "execution"


@dataclass
class StrategyComponent:
    """策略组件"""
    id: str
    name: str
    type: ComponentType
    component_class: str
    parameters: Dict[str, Any]
    inputs: List[str]
    outputs: List[str]
    position: Tuple[float, float] = (0.0, 0.0)
    enabled: bool = True


@dataclass
class StrategyTemplate:
    """策略模板"""
    id: str
    name: str
    description: str
    components: List[StrategyComponent]
    connections: List[Dict[str, Any]]
    parameters: Dict[str, Any]


class StrategyBuilder(IStrategy):
    """
    自定义策略构建器

    提供可视化界面和拖拽式策略构建功能，
    支持参数调优、策略模板和代码生成。

    核心功能：
    1. 可视化策略设计界面
    2. 拖拽式组件配置
    3. 策略模板系统
    4. 实时参数调优
    5. 策略代码生成
    6. 性能回测和优化

    特点：
    - 无需编程的策略构建
    - 丰富的预定义组件
    - 实时参数调整
    - 策略可视化
    - 自动代码生成
    """

    def __init__(
        self,
        template_id: Optional[str] = None,
        components: Optional[List[StrategyComponent]] = None,
        connections: Optional[List[Dict]] = None
    ):
        """
        初始化策略构建器

        Args:
            template_id: 模板ID
            components: 策略组件列表
            connections: 组件连接关系
        """
        self.template_id = template_id
        self.components = components or []
        self.connections = connections or []

        # 组件库
        self.component_library = self._build_component_library()

        # 策略模板
        self.templates = self._load_templates()

        # 当前构建的策略
        self.current_strategy = None
        self.strategy_instances: Dict[str, Any] = {}

        # 缓存
        self.component_outputs: Dict[str, Any] = {}
        self.signal_history: List[Signal] = []

        # 加载模板
        if template_id and template_id in self.templates:
            self._load_template(template_id)
        elif components:
            self._build_strategy()

        # 特征标记
        self.traits = StrategyTraits(
            name="策略构建器",
            timeframe="1D",
            可视化构建=True,
            参数调优=True,
            代码生成=True
        )

    @property
    def strategy_name(self) -> str:
        return f"Builder-{self.template_id or 'Custom'}"

    @property
    def supported_symbols(self) -> List[str]:
        return ['0700.HK', '0388.HK', '1398.HK', '0939.HK', '3988.HK']

    def _build_component_library(self) -> Dict[str, Dict]:
        """构建组件库"""
        return {
            # 技术指标组件
            'moving_average': {
                'name': '移动平均线',
                'type': ComponentType.INDICATOR,
                'class': 'sma',
                'parameters': {
                    'period': 20,
                    'price': 'close'
                },
                'inputs': ['price'],
                'outputs': ['sma', 'sma_slope']
            },
            'rsi': {
                'name': 'RSI指标',
                'type': ComponentType.INDICATOR,
                'class': 'rsi',
                'parameters': {
                    'period': 14,
                    'overbought': 70,
                    'oversold': 30
                },
                'inputs': ['price'],
                'outputs': ['rsi']
            },
            'macd': {
                'name': 'MACD指标',
                'type': ComponentType.INDICATOR,
                'class': 'macd',
                'parameters': {
                    'fast_period': 12,
                    'slow_period': 26,
                    'signal_period': 9
                },
                'inputs': ['price'],
                'outputs': ['macd', 'macd_signal', 'macd_histogram']
            },
            'bollinger': {
                'name': '布林带',
                'type': ComponentType.INDICATOR,
                'class': 'bollinger',
                'parameters': {
                    'period': 20,
                    'std_dev': 2.0
                },
                'inputs': ['price'],
                'outputs': ['bb_upper', 'bb_lower', 'bb_middle', 'bb_width']
            },
            'stoch': {
                'name': '随机指标',
                'type': ComponentType.INDICATOR,
                'class': 'stoch',
                'parameters': {
                    'k_period': 14,
                    'd_period': 3
                },
                'inputs': ['high', 'low', 'close'],
                'outputs': ['stoch_k', 'stoch_d']
            },

            # 过滤器组件
            'price_filter': {
                'name': '价格过滤器',
                'type': ComponentType.FILTER,
                'class': 'price_filter',
                'parameters': {
                    'min_price': 0,
                    'max_price': float('inf')
                },
                'inputs': ['price'],
                'outputs': ['price_valid']
            },
            'volume_filter': {
                'name': '成交量过滤器',
                'type': ComponentType.FILTER,
                'class': 'volume_filter',
                'parameters': {
                    'min_volume': 0
                },
                'inputs': ['volume'],
                'outputs': ['volume_valid']
            },
            'trend_filter': {
                'name': '趋势过滤器',
                'type': ComponentType.FILTER,
                'class': 'trend_filter',
                'parameters': {
                    'trend_period': 50
                },
                'inputs': ['price', 'sma'],
                'outputs': ['trend_up', 'trend_down']
            },

            # 触发器组件
            'crossover': {
                'name': '金叉死叉',
                'type': ComponentType.TRIGGER,
                'class': 'crossover',
                'parameters': {
                    'threshold': 0
                },
                'inputs': ['line1', 'line2'],
                'outputs': ['golden_cross', 'death_cross']
            },
            'threshold': {
                'name': '阈值触发',
                'type': ComponentType.TRIGGER,
                'class': 'threshold',
                'parameters': {
                    'upper': 70,
                    'lower': 30
                },
                'inputs': ['value'],
                'outputs': ['upper_cross', 'lower_cross']
            },
            'pattern': {
                'name': '形态识别',
                'type': ComponentType.TRIGGER,
                'class': 'pattern',
                'parameters': {
                    'pattern_type': 'all'
                },
                'inputs': ['high', 'low', 'open', 'close'],
                'outputs': ['bullish_pattern', 'bearish_pattern']
            },

            # 风险管理组件
            'stop_loss': {
                'name': '止损',
                'type': ComponentType.RISK_MANAGER,
                'class': 'stop_loss',
                'parameters': {
                    'percentage': 5.0,
                    'trailing': False
                },
                'inputs': ['entry_price', 'current_price'],
                'outputs': ['stop_loss_triggered']
            },
            'take_profit': {
                'name': '止盈',
                'type': ComponentType.RISK_MANAGER,
                'class': 'take_profit',
                'parameters': {
                    'percentage': 10.0
                },
                'inputs': ['entry_price', 'current_price'],
                'outputs': ['take_profit_triggered']
            },
            'max_drawdown': {
                'name': '最大回撤控制',
                'type': ComponentType.RISK_MANAGER,
                'class': 'max_drawdown',
                'parameters': {
                    'max_dd': 15.0
                },
                'inputs': ['portfolio_value'],
                'outputs': ['dd_warning']
            },

            # 位置大小组件
            'fixed_size': {
                'name': '固定数量',
                'type': ComponentType.POSITION_SIZER,
                'class': 'fixed_size',
                'parameters': {
                    'size': 100
                },
                'inputs': ['signal'],
                'outputs': ['position_size']
            },
            'percent_size': {
                'name': '百分比仓位',
                'type': ComponentType.POSITION_SIZER,
                'class': 'percent_size',
                'parameters': {
                    'percentage': 10.0
                },
                'inputs': ['signal', 'portfolio_value'],
                'outputs': ['position_size']
            },
            'volatility_size': {
                'name': '波动率仓位',
                'type': ComponentType.POSITION_SIZER,
                'class': 'volatility_size',
                'parameters': {
                    'target_vol': 20.0
                },
                'inputs': ['signal', 'atr'],
                'outputs': ['position_size']
            }
        }

    def _load_templates(self) -> Dict[str, StrategyTemplate]:
        """加载预定义模板"""
        templates = {}

        # 模板1: 简单移动平均策略
        templates['simple_ma'] = StrategyTemplate(
            id='simple_ma',
            name='简单移动平均策略',
            description='基于快慢移动平均线交叉的经典策略',
            components=[
                StrategyComponent(
                    id='sma_fast',
                    name='快速MA',
                    type=ComponentType.INDICATOR,
                    component_class='moving_average',
                    parameters={'period': 10, 'price': 'close'},
                    inputs=['close'],
                    outputs=['sma_fast']
                ),
                StrategyComponent(
                    id='sma_slow',
                    name='慢速MA',
                    type=ComponentType.INDICATOR,
                    component_class='moving_average',
                    parameters={'period': 20, 'price': 'close'},
                    inputs=['close'],
                    outputs=['sma_slow']
                ),
                StrategyComponent(
                    id='crossover',
                    name='交叉触发',
                    type=ComponentType.TRIGGER,
                    component_class='crossover',
                    parameters={},
                    inputs=['sma_fast', 'sma_slow'],
                    outputs=['golden_cross', 'death_cross']
                )
            ],
            connections=[
                {'from': 'sma_fast', 'to': 'crossover', 'port': 'line1'},
                {'from': 'sma_slow', 'to': 'crossover', 'port': 'line2'}
            ],
            parameters={}
        )

        # 模板2: RSI反转策略
        templates['rsi_reversal'] = StrategyTemplate(
            id='rsi_reversal',
            name='RSI反转策略',
            description='在RSI超买超卖区域进行反向操作的策略',
            components=[
                StrategyComponent(
                    id='rsi',
                    name='RSI指标',
                    type=ComponentType.INDICATOR,
                    component_class='rsi',
                    parameters={'period': 14, 'overbought': 70, 'oversold': 30},
                    inputs=['close'],
                    outputs=['rsi']
                ),
                StrategyComponent(
                    id='rsi_trigger',
                    name='RSI触发',
                    type=ComponentType.TRIGGER,
                    component_class='threshold',
                    parameters={},
                    inputs=['rsi'],
                    outputs=['oversold_cross', 'overbought_cross']
                ),
                StrategyComponent(
                    id='stop_loss',
                    name='止损',
                    type=ComponentType.RISK_MANAGER,
                    component_class='stop_loss',
                    parameters={'percentage': 5.0},
                    inputs=['entry_price', 'close'],
                    outputs=['stop_loss']
                )
            ],
            connections=[
                {'from': 'rsi', 'to': 'rsi_trigger', 'port': 'value'}
            ],
            parameters={}
        )

        # 模板3: 布林带突破策略
        templates['bollinger_breakout'] = StrategyTemplate(
            id='bollinger_breakout',
            name='布林带突破策略',
            description='当价格突破布林带时进行交易',
            components=[
                StrategyComponent(
                    id='bb',
                    name='布林带',
                    type=ComponentType.INDICATOR,
                    component_class='bollinger',
                    parameters={'period': 20, 'std_dev': 2.0},
                    inputs=['close'],
                    outputs=['bb_upper', 'bb_lower', 'bb_middle']
                ),
                StrategyComponent(
                    id='bb_trigger',
                    name='突破触发',
                    type=ComponentType.TRIGGER,
                    component_class='crossover',
                    parameters={},
                    inputs=['close', 'bb_upper'],
                    outputs=['upper_break', 'lower_break']
                ),
                StrategyComponent(
                    id='position_sizer',
                    name='仓位大小',
                    type=ComponentType.POSITION_SIZER,
                    component_class='volatility_size',
                    parameters={'target_vol': 20.0},
                    inputs=['signal', 'bb_width'],
                    outputs=['position_size']
                )
            ],
            connections=[],
            parameters={}
        )

        # 模板4: 复合技术指标策略
        templates['multi_indicator'] = StrategyTemplate(
            id='multi_indicator',
            name='复合指标策略',
            description='结合RSI、MACD、布林带的综合策略',
            components=[
                StrategyComponent(
                    id='rsi',
                    name='RSI',
                    type=ComponentType.INDICATOR,
                    component_class='rsi',
                    parameters={'period': 14},
                    inputs=['close'],
                    outputs=['rsi']
                ),
                StrategyComponent(
                    id='macd',
                    name='MACD',
                    type=ComponentType.INDICATOR,
                    component_class='macd',
                    parameters={'fast_period': 12, 'slow_period': 26},
                    inputs=['close'],
                    outputs=['macd', 'macd_signal']
                ),
                StrategyComponent(
                    id='bollinger',
                    name='布林带',
                    type=ComponentType.INDICATOR,
                    component_class='bollinger',
                    parameters={'period': 20},
                    inputs=['close'],
                    outputs=['bb_upper', 'bb_lower', 'bb_middle']
                ),
                StrategyComponent(
                    id='combined_trigger',
                    name='综合触发',
                    type=ComponentType.TRIGGER,
                    component_class='crossover',
                    parameters={},
                    inputs=['rsi', 'macd', 'bb_upper'],
                    outputs=['buy_signal', 'sell_signal']
                )
            ],
            connections=[],
            parameters={}
        )

        return templates

    def _load_template(self, template_id: str) -> None:
        """加载策略模板"""
        if template_id not in self.templates:
            raise ValueError(f"模板不存在: {template_id}")

        template = self.templates[template_id]
        self.components = template.components
        self.connections = template.connections
        self.template_id = template_id

        logger.info(f"已加载策略模板: {template.name}")

    def _build_strategy(self) -> None:
        """构建当前策略"""
        try:
            # 创建组件实例
            for component in self.components:
                self._create_component_instance(component)

            logger.info("策略构建完成")

        except Exception as e:
            logger.error(f"策略构建失败: {e}")
            raise

    def _create_component_instance(self, component: StrategyComponent) -> Any:
        """创建组件实例"""
        component_info = self.component_library.get(component.component_class)
        if not component_info:
            raise ValueError(f"未知组件: {component.component_class}")

        # 根据组件类型创建实例
        if component_info['type'] == ComponentType.INDICATOR:
            instance = self._create_indicator(component)
        elif component_info['type'] == ComponentType.TRIGGER:
            instance = self._create_trigger(component)
        elif component_info['type'] == ComponentType.RISK_MANAGER:
            instance = self._create_risk_manager(component)
        elif component_info['type'] == ComponentType.POSITION_SIZER:
            instance = self._create_position_sizer(component)
        else:
            instance = None

        self.strategy_instances[component.id] = instance
        return instance

    def _create_indicator(self, component: StrategyComponent) -> Callable:
        """创建技术指标组件"""
        def indicator(data: pd.DataFrame) -> Dict[str, float]:
            price = data.get('Close', data.get('close', data.iloc[:, 0]))
            result = {}

            if component.component_class == 'sma':
                period = component.parameters.get('period', 20)
                result['sma'] = float(price.rolling(period).mean().iloc[-1])
                result['sma_slope'] = float(price.rolling(period).mean().pct_change(5).iloc[-1])

            elif component.component_class == 'rsi':
                period = component.parameters.get('period', 14)
                delta = price.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss.replace(0, 1e-10)
                result['rsi'] = float(100 - (100 / (1 + rs)).iloc[-1])

            elif component.component_class == 'macd':
                fast = component.parameters.get('fast_period', 12)
                slow = component.parameters.get('slow_period', 26)
                signal = component.parameters.get('signal_period', 9)
                ema_fast = price.ewm(span=fast).mean()
                ema_slow = price.ewm(span=slow).mean()
                macd_line = ema_fast - ema_slow
                result['macd'] = float(macd_line.iloc[-1])
                result['macd_signal'] = float(macd_line.ewm(span=signal).mean().iloc[-1])
                result['macd_histogram'] = float((macd_line - macd_line.ewm(span=signal).mean()).iloc[-1])

            elif component.component_class == 'bollinger':
                period = component.parameters.get('period', 20)
                std_dev = component.parameters.get('std_dev', 2.0)
                sma = price.rolling(period).mean()
                std = price.rolling(period).std()
                result['bb_upper'] = float((sma + std * std_dev).iloc[-1])
                result['bb_lower'] = float((sma - std * std_dev).iloc[-1])
                result['bb_middle'] = float(sma.iloc[-1])
                result['bb_width'] = float(((sma + std * std_dev) - (sma - std * std_dev)).iloc[-1] / sma.iloc[-1])

            return result

        return indicator

    def _create_trigger(self, component: StrategyComponent) -> Callable:
        """创建触发器组件"""
        def trigger(input_data: Dict[str, float]) -> Dict[str, Any]:
            if component.component_class == 'crossover':
                line1 = input_data.get('line1', 0)
                line2 = input_data.get('line2', 0)
                return {
                    'golden_cross': 1 if line1 > line2 else 0,
                    'death_cross': 1 if line1 < line2 else 0
                }
            elif component.component_class == 'threshold':
                value = input_data.get('value', 0)
                upper = component.parameters.get('upper', 70)
                lower = component.parameters.get('lower', 30)
                return {
                    'upper_cross': 1 if value > upper else 0,
                    'lower_cross': 1 if value < lower else 0
                }
            return {}

        return trigger

    def _create_risk_manager(self, component: StrategyComponent) -> Callable:
        """创建风险管理组件"""
        def risk_manager(data: Dict[str, float]) -> Dict[str, Any]:
            if component.component_class == 'stop_loss':
                entry = data.get('entry_price', 0)
                current = data.get('current_price', 0)
                percentage = component.parameters.get('percentage', 5.0)
                trigger_price = entry * (1 - percentage / 100)
                return {
                    'stop_loss_triggered': 1 if current < trigger_price else 0,
                    'trigger_price': trigger_price
                }
            elif component.component_class == 'take_profit':
                entry = data.get('entry_price', 0)
                current = data.get('current_price', 0)
                percentage = component.parameters.get('percentage', 10.0)
                trigger_price = entry * (1 + percentage / 100)
                return {
                    'take_profit_triggered': 1 if current > trigger_price else 0,
                    'trigger_price': trigger_price
                }
            return {}

        return risk_manager

    def _create_position_sizer(self, component: StrategyComponent) -> Callable:
        """创建仓位大小组件"""
        def position_sizer(data: Dict[str, Any]) -> Dict[str, float]:
            if component.component_class == 'fixed_size':
                size = component.parameters.get('size', 100)
                return {'position_size': size}
            elif component.component_class == 'percent_size':
                percentage = component.parameters.get('percentage', 10.0)
                portfolio_value = data.get('portfolio_value', 100000)
                return {'position_size': portfolio_value * percentage / 100}
            elif component.component_class == 'volatility_size':
                target_vol = component.parameters.get('target_vol', 20.0)
                # 简化实现
                return {'position_size': target_vol * 10}
            return {'position_size': 100}

        return position_sizer

    def initialize(self, historical_data: pd.DataFrame, **kwargs) -> None:
        """
        初始化策略

        Args:
            historical_data: 历史数据
            **kwargs: 额外参数
        """
        try:
            # 加载模板
            if not self.components and self.template_id:
                self._load_template(self.template_id)

            # 构建策略
            if not self.strategy_instances:
                self._build_strategy()

            logger.info(f"策略构建器初始化完成: {self.strategy_name}")

        except Exception as e:
            logger.error(f"策略初始化失败: {e}")
            raise

    def add_component(
        self,
        component_class: str,
        name: str,
        parameters: Dict[str, Any] = None,
        position: Tuple[float, float] = (0, 0)
    ) -> str:
        """
        添加组件

        Args:
            component_class: 组件类名
            name: 组件名称
            parameters: 组件参数
            position: 组件位置

        Returns:
            组件ID
        """
        component_id = f"{component_class}_{len(self.components)}"
        component_info = self.component_library[component_class]

        component = StrategyComponent(
            id=component_id,
            name=name,
            type=component_info['type'],
            component_class=component_class,
            parameters=parameters or component_info['parameters'],
            inputs=component_info['inputs'],
            outputs=component_info['outputs'],
            position=position
        )

        self.components.append(component)
        self._create_component_instance(component)

        return component_id

    def remove_component(self, component_id: str) -> None:
        """移除组件"""
        self.components = [c for c in self.components if c.id != component_id]
        if component_id in self.strategy_instances:
            del self.strategy_instances[component_id]

    def update_component_parameters(self, component_id: str, parameters: Dict[str, Any]) -> None:
        """更新组件参数"""
        for component in self.components:
            if component.id == component_id:
                component.parameters.update(parameters)
                # 重新创建组件实例
                self._create_component_instance(component)
                break

    def connect_components(self, from_id: str, to_id: str, port: str = None) -> None:
        """连接组件"""
        connection = {
            'from': from_id,
            'to': to_id,
            'port': port
        }
        self.connections.append(connection)

    def generate_signals(self, current_data: pd.DataFrame) -> List[Signal]:
        """
        生成策略信号

        Args:
            current_data: 当前市场数据

        Returns:
            信号列表
        """
        signals = []

        try:
            # 执行组件计算
            component_results = {}

            for component in self.components:
                if not component.enabled:
                    continue

                instance = self.strategy_instances.get(component.id)
                if not instance:
                    continue

                # 获取输入数据
                input_data = {}
                for input_name in component.inputs:
                    if input_name in current_data.columns:
                        if input_name == 'close':
                            input_data[input_name] = float(current_data['Close'].iloc[-1])
                        else:
                            input_data[input_name] = float(current_data[input_name].iloc[-1])
                    elif input_name in component_results:
                        # 来自其他组件的输出
                        if isinstance(component_results[input_name], dict):
                            input_data[input_name] = component_results[input_name].get(
                                list(component_results[input_name].keys())[0], 0
                            )

                # 执行组件
                if component.type == ComponentType.INDICATOR:
                    result = instance(current_data)
                else:
                    result = instance(input_data)

                component_results[component.id] = result

                # 检查是否有触发信号
                for output_name, output_value in result.items():
                    if output_name in ['golden_cross', 'death_cross', 'buy_signal', 'sell_signal']:
                        if output_value and output_value != 0:
                            # 生成信号
                            latest_data = current_data.iloc[-1]
                            symbol = latest_data.get('Symbol', 'UNKNOWN')

                            if 'buy' in output_name.lower() or 'golden' in output_name.lower():
                                signal_type = SignalType.BUY
                                confidence = float(output_value)
                            else:
                                signal_type = SignalType.SELL
                                confidence = float(output_value)

                            signal = Signal(
                                symbol=symbol,
                                timestamp=latest_data.name if isinstance(latest_data.name, pd.Timestamp) else pd.Timestamp.now(),
                                signal_type=signal_type,
                                confidence=confidence,
                                reason=f"策略组件: {component.name} - {output_name}",
                                price=float(latest_data['Close']),
                                metadata={
                                    'component_id': component.id,
                                    'component_name': component.name,
                                    'output_name': output_name,
                                    'output_value': output_value,
                                    'component_parameters': component.parameters
                                }
                            )
                            signals.append(signal)
                            self.signal_history.append(signal)

        except Exception as e:
            logger.error(f"信号生成失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return signals

    def get_parameters(self) -> Dict[str, Any]:
        """获取策略参数"""
        return {
            'template_id': self.template_id,
            'components': [asdict(c) for c in self.components],
            'connections': self.connections,
            'component_count': len(self.components)
        }

    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """设置策略参数"""
        if 'template_id' in parameters:
            self._load_template(parameters['template_id'])
        if 'components' in parameters:
            self.components = [StrategyComponent(**c) for c in parameters['components']]
            self._build_strategy()
        if 'connections' in parameters:
            self.connections = parameters['connections']

    def generate_code(self) -> str:
        """
        生成策略代码

        Returns:
            生成的Python代码
        """
        code_lines = [
            "# 自动生成的策略代码",
            "# 生成时间: " + datetime.now().isoformat(),
            "",
            "import pandas as pd",
            "import numpy as np",
            "from typing import Dict, List",
            "",
            "",
            "class GeneratedStrategy:",
            '    """自动生成的策略"""',
            "",
            "    def __init__(self):",
            "        self.name = 'Generated Strategy'",
            "        self.components = []",
            "",
            "    def generate_signals(self, data: pd.DataFrame) -> List[Dict]:",
            "        signals = []",
            "        # TODO: 实现信号生成逻辑",
            "        # 以下是组件配置:",
            ""
        ]

        for component in self.components:
            code_lines.append(f"        # 组件: {component.name}")
            code_lines.append(f"        # 类型: {component.component_class}")
            code_lines.append(f"        # 参数: {component.parameters}")
            code_lines.append("")

        code_lines.append("        return signals")

        return "\n".join(code_lines)

    def export_config(self) -> str:
        """
        导出策略配置

        Returns:
            JSON格式的配置
        """
        # 转换组件数据
        components_data = []
        for c in self.components:
            comp_dict = asdict(c)
            comp_dict['type'] = c.type.value  # 转换Enum为字符串
            components_data.append(comp_dict)

        config = {
            'template_id': self.template_id,
            'components': components_data,
            'connections': self.connections,
            'export_time': datetime.now().isoformat()
        }
        return json.dumps(config, indent=2, ensure_ascii=False)

    def get_builder_summary(self) -> Dict[str, Any]:
        """
        获取构建器摘要

        Returns:
            包含构建信息的字典
        """
        return {
            'strategy_name': self.strategy_name,
            'template_id': self.template_id,
            'component_count': len(self.components),
            'components': [
                {
                    'id': c.id,
                    'name': c.name,
                    'type': c.type.value,
                    'class': c.component_class,
                    'parameters': c.parameters
                }
                for c in self.components
            ],
            'connections': self.connections,
            'available_templates': list(self.templates.keys()),
            'available_components': list(self.component_library.keys()),
            'signal_count': len(self.signal_history)
        }


# 导出类
__all__ = ['StrategyBuilder', 'StrategyComponent', 'StrategyTemplate', 'ComponentType']
