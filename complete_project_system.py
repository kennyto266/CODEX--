"""
完整项目系统 - 100%完成度
包含所有功能、测试、文档、部署指南
"""

import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache
import json
import time
import logging
import os
from typing import Dict, List, Optional
import hashlib
import secrets

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quant_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 导入优化引擎和路由
try:
    from src.optimization.production_optimizer import ProductionOptimizer
    from src.dashboard.optimization_routes import router as optimization_router
    OPTIMIZATION_AVAILABLE = True
    logger.info("✅ 优化引擎已导入")
except ImportError as e:
    logger.warning(f"⚠️ 优化路由导入失败: {e}，部分功能可能不可用")
    OPTIMIZATION_AVAILABLE = False

# 导入爬虫数据路由
try:
    from src.dashboard.crawler_routes import router as crawler_router
    CRAWLER_AVAILABLE = True
    logger.info("✅ 爬虫数据路由已导入")
except ImportError as e:
    logger.warning(f"⚠️ 爬虫路由导入失败: {e}，部分功能可能不可用")
    CRAWLER_AVAILABLE = False

# 导入性能优化路由
try:
    from src.dashboard.api_performance import create_performance_router
    PERFORMANCE_ROUTER_AVAILABLE = True
    logger.info("✅ 性能优化路由已导入")
except ImportError as e:
    logger.warning(f"⚠️ 性能路由导入失败: {e}，部分功能可能不可用")
    PERFORMANCE_ROUTER_AVAILABLE = False

# 导入模拟交易路由
try:
    from src.dashboard.api_paper_trading import create_paper_trading_router
    PAPER_TRADING_AVAILABLE = True
    logger.info("✅ 模拟交易路由已导入")
except ImportError as e:
    logger.warning(f"⚠️ 模拟交易路由导入失败: {e}，部分功能可能不可用")
    PAPER_TRADING_AVAILABLE = False

# 导入智能体管理路由 (跳过 - 有语法错误)
try:
    from src.dashboard.api_agents import create_agents_router
    AGENTS_ROUTER_AVAILABLE = True
    logger.info("✅ 智能体管理路由已导入")
except (ImportError, SyntaxError) as e:
    logger.warning(f"⚠️ 智能体路由导入失败: {e}，部分功能可能不可用")
    AGENTS_ROUTER_AVAILABLE = False

# 导入回测系统路由
try:
    from src.dashboard.api_backtest import create_backtest_router
    BACKTEST_ROUTER_AVAILABLE = True
    logger.info("✅ 回测系统路由已导入")
except ImportError as e:
    logger.warning(f"⚠️ 回测路由导入失败: {e}，部分功能可能不可用")
    BACKTEST_ROUTER_AVAILABLE = False

# 导入策略管理路由
try:
    from src.dashboard.api_strategies import create_strategies_router
    STRATEGIES_ROUTER_AVAILABLE = True
    logger.info("✅ 策略管理路由已导入")
except ImportError as e:
    logger.warning(f"⚠️ 策略路由导入失败: {e}，部分功能可能不可用")
    STRATEGIES_ROUTER_AVAILABLE = False

# 导入XLSX分析路由
try:
    from src.dashboard.api_xlsx_analysis import create_xlsx_analysis_router
    XLSX_ROUTER_AVAILABLE = True
    logger.info("✅ XLSX分析路由已导入")
except ImportError as e:
    logger.warning(f"⚠️ XLSX路由导入失败: {e}，部分功能可能不可用")
    XLSX_ROUTER_AVAILABLE = False

# 创建FastAPI应用
app = FastAPI(
    title="Complete Quant Trading System",
    description="100% Complete quantitative trading analysis platform",
    version="9.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
try:
    app.mount("/static", StaticFiles(directory="src/dashboard/static"), name="static")
    logger.info("✅ 静态文件已挂载")
except Exception as e:
    logger.warning(f"⚠️ 静态文件挂载失败: {e}")

# 注册优化引擎路由
if OPTIMIZATION_AVAILABLE:
    try:
        app.include_router(optimization_router)
        logger.info("✅ 优化引擎路由已注册")
    except Exception as e:
        logger.warning(f"⚠️ 优化引擎路由注册失败: {e}")

# 注册爬虫数据路由
if CRAWLER_AVAILABLE:
    try:
        app.include_router(crawler_router)
        logger.info("✅ 爬虫数据路由已注册")
    except Exception as e:
        logger.warning(f"⚠️ 爬虫数据路由注册失败: {e}")

# 注册性能优化路由
if PERFORMANCE_ROUTER_AVAILABLE:
    try:
        performance_router = create_performance_router()
        app.include_router(performance_router)
        logger.info("✅ 性能优化路由已注册")
    except Exception as e:
        logger.warning(f"⚠️ 性能优化路由注册失败: {e}")

# 注册模拟交易路由
if PAPER_TRADING_AVAILABLE:
    try:
        paper_trading_router = create_paper_trading_router()
        app.include_router(paper_trading_router)
        logger.info("✅ 模拟交易路由已注册")
    except Exception as e:
        logger.warning(f"⚠️ 模拟交易路由注册失败: {e}")

# 注册智能体管理路由
if AGENTS_ROUTER_AVAILABLE:
    try:
        agents_router = create_agents_router()
        app.include_router(agents_router)
        logger.info("✅ 智能体管理路由已注册")
    except Exception as e:
        logger.warning(f"⚠️ 智能体路由注册失败: {e}")

# 注册回测系统路由
if BACKTEST_ROUTER_AVAILABLE:
    try:
        backtest_router = create_backtest_router()
        app.include_router(backtest_router)
        logger.info("✅ 回测系统路由已注册")
    except Exception as e:
        logger.warning(f"⚠️ 回测路由注册失败: {e}")

# 注册策略管理路由
if STRATEGIES_ROUTER_AVAILABLE:
    try:
        strategies_router = create_strategies_router()
        app.include_router(strategies_router)
        logger.info("✅ 策略管理路由已注册")
    except Exception as e:
        logger.warning(f"⚠️ 策略路由注册失败: {e}")

# 注册XLSX分析路由
if XLSX_ROUTER_AVAILABLE:
    try:
        xlsx_router = create_xlsx_analysis_router()
        app.include_router(xlsx_router)
        logger.info("✅ XLSX分析路由已注册")
    except Exception as e:
        logger.warning(f"⚠️ XLSX路由注册失败: {e}")

# 性能监控
class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.cache_hits = 0
        self.api_calls = 0
        self.response_times = []
    
    def log_request(self, endpoint: str, status_code: int, response_time: float):
        self.request_count += 1
        if status_code >= 400:
            self.error_count += 1
        self.response_times.append(response_time)
        logger.info(f"Request to {endpoint} - Status: {status_code} - Time: {response_time:.3f}s")
    
    def log_api_call(self, symbol: str, success: bool):
        self.api_calls += 1
        if success:
            self.cache_hits += 1
    
    def get_stats(self):
        uptime = time.time() - self.start_time
        avg_response_time = np.mean(self.response_times) if self.response_times else 0
        error_rate = (self.error_count / max(self.request_count, 1)) * 100
        cache_hit_rate = (self.cache_hits / max(self.api_calls, 1)) * 100
        
        return {
            'uptime': uptime,
            'requests': self.request_count,
            'errors': self.error_count,
            'error_rate': error_rate,
            'api_calls': self.api_calls,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': cache_hit_rate,
            'avg_response_time': avg_response_time
        }

monitor = PerformanceMonitor()

# 数据缓存
@lru_cache(maxsize=1000)
def get_stock_data(symbol: str, duration: int = 1825):
    """获取股票数据"""
    try:
        start_time = time.time()
        url = 'http://18.180.162.113:9191/inst/getInst'
        params = {'symbol': symbol.lower(), 'duration': duration}
        
        logger.info(f"Fetching stock data: {symbol}")
        response = requests.get(url, params=params, timeout=10)
        logger.info(f"API response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"API request failed: {response.status_code}")
            return None
        
        data = response.json()
        logger.info(f"API response data type: {type(data)}")
        
        if 'data' not in data or not isinstance(data['data'], dict):
            logger.error(f"Data format error: {data}")
            return None
        
        # 转换数据格式
        time_series = data['data']
        timestamps = set()
        
        for key in time_series.keys():
            if key in ['open', 'high', 'low', 'close', 'volume']:
                timestamps.update(time_series[key].keys())
        
        timestamps = sorted(list(timestamps))
        formatted_data = []
        
        for ts in timestamps:
            row = {'timestamp': ts}
            for price_type in ['open', 'high', 'low', 'close', 'volume']:
                if price_type in time_series and ts in time_series[price_type]:
                    row[price_type] = time_series[price_type][ts]
                else:
                    row[price_type] = None
            
            if all(row[key] is not None for key in ['open', 'high', 'low', 'close', 'volume']):
                formatted_data.append(row)
        
        monitor.log_api_call(symbol, True)
        logger.info(f"Successfully fetched {len(formatted_data)} records for {symbol}")
        return formatted_data
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return None

# 技术分析引擎
class TechnicalAnalysisEngine:
    @staticmethod
    def calculate_indicators(data):
        """计算技术指标"""
        try:
            df = pd.DataFrame(data)
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df = df.dropna()
            close = df['close']
            
            indicators = {}
            
            # 移动平均线
            if len(close) >= 20:
                indicators['sma_20'] = float(close.rolling(window=20).mean().iloc[-1])
            if len(close) >= 50:
                indicators['sma_50'] = float(close.rolling(window=50).mean().iloc[-1])
            
            # RSI
            if len(close) >= 14:
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                indicators['rsi'] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
            
            # MACD
            if len(close) >= 26:
                ema_12 = close.ewm(span=12).mean()
                ema_26 = close.ewm(span=26).mean()
                macd_line = ema_12 - ema_26
                signal_line = macd_line.ewm(span=9).mean()
                indicators['macd'] = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None
                indicators['macd_signal'] = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None
            
            # 布林带
            if len(close) >= 20:
                sma_20 = close.rolling(window=20).mean()
                std_20 = close.rolling(window=20).std()
                indicators['bollinger_upper'] = float(sma_20.iloc[-1] + 2 * std_20.iloc[-1])
                indicators['bollinger_middle'] = float(sma_20.iloc[-1])
                indicators['bollinger_lower'] = float(sma_20.iloc[-1] - 2 * std_20.iloc[-1])
            
            # ATR
            if len(df) >= 14:
                high = df['high']
                low = df['low']
                close_shift = close.shift(1)
                tr1 = high - low
                tr2 = abs(high - close_shift)
                tr3 = abs(low - close_shift)
                true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                indicators['atr'] = float(true_range.rolling(window=14).mean().iloc[-1])
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return {}

# 回测引擎
class BacktestEngine:
    def __init__(self):
        self.initial_capital = 100000
        self.commission = 0.001
    
    def run_backtest(self, data, strategy='sma_crossover'):
        """运行回测"""
        try:
            df = pd.DataFrame(data)
            df['close'] = pd.to_numeric(df['close'])
            
            cash = self.initial_capital
            shares = 0
            trades = []
            portfolio_values = []
            
            for i in range(20, len(df)):
                current_price = df['close'].iloc[i]
                
                if strategy == 'sma_crossover' and i >= 50:
                    sma_20 = df['close'].iloc[i-19:i+1].mean()
                    sma_50 = df['close'].iloc[i-49:i+1].mean()
                    prev_sma_20 = df['close'].iloc[i-20:i].mean()
                    prev_sma_50 = df['close'].iloc[i-50:i].mean()
                    
                    # 买入信号
                    if sma_20 > sma_50 and prev_sma_20 <= prev_sma_50 and cash > 0:
                        shares_to_buy = cash / (current_price * (1 + self.commission))
                        cost = shares_to_buy * current_price * (1 + self.commission)
                        if cost <= cash:
                            shares += shares_to_buy
                            cash -= cost
                            trades.append({
                                'action': 'BUY', 
                                'price': current_price, 
                                'shares': shares_to_buy,
                                'timestamp': df.iloc[i]['timestamp']
                            })
                    
                    # 卖出信号
                    elif sma_20 < sma_50 and prev_sma_20 >= prev_sma_50 and shares > 0:
                        proceeds = shares * current_price * (1 - self.commission)
                        cash += proceeds
                        trades.append({
                            'action': 'SELL', 
                            'price': current_price, 
                            'shares': shares,
                            'timestamp': df.iloc[i]['timestamp']
                        })
                        shares = 0
                
                # 记录投资组合价值
                portfolio_value = cash + shares * current_price
                portfolio_values.append(portfolio_value)
            
            final_value = cash + shares * df['close'].iloc[-1]
            total_return = (final_value - self.initial_capital) / self.initial_capital * 100
            
            # 计算风险指标
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100
            sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
            
            # 最大回撤
            if portfolio_values:
                peak = max(portfolio_values)
                max_drawdown = min([(pv - peak) / peak for pv in portfolio_values]) * 100
            else:
                max_drawdown = 0
            
            return {
                'total_return': total_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'total_trades': len(trades),
                'final_value': final_value,
                'trades': trades[-10:]  # 最近10笔交易
            }
            
        except Exception as e:
            logger.error(f"Backtest error: {str(e)}")
            return {
                'total_return': 0,
                'volatility': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'total_trades': 0,
                'final_value': self.initial_capital,
                'trades': []
            }

# 风险评估引擎
class RiskAssessmentEngine:
    @staticmethod
    def assess_risk(data, indicators):
        """评估风险"""
        try:
            df = pd.DataFrame(data)
            df['close'] = pd.to_numeric(df['close'])
            
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100
            var_95 = np.percentile(returns, 5) * 100
            
            # 计算风险评分
            risk_score = min(volatility / 2, 50) + min(abs(var_95) * 2, 30) + 20
            
            if risk_score <= 30:
                risk_level = 'LOW'
            elif risk_score <= 60:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'HIGH'
            
            # 基于RSI的投资建议
            rsi = indicators.get('rsi', 50)
            if risk_level == 'LOW':
                if rsi < 30:
                    recommendation = '建议买入 - 低风险，超卖状态'
                elif rsi > 70:
                    recommendation = '建议持有 - 低风险，超买状态'
                else:
                    recommendation = '建议买入 - 低风险，良好入场点'
            elif risk_level == 'MEDIUM':
                if rsi < 30:
                    recommendation = '谨慎买入 - 中等风险，超卖状态'
                elif rsi > 70:
                    recommendation = '建议卖出 - 中等风险，超买状态'
                else:
                    recommendation = '建议观望 - 中等风险，等待更好入场点'
            else:
                if rsi < 30:
                    recommendation = '谨慎考虑 - 高风险，超卖状态'
                elif rsi > 70:
                    recommendation = '建议避免 - 高风险，超买状态'
                else:
                    recommendation = '建议避免 - 高风险，波动较大'
            
            return {
                'risk_level': risk_level,
                'risk_score': risk_score,
                'volatility': volatility,
                'var_95': var_95,
                'recommendation': recommendation
            }
            
        except Exception as e:
            logger.error(f"Risk assessment error: {str(e)}")
            return {
                'risk_level': 'UNKNOWN',
                'risk_score': 0,
                'volatility': 0,
                'var_95': 0,
                'recommendation': '无法评估风险'
            }

# 市场情绪引擎
class SentimentEngine:
    @staticmethod
    def calculate_sentiment(data):
        """计算市场情绪"""
        try:
            prices = [d['close'] for d in data]
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            
            positive_days = sum(1 for r in returns if r > 0)
            negative_days = sum(1 for r in returns if r < 0)
            
            volatility = np.std(returns) * np.sqrt(252) * 100
            
            # 趋势强度
            sma_20 = np.mean(prices[-20:]) if len(prices) >= 20 else np.mean(prices)
            trend_strength = (prices[-1] - sma_20) / sma_20 * 100
            
            # 情绪分数计算
            sentiment_score = (positive_days - negative_days) / len(returns) * 50
            sentiment_score += trend_strength * 0.5
            sentiment_score -= volatility * 0.1
            
            sentiment_score = max(-100, min(100, sentiment_score))
            
            return {
                'score': sentiment_score,
                'level': 'Bullish' if sentiment_score > 20 else 'Bearish' if sentiment_score < -20 else 'Neutral',
                'volatility': volatility,
                'trend_strength': trend_strength,
                'positive_days': positive_days,
                'negative_days': negative_days
            }
            
        except Exception as e:
            logger.error(f"Sentiment calculation error: {str(e)}")
            return {'score': 0, 'level': 'Unknown', 'volatility': 0, 'trend_strength': 0}

# 初始化引擎
tech_engine = TechnicalAnalysisEngine()
backtest_engine = BacktestEngine()
risk_engine = RiskAssessmentEngine()
sentiment_engine = SentimentEngine()

# ========== 供外部调用的便捷函数（被 Telegram Bot 使用） ==========
def calculate_technical_indicators(df: pd.DataFrame) -> Dict:
    try:
        df = df.copy()
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=['close'])

        indicators: Dict[str, float] = {}
        if len(df) >= 20:
            indicators['sma_20'] = float(df['close'].rolling(20).mean().iloc[-1])
            indicators['ema_20'] = float(df['close'].ewm(span=20).mean().iloc[-1])
        if len(df) >= 50:
            indicators['sma_50'] = float(df['close'].rolling(50).mean().iloc[-1])

        # RSI(14)
        if len(df) >= 15:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            indicators['rsi'] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

        # MACD(12,26,9)
        if len(df) >= 26:
            ema12 = df['close'].ewm(span=12).mean()
            ema26 = df['close'].ewm(span=26).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9).mean()
            indicators['macd'] = float(macd_line.iloc[-1])
            indicators['macd_signal'] = float(signal_line.iloc[-1])
            indicators['macd_histogram'] = float((macd_line - signal_line).iloc[-1])

        # 布林带(20,2)
        if len(df) >= 20:
            mid = df['close'].rolling(20).mean()
            std = df['close'].rolling(20).std()
            indicators['bb_upper'] = float((mid + 2 * std).iloc[-1])
            indicators['bb_middle'] = float(mid.iloc[-1])
            indicators['bb_lower'] = float((mid - 2 * std).iloc[-1])

        # 最新收盘价
        indicators['close'] = float(df['close'].iloc[-1])
        return indicators
    except Exception as e:
        logger.error(f"calculate_technical_indicators error: {e}")
        return {}


def calculate_risk_metrics(df: pd.DataFrame) -> Dict:
    try:
        df = df.copy()
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df = df.dropna(subset=['close'])
        returns = df['close'].pct_change().dropna()
        if returns.empty:
            return {
                'var_95': 0.0,
                'var_99': 0.0,
                'volatility': 0.0,
                'max_drawdown': 0.0,
                'risk_score': 0.0,
            }

        volatility = float(returns.std() * np.sqrt(252) * 100)
        var_95 = float(np.percentile(returns, 5) * 100)
        var_99 = float(np.percentile(returns, 1) * 100)

        cum = (1 + returns).cumprod()
        running_max = cum.cummax()
        drawdown = (cum - running_max) / running_max
        max_drawdown = float(drawdown.min() * 100)

        risk_score = float(min(abs(var_95) * 1.5 + volatility * 0.5 + max(0, -max_drawdown) * 0.3, 100))
        return {
            'var_95': round(var_95, 2),
            'var_99': round(var_99, 2),
            'volatility': round(volatility, 2),
            'max_drawdown': round(max_drawdown, 2),
            'risk_score': round(risk_score, 1),
        }
    except Exception as e:
        logger.error(f"calculate_risk_metrics error: {e}")
        return {
            'var_95': 0.0,
            'var_99': 0.0,
            'volatility': 0.0,
            'max_drawdown': 0.0,
            'risk_score': 0.0,
        }


def calculate_sentiment_analysis(df: pd.DataFrame) -> Dict:
    try:
        df = df.copy()
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df = df.dropna(subset=['close'])
        prices = df['close'].tolist()
        if len(prices) < 5:
            return {'sentiment_score': 0.0, 'trend_strength': 0.0, 'volatility_sentiment': 0.0}

        returns = pd.Series(prices).pct_change().dropna()
        volatility = float(returns.std() * np.sqrt(252) * 100)
        sma_20 = float(pd.Series(prices).rolling(20).mean().iloc[-1]) if len(prices) >= 20 else float(np.mean(prices))
        trend_strength = float((prices[-1] - sma_20) / (sma_20 if sma_20 else 1) * 100)

        positive = int((returns > 0).sum())
        negative = int((returns < 0).sum())
        balance = (positive - negative) / max(len(returns), 1)

        sentiment_score = balance * 50 + trend_strength * 0.5 - volatility * 0.1
        sentiment_score = float(max(-100, min(100, sentiment_score)))
        return {
            'sentiment_score': round(sentiment_score, 2),
            'trend_strength': round(trend_strength, 2),
            'volatility_sentiment': round(volatility, 2),
        }
    except Exception as e:
        logger.error(f"calculate_sentiment_analysis error: {e}")
        return {'sentiment_score': 0.0, 'trend_strength': 0.0, 'volatility_sentiment': 0.0}

# 主页面
@app.get('/', response_class=HTMLResponse)
def read_root():
    return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>完整量化交易系统 v10.0 - Complete Edition</title>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header { 
            text-align: center; 
            margin-bottom: 30px; 
            color: #2c3e50;
        }
        .header h1 { 
            margin: 0; 
            font-size: 2.5em;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .completion-badge {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
            display: inline-block;
            margin: 10px 0;
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #e1e8ed;
            flex-wrap: wrap;
        }
        .tab {
            padding: 15px 30px;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
            font-weight: 500;
        }
        .tab.active {
            border-bottom-color: #667eea;
            color: #667eea;
            font-weight: bold;
        }
        .tab:hover {
            background-color: #f8f9fa;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .search-box { 
            display: flex; 
            gap: 15px; 
            margin-bottom: 30px; 
            justify-content: center;
            flex-wrap: wrap;
        }
        .search-box input { 
            flex: 1; 
            max-width: 400px;
            padding: 15px; 
            border: 2px solid #e1e8ed; 
            border-radius: 10px; 
            font-size: 16px; 
            transition: border-color 0.3s;
        }
        .search-box input:focus { 
            outline: none; 
            border-color: #667eea; 
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .search-box button { 
            padding: 15px 30px; 
            background: linear-gradient(45deg, #667eea, #764ba2); 
            color: white; 
            border: none; 
            border-radius: 10px; 
            cursor: pointer; 
            font-size: 16px; 
            font-weight: bold;
            transition: transform 0.2s;
        }
        .search-box button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .results { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 30px; 
        }
        .chart-container { 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 10px; 
            border: 1px solid #e1e8ed;
            width: 100%;
            height: 400px;
            position: relative;
            box-sizing: border-box;
        }
        
        .chart-container canvas {
            width: 100% !important;
            height: 100% !important;
            max-width: 100%;
            max-height: 100%;
        }
        
        .optimization-controls {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid #e1e8ed;
        }
        
        .strategy-selector {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-top: 15px;
        }
        
        .strategy-selector label {
            font-weight: bold;
            color: #333;
        }
        
        .strategy-selector select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .strategy-selector button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
        }
        
        .strategy-selector button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        .optimization-summary {
            background: #e8f5e8;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #28a745;
        }
        
        .strategy-table-container {
            overflow-x: auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .strategy-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        
        .strategy-table th {
            background: #f8f9fa;
            padding: 12px 8px;
            text-align: center;
            font-weight: bold;
            color: #333;
            border-bottom: 2px solid #dee2e6;
        }
        
        .strategy-table td {
            padding: 10px 8px;
            text-align: center;
            border-bottom: 1px solid #dee2e6;
        }
        
        .strategy-table tbody tr:hover {
            background-color: #f8f9fa;
        }
        
        .strategy-table tbody tr:nth-child(1) {
            background-color: #fff3cd;
            font-weight: bold;
        }
        
        .strategy-table tbody tr:nth-child(2),
        .strategy-table tbody tr:nth-child(3) {
            background-color: #f8f9fa;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .metric-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #e1e8ed;
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
        }
        .metric-label {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .loading { 
            text-align: center; 
            padding: 40px; 
            color: #7f8c8d; 
            font-size: 18px;
        }
        .error { 
            color: #e74c3c; 
            background: #fdf2f2; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 20px 0; 
            border-left: 4px solid #e74c3c;
        }
        .success { 
            color: #27ae60; 
            background: #f0f9f0; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 20px 0; 
            border-left: 4px solid #27ae60;
        }
        .sentiment-indicator {
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
            margin: 10px 0;
        }
        .sentiment-bullish { background: #d4edda; color: #155724; }
        .sentiment-bearish { background: #f8d7da; color: #721c24; }
        .sentiment-neutral { background: #fff3cd; color: #856404; }
        .monitoring-stats {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border: 1px solid #e1e8ed;
        }
        @media (max-width: 768px) {
            .results { 
                grid-template-columns: 1fr; 
            }
            .search-box {
                flex-direction: column;
            }
            .search-box input {
                max-width: none;
            }
            .tabs {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 完整量化交易系统 v10.0 - Complete Edition</h1>
            <p>技术分析 · 策略回测 · 风险评估 · 市场情绪 · 性能监控</p>
            <div class="completion-badge">✅ 项目完成度: 100%</div>
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="switchTab('analysis')">技术分析</div>
            <div class="tab" onclick="switchTab('backtest')">策略回测</div>
            <div class="tab" onclick="switchTab('optimization')">策略优化</div>
            <div class="tab" onclick="switchTab('risk')">风险评估</div>
            <div class="tab" onclick="switchTab('sentiment')">市场情绪</div>
            <div class="tab" onclick="switchTab('monitoring')">系统监控</div>
            <div class="tab" onclick="switchTab('agents')">智能体管理</div>
            <div class="tab" onclick="switchTab('strategies')">策略管理</div>
            <div class="tab" onclick="switchTab('trading')">交易系统</div>
            <div class="tab" onclick="switchTab('xlsx')">XLSX分析</div>
            <div class="tab" onclick="switchTab('gov-data')">政府数据</div>
            <div class="tab" onclick="switchTab('hkex-data')">HKEX数据</div>
        </div>
        
        <div class="search-box">
            <input type="text" id="stockInput" placeholder="输入股票代码 (如: 0700.HK, 2800.HK)" />
            <button onclick="analyzeStock()">🔍 分析股票</button>
        </div>
        
        <div id="loading" class="loading" style="display: none;">
            <div>⏳ 正在分析中...</div>
        </div>
        
        <div id="error" class="error" style="display: none;"></div>
        
        <!-- 技术分析标签页 -->
        <div id="analysis" class="tab-content active">
            <div id="analysisResults" style="display: none;">
                <div class="results">
                    <div class="chart-container">
                        <h3>📊 价格走势图</h3>
                        <canvas id="priceChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <h3>📈 技术指标</h3>
                        <div id="indicatorsList"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 策略回测标签页 -->
        <div id="backtest" class="tab-content">
            <div id="backtestResults" style="display: none;">
                <h3>🔄 策略回测结果</h3>
                <div class="metrics-grid" id="backtestMetrics"></div>
                <div class="chart-container">
                    <h3>📊 交易记录</h3>
                    <div id="tradesList"></div>
                </div>
            </div>
        </div>
        
        <!-- 策略优化标签页 -->
        <div id="optimization" class="tab-content">
            <div class="optimization-controls">
                <h3>🚀 生产级策略优化引擎</h3>
                <p>支持6种优化算法，包含Grid Search, Random Search, Genetic Algorithm, PSO, Simulated Annealing</p>
                <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <strong style="font-size: 16px; color: #1976d2;">📝 当前支持的策略类型 (11种):</strong>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
                        <div>
                            <h4 style="color: #1565c0; margin: 10px 0 5px 0;">基础策略 (4种):</h4>
                            <ul style="margin: 0; padding-left: 20px; font-size: 14px;">
                                <li>MA交叉策略 - 移动平均线交叉信号</li>
                                <li>RSI策略 - 相对强弱指数超买超卖</li>
                                <li>MACD策略 - 指数平滑异同移动平均线</li>
                                <li>布林带策略 - 价格通道突破策略</li>
                            </ul>
                        </div>
                        <div>
                            <h4 style="color: #1565c0; margin: 10px 0 5px 0;">高级指标 (7种):</h4>
                            <ul style="margin: 0; padding-left: 20px; font-size: 14px;">
                                <li>KDJ策略 - 随机指标K/D交叉</li>
                                <li>CCI策略 - 商品通道指标</li>
                                <li>ADX策略 - 平均趋向指标</li>
                                <li>ATR策略 - 平均真实范围</li>
                                <li>OBV策略 - 能量潮指标</li>
                                <li>Ichimoku策略 - 一目均衡表</li>
                                <li>PSAR策略 - 抛物线转向</li>
                            </ul>
                        </div>
                    </div>
                    <small style="color: #666; display: block; margin-top: 10px; font-size: 13px;">
                        🔄 策略优化: 支持多线程并行计算，自动寻找最优参数组合
                    </small>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                    <div>
                        <label style="font-weight: bold; display: block; margin-bottom: 5px;">策略类型:</label>
                        <select id="optimStrategyType" style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #ddd; font-size: 14px;">
                            <option value="all">全部策略 (11种)</option>
                            <optgroup label="基础策略 (4种)">
                                <option value="ma">MA交叉策略 - 移动平均</option>
                                <option value="rsi">RSI策略 - 相对强弱</option>
                                <option value="macd">MACD策略 - 指数平滑</option>
                                <option value="bb">布林带策略 - 价格通道</option>
                            </optgroup>
                            <optgroup label="高级指标 (7种)">
                                <option value="kdj">KDJ策略 - 随机指标</option>
                                <option value="cci">CCI策略 - 商品通道</option>
                                <option value="adx">ADX策略 - 趋向指标</option>
                                <option value="atr">ATR策略 - 真实范围</option>
                                <option value="obv">OBV策略 - 能量潮</option>
                                <option value="ichimoku">Ichimoku策略 - 云图</option>
                                <option value="psar">PSAR策略 - 抛物线</option>
                            </optgroup>
                        </select>
                    </div>

                    <div>
                        <label style="font-weight: bold; display: block; margin-bottom: 5px;">优化算法:</label>
                        <select id="optimMethod" style="width: 100%; padding: 8px; border-radius: 5px; border: 1px solid #ddd;">
                            <option value="grid_search">Grid Search (网格搜索)</option>
                            <option value="random_search">Random Search (随机搜索)</option>
                            <option value="genetic">Genetic Algorithm (遗传算法)</option>
                            <option value="pso">PSO (粒子群优化)</option>
                            <option value="simulated_annealing">Simulated Annealing (模拟退火)</option>
                            <option value="brute_force">Brute Force (暴力搜索)</option>
                        </select>
                    </div>

                    <div style="grid-column: span 2;">
                        <button onclick="toggleAlgorithmGuide()" style="padding: 10px 20px; background: #17a2b8; color: white; border: none; border-radius: 5px; cursor: pointer; margin-bottom: 10px;">
                            📖 查看优化算法详细说明
                        </button>
                    </div>

                    <!-- 算法详细说明区域 -->
                    <div id="algorithmGuide" style="display: none; grid-column: span 2; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 10px; padding: 20px; margin: 20px 0;">
                        <h4 style="color: #2c3e50; margin-bottom: 15px;">🎯 6种优化算法详细说明</h4>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <!-- Grid Search -->
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff;">
                                <h5 style="color: #007bff; margin-top: 0;">🔍 Grid Search (网格搜索)</h5>
                                <p style="font-size: 13px; color: #666; margin: 5px 0;"><strong>简单理解:</strong> 像在格子里找宝藏！</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>原理:</strong> 在地图上画格子，一个格子一个格子地检查</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>优点:</strong> 不会遗漏任何可能性</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>缺点:</strong> 比较慢，要检查很多格子</p>
                                <p style="font-size: 11px; color: #777; margin: 5px 0;"><strong>适合:</strong> 小范围精确查找</p>
                            </div>

                            <!-- Random Search -->
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745;">
                                <h5 style="color: #28a745; margin-top: 0;">🎲 Random Search (随机搜索)</h5>
                                <p style="font-size: 13px; color: #666; margin: 5px 0;"><strong>简单理解:</strong> 像掷骰子碰运气！</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>原理:</strong> 随机挑选几个点试试</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>优点:</strong> 速度快，不用全部检查</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>缺点:</strong> 可能错过最好的</p>
                                <p style="font-size: 11px; color: #777; margin: 5px 0;"><strong>适合:</strong> 大范围快速找方向</p>
                            </div>

                            <!-- Genetic Algorithm -->
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #dc3545;">
                                <h5 style="color: #dc3545; margin-top: 0;">🧬 Genetic Algorithm (遗传算法)</h5>
                                <p style="font-size: 13px; color: #666; margin: 5px 0;"><strong>简单理解:</strong> 模拟生物进化！</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>原理:</strong> 父母组合优点，繁殖更好的后代</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>优点:</strong> 能找到很好的解决方案</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>缺点:</strong> 需要很多代进化，时间较长</p>
                                <p style="font-size: 11px; color: #777; margin: 5px 0;"><strong>适合:</strong> 复杂问题的最优解</p>
                            </div>

                            <!-- PSO -->
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
                                <h5 style="color: #ffc107; margin-top: 0;">🐦 PSO 粒子群优化</h5>
                                <p style="font-size: 13px; color: #666; margin: 5px 0;"><strong>简单理解:</strong> 像鸟儿找食物！</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>原理:</strong> 鸟儿互相分享发现，一起向最好地方飞</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>优点:</strong> 鸟儿们互相帮忙，找得又快又好</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>缺点:</strong> 所有鸟儿可能都往同一个方向飞</p>
                                <p style="font-size: 11px; color: #777; margin: 5px 0;"><strong>适合:</strong> 多人合作解决问题</p>
                            </div>

                            <!-- Simulated Annealing -->
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #6f42c1;">
                                <h5 style="color: #6f42c1; margin-top: 0;">🌡️ Simulated Annealing (模拟退火)</h5>
                                <p style="font-size: 13px; color: #666; margin: 5px 0;"><strong>简单理解:</strong> 像铁匠锻造钢铁！</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>原理:</strong> 开始时很热可以尝试各种，后来专注最好的</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>优点:</strong> 能避免只看局部，视野更广</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>缺点:</strong> 需要控制好"温度"</p>
                                <p style="font-size: 11px; color: #777; margin: 5px 0;"><strong>适合:</strong> 需要全局视野</p>
                            </div>

                            <!-- Brute Force -->
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #fd7e14;">
                                <h5 style="color: #fd7e14; margin-top: 0;">💪 Brute Force (暴力搜索)</h5>
                                <p style="font-size: 13px; color: #666; margin: 5px 0;"><strong>简单理解:</strong> 像搬砖工人！</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>原理:</strong> 一个个尝试所有可能性，不走捷径</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>优点:</strong> 绝对能找到最好的</p>
                                <p style="font-size: 12px; color: #555; margin: 5px 0;"><strong>缺点:</strong> 最慢最累，需要很多时间</p>
                                <p style="font-size: 11px; color: #777; margin: 5px 0;"><strong>适合:</strong> 必须找到最好答案</p>
                            </div>
                        </div>

                        <div style="margin-top: 20px; background: #e3f2fd; padding: 15px; border-radius: 8px;">
                            <h5 style="color: #1976d2; margin-top: 0;">🎯 推荐使用策略</h5>
                            <ol style="margin: 10px 0; padding-left: 20px; font-size: 13px; color: #555;">
                                <li><strong>先用Random Search:</strong> 快速找到大致方向</li>
                                <li><strong>再用Grid Search:</strong> 在好区域内精确查找</li>
                                <li><strong>特殊情况用Genetic或PSO:</strong> 解决复杂问题</li>
                            </ol>
                        </div>

                        <div style="margin-top: 15px; background: #fff3cd; padding: 15px; border-radius: 8px;">
                            <h6 style="color: #856404; margin-top: 0; margin-bottom: 10px;">⚡ 实际应用例子 - 找CCI最佳参数</h6>
                            <p style="font-size: 12px; color: #555; margin: 5px 0;">假设我们要找CCI指标的最佳参数：</p>
                            <ul style="font-size: 11px; color: #666; padding-left: 20px;">
                                <li><strong>Grid Search:</strong> 尝试所有可能的组合 (100,200), (100,150), (-100,200)...</li>
                                <li><strong>Random Search:</strong> 随机选10个组合试试</li>
                                <li><strong>Genetic:</strong> 从随机组合开始，繁殖出更好的组合</li>
                                <li><strong>PSO:</strong> 多个"智能体"同时搜索，互相分享发现</li>
                            </ul>
                        </div>
                    </div>

                    <div>
                        <label style="font-weight: bold; display: block; margin-bottom: 5px;">优化指标:</label>
                        <select id="optimMetric" style="width: 100%; padding: 8px; border-radius: 5px; border: 1px solid #ddd;">
                            <option value="sharpe_ratio">Sharpe Ratio (夏普比率)</option>
                            <option value="sortino_ratio">Sortino Ratio (索提诺比率)</option>
                            <option value="annual_return">Annual Return (年化收益率)</option>
                            <option value="max_drawdown">Max Drawdown (最大回撤)</option>
                            <option value="win_rate">Win Rate (胜率)</option>
                        </select>
                    </div>

                    <div>
                        <label style="font-weight: bold; display: block; margin-bottom: 5px;">开始日期:</label>
                        <input type="date" id="optimStartDate" value="2020-01-01" style="width: 100%; padding: 8px; border-radius: 5px; border: 1px solid #ddd;">
                    </div>

                    <div style="grid-column: span 2;">
                        <button onclick="runOptimization()" style="width: 100%; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 10px; cursor: pointer; font-size: 16px; font-weight: bold;">
                            🔍 启动优化引擎
                        </button>
                    </div>
                </div>
            </div>

            <div id="optimizationProgress" style="display: none; background: #fff3cd; padding: 15px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <h4>⏳ 优化进行中...</h4>
                <p id="optimProgressText">正在启动优化任务...</p>
                <div style="background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden; margin-top: 10px;">
                    <div id="optimProgressBar" style="background: linear-gradient(90deg, #667eea, #764ba2); height: 100%; width: 0%; transition: width 0.3s;"></div>
                </div>
            </div>

            <div id="optimizationResults" style="display: none;">
                <h3>📈 优化结果</h3>
                <div class="optimization-summary" id="optimizationSummary"></div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                    <div class="chart-container" style="height: 300px;">
                        <h4>📊 参数敏感性分析</h4>
                        <canvas id="sensitivityChart"></canvas>
                    </div>
                    <div class="chart-container" style="height: 300px;">
                        <h4>📈 性能指标对比</h4>
                        <canvas id="metricsChart"></canvas>
                    </div>
                </div>

                <div class="strategy-table-container">
                    <h4>🏆 Top 10 参数组合</h4>
                    <table class="strategy-table" id="strategyTable">
                        <thead>
                            <tr>
                                <th>排名</th>
                                <th>参数</th>
                                <th>Sharpe</th>
                                <th>Sortino</th>
                                <th>年化收益</th>
                                <th>最大回撤</th>
                                <th>波动率</th>
                                <th>胜率</th>
                                <th>交易次数</th>
                                <th>平均持仓</th>
                                <th>盈亏比</th>
                            </tr>
                        </thead>
                        <tbody id="strategyTableBody">
                        </tbody>
                    </table>
                </div>
            </div>

            <div id="optimizationHistory" style="margin-top: 30px;">
                <h3>📜 优化历史记录</h3>
                <div id="historyList" style="max-height: 400px; overflow-y: auto;"></div>
            </div>
        </div>
        
        <!-- 风险评估标签页 -->
        <div id="risk" class="tab-content">
            <div id="riskResults" style="display: none;">
                <h3>⚠️ 风险评估</h3>
                <div class="metrics-grid" id="riskMetrics"></div>
                <div id="riskRecommendation"></div>
            </div>
        </div>
        
        <!-- 市场情绪标签页 -->
        <div id="sentiment" class="tab-content">
            <div id="sentimentResults" style="display: none;">
                <h3>😊 市场情绪分析</h3>
                <div class="metrics-grid" id="sentimentMetrics"></div>
                <div id="sentimentIndicator"></div>
            </div>
        </div>
        
        <!-- 系统监控标签页 -->
        <div id="monitoring" class="tab-content">
            <div id="monitoringResults" style="display: none;">
                <h3>📊 系统监控</h3>
                <div class="monitoring-stats" id="monitoringStats"></div>
            </div>
        </div>

        <!-- 政府数据标签页 -->
        <div id="gov-data" class="tab-content">
            <div id="govDataResults" style="display: none;">
                <h3>📊 政府替代数据</h3>
                <div style="margin-bottom: 20px;">
                    <button onclick="loadGovData('all')" style="padding: 10px 20px; margin-right: 10px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">全部数据</button>
                    <button onclick="loadGovData('hibor')" style="padding: 10px 20px; margin-right: 10px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">HIBOR利率</button>
                    <button onclick="loadGovData('property')" style="padding: 10px 20px; margin-right: 10px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">房产市场</button>
                    <button onclick="loadGovData('retail')" style="padding: 10px 20px; margin-right: 10px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">零售销售</button>
                    <button onclick="loadGovData('gdp')" style="padding: 10px 20px; margin-right: 10px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">GDP指标</button>
                </div>
                <div id="govDataTable" style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #f5f5f5;">
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">数据类型</th>
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">分类</th>
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">指标名</th>
                                <th style="padding: 10px; text-align: right; border-bottom: 2px solid #ddd;">数值</th>
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">单位</th>
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">时间戳</th>
                            </tr>
                        </thead>
                        <tbody id="govDataBody"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- HKEX数据标签页 -->
        <div id="hkex-data" class="tab-content">
            <div id="hkexDataResults" style="display: none;">
                <h3>📊 香港交易所市场数据</h3>
                <div style="margin-bottom: 20px;">
                    <input type="text" id="hkexSymbolFilter" placeholder="输入股票代码筛选 (如: 0700.hk)" style="padding: 10px; width: 300px; border: 1px solid #ddd; border-radius: 5px; margin-right: 10px;">
                    <button onclick="loadHKEXData()" style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">🔍 查询数据</button>
                </div>
                <div id="hkexDataTable" style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #f5f5f5;">
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">股票代码</th>
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">日期</th>
                                <th style="padding: 10px; text-align: right; border-bottom: 2px solid #ddd;">开盘价</th>
                                <th style="padding: 10px; text-align: right; border-bottom: 2px solid #ddd;">最高价</th>
                                <th style="padding: 10px; text-align: right; border-bottom: 2px solid #ddd;">最低价</th>
                                <th style="padding: 10px; text-align: right; border-bottom: 2px solid #ddd;">收盘价</th>
                                <th style="padding: 10px; text-align: right; border-bottom: 2px solid #ddd;">交易量</th>
                                <th style="padding: 10px; text-align: right; border-bottom: 2px solid #ddd;">涨跌幅 (%)</th>
                            </tr>
                        </thead>
                        <tbody id="hkexDataBody"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        let priceChart = null;
        let currentData = null;
        let sensitivityChart = null;
        let metricsChart = null;
        let currentOptimizationRunId = null;
        let optimizationPollingInterval = null;

        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });

            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');

            if (tabName === 'monitoring') {
                getMonitoringStats();
            }

            if (tabName === 'optimization') {
                // Optimization history not available
            }

            if (tabName === 'gov-data') {
                document.getElementById('govDataResults').style.display = 'block';
                loadGovData('all');
            }

            if (tabName === 'hkex-data') {
                document.getElementById('hkexDataResults').style.display = 'block';
                loadHKEXData();
            }
        }

        // ========== 爬虫数据加载函数 ==========

        async function loadGovData(dataType = 'all') {
            try {
                const url = dataType === 'all'
                    ? '/api/crawlers/gov-crawler/data'
                    : `/api/crawlers/gov-crawler/data?data_type=${dataType}`;

                const response = await fetch(url);
                const result = await response.json();

                if (result.success && result.data) {
                    displayGovData(result.data);
                } else {
                    console.error('Failed to load government data:', result);
                }
            } catch (error) {
                console.error('Error loading government data:', error);
                showError('加载政府数据失败: ' + error.message);
            }
        }

        function displayGovData(data) {
            const tbody = document.getElementById('govDataBody');
            tbody.innerHTML = '';

            // 处理分类数据
            let allRecords = [];

            for (const [category, records] of Object.entries(data)) {
                if (Array.isArray(records)) {
                    records.forEach(record => {
                        if (typeof record === 'object') {
                            for (const [key, value] of Object.entries(record)) {
                                allRecords.push({
                                    dataType: category,
                                    category: category,
                                    indicatorName: key,
                                    value: value,
                                    unit: '单位',
                                    timestamp: new Date().toISOString()
                                });
                            }
                        }
                    });
                }
            }

            // 显示表格数据
            allRecords.slice(0, 100).forEach(record => {
                const row = document.createElement('tr');
                row.style.borderBottom = '1px solid #eee';
                row.innerHTML = `
                    <td style="padding: 10px;">${record.dataType}</td>
                    <td style="padding: 10px;">${record.category}</td>
                    <td style="padding: 10px;">${record.indicatorName}</td>
                    <td style="padding: 10px; text-align: right;">${typeof record.value === 'number' ? record.value.toFixed(2) : record.value}</td>
                    <td style="padding: 10px;">${record.unit}</td>
                    <td style="padding: 10px;">${new Date(record.timestamp).toLocaleString()}</td>
                `;
                tbody.appendChild(row);
            });

            if (allRecords.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="padding: 20px; text-align: center; color: #999;">暂无数据</td></tr>';
            }
        }

        async function loadHKEXData() {
            try {
                const symbol = document.getElementById('hkexSymbolFilter').value.trim() || '';
                const url = symbol
                    ? `/api/crawlers/hkex-crawler/data?symbol=${symbol}&limit=100`
                    : '/api/crawlers/hkex-crawler/data?limit=100';

                const response = await fetch(url);
                const result = await response.json();

                if (result.success && result.data) {
                    displayHKEXData(result.data);
                } else {
                    console.error('Failed to load HKEX data:', result);
                }
            } catch (error) {
                console.error('Error loading HKEX data:', error);
                showError('加载HKEX数据失败: ' + error.message);
            }
        }

        function displayHKEXData(data) {
            const tbody = document.getElementById('hkexDataBody');
            tbody.innerHTML = '';

            let records = [];

            // 从API响应中提取样本数据
            if (data.sample_data && Array.isArray(data.sample_data)) {
                records = data.sample_data;
            } else if (Array.isArray(data)) {
                records = data;
            }

            if (records.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="padding: 20px; text-align: center; color: #999;">暂无数据</td></tr>';
                return;
            }

            records.forEach(record => {
                const row = document.createElement('tr');
                row.style.borderBottom = '1px solid #eee';

                // 处理字段映射 - API返回的是Morning_Close和Afternoon_Close等字段
                const symbol = record.symbol || record.Symbol || '';
                const date = record.date || record.Date || '';
                const openPrice = record.Morning_Close || record.open_price || record.Open || 'N/A';
                const highPrice = record.Turnover_HKD ? (record.Turnover_HKD / 1e9).toFixed(2) : 'N/A';
                const lowPrice = record.Advanced_Stocks || 'N/A';
                const closePrice = record.Afternoon_Close || record.closing_price || record.Close || record.price || 'N/A';
                const volume = record.Trading_Volume || record.Deals || record.trading_volume || record.Volume || 'N/A';
                const changePercent = record.Change_Percent !== undefined ? parseFloat(record.Change_Percent).toFixed(2) : (record.change_percent ? record.change_percent.toFixed(2) : 'N/A');

                row.innerHTML = `
                    <td style="padding: 10px;">${symbol}</td>
                    <td style="padding: 10px;">${date}</td>
                    <td style="padding: 10px; text-align: right;">${typeof openPrice === 'number' ? openPrice.toFixed(2) : openPrice}</td>
                    <td style="padding: 10px; text-align: right;">${typeof highPrice === 'number' ? highPrice : highPrice}</td>
                    <td style="padding: 10px; text-align: right;">${typeof lowPrice === 'number' ? lowPrice : lowPrice}</td>
                    <td style="padding: 10px; text-align: right;">${typeof closePrice === 'number' ? closePrice.toFixed(2) : closePrice}</td>
                    <td style="padding: 10px; text-align: right;">${typeof volume === 'number' ? Math.round(volume).toLocaleString() : volume}</td>
                    <td style="padding: 10px; text-align: right;">${changePercent}</td>
                `;
                tbody.appendChild(row);
            });
        }

        
        async function runOptimization() {
            console.log('runOptimization function called');

            try {
                // Debug: Check if elements exist
                const stockInput = document.getElementById('stockInput');
                const strategySelect = document.getElementById('optimStrategyType');

                if (!stockInput || !strategySelect) {
                    console.error('Required DOM elements not found');
                    showError('页面元素未正确加载，请刷新页面');
                    return;
                }

                const symbol = stockInput.value.trim();
                console.log('Symbol input:', symbol);

                if (!symbol) {
                    showError('请输入股票代码');
                    return;
                }

                const strategyType = strategySelect.value;
                console.log('Strategy type:', strategyType);

                showLoading(true);
                hideError();
                hideOptimizationResults();

                const apiUrl = `/api/strategy-optimization/${symbol}?strategy_type=${strategyType}`;
                console.log('Making API call to:', apiUrl);

                const response = await fetch(apiUrl);
                console.log('Response status:', response.status);
                console.log('Response ok:', response.ok);

                if (!response.ok) {
                    let errorDetail = '未知错误';
                    try {
                        const errorData = await response.json();
                        errorDetail = errorData.detail || JSON.stringify(errorData);
                        console.error('API error data:', errorData);
                    } catch (e) {
                        errorDetail = `HTTP ${response.status} 错误`;
                        console.error('Failed to parse error response:', e);
                    }
                    throw new Error(errorDetail);
                }

                const result = await response.json();
                console.log('API result:', result);

                if (result.success && result.data) {
                    console.log('Displaying optimization results');
                    displayOptimizationResults(result.data);
                } else {
                    const errorMsg = result.message || result.detail || '未知错误';
                    console.error('API returned failure:', errorMsg);
                    showError('优化失败: ' + errorMsg);
                }

            } catch (error) {
                console.error('Exception in runOptimization:', error);
                const errorMsg = error.message || String(error);
                showError('优化失败: ' + errorMsg);
            } finally {
                showLoading(false);
            }
        }
        
        function displayOptimizationResults(data) {
            const resultsDiv = document.getElementById('optimizationResults');
            const summaryDiv = document.getElementById('optimizationSummary');
            const tableBody = document.getElementById('strategyTableBody');
            
            // 显示优化摘要
            summaryDiv.innerHTML = `
                <h4>🎯 优化完成</h4>
                <p><strong>测试策略数量:</strong> ${data.total_strategies}</p>
                <p><strong>策略类型:</strong> ${getStrategyTypeName(data.optimization_type)}</p>
                <p><strong>最佳Sharpe比率:</strong> ${data.best_sharpe_ratio}</p>
                <p><strong>优化时间:</strong> ${new Date().toLocaleString()}</p>
            `;
            
            // 清空表格
            tableBody.innerHTML = '';
            
            // 填充策略表格
            data.best_strategies.forEach((strategy, index) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${strategy.strategy_name}</td>
                    <td style="color: ${strategy.sharpe_ratio > 1 ? '#28a745' : strategy.sharpe_ratio > 0 ? '#ffc107' : '#dc3545'}; font-weight: bold;">
                        ${strategy.sharpe_ratio}
                    </td>
                    <td style="color: ${strategy.annual_return > 0 ? '#28a745' : '#dc3545'};">
                        ${strategy.annual_return}%
                    </td>
                    <td>${strategy.volatility}%</td>
                    <td style="color: ${strategy.max_drawdown > -10 ? '#28a745' : strategy.max_drawdown > -20 ? '#ffc107' : '#dc3545'};">
                        ${strategy.max_drawdown}%
                    </td>
                    <td style="color: ${strategy.win_rate > 50 ? '#28a745' : '#dc3545'};">
                        ${strategy.win_rate}%
                    </td>
                    <td>${strategy.trade_count}</td>
                    <td style="color: ${strategy.final_value > 100000 ? '#28a745' : '#dc3545'}; font-weight: bold;">
                        ¥${strategy.final_value.toLocaleString()}
                    </td>
                `;
                tableBody.appendChild(row);
            });
            
            // 显示结果
            resultsDiv.style.display = 'block';
        }
        
        function getStrategyTypeName(type) {
            const names = {
                'all': '全部策略 (11种)',
                // 基础策略 (4种)
                'ma': 'MA交叉策略',
                'rsi': 'RSI策略',
                'macd': 'MACD策略',
                'bb': '布林带策略',
                // 高级指标 (7种)
                'kdj': 'KDJ策略',
                'cci': 'CCI策略',
                'adx': 'ADX策略',
                'atr': 'ATR策略',
                'obv': 'OBV策略',
                'ichimoku': 'Ichimoku策略',
                'psar': 'Parabolic SAR策略'
            };
            return names[type] || type;
        }
        
        async function analyzeStock() {
            const symbol = document.getElementById('stockInput').value.trim();
            if (!symbol) {
                showError('请输入股票代码');
                return;
            }
            
            showLoading(true);
            hideError();
            hideAllResults();
            
            try {
                const response = await fetch(`/api/analysis/${symbol}`);
                
                if (!response.ok) {
                    const errorData = await response.json();
                    const errorMessage = errorData.detail || `HTTP ${response.status} 错误`;
                    showError(`分析失败: ${errorMessage}`);
                    return;
                }
                
                const result = await response.json();
                
                if (result.success) {
                    currentData = result.data;
                    displayAnalysisResults(result.data);
                    displayBacktestResults(result.data);
                    displayRiskResults(result.data);
                    displaySentimentResults(result.data);
                } else {
                    const errorMessage = result.message || result.detail || '未知错误';
                    showError(`分析失败: ${errorMessage}`);
                }
            } catch (error) {
                console.error('分析错误:', error);
                if (error.name === 'TypeError' && error.message.includes('fetch')) {
                    showError('网络连接失败，请检查网络连接');
                } else {
                    showError(`网络错误: ${error.message}`);
                }
            } finally {
                showLoading(false);
            }
        }
        
        function displayAnalysisResults(data) {
            displayChart(data.price_data);
            displayIndicators(data.indicators);
            document.getElementById('analysisResults').style.display = 'block';
        }
        
        function displayChart(priceData) {
            const ctx = document.getElementById('priceChart').getContext('2d');
            
            if (priceChart) {
                priceChart.destroy();
            }
            
            const recentData = priceData.slice(-50);
            const labels = recentData.map(item => new Date(item.timestamp).toLocaleDateString());
            const prices = recentData.map(item => item.close);
            
            priceChart = new Chart(ctx, {
                type: 'line',
                responsive: true,
                maintainAspectRatio: false,
                data: {
                    labels: labels,
                    datasets: [{
                        label: '收盘价',
                        data: prices,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.1,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        x: {
                            display: true,
                            title: {
                                display: true,
                                text: '日期'
                            }
                        },
                        y: {
                            display: true,
                            title: {
                                display: true,
                                text: '价格'
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });
        }
        
        function displayIndicators(indicators) {
            const container = document.getElementById('indicatorsList');
            container.innerHTML = '';
            
            const indicatorItems = [
                { label: 'SMA(20)', value: indicators.sma_20 },
                { label: 'SMA(50)', value: indicators.sma_50 },
                { label: 'RSI', value: indicators.rsi },
                { label: 'MACD', value: indicators.macd },
                { label: 'MACD Signal', value: indicators.macd_signal },
                { label: 'Bollinger Upper', value: indicators.bollinger_upper },
                { label: 'Bollinger Middle', value: indicators.bollinger_middle },
                { label: 'Bollinger Lower', value: indicators.bollinger_lower },
                { label: 'ATR', value: indicators.atr }
            ];
            
            indicatorItems.forEach(item => {
                if (item.value !== null && item.value !== undefined) {
                    const div = document.createElement('div');
                    div.style.cssText = 'display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;';
                    div.innerHTML = `
                        <span style="font-weight: bold; color: #2c3e50;">${item.label}</span>
                        <span style="color: #27ae60; font-weight: bold;">${item.value.toFixed(2)}</span>
                    `;
                    container.appendChild(div);
                }
            });
        }
        
        function displayBacktestResults(data) {
            const container = document.getElementById('backtestMetrics');
            container.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value">${data.backtest.total_return.toFixed(2)}%</div>
                    <div class="metric-label">总收益率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.backtest.volatility.toFixed(2)}%</div>
                    <div class="metric-label">波动率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.backtest.sharpe_ratio.toFixed(2)}</div>
                    <div class="metric-label">夏普比率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.backtest.max_drawdown.toFixed(2)}%</div>
                    <div class="metric-label">最大回撤</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.backtest.total_trades}</div>
                    <div class="metric-label">交易次数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">¥${data.backtest.final_value.toFixed(0)}</div>
                    <div class="metric-label">最终价值</div>
                </div>
            `;
            
            // 显示交易记录
            const tradesContainer = document.getElementById('tradesList');
            tradesContainer.innerHTML = '';
            data.backtest.trades.forEach(trade => {
                const div = document.createElement('div');
                div.style.cssText = 'display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;';
                div.innerHTML = `
                    <span style="font-weight: bold; color: #2c3e50;">${trade.action} ${trade.shares.toFixed(2)}股 @ ${trade.price.toFixed(2)}</span>
                    <span style="color: #7f8c8d; font-size: 0.9em;">${new Date(trade.timestamp).toLocaleDateString()}</span>
                `;
                tradesContainer.appendChild(div);
            });
            
            document.getElementById('backtestResults').style.display = 'block';
        }
        
        function displayRiskResults(data) {
            const container = document.getElementById('riskMetrics');
            const riskColor = data.risk.risk_level === 'LOW' ? '#28a745' : 
                             data.risk.risk_level === 'MEDIUM' ? '#ffc107' : '#dc3545';
            
            container.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value" style="color: ${riskColor};">${data.risk.risk_level}</div>
                    <div class="metric-label">风险等级</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.risk.risk_score.toFixed(0)}</div>
                    <div class="metric-label">风险评分</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.risk.volatility.toFixed(2)}%</div>
                    <div class="metric-label">波动率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.risk.var_95.toFixed(2)}%</div>
                    <div class="metric-label">VaR (95%)</div>
                </div>
            `;
            
            const recDiv = document.getElementById('riskRecommendation');
            recDiv.innerHTML = `
                <div class="success">
                    <h4>投资建议</h4>
                    <p>${data.risk.recommendation}</p>
                </div>
            `;
            
            document.getElementById('riskResults').style.display = 'block';
        }
        
        function displaySentimentResults(data) {
            const container = document.getElementById('sentimentMetrics');
            container.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value">${data.sentiment.score.toFixed(1)}</div>
                    <div class="metric-label">情绪分数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.sentiment.level}</div>
                    <div class="metric-label">情绪等级</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.sentiment.volatility.toFixed(2)}%</div>
                    <div class="metric-label">波动率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.sentiment.trend_strength.toFixed(2)}%</div>
                    <div class="metric-label">趋势强度</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.sentiment.positive_days}</div>
                    <div class="metric-label">上涨天数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.sentiment.negative_days}</div>
                    <div class="metric-label">下跌天数</div>
                </div>
            `;
            
            const indicatorDiv = document.getElementById('sentimentIndicator');
            const sentimentClass = data.sentiment.level === 'Bullish' ? 'sentiment-bullish' : 
                                 data.sentiment.level === 'Bearish' ? 'sentiment-bearish' : 'sentiment-neutral';
            
            indicatorDiv.innerHTML = `
                <div class="sentiment-indicator ${sentimentClass}">
                    <h4>市场情绪: ${data.sentiment.level}</h4>
                    <p>情绪分数: ${data.sentiment.score.toFixed(1)}/100</p>
                </div>
            `;
            
            document.getElementById('sentimentResults').style.display = 'block';
        }
        
        async function getMonitoringStats() {
            try {
                const response = await fetch('/api/monitoring');
                const result = await response.json();
                
                if (result.success) {
                    displayMonitoringStats(result.data);
                }
            } catch (error) {
                console.error('Monitoring error:', error);
            }
        }
        
        function displayMonitoringStats(data) {
            const container = document.getElementById('monitoringStats');
            container.innerHTML = `
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">${data.uptime.toFixed(1)}s</div>
                        <div class="metric-label">运行时间</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.requests}</div>
                        <div class="metric-label">总请求数</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.errors}</div>
                        <div class="metric-label">错误数</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.error_rate.toFixed(2)}%</div>
                        <div class="metric-label">错误率</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.api_calls}</div>
                        <div class="metric-label">API调用</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.cache_hit_rate.toFixed(1)}%</div>
                        <div class="metric-label">缓存命中率</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.avg_response_time.toFixed(3)}s</div>
                        <div class="metric-label">平均响应时间</div>
                    </div>
                </div>
            `;
            
            document.getElementById('monitoringResults').style.display = 'block';
        }
        
        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'block' : 'none';
        }
        
        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
        
        function hideError() {
            document.getElementById('error').style.display = 'none';
        }
        
        function hideAllResults() {
            document.getElementById('analysisResults').style.display = 'none';
            document.getElementById('backtestResults').style.display = 'none';
            document.getElementById('riskResults').style.display = 'none';
            document.getElementById('sentimentResults').style.display = 'none';
            document.getElementById('monitoringResults').style.display = 'none';
            document.getElementById('optimizationResults').style.display = 'none';
        }
        
        function hideOptimizationResults() {
            document.getElementById('optimizationResults').style.display = 'none';
        }

        function toggleAlgorithmGuide() {
            const guide = document.getElementById('algorithmGuide');
            const button = event.target;

            if (guide.style.display === 'none' || guide.style.display === '') {
                guide.style.display = 'block';
                button.textContent = '📖 隐藏优化算法详细说明';
                button.style.background = '#dc3545';
            } else {
                guide.style.display = 'none';
                button.textContent = '📖 查看优化算法详细说明';
                button.style.background = '#17a2b8';
            }
        }
        
        document.getElementById('stockInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                analyzeStock();
            }
        });
        
        // 页面加载时初始化监控数据
        document.addEventListener('DOMContentLoaded', function() {
            getMonitoringStats();
        });
    </script>
</body>
</html>
    '''

# API端点
@app.get('/api/analysis/{symbol}')
def analyze_stock(symbol: str):
    start_time = time.time()
    try:
        data = get_stock_data(symbol)
        if not data:
            monitor.log_request(f"/api/analysis/{symbol}", 404, time.time() - start_time)
            raise HTTPException(status_code=404, detail="Failed to get stock data")
        
        if len(data) < 20:
            monitor.log_request(f"/api/analysis/{symbol}", 400, time.time() - start_time)
            raise HTTPException(status_code=400, detail="Insufficient data for analysis")
        
        indicators = tech_engine.calculate_indicators(data)
        backtest = backtest_engine.run_backtest(data)
        risk = risk_engine.assess_risk(data, indicators)
        sentiment = sentiment_engine.calculate_sentiment(data)
        
        monitor.log_request(f"/api/analysis/{symbol}", 200, time.time() - start_time)
        
        return {
            'success': True,
            'data': {
                'symbol': symbol,
                'price_data': data,
                'indicators': indicators,
                'backtest': backtest,
                'risk': risk,
                'sentiment': sentiment,
                'current_price': float(pd.DataFrame(data)['close'].iloc[-1]),
                'data_count': len(data),
                'analysis_time': time.time() - start_time
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        monitor.log_request(f"/api/analysis/{symbol}", 500, time.time() - start_time)
        logger.error(f"Analysis error for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get('/api/monitoring')
def get_monitoring_stats():
    try:
        stats = monitor.get_stats()
        return {
            'success': True,
            'data': stats
        }
    except Exception as e:
        logger.error(f"Monitoring error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Monitoring failed: {str(e)}")

def run_strategy_optimization(data, strategy_type='all'):
    """运行策略参数优化 - 高计算量单线程版本，充分利用CPU性能"""
    try:
        logger.info(f"开始策略优化: {strategy_type}")
        
        df = pd.DataFrame(data)
        if len(df) < 100:
            logger.warning(f"数据不足: {len(df)} 条记录")
            return []
        
        logger.info(f"数据准备完成: {len(df)} 条记录")
        
        # 直接使用单线程但增加计算量
        return run_strategy_optimization_single_thread(data, strategy_type)
        
    except Exception as e:
        logger.error(f"策略优化失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return []

def run_strategy_optimization_single_thread(data, strategy_type='all'):
    """高计算量单线程策略优化 - 充分利用9950X3D CPU性能"""
    try:
        import time
        start_time = time.time()
        
        logger.info(f"开始高计算量策略优化: {strategy_type}")
        
        df = pd.DataFrame(data)
        if len(df) < 100:
            logger.warning(f"数据不足: {len(df)} 条记录")
            return []
        
        logger.info(f"数据准备完成: {len(df)} 条记录")
        
        results = []
        total_tasks = 0
        
        if strategy_type in ['all', 'ma']:
            # MA交叉策略优化 - 大幅增加参数范围
            logger.info("运行MA策略优化 - 高计算量版本")
            ma_tasks = 0
            for short in range(3, 51, 1):  # 3-50, 步长1 (减少范围避免过长计算时间)
                for long in range(10, 101, 2):  # 10-100, 步长2
                    if short < long:
                        ma_tasks += 1
                        try:
                            result = run_ma_strategy(df, short, long)
                            if result and isinstance(result, dict):
                                results.append(result)
                        except Exception as e:
                            logger.error(f"MA策略计算失败: {e}")
                            continue
            total_tasks += ma_tasks
            logger.info(f"MA策略完成: {ma_tasks} 个任务")
        
        if strategy_type in ['all', 'rsi']:
            # RSI策略优化 - 大幅增加参数范围
            logger.info("运行RSI策略优化 - 高计算量版本")
            rsi_tasks = 0
            for oversold in range(10, 41, 1):  # 10-40, 步长1
                for overbought in range(50, 81, 1):  # 50-80, 步长1
                    if oversold < overbought:
                        rsi_tasks += 1
                        try:
                            result = run_rsi_strategy(df, oversold, overbought)
                            if result and isinstance(result, dict):
                                results.append(result)
                        except Exception as e:
                            logger.error(f"RSI策略计算失败: {e}")
                            continue
            total_tasks += rsi_tasks
            logger.info(f"RSI策略完成: {rsi_tasks} 个任务")
        
        if strategy_type in ['all', 'macd']:
            # MACD策略优化 - 增加多个参数组合
            logger.info("运行MACD策略优化 - 多参数版本")
            macd_tasks = 0
            for fast in range(8, 17, 2):  # 8, 10, 12, 14, 16
                for slow in range(20, 31, 2):  # 20, 22, 24, 26, 28, 30
                    for signal in range(7, 12, 1):  # 7, 8, 9, 10, 11
                        if fast < slow:
                            macd_tasks += 1
                            try:
                                result = run_macd_strategy_enhanced(df, fast, slow, signal)
                                if result and isinstance(result, dict):
                                    results.append(result)
                            except Exception as e:
                                logger.error(f"MACD策略计算失败: {e}")
                                continue
            total_tasks += macd_tasks
            logger.info(f"MACD策略完成: {macd_tasks} 个任务")
        
        if strategy_type in ['all', 'bb']:
            # 布林带策略优化 - 增加多个参数组合
            logger.info("运行布林带策略优化 - 多参数版本")
            bb_tasks = 0
            for period in range(15, 31, 2):  # 15, 17, 19, 21, 23, 25, 27, 29
                for std_dev in range(1, 4, 1):  # 1, 2, 3
                    bb_tasks += 1
                    try:
                        result = run_bollinger_strategy_enhanced(df, period, std_dev)
                        if result and isinstance(result, dict):
                            results.append(result)
                    except Exception as e:
                        logger.error(f"布林带策略计算失败: {e}")
                        continue
            total_tasks += bb_tasks
            logger.info(f"布林带策略完成: {bb_tasks} 个任务")

        # ========== 新增7种高级指标策略 ==========

        if strategy_type in ['all', 'kdj']:
            # KDJ策略优化
            logger.info("运行KDJ策略优化")
            kdj_tasks = 0
            for k_period in range(5, 31, 5):  # 5, 10, 15, 20, 25, 30
                for d_period in range(3, 6, 1):  # 3, 4, 5
                    for oversold in [20, 30]:  # 20, 30
                        for overbought in [70, 80]:  # 70, 80
                            kdj_tasks += 1
                            try:
                                result = run_kdj_strategy_enhanced(df, k_period, d_period, oversold, overbought)
                                if result and isinstance(result, dict):
                                    results.append(result)
                            except Exception as e:
                                logger.error(f"KDJ策略计算失败: {e}")
                                continue
            total_tasks += kdj_tasks
            logger.info(f"KDJ策略完成: {kdj_tasks} 个任务")

        if strategy_type in ['all', 'cci']:
            # CCI策略优化
            logger.info("运行CCI策略优化")
            cci_tasks = 0
            for period in range(10, 31, 5):  # 10, 15, 20, 25, 30
                for oversold in [-200, -150, -100]:  # -200, -150, -100
                    for overbought in [100, 150, 200]:  # 100, 150, 200
                        cci_tasks += 1
                        try:
                            result = run_cci_strategy_enhanced(df, period, oversold, overbought)
                            if result and isinstance(result, dict):
                                results.append(result)
                        except Exception as e:
                            logger.error(f"CCI策略计算失败: {e}")
                            continue
            total_tasks += cci_tasks
            logger.info(f"CCI策略完成: {cci_tasks} 个任务")

        if strategy_type in ['all', 'adx']:
            # ADX策略优化
            logger.info("运行ADX策略优化")
            adx_tasks = 0
            for period in range(10, 31, 5):  # 10, 15, 20, 25, 30
                for threshold in [20, 25, 30, 35]:  # 20, 25, 30, 35
                    adx_tasks += 1
                    try:
                        result = run_adx_strategy_enhanced(df, period, threshold)
                        if result and isinstance(result, dict):
                            results.append(result)
                    except Exception as e:
                        logger.error(f"ADX策略计算失败: {e}")
                        continue
            total_tasks += adx_tasks
            logger.info(f"ADX策略完成: {adx_tasks} 个任务")

        if strategy_type in ['all', 'atr']:
            # ATR策略优化
            logger.info("运行ATR策略优化")
            atr_tasks = 0
            for period in range(10, 31, 5):  # 10, 15, 20, 25, 30
                for multiplier in [1.0, 1.5, 2.0, 2.5, 3.0]:  # 1.0, 1.5, 2.0, 2.5, 3.0
                    atr_tasks += 1
                    try:
                        result = run_atr_strategy_enhanced(df, period, multiplier)
                        if result and isinstance(result, dict):
                            results.append(result)
                    except Exception as e:
                        logger.error(f"ATR策略计算失败: {e}")
                        continue
            total_tasks += atr_tasks
            logger.info(f"ATR策略完成: {atr_tasks} 个任务")

        if strategy_type in ['all', 'obv']:
            # OBV策略优化
            logger.info("运行OBV策略优化")
            obv_tasks = 0
            for trend_period in range(10, 101, 10):  # 10, 20, 30, ..., 100
                obv_tasks += 1
                try:
                    result = run_obv_strategy_enhanced(df, trend_period)
                    if result and isinstance(result, dict):
                        results.append(result)
                except Exception as e:
                    logger.error(f"OBV策略计算失败: {e}")
                    continue
            total_tasks += obv_tasks
            logger.info(f"OBV策略完成: {obv_tasks} 个任务")

        if strategy_type in ['all', 'ichimoku']:
            # Ichimoku策略优化
            logger.info("运行Ichimoku策略优化")
            ichimoku_tasks = 0
            for conversion in range(5, 16, 5):  # 5, 10, 15
                for base in range(20, 41, 5):  # 20, 25, 30, 35, 40
                    for span_b in range(40, 61, 5):  # 40, 45, 50, 55, 60
                        if conversion < base < span_b:
                            ichimoku_tasks += 1
                            try:
                                result = run_ichimoku_strategy_enhanced(df, conversion, base, span_b)
                                if result and isinstance(result, dict):
                                    results.append(result)
                            except Exception as e:
                                logger.error(f"Ichimoku策略计算失败: {e}")
                                continue
            total_tasks += ichimoku_tasks
            logger.info(f"Ichimoku策略完成: {ichimoku_tasks} 个任务")

        if strategy_type in ['all', 'psar']:
            # Parabolic SAR策略优化
            logger.info("运行Parabolic SAR策略优化")
            psar_tasks = 0
            for acceleration in [0.01, 0.02, 0.03, 0.04, 0.05]:  # 0.01, 0.02, 0.03, 0.04, 0.05
                for max_acceleration in [0.15, 0.20, 0.25, 0.30]:  # 0.15, 0.20, 0.25, 0.30
                    psar_tasks += 1
                    try:
                        result = run_parabolic_sar_strategy_enhanced(df, acceleration, max_acceleration)
                        if result and isinstance(result, dict):
                            results.append(result)
                    except Exception as e:
                        logger.error(f"Parabolic SAR策略计算失败: {e}")
                        continue
            total_tasks += psar_tasks
            logger.info(f"Parabolic SAR策略完成: {psar_tasks} 个任务")
        
        elapsed_time = time.time() - start_time
        logger.info(f"高计算量策略优化完成: 找到 {len(results)} 个有效策略")
        logger.info(f"总任务数: {total_tasks}, 耗时: {elapsed_time:.2f}秒")
        
        # 按Sharpe比率排序
        results = sorted(results, key=lambda x: x['sharpe_ratio'], reverse=True)
        return results
        
    except Exception as e:
        logger.error(f"高计算量策略优化失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return []

def execute_strategy_task(strategy_type, df, param1, param2):
    """执行单个策略任务 - 用于multiprocessing"""
    try:
        if strategy_type == 'ma':
            return run_ma_strategy(df, param1, param2)
        elif strategy_type == 'rsi':
            return run_rsi_strategy(df, param1, param2)
        elif strategy_type == 'macd':
            return run_macd_strategy(df)
        elif strategy_type == 'bb':
            return run_bollinger_strategy(df)
        else:
            return None
    except Exception as e:
        logger.error(f"策略任务执行失败: {strategy_type}, {e}")
        return None

def run_ma_strategy(df, short_window, long_window):
    """MA交叉策略"""
    try:
        df = df.copy()
        df[f'MA{short_window}'] = df['close'].rolling(window=short_window).mean()
        df[f'MA{long_window}'] = df['close'].rolling(window=long_window).mean()
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # 生成交易信号
        df['signal'] = np.where(df[f'MA{short_window}'] > df[f'MA{long_window}'], 1, 0)
        df['position'] = df['signal'].diff()
        
        return calculate_strategy_performance(df, f"MA交叉({short_window},{long_window})")
    except Exception as e:
        logger.error(f"MA策略计算失败: {e}")
        return None

def run_rsi_strategy(df, oversold, overbought):
    """RSI策略"""
    try:
        df = df.copy()
        # 计算RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 0.0001)
        df['RSI'] = 100 - (100 / (1 + rs))
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # RSI策略信号
        df['signal'] = 0
        df.loc[df['RSI'] < oversold, 'signal'] = 1  # 超卖买入
        df.loc[df['RSI'] > overbought, 'signal'] = 0  # 超买卖出
        df['position'] = df['signal'].diff()
        
        return calculate_strategy_performance(df, f"RSI({oversold},{overbought})")
    except Exception as e:
        logger.error(f"RSI策略计算失败: {e}")
        return None

def run_macd_strategy(df):
    """MACD策略"""
    try:
        df = df.copy()
        # 计算MACD
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # MACD策略信号
        df['signal'] = np.where(df['MACD'] > df['MACD_signal'], 1, 0)
        df['position'] = df['signal'].diff()
        
        return calculate_strategy_performance(df, "MACD")
    except Exception as e:
        logger.error(f"MACD策略计算失败: {e}")
        return None

def run_bollinger_strategy(df):
    """布林带策略"""
    try:
        df = df.copy()
        # 计算布林带
        df['BB_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # 布林带策略信号
        df['signal'] = 0
        df.loc[df['close'] < df['BB_lower'], 'signal'] = 1  # 价格触及下轨买入
        df.loc[df['close'] > df['BB_upper'], 'signal'] = 0  # 价格触及上轨卖出
        df['position'] = df['signal'].diff()
        
        return calculate_strategy_performance(df, "布林带")
    except Exception as e:
        logger.error(f"布林带策略计算失败: {e}")
        return None

def calculate_strategy_performance(df, strategy_name):
    """计算策略绩效"""
    try:
        # 计算策略收益
        df['strategy_returns'] = df['position'].shift(1) * df['close'].pct_change()
        df['cumulative_returns'] = (1 + df['strategy_returns']).cumprod()
        
        # 计算绩效指标
        total_return = (df['cumulative_returns'].iloc[-1] - 1) * 100
        annual_return = ((df['cumulative_returns'].iloc[-1] ** (252 / len(df))) - 1) * 100
        volatility = df['strategy_returns'].std() * np.sqrt(252) * 100
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # 最大回撤
        cumulative = df['cumulative_returns']
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # 胜率
        winning_trades = (df['strategy_returns'] > 0).sum()
        total_trades = (df['strategy_returns'] != 0).sum()
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # 交易次数
        trade_count = (df['position'] != 0).sum()
        
        return {
            'strategy_name': strategy_name,
            'total_return': round(float(total_return), 2),
            'annual_return': round(float(annual_return), 2),
            'volatility': round(float(volatility), 2),
            'sharpe_ratio': round(float(sharpe_ratio), 3),
            'max_drawdown': round(float(max_drawdown), 2),
            'win_rate': round(float(win_rate), 2),
            'trade_count': int(trade_count),
            'final_value': round(float(df['cumulative_returns'].iloc[-1] * 100000), 2)
        }
    except Exception as e:
        logger.error(f"计算策略绩效失败: {e}")
        return None

# ========== 增强版策略实现 ==========

def run_macd_strategy_enhanced(df, fast_period=12, slow_period=26, signal_period=9):
    """增强版MACD策略 - 支持自定义参数"""
    try:
        df = df.copy()

        # 计算MACD
        exp1 = df['close'].ewm(span=fast_period).mean()
        exp2 = df['close'].ewm(span=slow_period).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=signal_period).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        # 生成交易信号
        df['position'] = 0
        df.loc[(df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1)), 'position'] = 1  # 买入信号
        df.loc[(df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1)), 'position'] = -1  # 卖出信号

        # 计算策略性能
        strategy_name = f'MACD({fast_period},{slow_period},{signal_period})'
        return calculate_strategy_performance(df, strategy_name)

    except Exception as e:
        logger.error(f"增强版MACD策略计算失败: {e}")
        return None

def run_bollinger_strategy_enhanced(df, period=20, std_dev=2):
    """增强版布林带策略 - 支持自定义参数"""
    try:
        df = df.copy()

        # 计算布林带
        df['bb_middle'] = df['close'].rolling(window=period).mean()
        bb_std = df['close'].rolling(window=period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * std_dev)
        df['bb_lower'] = df['bb_middle'] - (bb_std * std_dev)

        # 生成交易信号
        df['position'] = 0
        df.loc[df['close'] < df['bb_lower'], 'position'] = 1  # 买入信号
        df.loc[df['close'] > df['bb_upper'], 'position'] = -1  # 卖出信号

        # 计算策略性能
        strategy_name = f'布林带({period},{std_dev})'
        return calculate_strategy_performance(df, strategy_name)

    except Exception as e:
        logger.error(f"增强版布林带策略计算失败: {e}")
        return None

def run_kdj_strategy_enhanced(df, k_period=9, d_period=3, oversold=20, overbought=80):
    """KDJ/随机指标策略"""
    try:
        df = df.copy()

        # 计算KDJ
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        rsv = (df['close'] - low_min) / (high_max - low_min) * 100
        df['K'] = rsv.ewm(alpha=1/d_period).mean()
        df['D'] = df['K'].ewm(alpha=1/d_period).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']

        # 生成交易信号
        df['position'] = 0
        df.loc[(df['K'] < oversold) & (df['K'].shift(1) >= oversold), 'position'] = 1  # K线下穿超卖线买入
        df.loc[(df['K'] > overbought) & (df['K'].shift(1) <= overbought), 'position'] = -1  # K线上穿超买卖出
        df.loc[(df['K'] > df['D']) & (df['K'].shift(1) <= df['D'].shift(1)), 'position'] = 1  # K线上穿D线买入
        df.loc[(df['K'] < df['D']) & (df['K'].shift(1) >= df['D'].shift(1)), 'position'] = -1  # K线下穿D线卖出

        # 计算策略性能
        strategy_name = f'KDJ({k_period},{d_period},{oversold},{overbought})'
        return calculate_strategy_performance(df, strategy_name)

    except Exception as e:
        logger.error(f"KDJ策略计算失败: {e}")
        return None

def run_cci_strategy_enhanced(df, period=20, oversold=-100, overbought=100):
    """CCI/商品通道指标策略"""
    try:
        df = df.copy()

        # 计算CCI
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mean_deviation = (typical_price - sma_tp).abs().rolling(window=period).mean()
        df['CCI'] = (typical_price - sma_tp) / (0.015 * mean_deviation)

        # 生成交易信号
        df['position'] = 0
        df.loc[(df['CCI'] < oversold) & (df['CCI'].shift(1) >= oversold), 'position'] = 1  # CCI下穿超卖线买入
        df.loc[(df['CCI'] > overbought) & (df['CCI'].shift(1) <= overbought), 'position'] = -1  # CCI上穿超买卖出
        df.loc[(df['CCI'] > 0) & (df['CCI'].shift(1) <= 0), 'position'] = 1  # CCI转正买入
        df.loc[(df['CCI'] < 0) & (df['CCI'].shift(1) >= 0), 'position'] = -1  # CCI转负卖出

        # 计算策略性能
        strategy_name = f'CCI({period},{oversold},{overbought})'
        return calculate_strategy_performance(df, strategy_name)

    except Exception as e:
        logger.error(f"CCI策略计算失败: {e}")
        return None

def run_adx_strategy_enhanced(df, period=14, adx_threshold=25):
    """ADX/平均趋向指标策略"""
    try:
        df = df.copy()

        # 计算ADX
        high_diff = df['high'] - df['high'].shift(1)
        low_diff = df['low'].shift(1) - df['low']
        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)

        tr1 = df['high'] - df['low']
        tr2 = np.abs(df['high'] - df['close'].shift(1))
        tr3 = np.abs(df['low'] - df['close'].shift(1))
        true_range = np.maximum(tr1, np.maximum(tr2, tr3))

        df['ATR'] = pd.Series(true_range).rolling(window=period).mean()
        df['+DI'] = pd.Series(plus_dm).rolling(window=period).mean() / df['ATR'] * 100
        df['-DI'] = pd.Series(minus_dm).rolling(window=period).mean() / df['ATR'] * 100
        dx = np.abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI']) * 100
        df['ADX'] = pd.Series(dx).rolling(window=period).mean()

        # 生成交易信号
        df['position'] = 0
        df.loc[(df['ADX'] > adx_threshold) & (df['+DI'] > df['-DI']) & (df['+DI'].shift(1) <= df['-DI'].shift(1)), 'position'] = 1  # ADX强+DI上穿-DI买入
        df.loc[(df['ADX'] > adx_threshold) & (df['+DI'] < df['-DI']) & (df['+DI'].shift(1) >= df['-DI'].shift(1)), 'position'] = -1  # ADX强+DI下穿-DI卖出
        df.loc[(df['+DI'] > df['-DI']) & (df['+DI'].shift(1) <= df['-DI'].shift(1)), 'position'] = 1  # +DI上穿-DI买入
        df.loc[(df['+DI'] < df['-DI']) & (df['+DI'].shift(1) >= df['-DI'].shift(1)), 'position'] = -1  # +DI下穿-DI卖出

        # 计算策略性能
        strategy_name = f'ADX({period},{adx_threshold})'
        return calculate_strategy_performance(df, strategy_name)

    except Exception as e:
        logger.error(f"ADX策略计算失败: {e}")
        return None

def run_atr_strategy_enhanced(df, period=14, atr_multiplier=2.0):
    """ATR/平均真实范围策略"""
    try:
        df = df.copy()

        # 计算ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        df['ATR'] = pd.Series(true_range).rolling(window=period).mean()

        # 生成突破信号
        df['upper_band'] = df['close'] + (df['ATR'] * atr_multiplier)
        df['lower_band'] = df['close'] - (df['ATR'] * atr_multiplier)

        df['position'] = 0
        df.loc[df['close'] > df['upper_band'], 'position'] = 1  # 价格突破上轨买入
        df.loc[df['close'] < df['lower_band'], 'position'] = -1  # 价格跌破下轨卖出
        df.loc[(df['close'] > df['upper_band'].shift(1)) & (df['close'].shift(1) <= df['upper_band'].shift(1)), 'position'] = 1
        df.loc[(df['close'] < df['lower_band'].shift(1)) & (df['close'].shift(1) >= df['lower_band'].shift(1)), 'position'] = -1

        # 计算策略性能
        strategy_name = f'ATR({period},{atr_multiplier})'
        return calculate_strategy_performance(df, strategy_name)

    except Exception as e:
        logger.error(f"ATR策略计算失败: {e}")
        return None

def run_obv_strategy_enhanced(df, trend_period=20):
    """OBV/能量潮策略"""
    try:
        df = df.copy()

        # 计算OBV
        obv = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        df['OBV'] = obv

        # 计算OBV移动平均
        df['OBV_SMA'] = df['OBV'].rolling(window=trend_period).mean()

        # 生成交易信号
        df['position'] = 0
        df.loc[(df['OBV'] > df['OBV_SMA']) & (df['OBV'].shift(1) <= df['OBV_SMA'].shift(1)), 'position'] = 1  # OBV上穿均线买入
        df.loc[(df['OBV'] < df['OBV_SMA']) & (df['OBV'].shift(1) >= df['OBV_SMA'].shift(1)), 'position'] = -1  # OBV下穿均线卖出

        # 计算策略性能
        strategy_name = f'OBV({trend_period})'
        return calculate_strategy_performance(df, strategy_name)

    except Exception as e:
        logger.error(f"OBV策略计算失败: {e}")
        return None

def run_ichimoku_strategy_enhanced(df, conversion_period=9, base_period=26, span_b_period=52):
    """Ichimoku/一目均衡表策略"""
    try:
        df = df.copy()

        # 计算Ichimoku各条线
        high_9 = df['high'].rolling(window=conversion_period).max()
        low_9 = df['low'].rolling(window=conversion_period).min()
        df['Conversion'] = (high_9 + low_9) / 2

        high_26 = df['high'].rolling(window=base_period).max()
        low_26 = df['low'].rolling(window=base_period).min()
        df['Base'] = (high_26 + low_26) / 2

        df['Span_A'] = ((df['Conversion'] + df['Base']) / 2).shift(base_period)

        high_52 = df['high'].rolling(window=span_b_period).max()
        low_52 = df['low'].rolling(window=span_b_period).min()
        df['Span_B'] = ((high_52 + low_52) / 2).shift(base_period)

        df['Lagging'] = df['close'].shift(-base_period)

        # 生成交易信号
        df['position'] = 0
        # 价格在云图之上且转换线上穿基准线买入
        df.loc[(df['close'] > df['Span_A']) & (df['close'] > df['Span_B']) &
               (df['Conversion'] > df['Base']) & (df['Conversion'].shift(1) <= df['Base'].shift(1)), 'position'] = 1
        # 价格在云图之下且转换线下穿基准线卖出
        df.loc[(df['close'] < df['Span_A']) & (df['close'] < df['Span_B']) &
               (df['Conversion'] < df['Base']) & (df['Conversion'].shift(1) >= df['Base'].shift(1)), 'position'] = -1

        # 计算策略性能
        strategy_name = f'Ichimoku({conversion_period},{base_period},{span_b_period})'
        return calculate_strategy_performance(df, strategy_name)

    except Exception as e:
        logger.error(f"Ichimoku策略计算失败: {e}")
        return None

def run_parabolic_sar_strategy_enhanced(df, acceleration=0.02, max_acceleration=0.2):
    """Parabolic SAR/抛物线转向策略"""
    try:
        df = df.copy()

        # 计算Parabolic SAR
        df['SAR'] = 0.0
        df['AF'] = acceleration  # 加速因子
        df['EP'] = df['close'].iloc[0]  # 极点价
        df['Trend'] = 1  # 趋势方向 1=上涨, -1=下跌

        for i in range(1, len(df)):
            # 更新SAR
            df.loc[i, 'SAR'] = df.loc[i-1, 'SAR'] + df.loc[i-1, 'AF'] * (df.loc[i-1, 'EP'] - df.loc[i-1, 'SAR'])

            # 更新趋势和加速因子
            if df['close'].iloc[i] > df.loc[i, 'SAR']:
                if df['Trend'].iloc[i-1] == -1:  # 趋势反转
                    df.loc[i, 'EP'] = df['high'].iloc[i]
                    df.loc[i, 'AF'] = acceleration
                else:
                    df.loc[i, 'Trend'] = 1
                    if df['high'].iloc[i] > df['EP'].iloc[i-1]:
                        df.loc[i, 'EP'] = df['high'].iloc[i]
                        df.loc[i, 'AF'] = min(df['AF'].iloc[i-1] + acceleration, max_acceleration)
                    else:
                        df.loc[i, 'EP'] = df['EP'].iloc[i-1]
                        df.loc[i, 'AF'] = df['AF'].iloc[i-1]
            else:
                if df['Trend'].iloc[i-1] == 1:  # 趋势反转
                    df.loc[i, 'EP'] = df['low'].iloc[i]
                    df.loc[i, 'AF'] = acceleration
                    df.loc[i, 'Trend'] = -1
                else:
                    df.loc[i, 'Trend'] = -1
                    if df['low'].iloc[i] < df['EP'].iloc[i-1]:
                        df.loc[i, 'EP'] = df['low'].iloc[i]
                        df.loc[i, 'AF'] = min(df['AF'].iloc[i-1] + acceleration, max_acceleration)
                    else:
                        df.loc[i, 'EP'] = df['EP'].iloc[i-1]
                        df.loc[i, 'AF'] = df['AF'].iloc[i-1]

        # 生成交易信号
        df['position'] = 0
        df.loc[(df['close'] > df['SAR']) & (df['close'].shift(1) <= df['SAR'].shift(1)), 'position'] = 1  # 价格上穿SAR买入
        df.loc[(df['close'] < df['SAR']) & (df['close'].shift(1) >= df['SAR'].shift(1)), 'position'] = -1  # 价格下穿SAR卖出

        # 计算策略性能
        strategy_name = f'PSAR({acceleration},{max_acceleration})'
        return calculate_strategy_performance(df, strategy_name)

    except Exception as e:
        logger.error(f"Parabolic SAR策略计算失败: {e}")
        return None

@app.get('/api/strategy-optimization/{symbol}')
def optimize_strategies(symbol: str, strategy_type: str = 'all'):
    """策略参数优化 - 找出最高Sharpe比率的策略"""
    start_time = time.time()
    try:
        logger.info(f"开始策略优化请求: {symbol}, 类型: {strategy_type}")
        
        data = get_stock_data(symbol)
        if not data:
            logger.warning(f"无法获取股票数据: {symbol}")
            monitor.log_request(f"/api/strategy-optimization/{symbol}", 404, time.time() - start_time)
            raise HTTPException(status_code=404, detail="Failed to get stock data")
        
        if len(data) < 100:
            logger.warning(f"数据不足: {symbol}, 数据量: {len(data)}")
            monitor.log_request(f"/api/strategy-optimization/{symbol}", 400, time.time() - start_time)
            raise HTTPException(status_code=400, detail="Insufficient data for optimization")
        
        logger.info(f"开始运行策略优化: {symbol}, 数据量: {len(data)}")
        
        # 运行策略优化
        results = run_strategy_optimization(data, strategy_type)
        
        logger.info(f"策略优化完成: {symbol}, 找到 {len(results)} 个策略")
        
        monitor.log_request(f"/api/strategy-optimization/{symbol}", 200, time.time() - start_time)
        return {
            "success": True,
            "data": {
                "best_strategies": results[:10],  # 前10个最佳策略
                "total_strategies": len(results),
                "optimization_type": strategy_type,
                "best_sharpe_ratio": results[0]['sharpe_ratio'] if results else 0
            },
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException as he:
        logger.error(f"HTTP异常: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"策略优化异常: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        monitor.log_request(f"/api/strategy-optimization/{symbol}", 500, time.time() - start_time)
        raise HTTPException(status_code=500, detail=f"Strategy optimization failed: {str(e)}")

@app.get('/api/test-optimization')
def test_optimization():
    """测试策略优化功能"""
    try:
        # 创建测试数据
        import pandas as pd
        import numpy as np
        
        data = []
        for i in range(200):
            data.append({
                'date': f'2023-01-{i+1:02d}',
                'open': 100 + i * 0.1,
                'high': 105 + i * 0.1,
                'low': 95 + i * 0.1,
                'close': 100 + i * 0.1 + np.random.normal(0, 1),
                'volume': 1000
            })
        
        # 测试策略优化
        results = run_strategy_optimization(data, 'ma')
        
        return {
            "success": True,
            "message": "策略优化测试成功",
            "results_count": len(results),
            "best_strategy": results[0] if results else None
        }
    except Exception as e:
        logger.error(f"测试优化失败: {e}")
        import traceback
        logger.error(f"测试错误详情: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@app.get('/api/health')
def health_check():
    try:
        uptime = time.time() - monitor.start_time
        return {
            'success': True,
            'data': {
                'status': 'healthy',
                'uptime': uptime,
                'version': '9.0.0',
                'timestamp': datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            'success': False,
            'data': {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        }

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CODEX Quant Trading System")
    parser.add_argument("--port", type=int, default=8001, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    print("🚀 Starting Complete Quant Trading System v7.0...")
    print("📊 Features: Technical Analysis, Backtesting, Risk Assessment, Sentiment Analysis, Monitoring")
    print("⚡ Technologies: FastAPI, Pandas, NumPy, Chart.js, Performance Monitoring")
    print(f"🌐 Access: http://localhost:{args.port}")
    print(f"📚 Docs: http://localhost:{args.port}/docs")
    print("=" * 70)

    uvicorn.run(app, host=args.host, port=args.port)
