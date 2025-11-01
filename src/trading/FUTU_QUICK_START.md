# 富途牛牛API - 快速开始指南

## 🚀 5分钟快速集成

### 步骤1: 安装依赖
```bash
pip install futu-api
```

### 步骤2: 启动FutuOpenD
1. 下载并安装 [FutuOpenD客户端](https://www.futunn.com/download/openAPI)
2. 启动客户端
3. 登录**DEMO账户**（模拟账户）

### 步骤3: 运行测试
```bash
cd src/trading

# 基础连接测试
python test_futu_trading.py

# 完整交易系统测试
python futu_live_trading_system.py
```

---

## 📝 最小示例

### 1. 连接并下单
```python
import asyncio
from futu_trading_api import create_futu_trading_api
from base_trading_api import Order, OrderType, OrderSide
from decimal import Decimal

async def main():
    # 1. 创建API
    api = create_futu_trading_api(
        host='127.0.0.1',
        port=11111,
        trade_password='123456'
    )

    # 2. 连接和认证
    await api.connect()
    await api.authenticate({'trade_password': '123456'})
    print("✅ 连接成功")

    # 3. 查看账户
    account = await api.get_account_info()
    print(f"💰 现金: ${account.cash:,.2f}")

    # 4. 下单 (DEMO环境)
    order = Order(
        order_id="DEMO_001",
        symbol="00700.HK",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal('100'),
        price=Decimal('400.0')
    )

    order_id = await api.place_order(order)
    print(f"📤 订单ID: {order_id}")

    # 5. 清理
    await api.disconnect()

asyncio.run(main())
```

### 2. 集成到交易系统
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
        }
    }

    # 创建交易系统
    system = FutuLiveTradingSystem(config)
    await system.initialize()

    # 添加交易信号
    await system.add_signal_config(
        SignalConfig('00700.HK', 'rsi', {
            'period': 14,
            'oversold': 30,
            'overbought': 70
        })
    )

    # 手动交易
    order_id = await system.manual_trade(
        '00700.HK', 'buy', 100, 400.0
    )

    print(f"✅ 交易完成: {order_id}")

    # 清理
    await system.cleanup()

asyncio.run(main())
```

---

## 🔍 常见问题

### Q: 连接失败？
A: 检查以下几点：
- FutuOpenD是否启动？
- 端口11111是否开放？
- 是否已登录DEMO账户？

### Q: 认证失败？
A: 确认DEMO密码是否为 `123456`

### Q: 下单失败？
A: 检查：
- DEMO账户余额是否充足？
- 价格是否合理？
- 股票代码是否正确？

---

## 📁 重要文件

| 文件 | 说明 |
|------|------|
| `futu_trading_api.py` | 富途API适配器 |
| `test_futu_trading.py` | 基础测试脚本 |
| `futu_live_trading_system.py` | 完整交易系统 |
| `FUTU_API_INTEGRATION_GUIDE.md` | 详细文档 |

---

## ⚠️ 重要提醒

1. **仅使用DEMO环境测试**
2. **使用模拟资金，无真实风险**
3. **充分测试后再考虑实盘**

---

## 🎯 下一步

- 阅读 [完整集成指南](FUTU_API_INTEGRATION_GUIDE.md)
- 运行测试脚本验证功能
- 集成到您的交易策略中

**立即开始使用富途API进行真实交易！** 🚀
