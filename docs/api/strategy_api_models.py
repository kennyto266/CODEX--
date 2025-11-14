"""
策略框架API數據模型
港股量化交易系統 - 策略管理模組

基於阿程項目的模塊化設計，支持策略運行、參數優化和性能比較。
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class StrategyType(str, Enum):
    """策略類型枚舉"""
    USD_CNH_HSI = "usd_cnh_hsi"
    HIBOR_STRATEGY = "hibor_strategy"
    GDP_STRATEGY = "gdp_strategy"
    CPI_STRATEGY = "cpi_strategy"
    MULTI_FACTOR = "multi_factor"


class OptimizationStatus(str, Enum):
    """優化狀態枚舉"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TradingAction(str, Enum):
    """交易動作枚舉"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


# ==================== 策略參數模型 ====================

class StrategyParameters(BaseModel):
    """
    策略參數模型

    基於阿程項目的參數化框架：
    - 4天確認機制
    - 0.4%閾值
    - 14天持倉期
    """

    confirmation_days: int = Field(
        default=4,
        ge=1,
        le=30,
        description="確認天數 - 阿程的創新：連續N天滿足條件才觸發信號"
    )

    threshold: float = Field(
        default=0.004,
        ge=0.0,
        le=1.0,
        description="觸發閾值 - 阿程的0.4%閾值：累計回報必須超過此值"
    )

    holding_period: int = Field(
        default=14,
        ge=1,
        le=365,
        description="持倉期（天） - 阿程的14天固定持倉，避免過度交易"
    )

    # 權重參數（用於多因子策略）
    hibor_weight: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="HIBOR權重"
    )

    gdp_weight: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="GDP權重"
    )

    cpi_weight: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="CPI權重"
    )

    traffic_weight: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="交通流量權重"
    )

    weather_weight: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="天氣數據權重"
    )


# ==================== 請求模型 ====================

class StrategyRunRequest(BaseModel):
    """
    策略運行請求模型
    """

    strategy_type: StrategyType = Field(
        ...,
        description="策略類型"
    )

    symbol: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="股票代碼（如：0700.HK）"
    )

    start_date: str = Field(
        ...,
        description="開始日期（YYYY-MM-DD）"
    )

    end_date: str = Field(
        ...,
        description="結束日期（YYYY-MM-DD）"
    )

    params: Optional[StrategyParameters] = Field(
        default=None,
        description="策略參數（可選，不提供則使用默認值）"
    )


class ParameterOptimizationRequest(BaseModel):
    """
    參數優化請求模型

    支持多線程並行參數搜索，提升優化效率
    """

    strategy_type: StrategyType = Field(
        ...,
        description="策略類型"
    )

    symbol: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="股票代碼"
    )

    start_date: str = Field(
        ...,
        description="開始日期（YYYY-MM-DD）"
    )

    end_date: str = Field(
        ...,
        description="結束日期（YYYY-MM-DD）"
    )

    param_grid: Dict[str, List[Union[int, float]]] = Field(
        ...,
        description="參數搜索網格"
    )

    max_workers: int = Field(
        default=4,
        ge=1,
        le=16,
        description="並行工作進程數"
    )

    metric: str = Field(
        default="sharpe_ratio",
        description="優化目標指標（sharpe_ratio, total_return, max_drawdown等）"
    )


class StrategyComparisonRequest(BaseModel):
    """
    策略比較請求模型

    支持多個策略的性能比較和排名
    """

    strategy_configs: List[Dict[str, Any]] = Field(
        ...,
        min_items=2,
        max_items=10,
        description="策略配置列表"
    )

    symbol: str = Field(
        ...,
        description="股票代碼"
    )

    start_date: str = Field(
        ...,
        description="開始日期（YYYY-MM-DD）"
    )

    end_date: str = Field(
        ...,
        description="結束日期（YYYY-MM-DD）"
    )


class StrategyListRequest(BaseModel):
    """
    策略列表查詢請求模型
    """

    page: int = Field(
        default=1,
        ge=1,
        description="頁碼"
    )

    size: int = Field(
        default=50,
        ge=1,
        le=100,
        description="每頁數量"
    )

    strategy_type: Optional[StrategyType] = Field(
        default=None,
        description="策略類型過濾"
    )


# ==================== 響應模型 ====================

class TradeRecord(BaseModel):
    """
    交易記錄模型
    """

    date: str = Field(..., description="交易日期")
    action: TradingAction = Field(..., description="交易動作")
    price: float = Field(..., description="交易價格")
    quantity: int = Field(..., description="交易數量")
    signal_strength: float = Field(..., description="信號強度")


class PerformanceMetrics(BaseModel):
    """
    績效指標模型

    基於阿程的find_trading_statistics()函數計算的12+關鍵指標
    """

    # 基礎收益指標
    total_return: float = Field(..., description="總回報率")
    cagr: float = Field(..., description="年化收益率")
    annual_volatility: float = Field(..., description="年化波動率")

    # 風險調整指標
    sharpe_ratio: float = Field(..., description="夏普比率")
    sortino_ratio: float = Field(..., description="索提諾比率")
    calmar_ratio: float = Field(..., description="卡爾瑪比率")

    # 風險指標
    max_drawdown: float = Field(..., description="最大回撤")
    max_drawdown_duration: int = Field(..., description="最大回撤持續天數")
    var_95: float = Field(..., description="95% VaR")

    # 交易統計
    total_trades: int = Field(..., description="總交易次數")
    win_rate: float = Field(..., description="勝率")
    avg_win: float = Field(..., description="平均盈利")
    avg_loss: float = Field(..., description="平均虧損")
    profit_factor: float = Field(..., description="盈利因子")


class StrategyRunResponse(BaseModel):
    """
    策略運行響應模型
    """

    strategy_id: str = Field(..., description="策略唯一ID")
    strategy_type: StrategyType = Field(..., description="策略類型")
    symbol: str = Field(..., description="股票代碼")

    # 執行信息
    start_date: str = Field(..., description="開始日期")
    end_date: str = Field(..., description="結束日期")
    execution_time: float = Field(..., description="執行時間（秒）")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="創建時間")

    # 策略結果
    initial_capital: float = Field(default=100000.0, description="初始資本")
    final_value: float = Field(..., description="最終價值")

    # 交易記錄
    trades: List[TradeRecord] = Field(default_factory=list, description="交易記錄列表")

    # 績效指標
    metrics: PerformanceMetrics = Field(..., description="績效指標")

    # 原始數據（可選，用於調試）
    raw_data: Optional[Dict[str, Any]] = Field(default=None, description="原始策略數據")


class OptimizationResult(BaseModel):
    """
    單個優化結果模型
    """

    params: Dict[str, Any] = Field(..., description="參數組合")
    metrics: PerformanceMetrics = Field(..., description="績效指標")
    rank: int = Field(..., description="排名")
    score: float = Field(..., description="綜合得分")


class ParameterOptimizationResponse(BaseModel):
    """
    參數優化響應模型
    """

    optimization_id: str = Field(..., description="優化任務ID")
    strategy_type: StrategyType = Field(..., description="策略類型")
    symbol: str = Field(..., description="股票代碼")

    # 優化參數
    param_grid: Dict[str, List[Union[int, float]]] = Field(..., description="參數搜索網格")
    total_combinations: int = Field(..., description="總參數組合數")
    max_workers: int = Field(..., description="並行工作進程數")

    # 執行信息
    status: OptimizationStatus = Field(..., description="優化狀態")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="進度（0-1）")
    execution_time: float = Field(..., description="執行時間（秒）")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="創建時間")

    # 結果
    best_params: Optional[Dict[str, Any]] = Field(default=None, description="最佳參數")
    best_metrics: Optional[PerformanceMetrics] = Field(default=None, description="最佳績效指標")
    top_results: List[OptimizationResult] = Field(default_factory=list, description="前N名結果")


class StrategyComparisonItem(BaseModel):
    """
    策略比較項目模型
    """

    strategy_id: str = Field(..., description="策略ID")
    strategy_type: StrategyType = Field(..., description="策略類型")
    params: Dict[str, Any] = Field(..., description="策略參數")
    metrics: PerformanceMetrics = Field(..., description="績效指標")
    rank: int = Field(..., description="排名")


class StrategyComparisonResponse(BaseModel):
    """
    策略比較響應模型
    """

    comparison_id: str = Field(..., description="比較任務ID")
    symbol: str = Field(..., description="股票代碼")
    start_date: str = Field(..., description="開始日期")
    end_date: str = Field(..., description="結束日期")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="創建時間")

    # 比較結果
    strategies: List[StrategyComparisonItem] = Field(..., description="策略比較列表")
    best_strategy: StrategyComparisonItem = Field(..., description="最佳策略")
    total_strategies: int = Field(..., description="策略總數")


class StrategyListResponse(BaseModel):
    """
    策略列表響應模型
    """

    strategies: List[Dict[str, Any]] = Field(..., description="策略列表")
    total: int = Field(..., description="總數")
    page: int = Field(..., description="當前頁碼")
    size: int = Field(..., description="每頁數量")
    pages: int = Field(..., description="總頁數")


class OptimizationProgressResponse(BaseModel):
    """
    優化進度響應模型
    """

    optimization_id: str = Field(..., description="優化任務ID")
    status: OptimizationStatus = Field(..., description="優化狀態")
    progress: float = Field(..., ge=0.0, le=1.0, description="進度（0-1）")
    completed_combinations: int = Field(..., description="已完成組合數")
    total_combinations: int = Field(..., description="總組合數")
    current_params: Optional[Dict[str, Any]] = Field(default=None, description="當前參數")
    execution_time: float = Field(..., description="執行時間（秒）")


# ==================== 便利函數 ====================

def create_strategy_run_response(
    strategy_id: str,
    strategy_type: StrategyType,
    symbol: str,
    start_date: str,
    end_date: str,
    execution_time: float,
    final_value: float,
    trades: List[TradeRecord],
    metrics: PerformanceMetrics,
    initial_capital: float = 100000.0,
    raw_data: Optional[Dict[str, Any]] = None
) -> StrategyRunResponse:
    """
    創建策略運行響應

    Args:
        strategy_id: 策略ID
        strategy_type: 策略類型
        symbol: 股票代碼
        start_date: 開始日期
        end_date: 結束日期
        execution_time: 執行時間
        final_value: 最終價值
        trades: 交易記錄
        metrics: 績效指標
        initial_capital: 初始資本
        raw_data: 原始數據

    Returns:
        StrategyRunResponse: 策略運行響應
    """
    return StrategyRunResponse(
        strategy_id=strategy_id,
        strategy_type=strategy_type,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        execution_time=execution_time,
        initial_capital=initial_capital,
        final_value=final_value,
        trades=trades,
        metrics=metrics,
        raw_data=raw_data
    )


def create_optimization_response(
    optimization_id: str,
    strategy_type: StrategyType,
    symbol: str,
    param_grid: Dict[str, List[Union[int, float]]],
    total_combinations: int,
    max_workers: int,
    status: OptimizationStatus,
    execution_time: float,
    best_params: Optional[Dict[str, Any]] = None,
    best_metrics: Optional[PerformanceMetrics] = None,
    top_results: Optional[List[OptimizationResult]] = None
) -> ParameterOptimizationResponse:
    """
    創建參數優化響應

    Args:
        optimization_id: 優化任務ID
        strategy_type: 策略類型
        symbol: 股票代碼
        param_grid: 參數搜索網格
        total_combinations: 總參數組合數
        max_workers: 並行工作進程數
        status: 優化狀態
        execution_time: 執行時間
        best_params: 最佳參數
        best_metrics: 最佳績效指標
        top_results: 前N名結果

    Returns:
        ParameterOptimizationResponse: 參數優化響應
    """
    return ParameterOptimizationResponse(
        optimization_id=optimization_id,
        strategy_type=strategy_type,
        symbol=symbol,
        param_grid=param_grid,
        total_combinations=total_combinations,
        max_workers=max_workers,
        status=status,
        progress=1.0 if status == OptimizationStatus.COMPLETED else 0.0,
        execution_time=execution_time,
        best_params=best_params,
        best_metrics=best_metrics,
        top_results=top_results or []
    )


# ==================== 響應模板 ====================

class StrategyResponseTemplates:
    """策略API響應模板"""

    # 成功消息
    MSG_STRATEGY_RUN_SUCCESS = "策略運行成功"
    MSG_OPTIMIZATION_SUCCESS = "參數優化成功"
    MSG_COMPARISON_SUCCESS = "策略比較成功"

    # 錯誤消息
    ERROR_INVALID_STRATEGY_TYPE = "無效的策略類型"
    ERROR_STRATEGY_NOT_FOUND = "策略不存在"
    ERROR_OPTIMIZATION_NOT_FOUND = "優化任務不存在"
    ERROR_INVALID_DATE_RANGE = "無效的日期範圍"
    ERROR_OPTIMIZATION_RUNNING = "優化任務正在運行中"

    # 提示信息
    MSG_STRATEGY_CREATED = "策略創建成功"
    MSG_STRATEGY_UPDATED = "策略更新成功"
    MSG_STRATEGY_DELETED = "策略刪除成功"
