
from typing import Any, Dict, List, Optional

import structlog
import time
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = structlog.get_logger("api.config")

router = APIRouter()


class ConfigItem(BaseModel):
    """配置项模型"""
    key: str
    value: Any
    description: str
    category: str
    updated_at: Optional[float] = None


class UpdateConfigRequest(BaseModel):
    """更新配置请求模型"""
    key: str = Field(..., description="配置键名")
    value: Any = Field(..., description="配置值")


class StrategyConfig(BaseModel):
    """策略配置模型"""
    strategy_name: str
    parameters: Dict[str, Any]
    enabled: bool
    description: str


@router.get(
    "/config",
    response_model=List[ConfigItem],
    summary="获取系统配置",
    description="返回所有系统配置项",
)
async def get_config(
    category: Optional[str] = Query(None, description="配置分类筛选"),
) -> List[ConfigItem]:
    """
    获取系统配置

    可以按分类筛选配置项
    """
    try:
        logger.info("获取系统配置", category=category)

        # TODO: 从配置文件或数据库读取配置
        # 暂时返回模拟数据
        configs = [
            ConfigItem(
                key="api.port",
                value=8001,
                description="API服务端口",
                category="server",
            ),
            ConfigItem(
                key="api.host",
                value="0.0.0.0",
                description="API服务主机",
                category="server",
            ),
            ConfigItem(
                key="trading.initial_capital",
                value=100000.0,
                description="初始交易资金",
                category="trading",
            ),
            ConfigItem(
                key="trading.max_position",
                value=0.95,
                description="最大仓位比例",
                category="trading",
            ),
            ConfigItem(
                key="logging.level",
                value="INFO",
                description="日志级别",
                category="logging",
            ),
        ]

        # 按分类筛选
        if category:
            configs = [c for c in configs if c.category == category]

        logger.info("配置获取完成", count=len(configs))

        return configs

    except Exception as e:
        logger.error("获取配置失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.get(
    "/config/{key}",
    response_model=ConfigItem,
    summary="获取单个配置项",
    description="根据键名获取特定配置项",
)
async def get_config_item(key: str) -> ConfigItem:
    """
    获取单个配置项
    """
    try:
        logger.info("获取配置项", key=key)

        # TODO: 从配置文件或数据库读取
        # 模拟数据
        if key == "api.port":
            return ConfigItem(
                key="api.port",
                value=8001,
                description="API服务端口",
                category="server",
            )
        else:
            raise HTTPException(status_code=404, detail=f"配置项 '{key}' 不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取配置项失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.put(
    "/config",
    response_model=ConfigItem,
    summary="更新配置项",
    description="更新指定配置项的值",
)
async def update_config(request: UpdateConfigRequest) -> ConfigItem:
    """
    更新配置项

    注意：实际部署时应该需要管理员权限
    """
    try:
        logger.info("更新配置项", key=request.key, value=request.value)

        # TODO: 更新配置文件或数据库
        # 更新成功后返回新值
        updated_config = ConfigItem(
            key=request.key,
            value=request.value,
            description="配置项描述",
            category="general",
            updated_at=time.time(),
        )

        logger.info("配置更新完成", config=updated_config)

        return updated_config

    except Exception as e:
        logger.error("更新配置失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.get(
    "/config/strategies",
    response_model=List[StrategyConfig],
    summary="获取策略配置",
    description="返回所有策略的配置参数",
)
async def get_strategy_configs() -> List[StrategyConfig]:
    """
    获取所有策略配置
    """
    try:
        logger.info("获取策略配置")

        # TODO: 从数据库或配置文件读取
        strategies = [
            StrategyConfig(
                strategy_name="kdj",
                parameters={
                    "k_period": 9,
                    "d_period": 3,
                    "oversold": 20,
                    "overbought": 80,
                },
                enabled=True,
                description="KDJ随机指标策略",
            ),
            StrategyConfig(
                strategy_name="rsi",
                parameters={"period": 14, "oversold": 30, "overbought": 70},
                enabled=True,
                description="RSI相对强度指标策略",
            ),
            StrategyConfig(
                strategy_name="macd",
                parameters={
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9,
                },
                enabled=True,
                description="MACD指数平滑策略",
            ),
        ]

        logger.info("策略配置获取完成", count=len(strategies))

        return strategies

    except Exception as e:
        logger.error("获取策略配置失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取策略配置失败: {str(e)}")


@router.put(
    "/config/strategies/{strategy_name}",
    response_model=StrategyConfig,
    summary="更新策略配置",
    description="更新指定策略的参数配置",
)
async def update_strategy_config(
    strategy_name: str, config: StrategyConfig
) -> StrategyConfig:
    """
    更新策略配置
    """
    try:
        logger.info("更新策略配置", strategy=strategy_name, config=config)

        # TODO: 更新数据库或配置文件
        updated_config = StrategyConfig(
            strategy_name=strategy_name,
            parameters=config.parameters,
            enabled=config.enabled,
            description=config.description,
        )

        logger.info("策略配置更新完成", config=updated_config)

        return updated_config

    except Exception as e:
        logger.error("更新策略配置失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"更新策略配置失败: {str(e)}")
