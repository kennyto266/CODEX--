"""
風險管理系統 API 路由

提供投資組合風險監控、告警和壓力測試的 REST 端點
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# 導入緩存和統一響應
try:
    from ..cache.cache_manager import cache_manager, cached
    from ..models.api_response import create_success_response, create_error_response
except ImportError:
    # 如果導入失敗，創建空的緩存管理器
    class DummyCache:
        def cache_result(self, *args, **kwargs):
            def decorator(func):
                return func
    cache_manager = DummyCache()
    cached = cache_manager.cache_result

    def create_success_response(data=None):
        return {"success": True, "data": data}

    def create_error_response(error):
        return {"success": False, "error": error}


# ==================== Data Models ====================

class AlertSeverity(str, Enum):
    """告警嚴重程度"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class RiskMetric(BaseModel):
    """風險指標"""
    metric_name: str = Field(..., description="指標名稱")
    current_value: float = Field(..., description="當前值")
    threshold: float = Field(..., description="閾值")
    severity: AlertSeverity = Field(default=AlertSeverity.INFO)
    status: str = Field(description="狀態: safe, warning, danger")


class PortfolioRisk(BaseModel):
    """投資組合風險"""
    portfolio_value: float = Field(..., description="投資組合價值")
    var_95: float = Field(..., description="95% VaR (Value at Risk)")
    var_99: float = Field(..., description="99% VaR")
    expected_shortfall: float = Field(..., description="預期不足 (Expected Shortfall)")
    max_drawdown: float = Field(..., description="最大回撤")
    current_drawdown: float = Field(..., description="當前回撤")
    volatility: float = Field(..., description="波動率")
    beta: float = Field(..., description="Beta 係數")
    sharpe_ratio: float = Field(..., description="Sharpe 比率")


class Alert(BaseModel):
    """風險告警"""
    alert_id: str = Field(..., description="告警ID")
    severity: AlertSeverity = Field(..., description="嚴重程度")
    type: str = Field(..., description="告警類型")
    message: str = Field(..., description="告警消息")
    triggered_at: datetime = Field(..., description="觸發時間")
    acknowledged: bool = Field(default=False, description="是否已確認")
    acknowledged_at: Optional[datetime] = None


class StressTestScenario(BaseModel):
    """壓力測試場景"""
    scenario_name: str = Field(..., description="場景名稱")
    description: str = Field(..., description="場景描述")
    market_shock: float = Field(..., description="市場衝擊 (%)")
    volatility_multiplier: float = Field(default=2.0, description="波動率倍數")
    result_portfolio_value: float = Field(..., description="結果投資組合價值")
    estimated_loss: float = Field(..., description="估計損失")


# ==================== API Router ====================

def create_risk_router() -> APIRouter:
    """創建風險管理 API 路由"""
    router = APIRouter(prefix="/api/risk", tags=["Risk Management"])
    logger = logging.getLogger("hk_quant_system.dashboard.api_risk")

    # 模擬的風險數據存儲
    current_portfolio_value = 1000000.0
    alerts_store: List[Dict[str, Any]] = []

    # 初始化模擬告警
    def _init_alerts():
        return [
            {
                "alert_id": "alert_001",
                "severity": AlertSeverity.WARNING.value,
                "type": "drawdown_warning",
                "message": "當前回撤達到 5.2%，接近 6% 的風險限制",
                "triggered_at": datetime.now() - timedelta(hours=2),
                "acknowledged": False,
                "acknowledged_at": None
            },
            {
                "alert_id": "alert_002",
                "severity": AlertSeverity.INFO.value,
                "type": "position_concentration",
                "message": "單個頭寸佔投資組合的 12%，符合風險政策",
                "triggered_at": datetime.now() - timedelta(hours=1),
                "acknowledged": True,
                "acknowledged_at": datetime.now() - timedelta(minutes=30)
            }
        ]

    alerts_store = _init_alerts()

    # ==================== GET: 獲取投資組合風險 ====================

    @router.get("/portfolio")
    @cached(ttl=120, key_prefix="portfolio_risk")
    async def get_portfolio_risk() -> Dict[str, Any]:
        """
        獲取投資組合的風險指標 - 帶緩存

        Returns:
            投資組合風險信息，包含 VaR、最大回撤等
        """
        try:
            logger.debug("獲取投資組合風險")

            risk_data = {
                "portfolio_value": current_portfolio_value,
                "var_95": current_portfolio_value * 0.05,  # 5% VaR
                "var_99": current_portfolio_value * 0.08,  # 8% VaR
                "expected_shortfall": current_portfolio_value * 0.095,  # 9.5% ES
                "max_drawdown": 0.052,  # 5.2%
                "current_drawdown": 0.032,  # 3.2%
                "volatility": 0.18,  # 18% 年化波動率
                "beta": 1.05,  # Beta = 1.05
                "sharpe_ratio": 1.8,  # Sharpe 比率
                "timestamp": datetime.now().isoformat()
            }

            return create_success_response(data=risk_data)

        except Exception as e:
            logger.error(f"獲取投資組合風險失敗: {e}")
            return create_error_response(f"獲取投資組合風險失敗: {str(e)}")

    # ==================== GET: 獲取 VaR 數據 ====================

    @router.get("/var", response_model=Dict[str, Any])
    async def get_var_analysis() -> Dict[str, Any]:
        """
        獲取詳細的 VaR 分析

        Returns:
            不同置信度的 VaR 值
        """
        try:
            var_data = {
                "confidence_95": current_portfolio_value * 0.05,
                "confidence_99": current_portfolio_value * 0.08,
                "confidence_99_9": current_portfolio_value * 0.10,
                "expected_shortfall_95": current_portfolio_value * 0.075,
                "expected_shortfall_99": current_portfolio_value * 0.095,
                "historical_max_loss": current_portfolio_value * 0.052,
                "calculation_method": "Historical Simulation",
                "data_period_days": 252,
                "timestamp": datetime.now().isoformat()
            }
            return var_data

        except Exception as e:
            logger.error(f"獲取 VaR 分析失敗: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ==================== GET: 獲取風險告警 ====================

    @router.get("/alerts")
    @cached(ttl=60, key_prefix="risk_alerts")
    async def get_risk_alerts(
        severity: Optional[str] = Query(None, description="按嚴重程度過濾"),
        limit: int = Query(50, ge=1, le=100),
        acknowledged: Optional[bool] = Query(None, description="按確認狀態過濾")
    ) -> Dict[str, Any]:
        """
        獲取風險告警列表 - 帶緩存和過濾

        - **severity**: 告警嚴重程度 (info, warning, critical)
        - **acknowledged**: 按確認狀態過濾
        - **limit**: 返回告警數量

        Returns:
            告警列表
        """
        try:
            logger.debug(f"獲取風險告警: severity={severity}, acknowledged={acknowledged}, limit={limit}")

            alerts = alerts_store.copy()

            # 按嚴重程度過濾
            if severity:
                alerts = [a for a in alerts if a["severity"] == severity.lower()]

            # 按確認狀態過濾
            if acknowledged is not None:
                alerts = [a for a in alerts if a["acknowledged"] == acknowledged]

            # 按時間排序（最新在前）
            alerts.sort(key=lambda x: x["triggered_at"], reverse=True)

            # 轉換時間格式
            for alert in alerts[:limit]:
                alert["triggered_at"] = alert["triggered_at"].isoformat()
                if alert["acknowledged_at"]:
                    alert["acknowledged_at"] = alert["acknowledged_at"].isoformat()

            paginated_alerts = alerts[:limit]
            total = len(alerts)

            logger.info(f"返回 {len(paginated_alerts)} 個告警 (總數: {total})")

            return create_success_response(data={
                "items": paginated_alerts,
                "total": total,
                "filters": {
                    "severity": severity,
                    "acknowledged": acknowledged
                }
            })

        except Exception as e:
            logger.error(f"獲取風險告警失敗: {e}")
            return create_error_response(f"獲取風險告警失敗: {str(e)}")

    # ==================== GET: 獲取頭寸風險分析 ====================

    @router.get("/positions", response_model=List[Dict[str, Any]])
    async def get_position_risk() -> List[Dict[str, Any]]:
        """
        獲取每個頭寸的風險分析

        Returns:
            頭寸風險數據列表
        """
        try:
            positions = [
                {
                    "symbol": "0700.HK",
                    "name": "騰訊",
                    "quantity": 1000,
                    "current_price": 325.50,
                    "position_value": 325500,
                    "percentage_of_portfolio": 32.5,
                    "var_95": 16277.5,
                    "marginal_var": 0.05,
                    "beta": 1.15,
                    "delta": 0.95,
                    "risk_level": "moderate"
                },
                {
                    "symbol": "0939.HK",
                    "name": "中國建設銀行",
                    "quantity": 5000,
                    "current_price": 6.85,
                    "position_value": 34250,
                    "percentage_of_portfolio": 3.4,
                    "var_95": 1712.5,
                    "marginal_var": 0.05,
                    "beta": 1.05,
                    "delta": 0.90,
                    "risk_level": "low"
                },
                {
                    "symbol": "0388.HK",
                    "name": "香港交易所",
                    "quantity": 500,
                    "current_price": 420.80,
                    "position_value": 210400,
                    "percentage_of_portfolio": 21.0,
                    "var_95": 10520,
                    "marginal_var": 0.05,
                    "beta": 0.95,
                    "delta": 0.98,
                    "risk_level": "low"
                }
            ]
            return positions

        except Exception as e:
            logger.error(f"獲取頭寸風險失敗: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ==================== POST: 執行壓力測試 ====================

    @router.post("/stress-test", response_model=List[Dict[str, Any]])
    async def run_stress_test() -> List[Dict[str, Any]]:
        """
        執行投資組合壓力測試

        Returns:
            不同場景下的投資組合結果
        """
        try:
            scenarios = [
                {
                    "scenario_name": "市場崩盤 (-20%)",
                    "description": "市場一天下跌 20%",
                    "market_shock": -20.0,
                    "volatility_multiplier": 3.0,
                    "result_portfolio_value": current_portfolio_value * 0.80,
                    "estimated_loss": current_portfolio_value * 0.20,
                    "portfolio_return_pct": -20.0
                },
                {
                    "scenario_name": "中等衝擊 (-10%)",
                    "description": "市場下跌 10%",
                    "market_shock": -10.0,
                    "volatility_multiplier": 2.0,
                    "result_portfolio_value": current_portfolio_value * 0.90,
                    "estimated_loss": current_portfolio_value * 0.10,
                    "portfolio_return_pct": -10.0
                },
                {
                    "scenario_name": "輕微衝擊 (-5%)",
                    "description": "市場下跌 5%",
                    "market_shock": -5.0,
                    "volatility_multiplier": 1.5,
                    "result_portfolio_value": current_portfolio_value * 0.95,
                    "estimated_loss": current_portfolio_value * 0.05,
                    "portfolio_return_pct": -5.0
                },
                {
                    "scenario_name": "利率上升 (+100bps)",
                    "description": "利率上升 100 個基點",
                    "market_shock": -8.0,
                    "volatility_multiplier": 1.8,
                    "result_portfolio_value": current_portfolio_value * 0.92,
                    "estimated_loss": current_portfolio_value * 0.08,
                    "portfolio_return_pct": -8.0
                },
                {
                    "scenario_name": "匯率波動 (±10%)",
                    "description": "匯率波動 10%",
                    "market_shock": -3.0,
                    "volatility_multiplier": 1.3,
                    "result_portfolio_value": current_portfolio_value * 0.97,
                    "estimated_loss": current_portfolio_value * 0.03,
                    "portfolio_return_pct": -3.0
                }
            ]

            logger.info("壓力測試執行完成")
            return scenarios

        except Exception as e:
            logger.error(f"執行壓力測試失敗: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ==================== POST: 確認告警 ====================

    @router.post("/alerts/{alert_id}/acknowledge", response_model=Dict[str, str])
    async def acknowledge_alert(alert_id: str) -> Dict[str, str]:
        """
        確認一個風險告警

        - **alert_id**: 告警ID

        Returns:
            確認結果
        """
        try:
            for alert in alerts_store:
                if alert["alert_id"] == alert_id:
                    alert["acknowledged"] = True
                    alert["acknowledged_at"] = datetime.now()
                    logger.info(f"告警已確認: {alert_id}")
                    return {"status": "success", "message": f"告警 {alert_id} 已確認"}

            raise HTTPException(status_code=404, detail=f"告警不存在: {alert_id}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"確認告警失敗: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ==================== GET: 風險儀表板概覽 ====================

    @router.get("/dashboard", response_model=Dict[str, Any])
    async def get_risk_dashboard() -> Dict[str, Any]:
        """
        獲取風險管理儀表板概覽

        Returns:
            關鍵風險指標和統計信息
        """
        try:
            unacknowledged_alerts = sum(1 for a in alerts_store if not a["acknowledged"])
            critical_alerts = sum(1 for a in alerts_store if a["severity"] == "critical")

            dashboard = {
                "portfolio_value": current_portfolio_value,
                "var_95": current_portfolio_value * 0.05,
                "var_99": current_portfolio_value * 0.08,
                "max_drawdown": 0.052,
                "current_drawdown": 0.032,
                "volatility": 0.18,
                "sharpe_ratio": 1.8,
                "total_alerts": len(alerts_store),
                "unacknowledged_alerts": unacknowledged_alerts,
                "critical_alerts": critical_alerts,
                "alert_trend": "stable",  # stable, increasing, decreasing
                "risk_level": "moderate",  # low, moderate, high
                "timestamp": datetime.now().isoformat()
            }
            return dashboard

        except Exception as e:
            logger.error(f"獲取風險儀表板失敗: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router
