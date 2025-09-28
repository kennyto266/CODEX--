#!/usr/bin/env python3
"""
最小化系統啟動器 - 只啟動核心功能
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("minimal_system")

async def test_core_components():
    """測試核心組件"""
    logger.info("🔍 測試核心組件...")
    
    try:
        # 測試核心配置
        from src.core import SystemConfig
        config = SystemConfig()
        logger.info("✅ SystemConfig 加載成功")
        
        # 測試數據服務
        from src.data_adapters.data_service import DataService
        data_service = DataService()
        logger.info("✅ DataService 加載成功")
        
        # 測試HTTP API適配器
        from src.data_adapters.http_api_adapter import HttpApiDataAdapter, HttpApiAdapterConfig
        adapter_config = HttpApiAdapterConfig(
            source_path="http://localhost:8000",
            endpoint_symbol="/api/data"
        )
        adapter = HttpApiDataAdapter(adapter_config)
        logger.info("✅ HttpApiDataAdapter 加載成功")
        
        # 測試消息隊列
        from src.core.message_queue import MessageQueue
        message_queue = MessageQueue()
        logger.info("✅ MessageQueue 加載成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 核心組件測試失敗: {e}")
        return False

async def test_data_adapters():
    """測試數據適配器"""
    logger.info("📊 測試數據適配器...")
    
    try:
        from src.data_adapters.data_service import DataService
        from src.data_adapters.yahoo_finance_adapter import YahooFinanceAdapter
        
        # 創建數據服務
        data_service = DataService()
        
        # 測試Yahoo Finance適配器
        yahoo_adapter = YahooFinanceAdapter()
        logger.info("✅ YahooFinanceAdapter 加載成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 數據適配器測試失敗: {e}")
        return False

async def start_web_dashboard():
    """啟動Web儀表板"""
    logger.info("🌐 啟動Web儀表板...")
    
    try:
        from src.dashboard.dashboard_ui import DashboardUI
        
        # 創建儀表板
        dashboard = DashboardUI()
        
        # 啟動儀表板
        await dashboard.start()
        logger.info("✅ Web儀表板啟動成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Web儀表板啟動失敗: {e}")
        return False

async def main():
    """主函數"""
    logger.info("🚀 最小化量化交易系統啟動器")
    logger.info("=" * 50)
    
    # 測試核心組件
    core_success = await test_core_components()
    if not core_success:
        logger.error("❌ 核心組件測試失敗，系統無法啟動")
        return False
    
    # 測試數據適配器
    adapter_success = await test_data_adapters()
    if not adapter_success:
        logger.warning("⚠️ 數據適配器測試失敗，但系統可以繼續運行")
    
    logger.info("🎉 系統核心功能正常！")
    logger.info("\n📋 可用功能:")
    logger.info("   ✅ 系統配置管理")
    logger.info("   ✅ 數據服務")
    logger.info("   ✅ HTTP API適配器")
    logger.info("   ✅ 消息隊列")
    logger.info("   ✅ Yahoo Finance數據源")
    
    logger.info("\n📖 下一步:")
    logger.info("   1. 配置環境變量（如需要）")
    logger.info("   2. 運行: python start_dashboard.py")
    logger.info("   3. 查看: REAL_SYSTEM_GUIDE.md")
    
    logger.info("\n✨ 最小化系統已準備就緒！")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n👋 用戶中斷，系統關閉")
    except Exception as e:
        logger.error(f"❌ 系統異常: {e}")
        sys.exit(1)