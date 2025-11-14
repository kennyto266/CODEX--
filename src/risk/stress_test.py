"""
压力测试框架

实现历史压力事件、市场冲击场景、波动率跳跃等压力测试功能
支持流动性压力和跨资产相关性压力测试
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator
import json
from pathlib import Path


class StressTestType(str, Enum):
    """压力测试类型"""
    HISTORICAL = "historical"  # 历史事件
    SCENARIO_BASED = "scenario_based"  # 场景分析
    MONTE_CARLO = "monte_carlo"  # 蒙特卡洛
    VOLATILITY_SHOCK = "volatility_shock"  # 波动率冲击
    LIQUIDITY_Stress = "liquidity_stress"  # 流动性压力
    CORRELATION_SHOCK = "correlation_shock"  # 相关性冲击


class HistoricalStressEvent(BaseModel):
    """历史压力事件"""
    name: str = Field(..., description="事件名称")
    date: str = Field(..., description="发生日期")
    description: str = Field(..., description="事件描述")
    market_impact: Dict[str, float] = Field(..., description="市场影响")
    duration_days: int = Field(..., description="持续天数")
    recovery_days: int = Field(..., description="恢复天数")


class MarketShockScenario(BaseModel):
    """市场冲击场景"""
    name: str = Field(..., description="场景名称")
    description: str = Field(..., description="场景描述")
    equity_shock: float = Field(0.0, description="股票市场冲击")
    bond_shock: float = Field(0.0, description="债券市场冲击")
    fx_shock: float = Field(0.0, description="外汇冲击")
    commodity_shock: float = Field(0.0, description="商品冲击")
    interest_rate_shock: float = Field(0.0, description="利率冲击")
    volatility_multiplier: float = Field(1.0, description="波动率倍数")
    duration: int = Field(5, description="持续天数")
    probability: float = Field(0.01, description="发生概率")


class VolatilityShock(BaseModel):
    """波动率跳跃"""
    asset: str = Field(..., description="资产")
    baseline_volatility: float = Field(..., description="基准波动率")
    shock_magnitude: float = Field(..., description="冲击幅度")
    shock_duration: int = Field(..., description="冲击持续天数")
    mean_reversion_rate: float = Field(0.1, description="均值回归速率")


class LiquidityStress(BaseModel):
    """流动性压力"""
    asset: str = Field(..., description="资产")
    normal_bid_ask_spread: float = Field(0.001, description="正常买卖价差")
    stressed_spread: float = Field(0.01, description="压力下价差")
    market_impact_coefficient: float = Field(0.1, description="市场冲击系数")
    volume_reduction: float = Field(0.5, description="成交量减少比例")


class StressTestResult(BaseModel):
    """压力测试结果"""
    scenario_name: str = Field(..., description="场景名称")
    test_type: StressTestType = Field(..., description="测试类型")
    original_portfolio_value: float = Field(..., description="原始组合价值")
    stressed_portfolio_value: float = Field(..., description="压力后组合价值")
    absolute_loss: float = Field(..., description="绝对损失")
    percentage_loss: float = Field(..., description="百分比损失")
    var_impact: float = Field(0.0, description="VaR影响")
    max_drawdown_impact: float = Field(0.0, description="最大回撤影响")
    asset_impacts: Dict[str, float] = Field(..., description="各资产影响")
    survival_probability: float = Field(..., description="生存概率")
    tail_loss: float = Field(..., description="尾部损失")
    calculation_date: datetime = Field(default_factory=datetime.now, description="计算日期")


class StressTestReport(BaseModel):
    """压力测试报告"""
    test_date: datetime = Field(default_factory=datetime.now, description="测试日期")
    portfolio_summary: Dict[str, Any] = Field(..., description="组合摘要")
    scenarios_tested: List[str] = Field(..., description="测试场景")
    results: List[StressTestResult] = Field(..., description="测试结果")
    worst_case_scenario: str = Field(..., description="最坏情况")
    expected_shortfall: float = Field(..., description="期望损失")
    stress_var: float = Field(..., description="压力VaR")
    recommendation: str = Field(..., description="建议")


class StressTestEngine:
    """压力测试引擎"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.stress_test")
        self.stress_events = self._load_historical_events()
        self.scenarios = self._load_scenario_templates()

    def _load_historical_events(self) -> List[HistoricalStressEvent]:
        """加载历史压力事件"""
        events = [
            HistoricalStressEvent(
                name="2008金融危机",
                date="2008-09-15",
                description="雷曼兄弟破产引发全球金融危机",
                market_impact={
                    "equity": -0.45,
                    "credit_spread": 3.5,
                    "vix": 2.5,
                    "usd_index": 0.15
                },
                duration_days=30,
                recovery_days=365
            ),
            HistoricalStressEvent(
                name="2011欧债危机",
                date="2011-08-05",
                description="标普下调美国主权信用评级",
                market_impact={
                    "equity": -0.18,
                    "credit_spread": 1.2,
                    "vix": 1.8,
                    "treasury_yield": -0.5
                },
                duration_days=20,
                recovery_days=180
            ),
            HistoricalStressEvent(
                name="2020 COVID-19",
                date="2020-03-11",
                description="WHO宣布COVID-19大流行",
                market_impact={
                    "equity": -0.35,
                    "credit_spread": 2.0,
                    "vix": 3.0,
                    "gold": 0.12
                },
                duration_days=45,
                recovery_days=150
            ),
            HistoricalStressEvent(
                name="2022美联储加息",
                date="2022-03-16",
                description="美联储开始激进加息周期",
                market_impact={
                    "equity": -0.12,
                    "treasury_yield": 0.75,
                    "credit_spread": 0.8,
                    "usd_index": 0.08
                },
                duration_days=60,
                recovery_days=90
            )
        ]
        return events

    def _load_scenario_templates(self) -> List[MarketShockScenario]:
        """加载场景模板"""
        scenarios = [
            MarketShockScenario(
                name="温和衰退",
                description="经济增长放缓但未陷入衰退",
                equity_shock=-0.15,
                bond_shock=0.05,
                fx_shock=0.02,
                volatility_multiplier=1.5,
                duration=30,
                probability=0.15
            ),
            MarketShockScenario(
                name="严重衰退",
                description="经济衰退和股市大幅下跌",
                equity_shock=-0.30,
                bond_shock=0.08,
                fx_shock=-0.05,
                commodity_shock=-0.20,
                volatility_multiplier=2.0,
                duration=60,
                probability=0.05
            ),
            MarketShockScenario(
                name="滞胀",
                description="高通胀和低增长并存",
                equity_shock=-0.20,
                bond_shock=-0.10,
                interest_rate_shock=1.0,
                commodity_shock=0.15,
                volatility_multiplier=2.5,
                duration=90,
                probability=0.03
            ),
            MarketShockScenario(
                name="地缘政治危机",
                description="重大地缘政治冲突",
                equity_shock=-0.25,
                bond_shock=0.02,
                fx_shock=0.10,
                commodity_shock=0.30,
                interest_rate_shock=0.50,
                volatility_multiplier=2.2,
                duration=45,
                probability=0.02
            ),
            MarketShockScenario(
                name="技术泡沫破裂",
                description="科技股泡沫破裂",
                equity_shock=-0.35,
                bond_shock=0.03,
                fx_shock=0.00,
                volatility_multiplier=2.8,
                duration=90,
                probability=0.04
            )
        ]
        return scenarios

    async def run_historical_stress_test(
        self,
        portfolio_holdings: Dict[str, float],
        prices: Dict[str, float],
        event: HistoricalStressEvent
    ) -> StressTestResult:
        """运行历史压力事件测试"""
        try:
            self.logger.info(f"Running historical stress test: {event.name}")

            original_value = sum(
                holding * prices.get(symbol, 0)
                for symbol, holding in portfolio_holdings.items()
            )

            # 应用历史冲击
            stressed_prices = {}
            for symbol, holding in portfolio_holdings.items():
                if symbol in event.market_impact:
                    shock = event.market_impact[symbol]
                    stressed_price = prices[symbol] * (1 + shock)
                    stressed_prices[symbol] = stressed_price
                else:
                    # 假设同类资产的平均冲击
                    avg_shock = np.mean(list(event.market_impact.values()))
                    stressed_price = prices[symbol] * (1 + avg_shock)
                    stressed_prices[symbol] = stressed_price

            stressed_value = sum(
                holding * stressed_prices.get(symbol, 0)
                for symbol, holding in portfolio_holdings.items()
            )

            # 计算损失
            absolute_loss = original_value - stressed_value
            percentage_loss = absolute_loss / original_value if original_value > 0 else 0

            # 资产影响明细
            asset_impacts = {}
            for symbol in portfolio_holdings.keys():
                original_asset_value = portfolio_holdings[symbol] * prices[symbol]
                stressed_asset_value = portfolio_holdings[symbol] * stressed_prices.get(symbol, prices[symbol])
                asset_impact = (stressed_asset_value - original_asset_value) / original_asset_value
                asset_impacts[symbol] = asset_impact

            # 生存概率 (基于历史恢复率)
            survival_probability = max(0, 1 - event.duration_days / 365)

            result = StressTestResult(
                scenario_name=event.name,
                test_type=StressTestType.HISTORICAL,
                original_portfolio_value=original_value,
                stressed_portfolio_value=stressed_value,
                absolute_loss=absolute_loss,
                percentage_loss=percentage_loss,
                asset_impacts=asset_impacts,
                survival_probability=survival_probability,
                tail_loss=absolute_loss
            )

            self.logger.info(f"Historical stress test completed: {percentage_loss:.2%} loss")
            return result

        except Exception as e:
            self.logger.error(f"Error running historical stress test: {e}")
            raise

    async def run_scenario_based_test(
        self,
        portfolio_holdings: Dict[str, float],
        prices: Dict[str, float],
        scenario: MarketShockScenario
    ) -> StressTestResult:
        """运行基于场景的压力测试"""
        try:
            self.logger.info(f"Running scenario test: {scenario.name}")

            original_value = sum(
                holding * prices.get(symbol, 0)
                for symbol, holding in portfolio_holdings.items()
            )

            # 应用场景冲击
            stressed_prices = {}
            for symbol, holding in portfolio_holdings.items():
                # 简化的资产分类映射
                asset_class = self._classify_asset(symbol)
                shock = 0.0

                if asset_class == "equity":
                    shock = scenario.equity_shock
                elif asset_class == "bond":
                    shock = scenario.bond_shock
                elif asset_class == "fx":
                    shock = scenario.fx_shock
                elif asset_class == "commodity":
                    shock = scenario.commodity_shock

                # 添加随机冲击 (模拟市场不确定性)
                random_shock = np.random.normal(0, abs(shock) * 0.1)
                total_shock = shock + random_shock

                stressed_price = prices[symbol] * (1 + total_shock)
                stressed_prices[symbol] = stressed_price

            stressed_value = sum(
                holding * stressed_prices.get(symbol, 0)
                for symbol, holding in portfolio_holdings.items()
            )

            # 计算损失
            absolute_loss = original_value - stressed_value
            percentage_loss = absolute_loss / original_value if original_value > 0 else 0

            # 资产影响
            asset_impacts = {}
            for symbol in portfolio_holdings.keys():
                original_asset_value = portfolio_holdings[symbol] * prices[symbol]
                stressed_asset_value = portfolio_holdings[symbol] * stressed_prices.get(symbol, prices[symbol])
                asset_impact = (stressed_asset_value - original_asset_value) / original_asset_value
                asset_impacts[symbol] = asset_impact

            # VaR影响
            var_impact = abs(percentage_loss) * 1.2  # 简化计算

            # 生存概率
            survival_probability = max(0, 1 - scenario.probability)

            result = StressTestResult(
                scenario_name=scenario.name,
                test_type=StressTestType.SCENARIO_BASED,
                original_portfolio_value=original_value,
                stressed_portfolio_value=stressed_value,
                absolute_loss=absolute_loss,
                percentage_loss=percentage_loss,
                var_impact=var_impact,
                asset_impacts=asset_impacts,
                survival_probability=survival_probability,
                tail_loss=absolute_loss
            )

            self.logger.info(f"Scenario stress test completed: {percentage_loss:.2%} loss")
            return result

        except Exception as e:
            self.logger.error(f"Error running scenario-based stress test: {e}")
            raise

    def _classify_asset(self, symbol: str) -> str:
        """资产分类"""
        # 简化的资产分类逻辑
        if symbol.endswith('.HK'):
            return 'equity'
        elif 'BOND' in symbol.upper() or 'TREASURY' in symbol.upper():
            return 'bond'
        elif 'USD' in symbol.upper() or 'EUR' in symbol.upper():
            return 'fx'
        elif 'GOLD' in symbol.upper() or 'OIL' in symbol.upper():
            return 'commodity'
        else:
            return 'equity'  # 默认股票

    async def run_volatility_shock_test(
        self,
        returns_data: Dict[str, pd.Series],
        weights: Dict[str, float],
        shock_scenarios: List[VolatilityShock]
    ) -> StressTestResult:
        """运行波动率冲击测试"""
        try:
            self.logger.info("Running volatility shock test")

            portfolio_value = 1000000  # 假设100万

            # 正常波动率下的组合波动
            normal_volatility = np.sqrt(sum(
                (weights[symbol] ** 2) * (returns_data[symbol].std() ** 2)
                for symbol in returns_data.keys()
            ))

            stressed_volatility = 0.0
            total_weighted_shock = 0.0

            for shock in shock_scenarios:
                if shock.asset in returns_data:
                    # 新的波动率
                    new_vol = shock.baseline_volatility * (1 + shock.shock_magnitude)
                    stressed_volatility += (weights[shock.asset] ** 2) * (new_vol ** 2)
                    total_weighted_shock += weights[shock.asset]

            stressed_volatility = np.sqrt(stressed_volatility)

            # 计算波动率冲击影响
            vol_ratio = stressed_volatility / normal_volatility if normal_volatility > 0 else 1
            potential_loss = portfolio_value * 0.1 * (vol_ratio - 1)  # 简化

            result = StressTestResult(
                scenario_name="Volatility Shock",
                test_type=StressTestType.VOLATILITY_SHOCK,
                original_portfolio_value=portfolio_value,
                stressed_portfolio_value=portfolio_value - potential_loss,
                absolute_loss=potential_loss,
                percentage_loss=potential_loss / portfolio_value,
                var_impact=potential_loss / portfolio_value,
                asset_impacts={shock.asset: shock.shock_magnitude for shock in shock_scenarios},
                survival_probability=max(0, 1 - vol_ratio / 2),
                tail_loss=potential_loss
            )

            return result

        except Exception as e:
            self.logger.error(f"Error running volatility shock test: {e}")
            raise

    async def run_liquidity_stress_test(
        self,
        portfolio_holdings: Dict[str, float],
        prices: Dict[str, float],
        liquidity_scenarios: List[LiquidityStress]
    ) -> StressTestResult:
        """运行流动性压力测试"""
        try:
            self.logger.info("Running liquidity stress test")

            original_value = sum(
                holding * prices.get(symbol, 0)
                for symbol, holding in portfolio_holdings.items()
            )

            total_liquidation_cost = 0.0

            for liquidity in liquidity_scenarios:
                if liquidity.asset in portfolio_holdings:
                    holding_value = portfolio_holdings[liquidity.asset] * prices[liquidity.asset]

                    # 计算流动性成本
                    spread_cost = holding_value * (liquidity.stressed_spread / 2)
                    market_impact = holding_value * liquidity.market_impact_coefficient * (1 - liquidity.volume_reduction)
                    volume_cost = holding_value * 0.05 * (1 - liquidity.volume_reduction)

                    total_liquidation_cost += spread_cost + market_impact + volume_cost

            stressed_value = original_value - total_liquidation_cost
            absolute_loss = total_liquidation_cost
            percentage_loss = total_liquidation_cost / original_value

            result = StressTestResult(
                scenario_name="Liquidity Stress",
                test_type=StressTestType.LIQUIDITY_Stress,
                original_portfolio_value=original_value,
                stressed_portfolio_value=stressed_value,
                absolute_loss=absolute_loss,
                percentage_loss=percentage_loss,
                var_impact=0.0,
                asset_impacts={
                    liq.asset: -(liq.stressed_spread + liq.market_impact_coefficient)
                    for liq in liquidity_scenarios
                },
                survival_probability=max(0, 1 - percentage_loss * 2),
                tail_loss=absolute_loss
            )

            return result

        except Exception as e:
            self.logger.error(f"Error running liquidity stress test: {e}")
            raise

    async def run_comprehensive_stress_test(
        self,
        portfolio_holdings: Dict[str, float],
        prices: Dict[str, float],
        returns_data: Optional[Dict[str, pd.Series]] = None
    ) -> StressTestReport:
        """运行综合压力测试"""
        try:
            self.logger.info("Running comprehensive stress test")

            portfolio_value = sum(
                holding * prices.get(symbol, 0)
                for symbol, holding in portfolio_holdings.items()
            )

            # 测试多个场景
            all_results = []

            # 1. 历史事件测试 (测试最严重的几个)
            historical_events = [e for e in self.stress_events if e.duration_days > 30]
            for event in historical_events:
                result = await self.run_historical_stress_test(portfolio_holdings, prices, event)
                all_results.append(result)

            # 2. 场景分析测试
            for scenario in self.scenarios:
                result = await self.run_scenario_based_test(portfolio_holdings, prices, scenario)
                all_results.append(result)

            # 3. 波动率冲击测试
            if returns_data:
                vol_shocks = [
                    VolatilityShock(
                        asset=symbol,
                        baseline_volatility=returns_data[symbol].std(),
                        shock_magnitude=1.0,
                        shock_duration=30
                    )
                    for symbol in returns_data.keys()
                ]
                result = await self.run_volatility_shock_test(returns_data, None, vol_shocks)
                all_results.append(result)

            # 4. 流动性压力测试
            liquidity_scenarios = [
                LiquidityStress(
                    asset=symbol,
                    normal_bid_ask_spread=0.001,
                    stressed_spread=0.05,
                    market_impact_coefficient=0.1,
                    volume_reduction=0.7
                )
                for symbol in portfolio_holdings.keys()
            ]
            result = await self.run_liquidity_stress_test(portfolio_holdings, prices, liquidity_scenarios)
            all_results.append(result)

            # 找到最坏情况
            worst_result = max(all_results, key=lambda x: x.percentage_loss)

            # 计算期望损失
            expected_shortfall = np.mean([
                result.absolute_loss for result in all_results
                if result.percentage_loss > np.percentile([r.percentage_loss for r in all_results], 90)
            ])

            # 计算压力VaR
            stress_var = np.percentile([r.percentage_loss for r in all_results], 95)

            # 生成建议
            recommendation = self._generate_recommendation(worst_result, portfolio_value)

            report = StressTestReport(
                portfolio_summary={
                    "total_value": portfolio_value,
                    "number_of_positions": len(portfolio_holdings),
                    "largest_position": max(portfolio_holdings.values()) / portfolio_value if portfolio_value > 0 else 0
                },
                scenarios_tested=[r.scenario_name for r in all_results],
                results=all_results,
                worst_case_scenario=worst_result.scenario_name,
                expected_shortfall=expected_shortfall,
                stress_var=stress_var,
                recommendation=recommendation
            )

            self.logger.info(f"Comprehensive stress test completed. Worst case: {worst_result.percentage_loss:.2%}")
            return report

        except Exception as e:
            self.logger.error(f"Error running comprehensive stress test: {e}")
            raise

    def _generate_recommendation(
        self,
        worst_result: StressTestResult,
        portfolio_value: float
    ) -> str:
        """生成压力测试建议"""
        loss = worst_result.percentage_loss

        if loss < 0.05:
            return "压力测试显示组合风险可控，建议维持当前配置。"
        elif loss < 0.10:
            return "建议适度增加防御性资产配置，降低组合波动性。"
        elif loss < 0.20:
            return "建议显著降低风险资产比例，增加债券和现金配置。"
        else:
            return "当前组合在高压力情景下损失过大，建议立即减仓并重新平衡。"

    async def export_stress_test_report(
        self,
        report: StressTestReport,
        output_path: str
    ) -> None:
        """导出压力测试报告"""
        try:
            report_dict = report.model_dump()
            report_dict['test_date'] = report.test_date.isoformat()

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"Stress test report exported to {output_path}")

        except Exception as e:
            self.logger.error(f"Error exporting stress test report: {e}")
            raise
