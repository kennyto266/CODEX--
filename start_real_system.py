#!/usr/bin/env python3
"""
簡化的真實系統啟動腳本
避免shell環境問題
"""

import asyncio
import logging
import sys
from pathlib import Path

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('real_system.log', encoding='utf-8')
    ]
)

logger = logging.getLogger("real_system")

async def main():
    """主函數"""
    try:
        logger.info("🚀 啟動真實量化交易系統...")
        
        # 測試導入
        logger.info("📦 測試系統組件導入...")
        
        from src.data_adapters.data_service import DataService
        from src.agents.real_agents.enhanced_quantitative_analyst import EnhancedQuantitativeAnalyst, RealAgentConfig
        from src.risk_management.risk_calculator import RiskCalculator, RiskLimits
        from src.backtest.enhanced_backtest_engine import EnhancedBacktestEngine
        from src.backtest.base_backtest import BacktestConfig
        from src.monitoring.enhanced_monitoring import EnhancedMonitoringSystem
        from src.security.compliance_checker import ComplianceChecker
        from src.agents.coordinator import AgentCoordinator
        from src.core import SystemConfig
        
        logger.info("✅ 所有組件導入成功")
        
        # 初始化系統配置
        logger.info("⚙️ 初始化系統配置...")
        config = SystemConfig()
        
        # 初始化數據服務
        logger.info("📊 初始化數據服務...")
        data_service = DataService()
        await data_service.initialize()
        
        # 初始化風險計算器
        logger.info("🛡️ 初始化風險管理...")
        risk_calculator = RiskCalculator()
        
        # 初始化監控系統
        logger.info("📈 初始化監控系統...")
        monitoring_system = EnhancedMonitoringSystem(
            data_service=data_service,
            risk_calculator=risk_calculator
        )
        await monitoring_system.initialize()
        
        # 初始化合規檢查器
        logger.info("📋 初始化合規檢查...")
        compliance_checker = ComplianceChecker()
        await compliance_checker.initialize()
        
        # 初始化AI代理
        logger.info("🤖 初始化AI量化分析師...")
        agent_config = RealAgentConfig(
            agent_id="enhanced_qa_001",
            agent_type="quantitative_analyst",
            name="Enhanced Quantitative Analyst",
            description="AI驅動的量化分析師，使用機器學習進行市場分析",
            data_service=data_service,
            risk_calculator=risk_calculator,
            monitoring_system=monitoring_system,
            compliance_checker=compliance_checker
        )
        
        quantitative_analyst = EnhancedQuantitativeAnalyst(agent_config)
        await quantitative_analyst.initialize()
        
        # 初始化代理協調器
        logger.info("🎯 初始化代理協調器...")
        coordinator = AgentCoordinator()
        await coordinator.initialize()
        await coordinator.add_agent(quantitative_analyst)
        
        # 啟動監控
        logger.info("🔄 啟動監控系統...")
        await monitoring_system.start_monitoring()
        
        # 啟動代理
        logger.info("▶️ 啟動AI代理...")
        await coordinator.start_all_agents()
        
        logger.info("🎉 真實量化交易系統啟動成功！")
        logger.info("📊 系統狀態:")
        logger.info(f"   - 數據服務: ✅ 運行中")
        logger.info(f"   - AI代理: ✅ 運行中 ({quantitative_analyst.name})")
        logger.info(f"   - 風險管理: ✅ 運行中")
        logger.info(f"   - 監控系統: ✅ 運行中")
        logger.info(f"   - 合規檢查: ✅ 運行中")
        
        # 運行一個簡單的回測示例
        logger.info("📈 運行回測示例...")
        try:
            backtest_config = BacktestConfig(
                strategy_name="ml_strategy",
                symbols=["AAPL", "MSFT", "GOOGL"],
                start_date="2023-01-01",
                end_date="2023-12-31",
                initial_capital=1000000
            )
            
            backtest_engine = EnhancedBacktestEngine(backtest_config)
            await backtest_engine.initialize()
            
            # 簡單策略函數
            async def simple_strategy(market_data, positions):
                return []  # 空策略，僅測試系統
            
            result = await backtest_engine.run_backtest(simple_strategy)
            logger.info(f"✅ 回測完成: 總收益率 {result.total_return:.2%}")
            
        except Exception as e:
            logger.warning(f"⚠️ 回測示例失敗: {e}")
        
        # 保持系統運行
        logger.info("🔄 系統運行中... (按 Ctrl+C 停止)")
        logger.info("📖 查看 REAL_SYSTEM_GUIDE.md 了解詳細使用方法")
        
        try:
            while True:
                await asyncio.sleep(10)
                # 定期檢查系統狀態
                status = await monitoring_system.get_monitoring_status()
                logger.info(f"📊 系統狀態: {status.get('total_alerts', 0)} 個警報")
                
        except KeyboardInterrupt:
            logger.info("🛑 收到停止信號...")
            
    except Exception as e:
        logger.error(f"❌ 系統啟動失敗: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    finally:
        # 清理資源
        logger.info("🧹 清理系統資源...")
        try:
            if 'coordinator' in locals():
                await coordinator.stop_all_agents()
            if 'monitoring_system' in locals():
                await monitoring_system.stop_monitoring()
            if 'data_service' in locals():
                await data_service.cleanup()
            logger.info("✅ 資源清理完成")
        except Exception as e:
            logger.error(f"⚠️ 清理資源時出錯: {e}")
    
    return True

if __name__ == "__main__":
    print("🚀 真實量化交易系統啟動器")
    print("=" * 50)
    
    try:
        success = asyncio.run(main())
        if success:
            print("\n✅ 系統正常關閉")
        else:
            print("\n❌ 系統異常關閉")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 用戶中斷")
    except Exception as e:
        print(f"\n❌ 系統錯誤: {e}")
        sys.exit(1)