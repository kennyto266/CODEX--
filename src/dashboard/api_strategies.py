"""
策略管理系統 API 路由

提供策略瀏覽、配置管理和性能比較的 REST 端點
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

# 導入緩存和統一響應
try:
    from ..cache.cache_manager import cache_manager, cached
    from ..models.api_response import create_success_response, create_error_response, create_paginated_response
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

    def create_paginated_response(items, total, page, size, filters=None):
        return {
            "success": True,
            "data": {
                "items": items,
                "pagination": {
                    "total": total,
                    "page": page,
                    "size": size,
                    "pages": (total + size - 1) // size if total > 0 else 0,
                },
                "filters": filters or {}
            }
        }


# ==================== Data Models ====================

class StrategyParameter(BaseModel):
    """策略參數"""
    name: str = Field(..., description="參數名稱")
    value: Any = Field(..., description="參數值")
    type: str = Field(..., description="參數類型: int, float, str, bool")
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = Field(default="", description="參數描述")


class StrategyInfo(BaseModel):
    """策略信息"""
    strategy_id: str = Field(..., description="策略ID")
    name: str = Field(..., description="策略名稱")
    category: str = Field(..., description="策略類別: trend, mean_reversion, pairs, ml")
    description: str = Field(..., description="策略描述")
    author: str = Field(default="System", description="策略作者")
    version: str = Field(default="1.0", description="版本")
    created_date: datetime = Field(..., description="創建日期")
    parameters: List[StrategyParameter] = Field(default_factory=list)
    status: str = Field(default="active", description="狀態: active, inactive, deprecated")


class StrategyPerformance(BaseModel):
    """策略性能"""
    strategy_id: str
    period: str  # 1m, 3m, 1y, all
    total_return_pct: float
    annual_return_pct: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    average_profit_per_trade: float
    last_updated: datetime


class StrategyConfig(BaseModel):
    """策略配置"""
    config_id: str = Field(default_factory=lambda: str(uuid4()))
    strategy_id: str
    config_name: str
    parameters: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=False)


# ==================== API Router ====================

def create_strategies_router() -> APIRouter:
    """創建策略管理 API 路由"""
    router = APIRouter(prefix="/api/strategies", tags=["Strategies"])
    logger = logging.getLogger("hk_quant_system.dashboard.api_strategies")

    # 模擬的策略存儲
    strategies_store: Dict[str, Dict[str, Any]] = {
        "moving_average_crossover": {
            "strategy_id": "moving_average_crossover",
            "name": "移動平均線交叉",
            "category": "trend",
            "description": "基於快速和慢速移動平均線的交叉點進行交易",
            "author": "QuantTeam",
            "version": "2.1",
            "created_date": datetime.now() - timedelta(days=365),
            "parameters": [
                {"name": "fast_period", "value": 20, "type": "int", "min_value": 5, "max_value": 50},
                {"name": "slow_period", "value": 50, "type": "int", "min_value": 20, "max_value": 200},
                {"name": "signal_period", "value": 9, "type": "int", "min_value": 3, "max_value": 20}
            ],
            "status": "active",
            "performance": {
                "total_return_pct": 18.5,
                "annual_return_pct": 18.2,
                "sharpe_ratio": 1.8,
                "max_drawdown": 8.5,
                "win_rate": 0.62,
                "total_trades": 156
            }
        },
        "rsi_oscillator": {
            "strategy_id": "rsi_oscillator",
            "name": "RSI 震蕩策略",
            "category": "mean_reversion",
            "description": "基於相對強度指數 (RSI) 的超買超賣交易",
            "author": "QuantTeam",
            "version": "1.5",
            "created_date": datetime.now() - timedelta(days=180),
            "parameters": [
                {"name": "rsi_period", "value": 14, "type": "int", "min_value": 5, "max_value": 30},
                {"name": "oversold_level", "value": 30, "type": "float", "min_value": 10, "max_value": 40},
                {"name": "overbought_level", "value": 70, "type": "float", "min_value": 60, "max_value": 90}
            ],
            "status": "active",
            "performance": {
                "total_return_pct": 12.3,
                "annual_return_pct": 14.1,
                "sharpe_ratio": 1.5,
                "max_drawdown": 10.2,
                "win_rate": 0.58,
                "total_trades": 98
            }
        },
        "bollinger_bands": {
            "strategy_id": "bollinger_bands",
            "name": "布林帶策略",
            "category": "trend",
            "description": "基於布林帶上下軌的突破和回撤交易",
            "author": "QuantTeam",
            "version": "1.8",
            "created_date": datetime.now() - timedelta(days=120),
            "parameters": [
                {"name": "period", "value": 20, "type": "int", "min_value": 10, "max_value": 50},
                {"name": "num_std_dev", "value": 2.0, "type": "float", "min_value": 1.0, "max_value": 3.0}
            ],
            "status": "active",
            "performance": {
                "total_return_pct": 15.7,
                "annual_return_pct": 16.8,
                "sharpe_ratio": 1.7,
                "max_drawdown": 7.8,
                "win_rate": 0.61,
                "total_trades": 124
            }
        },
        "macd_strategy": {
            "strategy_id": "macd_strategy",
            "name": "MACD 指標策略",
            "category": "trend",
            "description": "基於 MACD 線和信號線交叉的趨勢追蹤",
            "author": "QuantTeam",
            "version": "1.3",
            "created_date": datetime.now() - timedelta(days=90),
            "parameters": [
                {"name": "fast_period", "value": 12, "type": "int"},
                {"name": "slow_period", "value": 26, "type": "int"},
                {"name": "signal_period", "value": 9, "type": "int"}
            ],
            "status": "active",
            "performance": {
                "total_return_pct": 11.2,
                "annual_return_pct": 12.5,
                "sharpe_ratio": 1.4,
                "max_drawdown": 9.5,
                "win_rate": 0.56,
                "total_trades": 87
            }
        },
        "kdj_strategy": {
            "strategy_id": "kdj_strategy",
            "name": "KDJ 隨機指標",
            "category": "mean_reversion",
            "description": "基於 KDJ 指標的超買超賣策略",
            "author": "QuantTeam",
            "version": "1.2",
            "created_date": datetime.now() - timedelta(days=60),
            "parameters": [
                {"name": "k_period", "value": 9, "type": "int"},
                {"name": "d_period", "value": 3, "type": "int"},
                {"name": "j_period", "value": 3, "type": "int"},
                {"name": "oversold", "value": 20, "type": "float"},
                {"name": "overbought", "value": 80, "type": "float"}
            ],
            "status": "active",
            "performance": {
                "total_return_pct": 9.8,
                "annual_return_pct": 11.2,
                "sharpe_ratio": 1.3,
                "max_drawdown": 11.0,
                "win_rate": 0.55,
                "total_trades": 76
            }
        }
    }

    # 存儲用戶配置
    user_configs: Dict[str, StrategyConfig] = {}

    # ==================== GET: 獲取策略列表 ====================

    @router.get("/list")
    @cached(ttl=300, key_prefix="strategies")
    async def list_strategies(
        category: Optional[str] = Query(None, description="按分類過濾 (trend/mean_reversion/pairs/ml)"),
        status: Optional[str] = Query(None, description="按狀態過濾 (active/inactive/deprecated)"),
        author: Optional[str] = Query(None, description="按作者過濾"),
        sort_by: str = Query("created_date", description="排序字段 (name/created_date/performance)"),
        sort_order: str = Query("desc", description="排序方向 (asc/desc)"),
        page: int = Query(1, ge=1, description="頁碼"),
        size: int = Query(50, ge=1, le=100, description="每頁數量"),
        fields: Optional[str] = Query(None, description="返回字段，逗號分隔"),
        min_sharpe: Optional[float] = Query(None, description="最小夏普比率過濾")
    ) -> Dict[str, Any]:
        """
        獲取策略列表 - 帶緩存、分頁、過濾和排序功能

        Returns:
            分頁的策略列表
        """
        try:
            logger.info(f"獲取策略列表: category={category}, status={status}, page={page}, size={size}")

            # 獲取所有策略
            strategies = list(strategies_store.values())

            # 應用過濾器
            if category:
                strategies = [s for s in strategies if s["category"] == category]

            if status:
                strategies = [s for s in strategies if s["status"] == status]

            if author:
                strategies = [s for s in strategies if s["author"].lower() == author.lower()]

            if min_sharpe is not None:
                strategies = [s for s in strategies if s["performance"]["sharpe_ratio"] >= min_sharpe]

            # 轉換為可序列化格式
            strategy_dicts = []
            for strategy in strategies:
                strategy_dict = {
                    "strategy_id": strategy["strategy_id"],
                    "name": strategy["name"],
                    "category": strategy["category"],
                    "description": strategy["description"],
                    "author": strategy["author"],
                    "version": strategy["version"],
                    "status": strategy["status"],
                    "created_date": strategy["created_date"].isoformat(),
                    "performance": strategy["performance"]
                }
                strategy_dicts.append(strategy_dict)

            # 應用排序
            reverse = sort_order.lower() == "desc"
            if sort_by == "name":
                strategy_dicts.sort(key=lambda x: x["name"].lower(), reverse=reverse)
            elif sort_by == "created_date":
                strategy_dicts.sort(key=lambda x: x["created_date"], reverse=reverse)
            elif sort_by == "performance":
                strategy_dicts.sort(key=lambda x: x["performance"]["sharpe_ratio"], reverse=reverse)

            # 計算總數和分頁
            total = len(strategy_dicts)
            start = (page - 1) * size
            end = start + size
            paginated_strategies = strategy_dicts[start:end]

            # 字段過濾
            if fields:
                requested_fields = [f.strip() for f in fields.split(",")]
                filtered_strategies = []
                for strategy in paginated_strategies:
                    filtered_strategy = {k: v for k, v in strategy.items() if k in requested_fields}
                    filtered_strategies.append(filtered_strategy)
                paginated_strategies = filtered_strategies

            # 構建過濾條件
            filters = {
                "category": category,
                "status": status,
                "author": author,
                "sort_by": sort_by,
                "sort_order": sort_order,
                "min_sharpe": min_sharpe
            }

            logger.info(f"返回 {len(paginated_strategies)} 個策略 (總數: {total})")

            # 使用統一響應格式
            return create_paginated_response(
                items=paginated_strategies,
                total=total,
                page=page,
                size=size,
                filters=filters
            )

        except Exception as e:
            logger.error(f"獲取策略列表失敗: {e}")
            return create_error_response(f"獲取策略列表失敗: {str(e)}")

    # ==================== GET: 獲取策略詳情 ====================

    @router.get("/{strategy_id}")
    @cached(ttl=120, key_prefix="strategy_detail")
    async def get_strategy_details(strategy_id: str) -> Dict[str, Any]:
        """
        獲取策略詳細信息 - 帶緩存

        - **strategy_id**: 策略ID

        Returns:
            策略詳細信息和參數
        """
        logger.debug(f"獲取策略詳情: {strategy_id}")

        if strategy_id not in strategies_store:
            return create_error_response(f"策略不存在: {strategy_id}")

        strategy = strategies_store[strategy_id]

        strategy_detail = {
            "strategy_id": strategy["strategy_id"],
            "name": strategy["name"],
            "category": strategy["category"],
            "description": strategy["description"],
            "author": strategy["author"],
            "version": strategy["version"],
            "status": strategy["status"],
            "created_date": strategy["created_date"].isoformat(),
            "parameters": [
                {
                    "name": p["name"],
                    "value": p["value"],
                    "type": p["type"],
                    "min_value": p.get("min_value"),
                    "max_value": p.get("max_value"),
                    "description": p.get("description", "")
                }
                for p in strategy.get("parameters", [])
            ],
            "performance": strategy["performance"]
        }

        return create_success_response(data=strategy_detail)

    # ==================== GET: 獲取策略性能 ====================

    @router.get("/{strategy_id}/performance", response_model=List[Dict[str, Any]])
    async def get_strategy_performance(
        strategy_id: str,
        period: Optional[str] = Query("all", description="時間週期: 1m, 3m, 1y, all")
    ) -> List[Dict[str, Any]]:
        """
        獲取策略的歷史性能數據

        - **strategy_id**: 策略ID
        - **period**: 時間週期

        Returns:
            不同週期的性能指標
        """
        if strategy_id not in strategies_store:
            raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

        strategy = strategies_store[strategy_id]
        performance = strategy["performance"]

        # 模擬不同週期的性能數據
        periods_data = {
            "1m": {
                "total_return_pct": performance["total_return_pct"] * 0.08,
                "annual_return_pct": performance["annual_return_pct"] * 0.08
            },
            "3m": {
                "total_return_pct": performance["total_return_pct"] * 0.25,
                "annual_return_pct": performance["annual_return_pct"] * 0.25
            },
            "1y": {
                "total_return_pct": performance["total_return_pct"] * 0.7,
                "annual_return_pct": performance["annual_return_pct"] * 0.7
            },
            "all": performance
        }

        selected_data = periods_data.get(period, periods_data["all"])
        return [{
            "strategy_id": strategy_id,
            "period": period,
            "total_return_pct": selected_data["total_return_pct"],
            "annual_return_pct": selected_data["annual_return_pct"],
            "sharpe_ratio": performance["sharpe_ratio"],
            "max_drawdown": performance["max_drawdown"],
            "win_rate": performance["win_rate"],
            "total_trades": performance["total_trades"],
            "average_profit_per_trade": performance["average_profit_per_trade"],
            "last_updated": datetime.now().isoformat()
        }]

    # ==================== POST: 比較策略 ====================

    @router.post("/compare", response_model=List[Dict[str, Any]])
    async def compare_strategies(
        strategy_ids: List[str] = Body(..., description="要比較的策略 ID 列表")
    ) -> List[Dict[str, Any]]:
        """
        比較多個策略的性能

        - **strategy_ids**: 策略 ID 列表

        Returns:
            策略性能對比數據
        """
        try:
            comparison = []
            for strategy_id in strategy_ids:
                if strategy_id not in strategies_store:
                    continue

                strategy = strategies_store[strategy_id]
                perf = strategy["performance"]
                comparison.append({
                    "strategy_id": strategy_id,
                    "name": strategy["name"],
                    "category": strategy["category"],
                    "total_return_pct": perf["total_return_pct"],
                    "annual_return_pct": perf["annual_return_pct"],
                    "sharpe_ratio": perf["sharpe_ratio"],
                    "max_drawdown": perf["max_drawdown"],
                    "win_rate": perf["win_rate"],
                    "total_trades": perf["total_trades"],
                    "rank": 0  # 待計算
                })

            # 計算排名（按 Sharpe 比率）
            comparison.sort(key=lambda x: x["sharpe_ratio"], reverse=True)
            for i, item in enumerate(comparison):
                item["rank"] = i + 1

            logger.info(f"比較 {len(comparison)} 個策略")
            return comparison

        except Exception as e:
            logger.error(f"策略比較失敗: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ==================== POST: 保存策略配置 ====================

    @router.post("/configs", response_model=Dict[str, str])
    async def save_strategy_config(
        strategy_id: str = Body(...),
        config_name: str = Body(...),
        parameters: Dict[str, Any] = Body(...)
    ) -> Dict[str, str]:
        """
        保存自定義策略配置

        - **strategy_id**: 策略ID
        - **config_name**: 配置名稱
        - **parameters**: 策略參數

        Returns:
            配置ID
        """
        try:
            if strategy_id not in strategies_store:
                raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

            config_id = str(uuid4())
            config = {
                "config_id": config_id,
                "strategy_id": strategy_id,
                "config_name": config_name,
                "parameters": parameters,
                "created_at": datetime.now(),
                "last_modified": datetime.now(),
                "is_active": False
            }

            user_configs[config_id] = config
            logger.info(f"保存策略配置: {config_id}, 策略: {strategy_id}")

            return {
                "config_id": config_id,
                "status": "success",
                "message": f"配置已保存: {config_name}"
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"保存策略配置失敗: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ==================== GET: 獲取已保存的配置 ====================

    @router.get("/configs", response_model=List[Dict[str, Any]])
    async def list_saved_configs() -> List[Dict[str, Any]]:
        """獲取所有已保存的策略配置"""
        try:
            configs = []
            for config_id, config in user_configs.items():
                configs.append({
                    "config_id": config["config_id"],
                    "strategy_id": config["strategy_id"],
                    "strategy_name": strategies_store.get(config["strategy_id"], {}).get("name", "Unknown"),
                    "config_name": config["config_name"],
                    "is_active": config["is_active"],
                    "created_at": config["created_at"].isoformat(),
                    "last_modified": config["last_modified"].isoformat()
                })

            return configs

        except Exception as e:
            logger.error(f"獲取配置列表失敗: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router
