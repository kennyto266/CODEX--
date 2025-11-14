# Week 1 实施计划
## API接口规范创建与数据层整合准备

---

## 📋 任务分解

### Day 1-2: API接口规范创建

#### 任务1.1: 创建策略API请求/响应模型
**文件**: `src/dashboard/models/strategy_api_models.py`
```python
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

class StrategyRunRequest(BaseModel):
    strategy_type: str
    symbol: str
    start_date: str
    end_date: str
    params: Optional[Dict] = {}

class StrategyRunResponse(BaseModel):
    status: str
    strategy_id: str
    results: Dict[str, Any]
    metrics: Dict[str, float]
    execution_time: float

class ParameterOptimizationRequest(BaseModel):
    strategy_type: str
    symbol: str
    start_date: str
    end_date: str
    param_grid: Dict[str, List]
    max_workers: int = 4
```

#### 任务1.2: 创建策略API路由模块
**文件**: `src/dashboard/api_strategies.py`
```python
from fastapi import APIRouter, HTTPException
from .models.strategy_api_models import *
from strategies.template.utils import optimize_strategy_parameters

router = APIRouter(prefix="/api/strategies", tags=["strategies"])

@router.post("/run", response_model=StrategyRunResponse)
async def run_strategy(request: StrategyRunRequest):
    """运行交易策略"""
    pass

@router.post("/optimize", response_model=Dict[str, Any])
async def optimize_parameters(request: ParameterOptimizationRequest):
    """运行参数优化"""
    pass
```

### Day 3-4: 数据层整合准备

#### 任务2.1: 修改DataLoader集成现有适配器
**文件**: `strategies/data_adapters/data_loader.py`
```python
from src.data_adapters.enhanced_market_data_adapter import EnhancedMarketDataAdapter

class DataLoader:
    def __init__(self):
        self.market_adapter = EnhancedMarketDataAdapter()
        
    def load_price_data(self, symbol, start_date, end_date):
        # 使用现有的EnhancedMarketDataAdapter
        return self.market_adapter.get_hk_stock_data(symbol, days)
```

#### 任务2.2: 创建数据层整合测试
**文件**: `tests/integration/test_data_layer_integration.py`
```python
def test_dataloader_integration():
    """测试DataLoader与现有适配器整合"""
    loader = DataLoader()
    data = loader.load_price_data("0700.HK", "2024-01-01", "2024-12-31")
    assert data is not None
```

### Day 5-7: 核心集成代码开发

#### 任务3.1: 创建策略工厂类
**文件**: `src/dashboard/strategy_factory.py`
```python
from strategies.usd_cnh_hsi.strategy_main import USDCNHToHSIStrategy

class StrategyFactory:
    @staticmethod
    def create(strategy_type: str, params: Dict = None):
        if strategy_type == "usd_cnh_hsi":
            return USDCNHToHSIStrategy(params or {})
        raise ValueError(f"Unknown strategy type: {strategy_type}")
```

#### 任务3.2: 创建单元测试
**文件**: `tests/unit/test_strategy_api.py`
```python
def test_strategy_run_api():
    """测试策略运行API"""
    # 测试用例
    pass

def test_parameter_optimization_api():
    """测试参数优化API"""
    # 测试用例
    pass
```

---

## 🎯 实施检查清单

### API接口规范
- [ ] 创建StrategyRunRequest/Response模型
- [ ] 创建ParameterOptimizationRequest模型
- [ ] 创建StrategyComparisonRequest模型
- [ ] 实现/api/strategies/run端点
- [ ] 实现/api/strategies/optimize端点
- [ ] 实现/api/strategies/compare端点

### 数据层整合
- [ ] 修改DataLoader使用EnhancedMarketDataAdapter
- [ ] 整合5个真实数据源（HIBOR, GDP, CPI, 交通, 天气）
- [ ] 验证数据格式兼容性
- [ ] 创建数据层整合测试

### 测试验证
- [ ] 创建策略API单元测试
- [ ] 创建数据层整合测试
- [ ] 创建端到端集成测试
- [ ] 验证API响应格式

### 文档更新
- [ ] 更新API文档
- [ ] 更新整合设计文档
- [ ] 创建API使用示例

---

## 📊 成功标准

### 技术指标
- ✅ API端点实现并通过测试
- ✅ 数据层成功整合现有适配器
- ✅ 单元测试覆盖率 > 80%
- ✅ API响应时间 < 500ms

### 质量指标
- ✅ 代码审查通过
- ✅ 文档完整且及时更新
- ✅ 无重大bug或错误

---

## 📅 时间安排

| 天数 | 任务 | 交付物 |
|------|------|--------|
| Day 1 | API模型创建 | strategy_api_models.py |
| Day 2 | API路由实现 | api_strategies.py |
| Day 3 | DataLoader整合 | data_loader.py |
| Day 4 | 数据层测试 | test_data_layer_integration.py |
| Day 5 | 策略工厂 | strategy_factory.py |
| Day 6 | 单元测试 | test_strategy_api.py |
| Day 7 | 文档更新 | API文档 + 示例 |

---

**状态**: 准备开始实施
**负责人**: [待分配]
**下一步**: Day 1 - 创建API请求/响应模型
