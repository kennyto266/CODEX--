# 富途牛牛API集成指南

## 概述

本指南详细说明如何将富途牛牛API集成到量化交易系统中，使用DEMO环境进行安全测试。

⚠️ **重要提醒**：
- 所有测试均使用DEMO环境 (SIMULATE)
- 使用模拟资金，不会造成真实损失
- 仅供学习和测试使用

---

## 📋 前置条件

### 1. 安装富途API

```bash
pip install futu-api
```

### 2. 下载FutuOpenD网关客户端

- 访问：https://www.futunn.com/download/openAPI
- 下载并安装Windows/Mac/Linux版本
- 启动FutuOpenD客户端

### 3. 配置DEMO账户

1. 打开FutuOpenD客户端
2. 登录DEMO账户（模拟账户）
3. 确认连接到端口11111

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│              富途API集成交易系统                           │
├─────────────────────────────────────────────────────────┤
│  Signal Manager       │  RealtimeExecutionEngine        │
│  - Technical Signals  │  - Risk Manager                 │
│  - Signal Config      │  - Order Monitor                │
│  - Signal History     │  - Performance Stats            │
│                       │                                 │
│  ┌─────────────────┐  │  ┌──────────────────────────┐  │
│  │ 策略配置         │  │  │ 风险控制                  │  │
│  │ - RSI           │  │  │ - 最大持仓                │  │
│  │ - MACD          │  │  │ - 最大订单                │  │
│  │ - MA Crossover  │  │  │ - 日内损失                │  │
│  │ - Bollinger     │  │  │ - 现金储备                │  │
│  └─────────────────┘  │  └──────────────────────────┘  │
│                       │                                 │
│                       │  富途交易API                    │
│                       │  - FutuTradingAPI              │
│                       │  - DEMO环境                    │
│                       │  - 真实订单执行                │
│                       │                                 │
└───────────────────────┴─────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  富途网关客户端     │
                    │  FutuOpenD        │
                    │  - DEMO账户        │
                    │  - 端口11111       │
                    │  - 行情数据        │
                    │  - 交易接口        │
                    └───────────────────┘
```

---

## 🔧 核心组件

### 1. 富途交易API (`futu_trading_api.py`)

#### 功能特性
- ✅ 完整的订单生命周期管理
- ✅ 真实市场数据获取
- ✅ 账户和持仓查询
- ✅ 订单状态实时监控
- ✅ 历史数据获取
- ✅ DEMO环境支持

#### 主要方法
```python
# 连接和认证
await api.connect()                    # 连接API
await api.authenticate({'trade_password': '123456'})  # 解锁交易

# 账户和持仓
await api.get_account_info()           # 账户信息
await api.get_positions()              # 持仓列表

# 市场数据
await api.get_market_data(symbol)      # 实时行情
await api.get_historical_data(...)     # 历史数据

# 订单管理
await api.place_order(order)           # 下单
await api.cancel_order(order_id)       # 取消订单
await api.get_order_status(order_id)   # 订单状态

# 批量查询
await api.get_orders()                 # 订单列表
```

#### 配置参数
```python
config = {
    'host': '127.0.0.1',        # 网关地址
    'port': 11111,              # 端口
    'market': 'HK',             # 市场: HK/US/CN
    'trade_password': '123456'  # DEMO交易密码
}
```

### 2. 真实交易系统 (`futu_live_trading_system.py`)

#### 主要功能
- 自动交易执行
- 风险管理
- 实时监控
- 手动交易接口

#### 使用示例
```python
# 初始化
trading_system = FutuLiveTradingSystem(config)
await trading_system.initialize()

# 添加信号配置
await trading_system.add_signal_config(
    SignalConfig('00700.HK', 'rsi', {
        'period': 14,
        'oversold': 30,
        'overbought': 70
    })
)

# 启动交易
await trading_system.start_trading(enable_auto_trading=True)

# 手动交易
order_id = await trading_system.manual_trade(
    symbol='00700.HK',
    side='buy',
    quantity=100,
    price=400.0
)

# 获取状态
status = await trading_system.get_status()
```

---

## 🚀 快速开始

### 1. 基础连接测试

```python
import asyncio
from futu_trading_api import create_futu_trading_api

async def test_connection():
    # 创建API实例
    api = create_futu_trading_api(
        host='127.0.0.1',
        port=11111,
        market='HK'
    )

    # 连接
    await api.connect()
    print("连接成功")

    # 认证 (DEMO环境)
    await api.authenticate({'trade_password': '123456'})
    print("认证成功")

    # 获取账户信息
    account = await api.get_account_info()
    print(f"账户现金: ${account.cash}")

    # 断开
    await api.disconnect()

asyncio.run(test_connection())
```

### 2. 下单测试

```python
async def test_order():
    api = create_futu_trading_api()
    await api.connect()
    await api.authenticate({'trade_password': '123456'})

    # 创建订单
    from base_trading_api import Order, OrderType, OrderSide
    from decimal import Decimal

    order = Order(
        order_id="TEST_001",
        symbol="00700.HK",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal('100'),
        price=Decimal('400.0')
    )

    # 下单
    order_id = await api.place_order(order)
    print(f"订单ID: {order_id}")

    # 等待并查看状态
    await asyncio.sleep(3)
    status = await api.get_order_status(order_id)
    print(f"订单状态: {status}")

asyncio.run(test_order())
```

### 3. 完整交易系统

```python
import asyncio
from futu_live_trading_system import FutuLiveTradingSystem
from signal_generator import SignalConfig

async def main():
    config = {
        'futu': {
            'host': '127.0.0.1',
            'port': 11111,
            'trade_password': '123456'
        },
        'risk': {
            'max_position_size': 500000,
            'max_order_size': 100000
        },
        'scan_interval': 60
    }

    # 创建系统
    system = FutuLiveTradingSystem(config)

    # 初始化
    if await system.initialize():
        print("系统初始化成功")

        # 添加信号
        await system.add_signal_config(
            SignalConfig('00700.HK', 'rsi', {'period': 14})
        )

        # 获取状态
        status = await system.get_status()
        print(json.dumps(status, indent=2, default=str))

        # 手动交易测试
        order_id = await system.manual_trade(
            '00700.HK', 'buy', 100, 400.0
        )

        # 清理
        await system.cleanup()

asyncio.run(main())
```

---

## 📊 支持的订单类型

### 1. 市价单 (MARKET)
```python
order = Order(
    order_id="MKT_001",
    symbol="00700.HK",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=Decimal('100')
)
```

### 2. 限价单 (LIMIT)
```python
order = Order(
    order_id="LMT_001",
    symbol="00700.HK",
    side=OrderSide.BUY,
    order_type=OrderType.LIMIT,
    quantity=Decimal('100'),
    price=Decimal('400.0')
)
```

---

## 🎯 支持的股票代码

### 港股
- `00700.HK` - 腾讯控股
- `0388.HK` - 香港交易所
- `1398.HK` - 中国工商银行
- `0939.HK` - 中国建设银行
- `3988.HK` - 中国银行

### 代码格式转换
```python
# 系统格式 -> 富途格式
"00700.HK" -> "HK.00700"
"00700.US" -> "US.00700"

# 富途格式 -> 系统格式
"HK.00700" -> "00700.HK"
"US.00700" -> "00700.US"
```

---

## ⚙️ 配置说明

### 完整配置示例
```python
config = {
    # 富途API配置
    'futu': {
        'host': '127.0.0.1',              # 网关地址
        'port': 11111,                    # 端口
        'market': 'HK',                   # 市场
        'trade_password': '123456'        # 交易密码
    },

    # 认证配置
    'auth': {
        'trade_password': '123456'        # DEMO密码
    },

    # 风险控制
    'risk': {
        'max_position_size': 500000,      # 最大持仓
        'max_daily_loss': 50000,          # 最大日内损失
        'max_order_size': 100000,         # 最大订单
        'min_cash_reserve': 10000         # 最小现金储备
    },

    # 系统设置
    'scan_interval': 60,                  # 扫描间隔(秒)
    'auto_trading': False                 # 是否启用自动交易
}
```

---

## 🧪 测试脚本

### 1. 基础连接测试
```bash
cd src/trading
python test_futu_trading.py
```

### 2. 完整交易系统测试
```bash
cd src/trading
python futu_live_trading_system.py
```

---

## ⚠️ 注意事项

### DEMO环境限制
1. **仅模拟交易**：使用虚拟资金，不会造成真实损失
2. **市场时间**：即使市场关闭也可以下单（模拟）
3. **数据延迟**：DEMO环境数据可能有延迟
4. **订单限制**：部分高级订单类型可能不支持

### 安全建议
1. **测试优先**：先在DEMO环境充分测试
2. **小额开始**：实盘交易时从小额开始
3. **风险控制**：始终设置风险参数
4. **定期监控**：定期检查订单状态和账户

### 故障排除

#### 1. 连接失败
```
错误：连接被拒绝
解决：
- 检查FutuOpenD是否启动
- 确认端口11111是否正确
- 检查防火墙设置
```

#### 2. 认证失败
```
错误：解锁失败
解决：
- 确认DEMO账户密码
- 检查是否已登录DEMO账户
- 重启FutuOpenD客户端
```

#### 3. 下单失败
```
错误：下单失败
可能原因：
- DEMO账户余额不足
- 价格超出有效范围
- 市场未开盘
- 股票代码错误
```

---

## 📈 性能优化

### 1. 连接池
```python
# 使用单例模式管理连接
class FutuAPIManager:
    _instance = None
    _api = None

    @classmethod
    async def get_api(cls):
        if not cls._api:
            cls._api = create_futu_trading_api()
            await cls._api.connect()
        return cls._api
```

### 2. 缓存市场数据
```python
# 缓存市场快照，减少API调用
class MarketDataCache:
    def __init__(self):
        self.cache = {}
        self.last_update = {}

    async def get_market_data(self, symbol):
        if self._is_cache_valid(symbol):
            return self.cache[symbol]
        data = await self.api.get_market_data(symbol)
        self._update_cache(symbol, data)
        return data
```

### 3. 异步并发
```python
# 并发获取多个股票数据
symbols = ['00700.HK', '0388.HK', '1398.HK']
tasks = [api.get_market_data(s) for s in symbols]
results = await asyncio.gather(*tasks)
```

---

## 📚 参考资源

- [富途OpenAPI官方文档](https://openapi.futunn.com/futu-api-doc/)
- [FutuOpenD下载](https://www.futunn.com/download/openAPI)
- [富途API GitHub](https://github.com/Futunnopen/py-futu-api)

---

## 🎉 总结

富途牛牛API集成为量化交易系统提供了：

1. **真实交易能力**：使用真实市场数据进行交易
2. **DEMO环境**：安全测试，无真实风险
3. **完整接口**：覆盖行情、交易、账户等所有功能
4. **易于集成**：统一接口，无缝接入现有系统

**立即开始使用富途API进行真实交易！** 🚀
