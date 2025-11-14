"""
定制化系統 API
統一的定制化功能入口點
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 導入自定義組件
from .indicator_sandbox import IndicatorSandbox, SandboxConfig
from .strategy_template import StrategyTemplateEngine, StrategyType
from ..workspace.manager import WorkspaceManager
from ..workspace.portfolio import PortfolioManager
from ..workspace.trade_history import TradeHistoryManager
from ..workspace.analytics import PersonalAnalytics
from ..security.sandbox import SecureSandbox, SecurityScanner

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/custom", tags=["customization"])

# 全局實例
_sandbox = None
_template_engine = None
_workspace_manager = None
_portfolio_manager = None
_trade_manager = None
_analytics = None
_secure_sandbox = None
_security_scanner = None


def get_dependencies():
    """獲取依賴"""
    global _sandbox, _template_engine, _workspace_manager
    global _portfolio_manager, _trade_manager, _analytics
    global _secure_sandbox, _security_scanner

    if _sandbox is None:
        config = SandboxConfig()
        _sandbox = IndicatorSandbox(config)
        _template_engine = StrategyTemplateEngine()
        _workspace_manager = WorkspaceManager()
        _portfolio_manager = PortfolioManager()
        _trade_manager = TradeHistoryManager()
        _analytics = PersonalAnalytics(_portfolio_manager, _trade_manager)
        _secure_sandbox = SecureSandbox()
        _security_scanner = SecurityScanner()

    return {
        'sandbox': _sandbox,
        'template_engine': _template_engine,
        'workspace_manager': _workspace_manager,
        'portfolio_manager': _portfolio_manager,
        'trade_manager': _trade_manager,
        'analytics': _analytics,
        'secure_sandbox': _secure_sandbox,
        'security_scanner': _security_scanner
    }


# Pydantic 模型
class IndicatorCreateRequest(BaseModel):
    name: str
    code: str
    parameters: Optional[List[Dict[str, Any]]] = []
    description: Optional[str] = ""


class IndicatorRunRequest(BaseModel):
    code: str
    name: str
    parameters: Optional[Dict[str, Any]] = {}
    data: Optional[Dict[str, Any]] = {}


class StrategyCreateRequest(BaseModel):
    name: str
    description: str
    type: str
    blocks: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]


class WorkspaceCreateRequest(BaseModel):
    user_id: str
    name: str
    theme: Optional[str] = "dark"
    language: Optional[str] = "zh-TW"


class PortfolioCreateRequest(BaseModel):
    user_id: str
    name: str
    initial_cash: float = 100000.0


class TradeAddRequest(BaseModel):
    user_id: str
    portfolio_name: str
    symbol: str
    side: str  # buy, sell
    quantity: float
    price: float
    fees: Optional[float] = 0.0
    notes: Optional[str] = ""
    strategy: Optional[str] = ""


# ==================== 指標管理 API ====================

@router.post("/indicators")
async def create_indicator(
    request: IndicatorCreateRequest,
    deps: Dict = Depends(get_dependencies)
):
    """創建自定義指標"""
    try:
        sandbox = deps['sandbox']

        # 驗證代碼
        errors = sandbox.validate_indicator(request.code)
        if errors:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'errors': [{'type': e.type, 'message': e.message} for e in errors]
                }
            )

        # TODO: 保存到數據庫
        # 這裡只是示例，實際需要保存到持久化存儲

        return {
            'success': True,
            'message': '指標已創建',
            'data': {
                'name': request.name,
                'code': request.code,
                'parameters': request.parameters
            }
        }

    except Exception as e:
        logger.error(f"創建指標失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indicators/run")
async def run_indicator(
    request: IndicatorRunRequest,
    deps: Dict = Depends(get_dependencies)
):
    """執行自定義指標"""
    try:
        sandbox = deps['sandbox']

        # 模擬股票數據（實際應從數據源獲取）
        import pandas as pd
        import numpy as np

        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        sample_data = pd.DataFrame({
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 105,
            'low': np.random.randn(100).cumsum() + 95,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000000, 10000000, 100)
        }, index=dates)

        # 執行指標
        result = sandbox.execute_indicator(
            code=request.code,
            data=sample_data,
            parameters=request.parameters
        )

        return {
            'success': True,
            'data': {
                'dates': result.index.strftime('%Y-%m-%d').tolist(),
                'datasets': [{
                    'label': request.name,
                    'data': result.iloc[:, 0].tolist() if isinstance(result, pd.DataFrame) else result.tolist(),
                    'borderColor': 'rgb(75, 192, 192)',
                    'tension': 0.1
                }]
            }
        }

    except Exception as e:
        logger.error(f"執行指標失敗: {e}")
        return JSONResponse(
            status_code=400,
            content={
                'success': False,
                'error': str(e)
            }
        )


@router.get("/indicators")
async def list_indicators(deps: Dict = Depends(get_dependencies)):
    """列出所有指標"""
    # TODO: 從數據庫讀取
    return {
        'success': True,
        'data': []
    }


@router.get("/indicators/examples")
async def get_indicator_examples(deps: Dict = Depends(get_dependencies)):
    """獲取指標範例"""
    examples = [
        {
            'id': 'sma_crossover',
            'name': '雙均線交叉',
            'description': '短期和長期移動平均線的交叉信號',
            'code': 'def sma_crossover(data, **params):\n    short_ma = sma(data, period=10)\n    long_ma = sma(data, period=20)\n    return (short_ma > long_ma).astype(int)'
        },
        {
            'id': 'rsi_divergence',
            'name': 'RSI背離',
            'description': '價格和RSI的背離信號',
            'code': 'def rsi_divergence(data, **params):\n    rsi_value = rsi(data, period=14)\n    return rsi_value'
        }
    ]

    return {
        'success': True,
        'data': examples
    }


# ==================== 策略模板 API ====================

@router.get("/strategies/templates")
async def list_strategy_templates(
    deps: Dict = Depends(get_dependencies)
):
    """列出策略模板"""
    template_engine = deps['template_engine']
    templates = template_engine.list_templates()

    return {
        'success': True,
        'data': [
            {
                'id': t.id,
                'name': t.name,
                'description': t.description,
                'type': t.type.value,
                'block_count': len(t.blocks)
            }
            for t in templates
        ]
    }


@router.post("/strategies")
async def create_strategy(
    request: StrategyCreateRequest,
    deps: Dict = Depends(get_dependencies)
):
    """創建策略"""
    try:
        template_engine = deps['template_engine']

        from .strategy_template import StrategyBlock, StrategyType as ST

        # 轉換請求數據
        blocks = [StrategyBlock(**b) for b in request.blocks]

        # 創建模板
        template = template_engine.create_template(
            name=request.name,
            description=request.description,
            strategy_type=ST(request.type),
            blocks=blocks,
            connections=request.connections
        )

        return {
            'success': True,
            'message': '策略已創建',
            'data': {
                'id': template.id,
                'name': template.name
            }
        }

    except Exception as e:
        logger.error(f"創建策略失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/strategies/{strategy_id}/backtest")
async def backtest_strategy(
    strategy_id: str,
    request: Dict[str, Any],
    deps: Dict = Depends(get_dependencies)
):
    """回測策略"""
    try:
        # 這裡應該調用實際的回測引擎
        # 現在返回模擬數據

        import random

        backtest_id = f"bt_{strategy_id}_{random.randint(1000, 9999)}"

        return {
            'success': True,
            'message': '回測已啟動',
            'data': {
                'backtest_id': backtest_id,
                'status': 'running',
                'estimated_time': 60  # 秒
            }
        }

    except Exception as e:
        logger.error(f"回測策略失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 工作區管理 API ====================

@router.post("/workspace")
async def create_workspace(
    request: WorkspaceCreateRequest,
    deps: Dict = Depends(get_dependencies)
):
    """創建工作區"""
    try:
        workspace_manager = deps['workspace_manager']

        workspace = workspace_manager.create_workspace(
            user_id=request.user_id,
            name=request.name,
            theme=request.theme,
            language=request.language
        )

        return {
            'success': True,
            'message': '工作區已創建',
            'data': {
                'user_id': workspace.settings.user_id,
                'name': workspace.settings.name
            }
        }

    except Exception as e:
        logger.error(f"創建工作區失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspace/{user_id}")
async def get_workspace(
    user_id: str,
    deps: Dict = Depends(get_dependencies)
):
    """獲取工作區"""
    workspace_manager = deps['workspace_manager']
    workspace = workspace_manager.get_workspace(user_id)

    if not workspace:
        raise HTTPException(status_code=404, detail="工作區不存在")

    return {
        'success': True,
        'data': {
            'user_id': workspace.settings.user_id,
            'name': workspace.settings.name,
            'theme': workspace.settings.theme,
            'preferences': workspace.preferences.__dict__
        }
    }


@router.put("/workspace/{user_id}")
async def update_workspace(
    user_id: str,
    request: Dict[str, Any],
    deps: Dict = Depends(get_dependencies)
):
    """更新工作區"""
    try:
        workspace_manager = deps['workspace_manager']

        updated = workspace_manager.update_workspace(user_id, **request)

        if not updated:
            raise HTTPException(status_code=404, detail="工作區不存在")

        return {
            'success': True,
            'message': '工作區已更新'
        }

    except Exception as e:
        logger.error(f"更新工作區失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 投資組合 API ====================

@router.post("/portfolios")
async def create_portfolio(
    request: PortfolioCreateRequest,
    deps: Dict = Depends(get_dependencies)
):
    """創建投資組合"""
    try:
        portfolio_manager = deps['portfolio_manager']

        portfolio = portfolio_manager.create_portfolio(
            user_id=request.user_id,
            name=request.name,
            initial_cash=request.initial_cash
        )

        return {
            'success': True,
            'message': '投資組合已創建',
            'data': {
                'name': portfolio.name,
                'total_value': portfolio.total_value
            }
        }

    except Exception as e:
        logger.error(f"創建投資組合失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolios/{user_id}/{portfolio_name}")
async def get_portfolio(
    user_id: str,
    portfolio_name: str,
    deps: Dict = Depends(get_dependencies)
):
    """獲取投資組合"""
    portfolio_manager = deps['portfolio_manager']
    portfolio = portfolio_manager.get_portfolio(user_id, portfolio_name)

    if not portfolio:
        raise HTTPException(status_code=404, detail="投資組合不存在")

    return {
        'success': True,
        'data': {
            'name': portfolio.name,
            'total_value': portfolio.total_value,
            'cash': portfolio.cash,
            'positions': {
                k: {
                    'symbol': v.symbol,
                    'quantity': v.quantity,
                    'current_price': v.current_price,
                    'unrealized_pnl': v.unrealized_pnl
                }
                for k, v in portfolio.positions.items()
            }
        }
    }


@router.post("/portfolios/{user_id}/{portfolio_name}/position")
async def add_position(
    user_id: str,
    portfolio_name: str,
    request: Dict[str, Any],
    deps: Dict = Depends(get_dependencies)
):
    """添加持倉"""
    try:
        portfolio_manager = deps['portfolio_manager']

        result = portfolio_manager.add_position(
            user_id=user_id,
            portfolio_name=portfolio_name,
            symbol=request['symbol'],
            quantity=request['quantity'],
            price=request['price']
        )

        if not result:
            raise HTTPException(status_code=400, detail="添加持倉失敗")

        return {
            'success': True,
            'message': '持倉已添加'
        }

    except Exception as e:
        logger.error(f"添加持倉失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 交易歷史 API ====================

@router.post("/trades")
async def add_trade(
    request: TradeAddRequest,
    deps: Dict = Depends(get_dependencies)
):
    """添加交易記錄"""
    try:
        trade_manager = deps['trade_manager']

        trade = trade_manager.add_trade(
            user_id=request.user_id,
            portfolio_name=request.portfolio_name,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            price=request.price,
            fees=request.fees,
            notes=request.notes,
            strategy=request.strategy
        )

        return {
            'success': True,
            'message': '交易記錄已添加',
            'data': {
                'id': trade.id,
                'symbol': trade.symbol,
                'side': trade.side
            }
        }

    except Exception as e:
        logger.error(f"添加交易記錄失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades/{user_id}")
async def get_trades(
    user_id: str,
    portfolio_name: Optional[str] = None,
    symbol: Optional[str] = None,
    deps: Dict = Depends(get_dependencies)
):
    """獲取交易記錄"""
    trade_manager = deps['trade_manager']
    trades = trade_manager.get_trades(user_id, portfolio_name, symbol)

    return {
        'success': True,
        'data': [
            {
                'id': t.id,
                'symbol': t.symbol,
                'side': t.side,
                'quantity': t.quantity,
                'price': t.price,
                'timestamp': t.timestamp,
                'pnl': t.pnl
            }
            for t in trades
        ]
    }


# ==================== 分析 API ====================

@router.get("/analytics/{user_id}/behavior")
async def analyze_trading_behavior(
    user_id: str,
    deps: Dict = Depends(get_dependencies)
):
    """分析交易行為"""
    analytics = deps['analytics']
    behavior = analytics.analyze_trading_behavior(user_id)

    return {
        'success': True,
        'data': behavior
    }


@router.get("/analytics/{user_id}/performance")
async def analyze_performance(
    user_id: str,
    portfolio_name: str,
    deps: Dict = Depends(get_dependencies)
):
    """分析投資組合表現"""
    analytics = deps['analytics']
    performance = analytics.analyze_performance(user_id, portfolio_name)

    return {
        'success': True,
        'data': performance
    }


@router.get("/analytics/{user_id}/risk")
async def get_risk_profile(
    user_id: str,
    deps: Dict = Depends(get_dependencies)
):
    """獲取風險概況"""
    analytics = deps['analytics']
    risk = analytics.get_risk_profile(user_id)

    return {
        'success': True,
        'data': risk
    }


@router.get("/analytics/{user_id}/recommendations")
async def get_recommendations(
    user_id: str,
    deps: Dict = Depends(get_dependencies)
):
    """獲取個人化建議"""
    analytics = deps['analytics']
    recommendations = analytics.get_recommendations(user_id)

    return {
        'success': True,
        'data': recommendations
    }


@router.get("/analytics/{user_id}/report")
async def generate_report(
    user_id: str,
    portfolio_name: str,
    deps: Dict = Depends(get_dependencies)
):
    """生成分析報告"""
    analytics = deps['analytics']
    report = analytics.generate_report(user_id, portfolio_name)

    return {
        'success': True,
        'data': {
            'report': report
        }
    }


# ==================== 安全沙箱 API ====================

@router.post("/sandbox/scan")
async def scan_code(
    request: Dict[str, Any],
    deps: Dict = Depends(get_dependencies)
):
    """掃描代碼安全性"""
    security_scanner = deps['security_scanner']
    result = security_scanner.scan(request['code'])

    return {
        'success': True,
        'data': result
    }


@router.post("/sandbox/execute")
async def execute_in_sandbox(
    request: Dict[str, Any],
    deps: Dict = Depends(get_dependencies)
):
    """在安全沙箱中執行代碼"""
    secure_sandbox = deps['secure_sandbox']

    try:
        result = secure_sandbox.execute(
            code=request['code'],
            timeout=request.get('timeout', 5.0),
            memory_limit_mb=request.get('memory_limit_mb', 256)
        )

        return {
            'success': result['success'],
            'data': {
                'output': result['output'],
                'execution_time': result['execution_time'],
                'error': result['error']
            }
        }

    except Exception as e:
        logger.error(f"沙箱執行失敗: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sandbox/stats")
async def get_sandbox_stats(
    deps: Dict = Depends(get_dependencies)
):
    """獲取沙箱統計"""
    secure_sandbox = deps['secure_sandbox']
    stats = secure_sandbox.get_execution_stats()

    return {
        'success': True,
        'data': stats
    }


# ==================== 健康檢查 ====================

@router.get("/health")
async def health_check():
    """健康檢查"""
    return {
        'status': 'ok',
        'service': 'customization_system',
        'version': '1.0.0'
    }
