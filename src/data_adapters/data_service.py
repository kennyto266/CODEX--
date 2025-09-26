"""
数据服务管理器

统一管理多个数据适配器，提供数据获取、质量监控和故障切换功能。
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal

from .base_adapter import BaseDataAdapter, RealMarketData, DataValidationResult
from .raw_data_adapter import RawDataAdapter, RawDataAdapterConfig
from .config_manager import DataAdapterConfigManager, AdapterConfigEntry
from .http_api_adapter import HttpApiDataAdapter, HttpApiAdapterConfig


class DataService:
    """数据服务管理器"""
    
    def __init__(self, config_manager: Optional[DataAdapterConfigManager] = None):
        self.config_manager = config_manager or DataAdapterConfigManager()
        self.logger = logging.getLogger("hk_quant_system.data_service")
        self.adapters: Dict[str, BaseDataAdapter] = {}
        self._initialized = False
        
    async def initialize(self) -> bool:
        """初始化数据服务"""
        try:
            self.logger.info("Initializing data service...")
            
            # 加载配置
            await self.config_manager.load_config_from_file()
            
            # 初始化适配器
            await self._initialize_adapters()
            
            # 启动健康检查任务
            asyncio.create_task(self._health_check_loop())
            
            self._initialized = True
            self.logger.info("Data service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize data service: {e}")
            return False
    
    async def _initialize_adapters(self) -> None:
        """初始化所有启用的适配器"""
        enabled_adapters = self.config_manager.get_enabled_adapters()
        
        for entry in enabled_adapters:
            try:
                adapter = await self._create_adapter(entry)
                if adapter:
                    self.adapters[entry.name] = adapter
                    self.logger.info(f"Initialized adapter: {entry.name}")
                else:
                    self.logger.error(f"Failed to create adapter: {entry.name}")
                    
            except Exception as e:
                self.logger.error(f"Error initializing adapter {entry.name}: {e}")
    
    async def _create_adapter(self, entry: AdapterConfigEntry) -> Optional[BaseDataAdapter]:
        """创建适配器实例"""
        try:
            if str(entry.config.get('source_type')) == "raw_data":
                raw_config = RawDataAdapterConfig(**entry.config)
                adapter = RawDataAdapter(raw_config)
                
                # 连接到数据源
                connected = await adapter.connect()
                if connected:
                    return adapter
                else:
                    self.logger.error(f"Failed to connect adapter: {entry.name}")
                    return None
            elif str(entry.config.get('source_type')) == "http_api":
                http_config = HttpApiAdapterConfig(**entry.config)
                adapter = HttpApiDataAdapter(http_config)
                connected = await adapter.connect()
                if connected:
                    return adapter
                else:
                    self.logger.error(f"Failed to connect adapter: {entry.name}")
                    return None
            else:
                self.logger.warning(f"Unsupported adapter type: {entry.config.get('source_type')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to create adapter {entry.name}: {e}")
            return None
    
    async def get_market_data(
        self, 
        symbol: str, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        source_preference: Optional[str] = None
    ) -> List[RealMarketData]:
        """获取市场数据（支持多数据源和故障切换）"""
        try:
            if not self._initialized:
                self.logger.error("Data service not initialized")
                return []
            
            # 确定要使用的适配器
            adapters_to_try = self._select_adapters(source_preference)
            
            last_error = None
            for adapter_entry in adapters_to_try:
                adapter_name = adapter_entry.name
                if adapter_name not in self.adapters:
                    self.logger.warning(f"Adapter {adapter_name} not available")
                    continue
                
                try:
                    adapter = self.adapters[adapter_name]
                    data = await adapter.get_market_data(symbol, start_date, end_date)
                    
                    if data:
                        self.logger.info(f"Successfully retrieved {len(data)} records for {symbol} from {adapter_name}")
                        return data
                    else:
                        self.logger.warning(f"No data returned from adapter {adapter_name} for {symbol}")
                        
                except Exception as e:
                    last_error = e
                    self.logger.warning(f"Adapter {adapter_name} failed for {symbol}: {e}")
                    continue
            
            # 所有适配器都失败了
            self.logger.error(f"All adapters failed to retrieve data for {symbol}. Last error: {last_error}")
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get market data for {symbol}: {e}")
            return []
    
    def _select_adapters(self, source_preference: Optional[str] = None) -> List[AdapterConfigEntry]:
        """选择要使用的适配器（按优先级排序）"""
        if source_preference:
            # 优先使用指定的适配器
            preferred_entry = self.config_manager.get_adapter_config(source_preference)
            if preferred_entry and preferred_entry.enabled:
                adapters = [preferred_entry]
                # 添加其他启用的适配器作为备用
                other_adapters = [
                    entry for entry in self.config_manager.get_enabled_adapters()
                    if entry.name != source_preference
                ]
                adapters.extend(other_adapters)
                return adapters
        
        # 返回所有启用的适配器（按优先级排序）
        return self.config_manager.get_enabled_adapters()
    
    async def validate_data_quality(
        self, 
        data: List[RealMarketData],
        adapter_name: Optional[str] = None
    ) -> DataValidationResult:
        """验证数据质量"""
        try:
            if not data:
                return DataValidationResult(
                    is_valid=False,
                    quality_score=0.0,
                    quality_level="unknown",
                    errors=["No data provided"],
                    warnings=[]
                )
            
            # 使用指定适配器或第一个可用适配器进行验证
            if adapter_name and adapter_name in self.adapters:
                adapter = self.adapters[adapter_name]
            else:
                # 使用第一个可用的适配器
                available_adapters = list(self.adapters.values())
                if not available_adapters:
                    return DataValidationResult(
                        is_valid=False,
                        quality_score=0.0,
                        quality_level="unknown",
                        errors=["No adapters available for validation"],
                        warnings=[]
                    )
                adapter = available_adapters[0]
            
            return await adapter.validate_data(data)
            
        except Exception as e:
            self.logger.error(f"Failed to validate data quality: {e}")
            return DataValidationResult(
                is_valid=False,
                quality_score=0.0,
                quality_level="unknown",
                errors=[f"Validation error: {str(e)}"],
                warnings=[]
            )
    
    async def get_available_symbols(self, adapter_name: Optional[str] = None) -> List[str]:
        """获取可用的股票代码列表"""
        try:
            if adapter_name:
                if adapter_name in self.adapters:
                    adapter = self.adapters[adapter_name]
                    if hasattr(adapter, 'get_available_symbols'):
                        return await adapter.get_available_symbols()
                return []
            
            # 从所有适配器获取股票代码
            all_symbols = set()
            for adapter in self.adapters.values():
                if hasattr(adapter, 'get_available_symbols'):
                    try:
                        symbols = await adapter.get_available_symbols()
                        all_symbols.update(symbols)
                    except Exception as e:
                        self.logger.warning(f"Failed to get symbols from adapter: {e}")
            
            return sorted(list(all_symbols))
            
        except Exception as e:
            self.logger.error(f"Failed to get available symbols: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            health_status = {
                "service_status": "healthy" if self._initialized else "unhealthy",
                "initialized": self._initialized,
                "total_adapters": len(self.adapters),
                "config_summary": self.config_manager.get_config_summary(),
                "adapters": {}
            }
            
            # 检查每个适配器的健康状态
            for name, adapter in self.adapters.items():
                try:
                    adapter_health = await adapter.health_check()
                    health_status["adapters"][name] = adapter_health
                except Exception as e:
                    health_status["adapters"][name] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "service_status": "error",
                "error": str(e),
                "initialized": self._initialized
            }
    
    async def _health_check_loop(self) -> None:
        """定期健康检查循环"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                health_status = await self.health_check()
                
                # 检查是否有适配器需要重新连接
                for name, adapter_health in health_status.get("adapters", {}).items():
                    if adapter_health.get("status") == "unhealthy":
                        self.logger.warning(f"Adapter {name} is unhealthy, attempting to reconnect...")
                        await self._reconnect_adapter(name)
                        
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
    
    async def _reconnect_adapter(self, adapter_name: str) -> bool:
        """重新连接适配器"""
        try:
            if adapter_name not in self.adapters:
                return False
            
            # 断开现有连接
            adapter = self.adapters[adapter_name]
            await adapter.disconnect()
            
            # 重新创建适配器
            entry = self.config_manager.get_adapter_config(adapter_name)
            if entry:
                new_adapter = await self._create_adapter(entry)
                if new_adapter:
                    self.adapters[adapter_name] = new_adapter
                    self.logger.info(f"Successfully reconnected adapter: {adapter_name}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to reconnect adapter {adapter_name}: {e}")
            return False
    
    async def refresh_adapter(self, adapter_name: str) -> bool:
        """刷新适配器（重新扫描数据文件等）"""
        try:
            if adapter_name not in self.adapters:
                self.logger.error(f"Adapter {adapter_name} not found")
                return False
            
            adapter = self.adapters[adapter_name]
            if hasattr(adapter, 'refresh_data_files'):
                return await adapter.refresh_data_files()
            
            self.logger.warning(f"Adapter {adapter_name} does not support refresh operation")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to refresh adapter {adapter_name}: {e}")
            return False
    
    async def get_data_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        try:
            stats = {
                "total_adapters": len(self.adapters),
                "enabled_adapters": len([a for a in self.adapters.values()]),
                "timestamp": datetime.now(),
                "adapters": {}
            }
            
            for name, adapter in self.adapters.items():
                try:
                    adapter_stats = {
                        "source_type": adapter.config.source_type,
                        "last_update": adapter._last_update,
                        "cache_size": len(adapter._cache),
                        "config": {
                            "update_frequency": adapter.config.update_frequency,
                            "cache_enabled": adapter.config.cache_enabled,
                            "quality_threshold": adapter.config.quality_threshold
                        }
                    }
                    
                    # 获取可用股票代码数量
                    if hasattr(adapter, 'get_available_symbols'):
                        try:
                            symbols = await adapter.get_available_symbols()
                            adapter_stats["available_symbols_count"] = len(symbols)
                        except:
                            adapter_stats["available_symbols_count"] = "unknown"
                    
                    stats["adapters"][name] = adapter_stats
                    
                except Exception as e:
                    stats["adapters"][name] = {"error": str(e)}
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get data statistics: {e}")
            return {"error": str(e)}
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            self.logger.info("Cleaning up data service...")
            
            # 断开所有适配器连接
            for name, adapter in self.adapters.items():
                try:
                    await adapter.disconnect()
                    self.logger.debug(f"Disconnected adapter: {name}")
                except Exception as e:
                    self.logger.warning(f"Error disconnecting adapter {name}: {e}")
            
            self.adapters.clear()
            self._initialized = False
            
            self.logger.info("Data service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during data service cleanup: {e}")
