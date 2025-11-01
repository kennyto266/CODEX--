"""
模拟交易风险管理器

负责模拟交易系统的风险控制，包括：
- 资金充足性检查
- 仓位限制检查
- 日交易次数限制
- 集中度风险检查
- 最大回撤控制
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass, field

from .base_trading_api import AccountInfo, Position
from .realtime_execution_engine import TradeSignal


@dataclass
class RiskLimits:
    """风险限额配置"""
    # 资金相关
    min_cash_reserve: Decimal = field(default_factory=lambda: Decimal('10000'))  # 最小现金保留
    max_trade_value: Decimal = field(default_factory=lambda: Decimal('100000'))  # 单笔最大交易金额
    max_daily_loss: Decimal = field(default_factory=lambda: Decimal('50000'))  # 日最大亏损

    # 仓位相关
    max_position_value: Decimal = field(default_factory=lambda: Decimal('500000'))  # 单个股票最大仓位
    max_position_ratio: float = 0.3  # 单个股票占总资产最大比例
    max_sector_concentration: float = 0.5  # 行业集中度限制

    # 交易相关
    max_daily_trades: int = 100  # 日最大交易次数
    max_order_frequency: int = 10  # 单个股票日最大交易次数

    # 回撤相关
    max_drawdown: float = 0.15  # 最大回撤限制 (15%)


class PaperTradingRiskManager:
    """
    模拟交易风险管理器

    在交易执行前进行全面的风险检查，确保交易符合预定义的风险策略
    """

    def __init__(self, limits: Optional[RiskLimits] = None):
        """
        初始化风险管理器

        Args:
            limits: 风险限额配置，如果为None则使用默认配置
        """
        self.limits = limits or RiskLimits()
        self.logger = logging.getLogger("hk_quant_system.paper_trading.risk")

        # 实时风险状态
        self.daily_pnl = Decimal('0')
        self.daily_trade_count = 0
        self.daily_trades_by_symbol: Dict[str, int] = {}
        self.last_reset_date = datetime.now().date()
        self.peak_equity = Decimal('0')
        self.current_drawdown = Decimal('0')

        # 紧急停止状态
        self.emergency_stop_active = False
        self.emergency_stop_time: Optional[datetime] = None
        self.emergency_stop_reason: Optional[str] = None
        self._original_limits_backup: Optional[RiskLimits] = None

        self.logger.info("PaperTradingRiskManager 已初始化")
        self.logger.info(f"风险限额配置: {self.limits}")

    async def check_pre_trade_risk(
        self,
        signal: TradeSignal,
        account: AccountInfo,
        positions: List[Position]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        执行交易前风险检查

        Args:
            signal: 交易信号
            account: 账户信息
            positions: 当前持仓列表

        Returns:
            Tuple[bool, str, Dict]: (是否通过检查, 错误信息, 风险详情)
        """
        try:
            # 重置日统计（如果是新的一天）
            await self._reset_daily_stats_if_needed()

            # 检查紧急停止状态
            if self.emergency_stop_active:
                stop_duration = (datetime.now() - self.emergency_stop_time).total_seconds() if self.emergency_stop_time else 0
                return False, (
                    f"系统处于紧急停止状态，所有交易已被阻止！"
                    f"停止时间: {self.emergency_stop_time.strftime('%Y-%m-%d %H:%M:%S') if self.emergency_stop_time else 'N/A'}, "
                    f"已持续: {stop_duration:.0f}秒, "
                    f"原因: {self.emergency_stop_reason or '未指定'}"
                ), {
                    'emergency_stop': True,
                    'stop_time': self.emergency_stop_time.isoformat() if self.emergency_stop_time else None,
                    'stop_reason': self.emergency_stop_reason,
                    'duration_seconds': stop_duration
                }

            risk_details = {
                'signal_id': signal.signal_id,
                'symbol': signal.symbol,
                'side': signal.side,
                'quantity': str(signal.quantity),
                'price': str(signal.price) if signal.price else 'MARKET',
                'trade_value': Decimal('0'),
                'checks': {}
            }

            # 1. 基础验证
            valid, msg = self._validate_basic_requirements(signal)
            risk_details['checks']['basic'] = {'passed': valid, 'message': msg}
            if not valid:
                return False, msg, risk_details

            # 2. 资金充足性检查
            trade_value = signal.quantity * (signal.price or Decimal('0'))
            risk_details['trade_value'] = str(trade_value)
            valid, msg = self._check_cash_sufficiency(trade_value, account)
            risk_details['checks']['cash'] = {'passed': valid, 'message': msg, 'trade_value': str(trade_value)}
            if not valid:
                return False, msg, risk_details

            # 3. 仓位限制检查
            valid, msg = self._check_position_limits(signal, trade_value, account, positions)
            risk_details['checks']['position'] = {'passed': valid, 'message': msg}
            if not valid:
                return False, msg, risk_details

            # 4. 集中度风险检查
            valid, msg = self._check_concentration_risk(signal, trade_value, account, positions)
            risk_details['checks']['concentration'] = {'passed': valid, 'message': msg}
            if not valid:
                return False, msg, risk_details

            # 5. 交易次数限制检查
            valid, msg = self._check_trade_frequency(signal.symbol)
            risk_details['checks']['frequency'] = {'passed': valid, 'message': msg}
            if not valid:
                return False, msg, risk_details

            # 6. 最大回撤检查
            valid, msg = self._check_max_drawdown(account.equity)
            risk_details['checks']['drawdown'] = {'passed': valid, 'message': msg}
            if not valid:
                return False, msg, risk_details

            # 7. 日亏损检查
            valid, msg = self._check_daily_loss_limit(trade_value if signal.side.value == 'sell' else Decimal('0'))
            risk_details['checks']['daily_loss'] = {'passed': valid, 'message': msg}
            if not valid:
                return False, msg, risk_details

            self.logger.info(f"✅ 风险检查通过: {signal.symbol} {signal.side} {signal.quantity}")
            return True, "风险检查通过", risk_details

        except Exception as e:
            self.logger.error(f"风险检查异常: {e}", exc_info=True)
            return False, f"风险检查异常: {str(e)}", {}

    def _validate_basic_requirements(self, signal: TradeSignal) -> Tuple[bool, str]:
        """验证基础要求"""
        if not signal.symbol:
            return False, "股票代码不能为空"

        if signal.quantity <= 0:
            return False, "交易数量必须大于0"

        if signal.side.value not in ['buy', 'sell']:
            return False, "无效的交易方向"

        if signal.price and signal.price <= 0:
            return False, "交易价格必须大于0"

        return True, "基础验证通过"

    def _check_cash_sufficiency(
        self,
        trade_value: Decimal,
        account: AccountInfo
    ) -> Tuple[bool, str]:
        """检查资金充足性"""
        # 计算需要的现金（包括手续费）
        commission = trade_value * Decimal('0.001')  # 假设0.1%手续费
        required_cash = trade_value + commission + self.limits.min_cash_reserve

        available_cash = account.cash or Decimal('0')

        if available_cash < required_cash:
            return False, (
                f"现金不足: 需要 {required_cash:,.2f}, "
                f"可用 {available_cash:,.2f}, "
                f"缺口 {required_cash - available_cash:,.2f}"
            )

        # 检查单笔交易金额限制
        if trade_value > self.limits.max_trade_value:
            return False, (
                f"单笔交易金额超限: {trade_value:,.2f} > "
                f"{self.limits.max_trade_value:,.2f}"
            )

        return True, f"资金充足 (需要 {required_cash:,.2f}, 可用 {available_cash:,.2f})"

    def _check_position_limits(
        self,
        signal: TradeSignal,
        trade_value: Decimal,
        account: AccountInfo,
        positions: List[Position]
    ) -> Tuple[bool, str]:
        """检查仓位限制"""
        # 计算交易后的持仓
        current_position = Decimal('0')
        for pos in positions:
            if pos.symbol == signal.symbol:
                current_position = pos.quantity
                break

        if signal.side.value == 'buy':
            new_position = current_position + signal.quantity
        else:
            new_position = current_position - signal.quantity
            if new_position < 0:
                return False, "卖出数量超过当前持仓"

        # 计算交易后市值
        avg_price = signal.price or Decimal('350')  # 使用信号价格或默认价格
        position_value = new_position * avg_price

        # 检查单个股票最大仓位
        if position_value > self.limits.max_position_value:
            return False, (
                f"单个股票仓位超限: {position_value:,.2f} > "
                f"{self.limits.max_position_value:,.2f}"
            )

        # 检查持仓比例
        total_equity = account.equity or Decimal('0')
        if total_equity > 0:
            position_ratio = float(position_value / total_equity)
            if position_ratio > self.limits.max_position_ratio:
                return False, (
                    f"持仓比例超限: {position_ratio:.2%} > "
                    f"{self.limits.max_position_ratio:.2%}"
                )

        return True, f"仓位检查通过 (新仓位: {new_position})"

    def _check_concentration_risk(
        self,
        signal: TradeSignal,
        trade_value: Decimal,
        account: AccountInfo,
        positions: List[Position]
    ) -> Tuple[bool, str]:
        """检查集中度风险"""
        # 计算当前总市值
        total_market_value = Decimal('0')
        for pos in positions:
            if pos.market_value:
                total_market_value += pos.market_value

        # 如果当前总市值为0（没有持仓），则不检查集中度风险
        if total_market_value == 0:
            return True, "无持仓，跳过集中度风险检查"

        # 添加交易价值（如果是买入）
        if signal.side.value == 'buy':
            total_market_value += trade_value

        # 计算交易后的持仓比例
        position_value = trade_value
        if total_market_value > 0:
            new_ratio = float(position_value / total_market_value)
            if new_ratio > self.limits.max_sector_concentration:
                return False, (
                    f"集中度风险: 新交易占比 {new_ratio:.2%} > "
                    f"{self.limits.max_sector_concentration:.2%}"
                )

        return True, "集中度风险检查通过"

    def _check_trade_frequency(self, symbol: str) -> Tuple[bool, str]:
        """检查交易频率"""
        # 检查日交易次数
        if self.daily_trade_count >= self.limits.max_daily_trades:
            return False, (
                f"日交易次数超限: {self.daily_trade_count} >= "
                f"{self.limits.max_daily_trades}"
            )

        # 检查单个股票交易次数
        symbol_count = self.daily_trades_by_symbol.get(symbol, 0)
        if symbol_count >= self.limits.max_order_frequency:
            return False, (
                f"股票 {symbol} 交易次数超限: {symbol_count} >= "
                f"{self.limits.max_order_frequency}"
            )

        return True, f"交易频率检查通过 (日交易: {self.daily_trade_count}, {symbol}: {symbol_count})"

    def _check_max_drawdown(self, current_equity: Decimal) -> Tuple[bool, str]:
        """检查最大回撤"""
        # 更新峰值
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity

        # 计算当前回撤
        if self.peak_equity > 0:
            self.current_drawdown = (self.peak_equity - current_equity) / self.peak_equity

            if self.current_drawdown > Decimal(str(self.limits.max_drawdown)):
                return False, (
                    f"最大回撤超限: {self.current_drawdown:.2%} > "
                    f"{self.limits.max_drawdown:.2%}"
                )

        return True, f"回撤检查通过 (当前回撤: {self.current_drawdown:.2%})"

    def _check_daily_loss_limit(self, potential_loss: Decimal) -> Tuple[bool, str]:
        """检查日亏损限制"""
        # 如果是卖出，计算潜在亏损
        if potential_loss > 0:
            new_daily_pnl = self.daily_pnl - potential_loss
            if abs(new_daily_pnl) > self.limits.max_daily_loss:
                return False, (
                    f"日亏损超限: {abs(new_daily_pnl):,.2f} > "
                    f"{self.limits.max_daily_loss:,.2f}"
                )

        return True, f"日亏损检查通过 (当前: {self.daily_pnl:,.2f})"

    async def _reset_daily_stats_if_needed(self):
        """如果日期变更，重置日统计"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.logger.info(f"重置日统计数据 (从 {self.last_reset_date} 到 {today})")
            self.daily_pnl = Decimal('0')
            self.daily_trade_count = 0
            self.daily_trades_by_symbol.clear()
            self.last_reset_date = today

    async def record_trade(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        pnl: Decimal = Decimal('0')
    ):
        """记录已执行的交易"""
        try:
            # 重置日统计（如果是新的一天）
            await self._reset_daily_stats_if_needed()

            # 更新统计
            self.daily_pnl += pnl
            self.daily_trade_count += 1

            # 更新单个股票交易次数
            self.daily_trades_by_symbol[symbol] = self.daily_trades_by_symbol.get(symbol, 0) + 1

            self.logger.info(
                f"记录交易: {symbol} {side} {quantity} @ {price}, "
                f"PNL: {pnl:,.2f}, "
                f"日交易次数: {self.daily_trade_count}"
            )

        except Exception as e:
            self.logger.error(f"记录交易失败: {e}", exc_info=True)

    async def get_risk_status(self) -> Dict[str, Any]:
        """
        获取当前风险状态

        Returns:
            Dict[str, Any]: 风险状态信息
        """
        # 计算紧急停止持续时间
        emergency_stop_duration = None
        if self.emergency_stop_active and self.emergency_stop_time:
            emergency_stop_duration = (datetime.now() - self.emergency_stop_time).total_seconds()

        return {
            'daily_pnl': str(self.daily_pnl),
            'daily_trade_count': self.daily_trade_count,
            'peak_equity': str(self.peak_equity),
            'current_drawdown': str(self.current_drawdown),
            'trades_by_symbol': dict(self.daily_trades_by_symbol),
            'emergency_stop': {
                'active': self.emergency_stop_active,
                'trigger_time': self.emergency_stop_time.isoformat() if self.emergency_stop_time else None,
                'reason': self.emergency_stop_reason,
                'duration_seconds': emergency_stop_duration,
                'has_backup': self._original_limits_backup is not None
            },
            'risk_limits': {
                'min_cash_reserve': str(self.limits.min_cash_reserve),
                'max_trade_value': str(self.limits.max_trade_value),
                'max_daily_loss': str(self.limits.max_daily_loss),
                'max_position_value': str(self.limits.max_position_value),
                'max_position_ratio': self.limits.max_position_ratio,
                'max_daily_trades': self.limits.max_daily_trades,
                'max_drawdown': self.limits.max_drawdown
            },
            'last_reset_date': self.last_reset_date.isoformat()
        }

    async def update_limits(self, new_limits: RiskLimits):
        """
        更新风险限额

        Args:
            new_limits: 新的风险限额配置
        """
        old_limits = self.limits
        self.limits = new_limits
        self.logger.info(f"风险限额已更新: {old_limits} -> {new_limits}")

    async def emergency_stop(self, reason: str = "未指定原因") -> bool:
        """
        执行紧急停止

        Args:
            reason: 紧急停止原因

        Returns:
            bool: 是否成功执行
        """
        try:
            # 如果已经在紧急停止状态，记录但不重复执行
            if self.emergency_stop_active:
                self.logger.warning(f"⚠️ 系统已在紧急停止状态，停止时间: {self.emergency_stop_time}")
                return True

            self.logger.warning("⚠️ 执行紧急停止！")
            self.logger.warning(f"紧急停止原因: {reason}")

            # 备份当前限制设置
            import copy
            self._original_limits_backup = copy.deepcopy(self.limits)

            # 设置紧急停止状态
            self.emergency_stop_active = True
            self.emergency_stop_time = datetime.now()
            self.emergency_stop_reason = reason

            # 记录紧急停止的详细信息到日志
            self.logger.warning("=" * 80)
            self.logger.warning("紧急停止详细信息")
            self.logger.warning("=" * 80)
            self.logger.warning(f"停止时间: {self.emergency_stop_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.warning(f"停止原因: {reason}")
            self.logger.warning(f"备份的风险限额:")
            self.logger.warning(f"  - 日最大交易次数: {self._original_limits_backup.max_daily_trades}")
            self.logger.warning(f"  - 单笔最大交易金额: {self._original_limits_backup.max_trade_value:,.2f}")
            self.logger.warning(f"  - 单个股票最大仓位: {self._original_limits_backup.max_position_value:,.2f}")
            self.logger.warning(f"  - 最大回撤: {self._original_limits_backup.max_drawdown:.2%}")
            self.logger.warning("=" * 80)
            self.logger.warning("✅ 紧急停止执行完成，所有交易已被阻止")

            return True

        except Exception as e:
            self.logger.error(f"紧急停止失败: {e}", exc_info=True)
            return False

    async def resume_from_emergency_stop(self) -> bool:
        """
        从紧急停止状态恢复

        Returns:
            bool: 是否成功恢复
        """
        try:
            # 如果没有处于紧急停止状态，记录并返回
            if not self.emergency_stop_active:
                self.logger.warning("⚠️ 系统未处于紧急停止状态，无需恢复")
                return True

            self.logger.warning("🔄 开始从紧急停止状态恢复...")

            # 恢复原始风险限额
            if self._original_limits_backup:
                old_limits = self.limits
                self.limits = self._original_limits_backup
                self.logger.info(f"风险限额已恢复到紧急停止前: {old_limits} -> {self.limits}")

            # 清除紧急停止状态
            stop_duration = (datetime.now() - self.emergency_stop_time).total_seconds() if self.emergency_stop_time else 0
            self.emergency_stop_active = False
            self.emergency_stop_time = None
            self.emergency_stop_reason = None
            self._original_limits_backup = None

            # 记录恢复详情
            self.logger.warning("=" * 80)
            self.logger.warning("紧急停止恢复详情")
            self.logger.warning("=" * 80)
            self.logger.warning(f"恢复时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.warning(f"紧急停止持续时间: {stop_duration:.0f}秒 ({stop_duration/60:.1f}分钟)")
            self.logger.warning("✅ 系统已恢复正常交易")
            self.logger.warning("=" * 80)

            return True

        except Exception as e:
            self.logger.error(f"从紧急停止恢复失败: {e}", exc_info=True)
            return False

    def is_emergency_stop_active(self) -> bool:
        """
        检查是否处于紧急停止状态

        Returns:
            bool: 是否处于紧急停止状态
        """
        return self.emergency_stop_active

    async def reset_risk_state(self):
        """重置风险状态"""
        self.logger.info("重置风险状态")
        self.daily_pnl = Decimal('0')
        self.daily_trade_count = 0
        self.daily_trades_by_symbol.clear()
        self.peak_equity = Decimal('0')
        self.current_drawdown = Decimal('0')
        self.last_reset_date = datetime.now().date()

        # 清除紧急停止状态（如果需要）
        if self.emergency_stop_active:
            self.logger.warning("⚠️ 重置风险状态时检测到紧急停止状态，将同时清除")
            self.emergency_stop_active = False
            self.emergency_stop_time = None
            self.emergency_stop_reason = None
            self._original_limits_backup = None


# 便捷函数：创建风险管理器
def create_risk_manager(
    min_cash_reserve: Decimal = Decimal('10000'),
    max_trade_value: Decimal = Decimal('100000'),
    max_daily_trades: int = 100,
    max_position_value: Decimal = Decimal('500000'),
    max_drawdown: float = 0.15
) -> PaperTradingRiskManager:
    """
    创建风险管理器实例

    Args:
        min_cash_reserve: 最小现金保留
        max_trade_value: 单笔最大交易金额
        max_daily_trades: 日最大交易次数
        max_position_value: 单个股票最大仓位
        max_drawdown: 最大回撤

    Returns:
        PaperTradingRiskManager: 风险管理器实例
    """
    limits = RiskLimits(
        min_cash_reserve=min_cash_reserve,
        max_trade_value=max_trade_value,
        max_daily_trades=max_daily_trades,
        max_position_value=max_position_value,
        max_drawdown=max_drawdown
    )

    return PaperTradingRiskManager(limits)
