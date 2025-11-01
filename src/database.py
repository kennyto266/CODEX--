from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from typing import List, Optional
import os
from datetime import datetime
import logging
import json

logger = logging.getLogger('quant_system')

Base = declarative_base()

class StockData(Base):
    """股票数据表"""
    __tablename__ = 'stock_data'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    source = Column(String(50))  # 数据源

    def __repr__(self):
        return f"<StockData(symbol='{self.symbol}', timestamp='{self.timestamp}', close={self.close_price})>"

class StrategySignal(Base):
    """策略信号表"""
    __tablename__ = 'strategy_signals'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    strategy_name = Column(String(100), nullable=False)
    signal_type = Column(String(20))  # BUY, SELL, HOLD
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    parameters = Column(Text)  # JSON格式的参数

class MLModel(Base):
    """机器学习模型表"""
    __tablename__ = 'ml_models'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    model_type = Column(String(50))  # linear_regression, random_forest, lstm
    trained_at = Column(DateTime, default=datetime.utcnow)
    accuracy = Column(Float)
    parameters = Column(Text)  # JSON格式的模型参数
    model_path = Column(String(500))  # 模型文件路径

class User(Base):
    """用户表"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(20), default='user')  # admin, user
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)


class OptimizationRun(Base):
    """策略优化运行表 - 记录每次优化的元数据"""
    __tablename__ = 'optimization_runs'

    id = Column(Integer, primary_key=True)
    run_id = Column(String(50), unique=True, nullable=False, index=True)  # 唯一运行ID
    symbol = Column(String(20), nullable=False, index=True)  # 股票代码
    strategy_name = Column(String(100), nullable=False, index=True)  # 策略名称
    metric = Column(String(50), default='sharpe_ratio')  # 优化指标
    method = Column(String(50))  # 优化方法 (grid_search, random_search, etc)
    total_combinations = Column(Integer)  # 参数组合总数
    evaluated_combinations = Column(Integer, default=0)  # 已评估组合数
    status = Column(String(20), default='running')  # 状态: running, completed, failed
    best_parameters = Column(Text)  # JSON格式的最佳参数
    best_metrics = Column(Text)  # JSON格式的最佳指标
    train_ratio = Column(Float, default=0.7)  # 训练集比例
    start_time = Column(DateTime, default=datetime.utcnow)  # 开始时间
    end_time = Column(DateTime)  # 结束时间
    duration_seconds = Column(Float)  # 耗时（秒）
    error_message = Column(Text)  # 错误信息
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    results = relationship("OptimizationResult", back_populates="run", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index('idx_optimization_runs_symbol_strategy', 'symbol', 'strategy_name'),
        Index('idx_optimization_runs_created_at', 'created_at'),
    )


class OptimizationResult(Base):
    """优化结果表 - 记录每个参数组合的评估结果"""
    __tablename__ = 'optimization_results'

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey('optimization_runs.id'), nullable=False, index=True)
    rank = Column(Integer, index=True)  # 排名（按指标降序）
    param_hash = Column(String(32), index=True)  # 参数哈希（用于去重和缓存）
    parameters = Column(Text, nullable=False)  # JSON格式的参数
    metrics = Column(Text, nullable=False)  # JSON格式的性能指标

    # 性能指标（冗余存储以便快速查询）
    sharpe_ratio = Column(Float, index=True)
    annual_return = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    sortino_ratio = Column(Float)
    profit_loss_ratio = Column(Float)
    volatility = Column(Float)
    trade_count = Column(Integer)
    avg_holding_period = Column(Float)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    run = relationship("OptimizationRun", back_populates="results")

    # 索引
    __table_args__ = (
        Index('idx_optimization_results_run_rank', 'run_id', 'rank'),
        Index('idx_optimization_results_sharpe', 'run_id', 'sharpe_ratio'),
        Index('idx_optimization_results_param_hash', 'param_hash'),
    )


class GovernmentData(Base):
    """政府替代数据表"""
    __tablename__ = 'government_data'

    id = Column(Integer, primary_key=True)
    data_type = Column(String(50), nullable=False, index=True)  # hibor, property, retail, gdp, etc.
    category = Column(String(100), nullable=False)  # 数据分类
    indicator_name = Column(String(200), nullable=False)  # 指标名称
    value = Column(Float, nullable=False)  # 数值
    unit = Column(String(50))  # 单位
    period = Column(String(50))  # 时期（日、周、月、季度、年）
    source = Column(String(200))  # 数据源
    timestamp = Column(DateTime, nullable=False, index=True)  # 数据时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 索引
    __table_args__ = (
        Index('idx_gov_data_type_timestamp', 'data_type', 'timestamp'),
        Index('idx_gov_data_category_timestamp', 'category', 'timestamp'),
    )


class HKEXMarketData(Base):
    """香港交易所市场数据表"""
    __tablename__ = 'hkex_market_data'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)  # 股票代码
    date = Column(String(10), nullable=False, index=True)  # 交易日期 (YYYY-MM-DD)
    time = Column(String(10))  # 交易时间

    # OHLCV数据
    opening_price = Column(Float)  # 开盘价
    highest_price = Column(Float)  # 最高价
    lowest_price = Column(Float)  # 最低价
    closing_price = Column(Float)  # 收盘价
    trading_volume = Column(Integer)  # 交易量

    # 其他市场数据
    afternoon_close = Column(Float)  # 下午收盘价
    afternoon_volume = Column(Integer)  # 下午交易量
    turnover_per_deal = Column(Float)  # 每笔成交金额
    change_percent = Column(Float)  # 涨跌幅 (%)

    source = Column(String(50), default='hkex')  # 数据源
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 索引
    __table_args__ = (
        Index('idx_hkex_symbol_date', 'symbol', 'date'),
        Index('idx_hkex_symbol_timestamp', 'symbol', 'timestamp'),
    )


class CrawlerStatus(Base):
    """爬虫状态跟踪表"""
    __tablename__ = 'crawler_status'

    id = Column(Integer, primary_key=True)
    crawler_name = Column(String(50), nullable=False, unique=True, index=True)  # gov_crawler, hkex_crawler
    last_update = Column(DateTime, default=datetime.utcnow)  # 最后更新时间
    status = Column(String(20), default='active')  # active, failed, paused
    record_count = Column(Integer, default=0)  # 数据记录数
    last_data_point = Column(DateTime)  # 最后一条数据的时间戳
    error_message = Column(Text)  # 错误信息（如有）
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_crawler_status_name', 'crawler_name'),
    )


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        database_url = os.getenv('DATABASE_URL', 'sqlite:///codex_quant.db')
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # 创建表
        self.create_tables()

    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")

    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()

    def save_stock_data(self, symbol: str, data: dict, source: str = 'primary'):
        """保存股票数据"""
        session = self.get_session()
        try:
            stock_data = StockData(
                symbol=symbol,
                timestamp=datetime.fromisoformat(data['date']) if 'date' in data else datetime.utcnow(),
                open_price=data.get('open'),
                high_price=data.get('high'),
                low_price=data.get('low'),
                close_price=data['price'],
                volume=data.get('volume'),
                source=source
            )
            session.add(stock_data)
            session.commit()
            logger.info(f"Saved stock data for {symbol}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save stock data: {e}")
        finally:
            session.close()

    def get_stock_history(self, symbol: str, limit: int = 1000) -> List[dict]:
        """获取股票历史数据"""
        session = self.get_session()
        try:
            records = session.query(StockData).filter_by(symbol=symbol).order_by(
                StockData.timestamp.desc()
            ).limit(limit).all()

            return [{
                'symbol': record.symbol,
                'timestamp': record.timestamp.isoformat(),
                'open': record.open_price,
                'high': record.high_price,
                'low': record.low_price,
                'close': record.close_price,
                'volume': record.volume
            } for record in records]
        except Exception as e:
            logger.error(f"Failed to get stock history: {e}")
            return []
        finally:
            session.close()

    def save_strategy_signal(self, symbol: str, strategy_name: str, signal_type: str,
                           confidence: float, parameters: dict = None):
        """保存策略信号"""
        session = self.get_session()
        try:
            signal = StrategySignal(
                symbol=symbol,
                strategy_name=strategy_name,
                signal_type=signal_type,
                confidence=confidence,
                parameters=str(parameters) if parameters else None
            )
            session.add(signal)
            session.commit()
            logger.info(f"Saved strategy signal: {strategy_name} for {symbol}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save strategy signal: {e}")
        finally:
            session.close()

    def get_strategy_signals(self, symbol: str = None, limit: int = 100) -> List[dict]:
        """获取策略信号"""
        session = self.get_session()
        try:
            query = session.query(StrategySignal)
            if symbol:
                query = query.filter_by(symbol=symbol)

            signals = query.order_by(StrategySignal.timestamp.desc()).limit(limit).all()

            return [{
                'id': signal.id,
                'symbol': signal.symbol,
                'strategy_name': signal.strategy_name,
                'signal_type': signal.signal_type,
                'confidence': signal.confidence,
                'timestamp': signal.timestamp.isoformat(),
                'parameters': signal.parameters
            } for signal in signals]
        except Exception as e:
            logger.error(f"Failed to get strategy signals: {e}")
            return []
        finally:
            session.close()

    def save_ml_model(self, name: str, model_type: str, accuracy: float,
                     parameters: dict = None, model_path: str = None):
        """保存ML模型信息"""
        session = self.get_session()
        try:
            # 检查是否已存在
            existing = session.query(MLModel).filter_by(name=name).first()
            if existing:
                existing.trained_at = datetime.utcnow()
                existing.accuracy = accuracy
                existing.parameters = str(parameters) if parameters else None
                existing.model_path = model_path
            else:
                model = MLModel(
                    name=name,
                    model_type=model_type,
                    accuracy=accuracy,
                    parameters=str(parameters) if parameters else None,
                    model_path=model_path
                )
                session.add(model)

            session.commit()
            logger.info(f"Saved ML model: {name}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save ML model: {e}")
        finally:
            session.close()

    def get_ml_models(self) -> List[dict]:
        """获取所有ML模型"""
        session = self.get_session()
        try:
            models = session.query(MLModel).all()
            return [{
                'id': model.id,
                'name': model.name,
                'model_type': model.model_type,
                'trained_at': model.trained_at.isoformat(),
                'accuracy': model.accuracy,
                'model_path': model.model_path
            } for model in models]
        except Exception as e:
            logger.error(f"Failed to get ML models: {e}")
            return []
        finally:
            session.close()

    # ============ 优化相关方法 ============

    def save_optimization_run(self, run_id: str, symbol: str, strategy_name: str,
                            metric: str = 'sharpe_ratio', method: str = 'grid_search',
                            total_combinations: int = 0) -> Optional[int]:
        """保存优化运行记录"""
        session = self.get_session()
        try:
            opt_run = OptimizationRun(
                run_id=run_id,
                symbol=symbol,
                strategy_name=strategy_name,
                metric=metric,
                method=method,
                total_combinations=total_combinations,
                status='running'
            )
            session.add(opt_run)
            session.commit()
            run_db_id = opt_run.id
            logger.info(f"Saved optimization run: {run_id}")
            return run_db_id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save optimization run: {e}")
            return None
        finally:
            session.close()

    def save_optimization_result(self, run_id: int, rank: int, param_hash: str,
                                parameters: dict, metrics: dict) -> bool:
        """保存单个优化结果"""
        session = self.get_session()
        try:
            result = OptimizationResult(
                run_id=run_id,
                rank=rank,
                param_hash=param_hash,
                parameters=json.dumps(parameters),
                metrics=json.dumps(metrics),
                sharpe_ratio=metrics.get('sharpe_ratio'),
                annual_return=metrics.get('annual_return'),
                max_drawdown=metrics.get('max_drawdown'),
                win_rate=metrics.get('win_rate'),
                sortino_ratio=metrics.get('sortino_ratio'),
                profit_loss_ratio=metrics.get('profit_loss_ratio'),
                volatility=metrics.get('volatility'),
                trade_count=metrics.get('trade_count'),
                avg_holding_period=metrics.get('avg_holding_period')
            )
            session.add(result)
            session.commit()
            logger.debug(f"Saved optimization result for run {run_id}, rank {rank}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save optimization result: {e}")
            return False
        finally:
            session.close()

    def update_optimization_run(self, run_id: str, status: str, duration: float,
                               best_parameters: dict = None, best_metrics: dict = None,
                               error_message: str = None) -> bool:
        """更新优化运行状态和结果"""
        session = self.get_session()
        try:
            opt_run = session.query(OptimizationRun).filter_by(run_id=run_id).first()
            if not opt_run:
                logger.error(f"Optimization run not found: {run_id}")
                return False

            opt_run.status = status
            opt_run.end_time = datetime.utcnow()
            opt_run.duration_seconds = duration
            opt_run.updated_at = datetime.utcnow()

            if best_parameters:
                opt_run.best_parameters = json.dumps(best_parameters)
            if best_metrics:
                opt_run.best_metrics = json.dumps(best_metrics)
            if error_message:
                opt_run.error_message = error_message

            session.commit()
            logger.info(f"Updated optimization run: {run_id}, status: {status}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update optimization run: {e}")
            return False
        finally:
            session.close()

    def get_optimization_run(self, run_id: str) -> Optional[dict]:
        """获取优化运行详情"""
        session = self.get_session()
        try:
            opt_run = session.query(OptimizationRun).filter_by(run_id=run_id).first()
            if not opt_run:
                return None

            return {
                'run_id': opt_run.run_id,
                'symbol': opt_run.symbol,
                'strategy_name': opt_run.strategy_name,
                'metric': opt_run.metric,
                'method': opt_run.method,
                'status': opt_run.status,
                'total_combinations': opt_run.total_combinations,
                'evaluated_combinations': opt_run.evaluated_combinations,
                'best_parameters': json.loads(opt_run.best_parameters) if opt_run.best_parameters else None,
                'best_metrics': json.loads(opt_run.best_metrics) if opt_run.best_metrics else None,
                'duration_seconds': opt_run.duration_seconds,
                'start_time': opt_run.start_time.isoformat(),
                'end_time': opt_run.end_time.isoformat() if opt_run.end_time else None,
                'created_at': opt_run.created_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get optimization run: {e}")
            return None
        finally:
            session.close()

    def get_optimization_results(self, run_id: str, limit: int = 10) -> List[dict]:
        """获取优化结果（按排名前N个）"""
        session = self.get_session()
        try:
            opt_run = session.query(OptimizationRun).filter_by(run_id=run_id).first()
            if not opt_run:
                return []

            results = session.query(OptimizationResult).filter_by(
                run_id=opt_run.id
            ).order_by(OptimizationResult.rank).limit(limit).all()

            return [{
                'rank': r.rank,
                'parameters': json.loads(r.parameters),
                'metrics': json.loads(r.metrics),
                'sharpe_ratio': r.sharpe_ratio,
                'annual_return': r.annual_return,
                'max_drawdown': r.max_drawdown,
                'win_rate': r.win_rate,
                'trade_count': r.trade_count
            } for r in results]
        except Exception as e:
            logger.error(f"Failed to get optimization results: {e}")
            return []
        finally:
            session.close()

    def get_optimization_history(self, symbol: str = None, strategy_name: str = None,
                                limit: int = 20) -> List[dict]:
        """获取优化历史记录"""
        session = self.get_session()
        try:
            query = session.query(OptimizationRun)

            if symbol:
                query = query.filter_by(symbol=symbol)
            if strategy_name:
                query = query.filter_by(strategy_name=strategy_name)

            runs = query.order_by(OptimizationRun.created_at.desc()).limit(limit).all()

            return [{
                'run_id': r.run_id,
                'symbol': r.symbol,
                'strategy_name': r.strategy_name,
                'metric': r.metric,
                'status': r.status,
                'duration_seconds': r.duration_seconds,
                'best_sharpe_ratio': json.loads(r.best_metrics).get('sharpe_ratio') if r.best_metrics else None,
                'created_at': r.created_at.isoformat()
            } for r in runs]
        except Exception as e:
            logger.error(f"Failed to get optimization history: {e}")
            return []
        finally:
            session.close()

    # ============ 爬虫数据相关方法 ============

    def save_government_data(self, data_type: str, category: str, indicator_name: str,
                            value: float, unit: str = None, period: str = None,
                            source: str = None, timestamp: datetime = None) -> bool:
        """保存政府替代数据"""
        session = self.get_session()
        try:
            gov_data = GovernmentData(
                data_type=data_type,
                category=category,
                indicator_name=indicator_name,
                value=value,
                unit=unit,
                period=period,
                source=source,
                timestamp=timestamp or datetime.utcnow()
            )
            session.add(gov_data)
            session.commit()
            logger.debug(f"Saved government data: {data_type}/{indicator_name}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save government data: {e}")
            return False
        finally:
            session.close()

    def get_government_data(self, data_type: str = None, category: str = None,
                           limit: int = 1000) -> List[dict]:
        """获取政府替代数据"""
        session = self.get_session()
        try:
            query = session.query(GovernmentData)

            if data_type:
                query = query.filter_by(data_type=data_type)
            if category:
                query = query.filter_by(category=category)

            records = query.order_by(GovernmentData.timestamp.desc()).limit(limit).all()

            return [{
                'id': r.id,
                'data_type': r.data_type,
                'category': r.category,
                'indicator_name': r.indicator_name,
                'value': r.value,
                'unit': r.unit,
                'period': r.period,
                'source': r.source,
                'timestamp': r.timestamp.isoformat(),
                'created_at': r.created_at.isoformat()
            } for r in records]
        except Exception as e:
            logger.error(f"Failed to get government data: {e}")
            return []
        finally:
            session.close()

    def save_hkex_market_data(self, symbol: str, date: str, closing_price: float,
                             opening_price: float = None, highest_price: float = None,
                             lowest_price: float = None, trading_volume: int = None,
                             afternoon_close: float = None, afternoon_volume: int = None,
                             turnover_per_deal: float = None, change_percent: float = None,
                             time: str = None) -> bool:
        """保存HKEX市场数据"""
        session = self.get_session()
        try:
            hkex_data = HKEXMarketData(
                symbol=symbol,
                date=date,
                time=time,
                opening_price=opening_price,
                highest_price=highest_price,
                lowest_price=lowest_price,
                closing_price=closing_price,
                trading_volume=trading_volume,
                afternoon_close=afternoon_close,
                afternoon_volume=afternoon_volume,
                turnover_per_deal=turnover_per_deal,
                change_percent=change_percent
            )
            session.add(hkex_data)
            session.commit()
            logger.debug(f"Saved HKEX data: {symbol} on {date}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save HKEX market data: {e}")
            return False
        finally:
            session.close()

    def get_hkex_market_data(self, symbol: str = None, start_date: str = None,
                            end_date: str = None, limit: int = 1000) -> List[dict]:
        """获取HKEX市场数据"""
        session = self.get_session()
        try:
            query = session.query(HKEXMarketData)

            if symbol:
                query = query.filter_by(symbol=symbol)
            if start_date:
                query = query.filter(HKEXMarketData.date >= start_date)
            if end_date:
                query = query.filter(HKEXMarketData.date <= end_date)

            records = query.order_by(HKEXMarketData.date.desc()).limit(limit).all()

            return [{
                'id': r.id,
                'symbol': r.symbol,
                'date': r.date,
                'time': r.time,
                'opening_price': r.opening_price,
                'highest_price': r.highest_price,
                'lowest_price': r.lowest_price,
                'closing_price': r.closing_price,
                'trading_volume': r.trading_volume,
                'afternoon_close': r.afternoon_close,
                'afternoon_volume': r.afternoon_volume,
                'turnover_per_deal': r.turnover_per_deal,
                'change_percent': r.change_percent,
                'timestamp': r.timestamp.isoformat()
            } for r in records]
        except Exception as e:
            logger.error(f"Failed to get HKEX market data: {e}")
            return []
        finally:
            session.close()

    def update_crawler_status(self, crawler_name: str, status: str = 'active',
                             record_count: int = None, error_message: str = None) -> bool:
        """更新爬虫状态"""
        session = self.get_session()
        try:
            crawler_status = session.query(CrawlerStatus).filter_by(crawler_name=crawler_name).first()

            if not crawler_status:
                # 创建新的爬虫状态记录
                crawler_status = CrawlerStatus(
                    crawler_name=crawler_name,
                    status=status,
                    record_count=record_count or 0,
                    last_data_point=datetime.utcnow(),
                    error_message=error_message
                )
                session.add(crawler_status)
            else:
                # 更新现有记录
                crawler_status.status = status
                crawler_status.last_update = datetime.utcnow()
                if record_count is not None:
                    crawler_status.record_count = record_count
                if error_message:
                    crawler_status.error_message = error_message
                else:
                    crawler_status.error_message = None  # 清除错误信息

            session.commit()
            logger.info(f"Updated crawler status: {crawler_name}, status: {status}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update crawler status: {e}")
            return False
        finally:
            session.close()

    def get_crawler_status(self, crawler_name: str = None) -> List[dict]:
        """获取爬虫状态"""
        session = self.get_session()
        try:
            query = session.query(CrawlerStatus)

            if crawler_name:
                query = query.filter_by(crawler_name=crawler_name)

            records = query.all()

            return [{
                'crawler_name': r.crawler_name,
                'status': r.status,
                'record_count': r.record_count,
                'last_update': r.last_update.isoformat(),
                'last_data_point': r.last_data_point.isoformat() if r.last_data_point else None,
                'error_message': r.error_message,
                'created_at': r.created_at.isoformat()
            } for r in records]
        except Exception as e:
            logger.error(f"Failed to get crawler status: {e}")
            return []
        finally:
            session.close()

# 全局实例
db_manager = DatabaseManager()