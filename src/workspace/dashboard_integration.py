"""
工作区仪表板集成
提供API端点供前端调用
"""

import sys
import os
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
import json

# 导入工作区模块
from . import (
    WorkspaceManager,
    PortfolioManager,
    TradeHistoryManager,
    PersonalAnalytics,
    TradingJournal,
)


class WorkspaceAPI:
    """工作区API包装器"""

    def __init__(self):
        self.workspace_manager = WorkspaceManager()
        self.portfolio_manager = PortfolioManager()
        self.trade_manager = TradeHistoryManager()
        self.analytics = None  # 将在需要时初始化
        self.journal = TradingJournal()

    def get_analytics(self):
        """获取分析引擎实例"""
        if self.analytics is None:
            self.analytics = PersonalAnalytics(
                self.portfolio_manager,
                self.trade_manager
            )
        return self.analytics


# 创建API路由器
router = APIRouter(prefix="/api/workspace", tags=["workspace"])
workspace_api = WorkspaceAPI()


# ========== 工作区管理端点 ==========

@router.get("/workspace/{user_id}")
async def get_workspace(user_id: str):
    """获取工作区"""
    workspace = workspace_api.workspace_manager.get_workspace(user_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return JSONResponse(content=workspace.to_dict())


@router.post("/workspace")
async def create_workspace(
    user_id: str,
    name: str,
    theme: str = "dark",
    language: str = "zh-TW"
):
    """创建工作区"""
    workspace = workspace_api.workspace_manager.create_workspace(
        user_id=user_id,
        name=name,
        theme=theme,
        language=language
    )
    return JSONResponse(content=workspace.to_dict())


@router.put("/workspace/{user_id}")
async def update_workspace(user_id: str, **kwargs):
    """更新工作区"""
    workspace = workspace_api.workspace_manager.update_workspace(user_id, **kwargs)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return JSONResponse(content=workspace.to_dict())


# ========== 投资组合端点 ==========

@router.get("/portfolios/{user_id}")
async def get_portfolios(user_id: str):
    """获取用户的所有投资组合"""
    portfolio_names = workspace_api.portfolio_manager.list_portfolios(user_id)
    portfolios = []
    for name in portfolio_names:
        portfolio = workspace_api.portfolio_manager.get_portfolio(user_id, name)
        if portfolio:
            portfolios.append(portfolio.to_dict())
    return JSONResponse(content=portfolios)


@router.get("/portfolio/{user_id}/{portfolio_name}")
async def get_portfolio(user_id: str, portfolio_name: str):
    """获取特定投资组合"""
    portfolio = workspace_api.portfolio_manager.get_portfolio(user_id, portfolio_name)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # 获取摘要信息
    summary = workspace_api.portfolio_manager.get_portfolio_summary(user_id, portfolio_name)

    return JSONResponse(content={
        'portfolio': portfolio.to_dict(),
        'summary': summary
    })


@router.post("/portfolio")
async def create_portfolio(
    user_id: str,
    name: str,
    initial_cash: float = 100000.0
):
    """创建投资组合"""
    portfolio = workspace_api.portfolio_manager.create_portfolio(
        user_id=user_id,
        name=name,
        initial_cash=initial_cash
    )
    return JSONResponse(content=portfolio.to_dict())


@router.post("/portfolio/{user_id}/{portfolio_name}/position")
async def add_position(
    user_id: str,
    portfolio_name: str,
    symbol: str,
    quantity: float,
    price: float
):
    """添加持仓"""
    success = workspace_api.portfolio_manager.add_position(
        user_id=user_id,
        portfolio_name=portfolio_name,
        symbol=symbol,
        quantity=quantity,
        price=price
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add position")
    return JSONResponse(content={'status': 'success'})


@router.put("/portfolio/{user_id}/{portfolio_name}/prices")
async def update_prices(
    user_id: str,
    portfolio_name: str,
    price_data: Dict[str, float]
):
    """更新价格"""
    success = workspace_api.portfolio_manager.update_prices(
        user_id=user_id,
        portfolio_name=portfolio_name,
        price_data=price_data
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update prices")
    return JSONResponse(content={'status': 'success'})


# ========== 交易历史端点 ==========

@router.get("/trades/{user_id}")
async def get_trades(
    user_id: str,
    portfolio_name: Optional[str] = Query(None, description="组合名称"),
    symbol: Optional[str] = Query(None, description="股票代码"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期")
):
    """获取交易记录"""
    trades = workspace_api.trade_manager.get_trades(
        user_id=user_id,
        portfolio_name=portfolio_name,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date
    )
    return JSONResponse(content=[trade.__dict__ for trade in trades])


@router.post("/trade")
async def add_trade(
    user_id: str,
    portfolio_name: str,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    fees: float = 0.0,
    notes: str = "",
    strategy: str = ""
):
    """添加交易记录"""
    trade = workspace_api.trade_manager.add_trade(
        user_id=user_id,
        portfolio_name=portfolio_name,
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        fees=fees,
        notes=notes,
        strategy=strategy
    )
    return JSONResponse(content=trade.__dict__)


@router.get("/trades/{user_id}/statistics")
async def get_trade_statistics(
    user_id: str,
    portfolio_name: Optional[str] = Query(None, description="组合名称")
):
    """获取交易统计"""
    stats = workspace_api.trade_manager.get_statistics(user_id, portfolio_name)
    return JSONResponse(content=stats.__dict__)


@router.get("/trades/{user_id}/symbol-performance")
async def get_symbol_performance(user_id: str):
    """获取股票表现"""
    performance = workspace_api.trade_manager.get_symbol_performance(user_id)
    return JSONResponse(content=performance)


@router.get("/trades/{user_id}/daily-pnl")
async def get_daily_pnl(
    user_id: str,
    days: int = Query(30, description="天数")
):
    """获取每日损益"""
    df = workspace_api.trade_manager.get_daily_pnl_series(user_id, days)
    return JSONResponse(content=df.to_dict('records'))


# ========== 分析端点 ==========

@router.get("/analytics/{user_id}/behavior")
async def get_trading_behavior(user_id: str):
    """获取交易行为分析"""
    analytics = workspace_api.get_analytics()
    behavior = analytics.analyze_trading_behavior(user_id)
    return JSONResponse(content=behavior)


@router.get("/analytics/{user_id}/{portfolio_name}/performance")
async def get_performance(user_id: str, portfolio_name: str):
    """获取组合表现分析"""
    analytics = workspace_api.get_analytics()
    performance = analytics.analyze_performance(user_id, portfolio_name)
    return JSONResponse(content=performance)


@router.get("/analytics/{user_id}/risk")
async def get_risk_profile(user_id: str):
    """获取风险概况"""
    analytics = workspace_api.get_analytics()
    risk = analytics.get_risk_profile(user_id)
    return JSONResponse(content=risk)


@router.get("/analytics/{user_id}/recommendations")
async def get_recommendations(user_id: str):
    """获取个性化建议"""
    analytics = workspace_api.get_analytics()
    recommendations = analytics.get_recommendations(user_id)
    return JSONResponse(content=recommendations)


@router.get("/analytics/{user_id}/{portfolio_name}/report")
async def get_analytics_report(user_id: str, portfolio_name: str):
    """获取分析报告"""
    analytics = workspace_api.get_analytics()
    report = analytics.generate_report(user_id, portfolio_name)
    return JSONResponse(content={'report': report})


# ========== 交易日志端点 ==========

@router.get("/journal/{user_id}/notes")
async def get_trade_notes(
    user_id: str,
    symbol: Optional[str] = Query(None),
    note_type: Optional[str] = Query(None)
):
    """获取交易笔记"""
    notes = workspace_api.journal.get_trade_notes(
        user_id=user_id,
        symbol=symbol,
        note_type=note_type
    )
    return JSONResponse(content=[note.__dict__ for note in notes])


@router.post("/journal/{user_id}/note")
async def add_trade_note(
    user_id: str,
    symbol: str,
    note_type: str,
    content: str,
    strategy: str = "",
    emotion: str = "",
    tags: Optional[List[str]] = None
):
    """添加交易笔记"""
    note = workspace_api.journal.add_trade_note(
        user_id=user_id,
        symbol=symbol,
        note_type=note_type,
        content=content,
        strategy=strategy,
        emotion=emotion,
        tags=tags
    )
    return JSONResponse(content=note.__dict__)


@router.get("/journal/{user_id}/observations")
async def get_market_observations(
    user_id: str,
    market: Optional[str] = Query(None),
    mood: Optional[str] = Query(None)
):
    """获取市场观察"""
    observations = workspace_api.journal.get_market_observations(
        user_id=user_id,
        market=market,
        mood=mood
    )
    return JSONResponse(content=[obs.__dict__ for obs in observations])


@router.post("/journal/{user_id}/observation")
async def add_market_observation(
    user_id: str,
    market: str,
    mood: str,
    observations: str,
    key_events: Optional[List[str]] = None,
    symbol_specific: Optional[str] = None,
    tags: Optional[List[str]] = None
):
    """添加市场观察"""
    obs = workspace_api.journal.add_market_observation(
        user_id=user_id,
        market=market,
        mood=mood,
        observations=observations,
        key_events=key_events,
        symbol_specific=symbol_specific,
        tags=tags
    )
    return JSONResponse(content=obs.__dict__)


@router.get("/journal/{user_id}/reflections")
async def get_strategy_reflections(user_id: str):
    """获取策略反思"""
    reflections = workspace_api.journal.get_strategy_reflections(user_id)
    return JSONResponse(content=[ref.__dict__ for ref in reflections])


@router.post("/journal/{user_id}/reflection")
async def add_strategy_reflection(
    user_id: str,
    strategy_name: str,
    period_start: str,
    period_end: str,
    performance: float,
    what_worked: Optional[List[str]] = None,
    what_didnt_work: Optional[List[str]] = None,
    improvements: Optional[List[str]] = None,
    overall_rating: int = 5
):
    """添加策略反思"""
    reflection = workspace_api.journal.add_strategy_reflection(
        user_id=user_id,
        strategy_name=strategy_name,
        period_start=period_start,
        period_end=period_end,
        performance=performance,
        what_worked=what_worked,
        what_didnt_work=what_didnt_work,
        improvements=improvements,
        overall_rating=overall_rating
    )
    return JSONResponse(content=reflection.__dict__)


@router.get("/journal/{user_id}/search")
async def search_journal(user_id: str, q: str = Query(..., description="搜索关键词")):
    """搜索日志"""
    results = workspace_api.journal.search_journal(user_id, q)
    return JSONResponse(content={
        'trade_notes': [n.__dict__ for n in results['trade_notes']],
        'market_observations': [o.__dict__ for o in results['market_observations']],
        'strategy_reflections': [r.__dict__ for r in results['strategy_reflections']]
    })


@router.get("/journal/{user_id}/emotions")
async def get_emotion_analysis(user_id: str):
    """获取情绪分析"""
    analysis = workspace_api.journal.get_emotion_analysis(user_id)
    return JSONResponse(content=analysis)


@router.get("/journal/{user_id}/sentiment-timeline")
async def get_sentiment_timeline(
    user_id: str,
    days: int = Query(30, description="天数")
):
    """获取情绪时间线"""
    df = workspace_api.journal.get_market_sentiment_timeline(user_id, days)
    return JSONResponse(content=df.to_dict('records'))


@router.get("/journal/{user_id}/tags")
async def get_most_active_tags(user_id: str):
    """获取最活跃标签"""
    tags = workspace_api.journal.get_most_active_tags(user_id)
    return JSONResponse(content=tags)


# ========== 导入导出端点 ==========

@router.get("/export/{user_id}")
async def export_workspace(user_id: str, format: str = "json"):
    """导出工作区"""
    workspace_json = workspace_api.workspace_manager.export_workspace(user_id)
    trades_json = workspace_api.trade_manager.export_trades(user_id, format)
    journal_json = workspace_api.journal.export_journal(user_id, format)

    return JSONResponse(content={
        'workspace': json.loads(workspace_json),
        'trades': json.loads(trades_json),
        'journal': json.loads(journal_json)
    })


@router.post("/import")
async def import_workspace(data: Dict[str, Any]):
    """导入工作区"""
    try:
        if 'workspace' in data:
            workspace_api.workspace_manager.import_workspace(
                json.dumps(data['workspace'])
            )
        return JSONResponse(content={'status': 'success'})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== 仪表板数据聚合端点 ==========

@router.get("/dashboard/{user_id}")
async def get_dashboard_data(user_id: str):
    """获取仪表板数据"""
    analytics = workspace_api.get_analytics()

    # 获取所有组合
    portfolios = workspace_api.portfolio_manager.list_portfolios(user_id)

    dashboard_data = {
        'portfolios': [],
        'total_value': 0,
        'total_pnl': 0,
        'behavior': analytics.analyze_trading_behavior(user_id),
        'recommendations': analytics.get_recommendations(user_id)
    }

    for portfolio_name in portfolios:
        portfolio = workspace_api.portfolio_manager.get_portfolio(user_id, portfolio_name)
        if portfolio:
            summary = workspace_api.portfolio_manager.get_portfolio_summary(
                user_id, portfolio_name
            )
            dashboard_data['portfolios'].append(summary)
            dashboard_data['total_value'] += summary['total_value']
            dashboard_data['total_pnl'] += summary['total_pnl']

    return JSONResponse(content=dashboard_data)


# 导出路由器
__all__ = ['router']
