"""
港股量化分析AI代理团队集成测试

测试prompt模板、执行引擎和代理的基本功能。
"""

import asyncio
import logging
import json
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.hk_prompt_templates import HKPromptTemplates, AgentType
from src.agents.hk_prompt_engine import HKPromptEngine, LLMConfig, LLMProvider
from src.agents.hk_prompt_agents import HKPromptAgentFactory
from src.core.message_queue import MessageQueue
from src.core import SystemConfig
from src.agents.base_agent import AgentConfig


# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hk_prompt_test")


class HKPromptIntegrationTest:
    """港股Prompt集成测试类"""
    
    def __init__(self):
        self.logger = logging.getLogger("hk_prompt_test")
        self.templates = HKPromptTemplates()
        self.message_queue = None
        self.prompt_engine = None
        
    async def test_prompt_templates(self):
        """测试Prompt模板"""
        self.logger.info("测试Prompt模板...")
        
        try:
            # 测试所有模板
            for agent_type in AgentType:
                template = self.templates.get_template(agent_type)
                if template:
                    self.logger.info(f"✓ 模板 {agent_type.value} 加载成功")
                    
                    # 测试prompt生成
                    input_data = {"test": "data"}
                    prompt = self.templates.generate_prompt(agent_type, input_data)
                    if prompt and len(prompt) > 100:
                        self.logger.info(f"✓ 模板 {agent_type.value} prompt生成成功")
                    else:
                        self.logger.error(f"✗ 模板 {agent_type.value} prompt生成失败")
                else:
                    self.logger.error(f"✗ 模板 {agent_type.value} 加载失败")
            
            self.logger.info("Prompt模板测试完成")
            return True
            
        except Exception as e:
            self.logger.error(f"Prompt模板测试失败: {e}")
            return False
    
    async def test_prompt_engine(self):
        """测试Prompt引擎"""
        self.logger.info("测试Prompt引擎...")
        
        try:
            # 创建模拟LLM配置（不实际调用API）
            llm_config = LLMConfig(
                provider=LLMProvider.OPENAI,
                api_key="test-key",
                model="gpt-4",
                max_tokens=1000,
                temperature=0.1
            )
            
            # 创建引擎
            engine = HKPromptEngine(llm_config)
            
            # 测试引擎创建
            if engine:
                self.logger.info("✓ Prompt引擎创建成功")
            else:
                self.logger.error("✗ Prompt引擎创建失败")
                return False
            
            # 测试统计信息
            stats = engine.get_execution_stats()
            if isinstance(stats, dict) and "execution_count" in stats:
                self.logger.info("✓ 统计信息获取成功")
            else:
                self.logger.error("✗ 统计信息获取失败")
                return False
            
            self.logger.info("Prompt引擎测试完成")
            return True
            
        except Exception as e:
            self.logger.error(f"Prompt引擎测试失败: {e}")
            return False
    
    async def test_agent_creation(self):
        """测试代理创建"""
        self.logger.info("测试代理创建...")
        
        try:
            # 初始化消息队列
            self.message_queue = MessageQueue()
            await self.message_queue.initialize()
            
            # 初始化系统配置
            system_config = SystemConfig()
            
            # 创建模拟LLM配置
            llm_config = LLMConfig(
                provider=LLMProvider.OPENAI,
                api_key="test-key",
                model="gpt-4"
            )
            
            # 创建Prompt引擎
            self.prompt_engine = HKPromptEngine(llm_config)
            
            # 创建所有代理
            agents = HKPromptAgentFactory.create_all_agents(
                self.message_queue, system_config, self.prompt_engine
            )
            
            if len(agents) == len(AgentType):
                self.logger.info(f"✓ 成功创建 {len(agents)} 个代理")
            else:
                self.logger.error(f"✗ 代理创建数量不匹配: 期望 {len(AgentType)}, 实际 {len(agents)}")
                return False
            
            # 测试代理类型
            for agent_type in AgentType:
                if agent_type in agents:
                    self.logger.info(f"✓ 代理 {agent_type.value} 创建成功")
                else:
                    self.logger.error(f"✗ 代理 {agent_type.value} 创建失败")
                    return False
            
            self.logger.info("代理创建测试完成")
            return True
            
        except Exception as e:
            self.logger.error(f"代理创建测试失败: {e}")
            return False
    
    async def test_agent_initialization(self):
        """测试代理初始化"""
        self.logger.info("测试代理初始化...")
        
        try:
            if not self.message_queue or not self.prompt_engine:
                self.logger.error("消息队列或Prompt引擎未初始化")
                return False
            
            # 创建代理
            system_config = SystemConfig()
            agents = HKPromptAgentFactory.create_all_agents(
                self.message_queue, system_config, self.prompt_engine
            )
            
            # 初始化所有代理
            success_count = 0
            for agent_type, agent in agents.items():
                try:
                    success = await agent.initialize()
                    if success:
                        self.logger.info(f"✓ 代理 {agent_type.value} 初始化成功")
                        success_count += 1
                    else:
                        self.logger.error(f"✗ 代理 {agent_type.value} 初始化失败")
                except Exception as e:
                    self.logger.error(f"✗ 代理 {agent_type.value} 初始化异常: {e}")
            
            if success_count == len(agents):
                self.logger.info("✓ 所有代理初始化成功")
                return True
            else:
                self.logger.error(f"✗ 部分代理初始化失败: {success_count}/{len(agents)}")
                return False
                
        except Exception as e:
            self.logger.error(f"代理初始化测试失败: {e}")
            return False
    
    async def test_data_preparation(self):
        """测试数据准备"""
        self.logger.info("测试数据准备...")
        
        try:
            # 创建模拟市场数据
            market_data = [
                {
                    "symbol": "0700.HK",
                    "timestamp": datetime.now().isoformat(),
                    "open": 100.0,
                    "high": 102.0,
                    "low": 98.0,
                    "close": 101.0,
                    "volume": 1000000
                }
            ]
            
            # 测试模板数据准备
            for agent_type in AgentType:
                template = self.templates.get_template(agent_type)
                if template:
                    # 模拟数据准备
                    input_data = {"market_data": market_data}
                    prompt = self.templates.generate_prompt(agent_type, input_data)
                    
                    if prompt and "港股" in prompt:
                        self.logger.info(f"✓ 代理 {agent_type.value} 数据准备成功")
                    else:
                        self.logger.error(f"✗ 代理 {agent_type.value} 数据准备失败")
            
            self.logger.info("数据准备测试完成")
            return True
            
        except Exception as e:
            self.logger.error(f"数据准备测试失败: {e}")
            return False
    
    async def test_json_parsing(self):
        """测试JSON解析"""
        self.logger.info("测试JSON解析...")
        
        try:
            # 测试响应解析
            test_responses = [
                '{"undervalued_stocks": [{"code": "0700.HK", "pe": 12.5}], "pe_avg": 10.35, "sharpe_contribution": 0.75, "recommendations": ["买入0700.HK"]}',
                '{"sentiment_scores": [0.8, -0.4], "avg_score": 0.2, "sharpe_contribution": 0.4, "recommendations": ["买入高情绪股"]}',
                '{"signals": [1, -1, 1], "rsi_avg": 55.2, "sharpe_contribution": 0.6, "recommendations": ["买入MA上穿"]}'
            ]
            
            for i, response in enumerate(test_responses):
                parsed = self.templates.parse_agent_response(response)
                if parsed and "json_data" in parsed:
                    self.logger.info(f"✓ 响应 {i+1} 解析成功")
                else:
                    self.logger.error(f"✗ 响应 {i+1} 解析失败")
            
            self.logger.info("JSON解析测试完成")
            return True
            
        except Exception as e:
            self.logger.error(f"JSON解析测试失败: {e}")
            return False
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.message_queue:
                await self.message_queue.cleanup()
            self.logger.info("资源清理完成")
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("开始港股Prompt集成测试...")
        print("=" * 60)
        
        tests = [
            ("Prompt模板测试", self.test_prompt_templates),
            ("Prompt引擎测试", self.test_prompt_engine),
            ("代理创建测试", self.test_agent_creation),
            ("代理初始化测试", self.test_agent_initialization),
            ("数据准备测试", self.test_data_preparation),
            ("JSON解析测试", self.test_json_parsing)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n运行 {test_name}...")
            try:
                success = await test_func()
                if success:
                    print(f"✓ {test_name} 通过")
                    passed += 1
                else:
                    print(f"✗ {test_name} 失败")
            except Exception as e:
                print(f"✗ {test_name} 异常: {e}")
        
        print("\n" + "=" * 60)
        print(f"测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有测试通过！港股Prompt代理系统集成成功！")
        else:
            print("❌ 部分测试失败，请检查错误信息")
        
        print("=" * 60)
        
        # 清理资源
        await self.cleanup()
        
        return passed == total


async def main():
    """主函数"""
    test = HKPromptIntegrationTest()
    success = await test.run_all_tests()
    return success


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
