"""
富途牛牛API交易适配器 - 真实交易API

使用富途OpenAPI进行真实交易
支持DEMO环境 (SIMULATE) 安全测试

前置条件:
1. 安装富途API: pip install futu-api
2. 启动FutuOpenD网关客户端
3. 配置DEMO账户 (模拟环境)
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime

from .base_trading_api import (
    BaseTradingAPI, Order, OrderType, OrderSide, OrderStatus,
    Position, AccountInfo, MarketData
)

# 尝试导入富途API
try:
    import futu as ft
    FUTU_AVAILABLE = True
except ImportError:
    FUTU_AVAILABLE = False
    logging.warning("富途API未安装，请运行: pip install futu-api")


class FutuTradingAPI(BaseTradingAPI):
    """富途交易API适配器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        if not FUTU_AVAILABLE:
            raise ImportError("富途API未安装，请先安装: pip install futu-api")

        # 富途配置
        self.host = config.get('host', '127.0.0.1')
        self.port = config.get('port', 11111)
        self.trade_password = config.get('trade_password', '')
        self.market = config.get('market', 'HK')  # HK, US, CN

        # 交易环境 (使用DEMO模拟环境)
        self.trd_env = ft.TrdEnv.SIMULATE  # 模拟环境

        # 交易上下文
        self.trade_ctx = None
        self.quote_ctx = None

        # 订单映射
        self.order_mapping: Dict[str, str] = {}  # 本地订单ID -> 富途订单ID

    async def connect(self) -> bool:
        """连接到富途API"""
        try:
            # 创建交易上下文 (港股)
            if self.market.upper() == 'HK':
                self.trade_ctx = ft.OpenHKTradeContext(host=self.host, port=self.port)
            elif self.market.upper() == 'US':
                self.trade_ctx = ft.OpenUSTradeContext(host=self.host, port=self.port)
            elif self.market.upper() == 'CN':
                self.trade_ctx = ft.OpenCNTradeContext(host=self.host, port=self.port)
            else:
                raise ValueError(f"不支持的市场: {self.market}")

            # 创建行情上下文
            self.quote_ctx = ft.OpenQuoteContext(host=self.host, port=self.port)

            self.logger.info(f"富途API已连接: {self.host}:{self.port}")
            return True

        except Exception as e:
            self.logger.error(f"富途API连接失败: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开连接"""
        try:
            if self.trade_ctx:
                self.trade_ctx.close()
            if self.quote_ctx:
                self.quote_ctx.close()

            self._connected = False
            self._authenticated = False
            self.logger.info("富途API已断开")
            return True

        except Exception as e:
            self.logger.error(f"富途API断开失败: {e}")
            return False

    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """身份验证 - 解锁交易"""
        try:
            if not self.trade_ctx:
                return False

            # 获取交易密码
            password = credentials.get('trade_password', self.trade_password)
            if not password:
                self.logger.warning("未设置交易密码，使用DEMO环境可能需要密码")
                password = '123456'  # DEMO默认密码

            # 解锁交易接口
            ret, data = self.trade_ctx.unlock_trade(password=password)
            if ret == ft.RET_OK:
                self._authenticated = True
                self.logger.info("富途交易接口已解锁 (DEMO环境)")
                return True
            else:
                self.logger.error(f"解锁失败: {data}")
                return False

        except Exception as e:
            self.logger.error(f"身份验证失败: {e}")
            return False

    async def get_account_info(self) -> Optional[AccountInfo]:
        """获取账户信息"""
        try:
            if not self.trade_ctx or not self._authenticated:
                return None

            # 查询账户信息
            ret, data = self.trade_ctx.accinfo_query(trd_env=self.trd_env)
            if ret != ft.RET_OK:
                self.logger.error(f"查询账户信息失败: {data}")
                return None

            if data.empty:
                return None

            # 取第一个账户 (通常只有一个)
            row = data.iloc[0]

            # 获取账户ID - 使用连接的UserID或默认账户ID
            account_id = getattr(self, '_account_id', None)
            if not account_id:
                # 如果没有存储的账户ID，尝试从上下文获取或使用默认
                account_id = "DEMO_ACCOUNT_2860386"  # 基于您的用户ID

            return AccountInfo(
                account_id=account_id,
                account_type="SIMULATE",  # DEMO环境
                buying_power=Decimal(str(row.get('power', 0))),
                cash=Decimal(str(row.get('cash', 0))),
                equity=Decimal(str(row.get('total_assets', 0))),
                margin_used=Decimal(str(row.get('frozen_cash', 0))),
                margin_available=Decimal(str(row.get('avl_withdrawal_cash', 0))),
                last_updated=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"获取账户信息失败: {e}")
            return None

    async def get_positions(self) -> List[Position]:
        """获取持仓信息"""
        try:
            if not self.trade_ctx or not self._authenticated:
                return []

            # 查询持仓列表
            ret, data = self.trade_ctx.position_list_query(trd_env=self.trd_env)
            if ret != ft.RET_OK:
                self.logger.error(f"查询持仓失败: {data}")
                return []

            positions = []
            for _, row in data.iterrows():
                # 富途港股代码格式: HK.00700 -> 00700.HK, US.WATT -> WATT.US
                futu_code = str(row['code'])
                if futu_code.startswith('HK.'):
                    symbol = futu_code.replace('HK.', '') + '.HK'
                elif futu_code.startswith('US.'):
                    symbol = futu_code.replace('US.', '') + '.US'
                else:
                    symbol = futu_code

                position = Position(
                    symbol=symbol,
                    quantity=Decimal(str(row['qty'])),
                    average_price=Decimal(str(row['cost_price'])),
                    current_price=Decimal(str(row.get('nominal_price', 0))),
                    market_value=Decimal(str(row.get('market_val', 0))),
                    unrealized_pnl=Decimal(str(row.get('pl_val', 0))),
                    last_updated=datetime.now()
                )
                positions.append(position)

            return positions

        except Exception as e:
            self.logger.error(f"获取持仓失败: {e}")
            return []

    async def get_orders(self, status_filter: Optional[OrderStatus] = None) -> List[Order]:
        """获取订单列表"""
        try:
            if not self.trade_ctx or not self._authenticated:
                return []

            # 查询订单列表
            ret, data = self.trade_ctx.order_list_query(trd_env=self.trd_env)
            if ret != ft.RET_OK:
                self.logger.error(f"查询订单失败: {data}")
                return []

            orders = []
            for _, row in data.iterrows():
                # 富途港股代码格式转换
                futu_code = str(row['code'])
                symbol = futu_code.replace('HK.', '').replace('US.', '') + '.HK' if futu_code.startswith('HK.') else futu_code

                # 转换订单状态
                futu_status = str(row['orderStatus'])
                order_status = self._convert_futu_status(futu_status)

                # 过滤状态
                if status_filter and order_status != status_filter:
                    continue

                # 转换买卖方向
                futu_side = str(row['trdSide'])
                order_side = OrderSide.BUY if futu_side == 'BUY' else OrderSide.SELL

                # 转换订单类型
                futu_type = str(row['orderType'])
                order_type = self._convert_futu_order_type(futu_type)

                order = Order(
                    order_id=str(row['orderID']),
                    symbol=symbol,
                    side=order_side,
                    order_type=order_type,
                    quantity=Decimal(str(row['qty'])),
                    price=Decimal(str(row.get('price', 0))),
                    status=order_status,
                    filled_quantity=Decimal(str(row.get('fillQty', 0))),
                    average_fill_price=Decimal(str(row.get('avgPrice', 0))),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                orders.append(order)

            return orders

        except Exception as e:
            self.logger.error(f"获取订单失败: {e}")
            return []

    async def place_order(self, order: Order) -> Optional[str]:
        """下单"""
        try:
            if not self.trade_ctx or not self._authenticated:
                return None

            # 验证订单
            errors = await self.validate_order(order)
            if errors:
                self.logger.error(f"订单验证失败: {errors}")
                return None

            # 转换富途代码格式
            futu_code = self._convert_to_futu_code(order.symbol)

            # 转换买卖方向
            futu_side = ft.TrdSide.BUY if order.side == OrderSide.BUY else ft.TrdSide.SELL

            # 转换订单类型
            futu_order_type = ft.OrderType.NORMAL  # 默认为普通订单
            if order.order_type == OrderType.MARKET:
                futu_order_type = ft.OrderType.MARKET
            elif order.order_type == OrderType.LIMIT:
                futu_order_type = ft.OrderType.NORMAL

            # 下单
            ret, data = self.trade_ctx.place_order(
                price=float(order.price) if order.price else 0,
                qty=float(order.quantity),
                code=futu_code,
                trd_side=futu_side,
                order_type=futu_order_type,
                trd_env=self.trd_env
            )

            if ret == ft.RET_OK:
                # 获取富途订单ID
                futu_order_id = str(data.iloc[0]['orderID'])
                self.order_mapping[order.order_id] = futu_order_id
                self.logger.info(f"下单成功: {order.order_id} -> {futu_order_id}")
                return order.order_id
            else:
                self.logger.error(f"下单失败: {data}")
                return None

        except Exception as e:
            self.logger.error(f"下单异常: {e}")
            return None

    async def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        try:
            if not self.trade_ctx or not self._authenticated:
                return False

            # 获取富途订单ID
            futu_order_id = self.order_mapping.get(order_id, order_id)

            # 取消订单
            ret, data = self.trade_ctx.cancel_order(
                order_id=futu_order_id,
                trd_env=self.trd_env
            )

            if ret == ft.RET_OK:
                self.logger.info(f"取消订单成功: {order_id}")
                return True
            else:
                self.logger.error(f"取消订单失败: {data}")
                return False

        except Exception as e:
            self.logger.error(f"取消订单异常: {e}")
            return False

    async def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> bool:
        """修改订单"""
        try:
            # 富途API通常不支持修改订单，需要先取消再重新下单
            self.logger.warning("富途API不支持修改订单，建议取消后重新下单")
            return False

        except Exception as e:
            self.logger.error(f"修改订单异常: {e}")
            return False

    async def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """获取订单状态"""
        try:
            if not self.trade_ctx:
                return None

            # 获取富途订单ID
            futu_order_id = self.order_mapping.get(order_id, order_id)

            # 查询订单详情
            ret, data = self.trade_ctx.order_list_query(
                order_id=futu_order_id,
                trd_env=self.trd_env
            )

            if ret == ft.RET_OK and not data.empty:
                futu_status = str(data.iloc[0]['orderStatus'])
                return self._convert_futu_status(futu_status)

            return None

        except Exception as e:
            self.logger.error(f"获取订单状态异常: {e}")
            return None

    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """获取市场数据"""
        try:
            if not self.quote_ctx:
                return None

            # 转换富途代码格式
            futu_code = self._convert_to_futu_code(symbol)

            # 获取市场快照
            ret, data = self.quote_ctx.get_market_snapshot([futu_code])
            if ret != ft.RET_OK or data.empty:
                return None

            row = data.iloc[0]

            return MarketData(
                symbol=symbol,
                bid_price=Decimal(str(row.get('bidPrice', 0))),
                ask_price=Decimal(str(row.get('askPrice', 0))),
                last_price=Decimal(str(row.get('lastPrice', 0))),
                volume=int(row.get('volume', 0)),
                high_price=Decimal(str(row.get('highPrice', 0))),
                low_price=Decimal(str(row.get('lowPrice', 0))),
                open_price=Decimal(str(row.get('openPrice', 0))),
                timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"获取市场数据失败: {e}")
            return None

    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> List[Dict[str, Any]]:
        """获取历史数据"""
        try:
            if not self.quote_ctx:
                return []

            # 转换富途代码格式
            futu_code = self._convert_to_futu_code(symbol)

            # 转换K线类型
            kl_type = ft.KLType.K_DAY
            if interval == "1m":
                kl_type = ft.KLType.K_1M
            elif interval == "5m":
                kl_type = ft.KLType.K_5M
            elif interval == "1h":
                kl_type = ft.KLType.K_1H

            # 获取K线数据
            ret, data = self.quote_ctx.get_history_kline(
                code=futu_code,
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                kl_type=kl_type,
                autype='qfq'  # 前复权
            )

            if ret != ft.RET_OK:
                self.logger.error(f"获取历史数据失败: {data}")
                return []

            # 转换为标准格式
            result = []
            for _, row in data.iterrows():
                result.append({
                    'timestamp': row['time'],
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume'])
                })

            return result

        except Exception as e:
            self.logger.error(f"获取历史数据异常: {e}")
            return []

    def _convert_to_futu_code(self, symbol: str) -> str:
        """转换为本系统代码为富途格式"""
        # 00700.HK -> HK.00700
        if symbol.endswith('.HK'):
            code = symbol.replace('.HK', '')
            return f'HK.{code}'
        elif symbol.endswith('.US'):
            code = symbol.replace('.US', '')
            return f'US.{code}'
        else:
            # 默认为港股
            return f'HK.{symbol}'

    def _convert_futu_status(self, futu_status: str) -> OrderStatus:
        """转换富途订单状态"""
        status_map = {
            'OPENING': OrderStatus.SUBMITTED,
            'FILLED_ALL': OrderStatus.FILLED,
            'FILLED_PART': OrderStatus.PARTIALLY_FILLED,
            'CANCELLED': OrderStatus.CANCELLED,
            'DELETED': OrderStatus.CANCELLED,
        }
        return status_map.get(futu_status, OrderStatus.PENDING)

    def _convert_futu_order_type(self, futu_type: str) -> OrderType:
        """转换富途订单类型"""
        type_map = {
            'NORMAL': OrderType.LIMIT,
            'MARKET': OrderType.MARKET,
        }
        return type_map.get(futu_type, OrderType.LIMIT)

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self._connected or not self._authenticated:
                return {
                    'status': 'unhealthy',
                    'connected': self._connected,
                    'authenticated': self._authenticated,
                    'error': 'Not connected or authenticated'
                }

            # 尝试获取账户信息
            account = await self.get_account_info()
            if not account:
                return {
                    'status': 'unhealthy',
                    'error': 'Failed to get account info'
                }

            return {
                'status': 'healthy',
                'connected': self._connected,
                'authenticated': self._authenticated,
                'account_id': account.account_id,
                'trading_env': 'DEMO/SIMULATE',
                'market': self.market
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }


# 便捷函数：创建富途交易API实例
def create_futu_trading_api(
    host: str = '127.0.0.1',
    port: int = 11111,
    trade_password: str = '',
    market: str = 'HK'
) -> FutuTradingAPI:
    """创建富途交易API实例"""
    config = {
        'host': host,
        'port': port,
        'trade_password': trade_password,
        'market': market
    }
    return FutuTradingAPI(config)
