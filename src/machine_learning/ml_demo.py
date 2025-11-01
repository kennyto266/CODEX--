"""
机器学习预测系统演示
展示如何使用ML模型进行股票价格预测
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from ml_prediction_system import MLPredictionSystem
from feature_engineering import FeatureEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_sample_data(symbol: str = '0700.HK', days: int = 365) -> pd.DataFrame:
    """
    生成模拟股票数据

    Args:
        symbol: 股票代码
        days: 数据天数

    Returns:
        股票数据框
    """
    np.random.seed(42)

    # 生成日期
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')

    # 过滤工作日 (简化处理)
    dates = dates[dates.weekday < 5]

    # 生成价格数据
    n = len(dates)
    returns = np.random.normal(0.0005, 0.02, n)  # 日收益率

    # 添加趋势和波动率聚集
    for i in range(1, n):
        returns[i] += 0.1 * returns[i-1]  # 波动率聚集

    # 生成价格
    initial_price = 400.0  # 腾讯股价
    prices = [initial_price]

    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))

    # 生成OHLC
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # 生成开盘、最高、最低价格
        volatility = abs(np.random.normal(0, 0.01))
        open_price = close * (1 + np.random.normal(0, volatility))
        high_price = max(open_price, close) * (1 + abs(np.random.normal(0, 0.01)))
        low_price = min(open_price, close) * (1 - abs(np.random.normal(0, 0.01)))

        # 生成成交量
        volume = int(np.random.lognormal(15, 0.5))

        data.append({
            'timestamp': date,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close, 2),
            'volume': volume
        })

    return pd.DataFrame(data)


def demo_basic_usage():
    """演示基本用法"""
    print("\n" + "="*60)
    print("演示1: 基本ML预测系统使用")
    print("="*60)

    # 生成模拟数据
    print("\n1. 生成模拟股票数据...")
    data = generate_sample_data(days=500)
    print(f"   生成 {len(data)} 天的数据")
    print(f"   数据范围: {data['timestamp'].min()} 到 {data['timestamp'].max()}")

    # 初始化ML系统
    print("\n2. 初始化ML预测系统...")
    ml_system = MLPredictionSystem(models=['rf', 'xgboost'])
    print(f"   使用模型: {list(ml_system.models.keys())}")

    # 训练模型
    print("\n3. 训练模型...")
    train_results = ml_system.train_all_models(
        data,
        target_type='next_return',
        periods=1
    )

    # 显示训练结果
    print("\n4. 训练结果:")
    for model_name, result in train_results.items():
        if result.get('status') == 'success':
            if 'train_rmse' in result:
                print(f"   {model_name}: RMSE={result['train_rmse']:.6f}")
            elif 'train_accuracy' in result:
                print(f"   {model_name}: Accuracy={result['train_accuracy']:.4f}")

    # 预测
    print("\n5. 生成预测...")
    predictions = ml_system.predict(data[-30:])

    for model_name, pred in predictions.items():
        if len(pred) > 0:
            print(f"   {model_name}: 未来预测 = {pred[-1]:.6f}")

    # 生成交易信号
    print("\n6. 生成交易信号...")
    signal = ml_system.generate_signals(data[-60:], threshold=0.02)
    print(f"   信号: {signal['signal']}")
    print(f"   置信度: {signal['confidence']:.2%}")
    print(f"   预测值: {signal['prediction']:.6f}")


def demo_feature_engineering():
    """演示特征工程"""
    print("\n" + "="*60)
    print("演示2: 特征工程")
    print("="*60)

    # 生成数据
    print("\n1. 生成模拟数据...")
    data = generate_sample_data(days=200)
    print(f"   原始数据形状: {data.shape}")
    print(f"   原始特征数量: {len(data.columns)}")

    # 特征工程
    print("\n2. 执行特征工程...")
    feature_engine = FeatureEngine()
    features = feature_engine.create_all_features(data)
    print(f"   生成特征数量: {len(features.columns)}")

    # 显示部分特征
    print("\n3. 主要特征示例:")
    key_features = [col for col in features.columns if any(k in col.lower() for k in
                     ['sma', 'rsi', 'macd', 'bb', 'volume'])]
    for i, feature in enumerate(key_features[:10]):
        print(f"   {i+1}. {feature}")

    # 创建目标变量
    print("\n4. 创建目标变量...")
    target_return = feature_engine.create_target(data, 'next_return')
    target_direction = feature_engine.create_target(data, 'direction', threshold=0.01)

    print(f"   收益率目标: {len(target_return)} 个值")
    print(f"   方向目标: {len(target_direction)} 个值")


def demo_multiple_models():
    """演示多模型比较"""
    print("\n" + "="*60)
    print("演示3: 多模型比较")
    print("="*60)

    # 生成数据
    print("\n1. 生成模拟数据...")
    data = generate_sample_data(days=1000)

    # 测试不同模型
    model_configs = {
        'rf': ['rf'],
        'xgboost': ['xgboost'],
        'ensemble': ['rf', 'xgboost']
    }

    results = {}

    for name, models in model_configs.items():
        print(f"\n2. 测试 {name} 模型...")
        ml_system = MLPredictionSystem(models=models)

        # 训练
        train_results = ml_system.train_all_models(
            data[:-100],  # 使用前900天训练
            target_type='next_return'
        )

        # 预测测试集
        test_data = data[-100:]
        predictions = ml_system.predict(test_data)

        # 计算误差
        if predictions:
            pred_key = 'ensemble' if name == 'ensemble' else name
            if pred_key in predictions and len(predictions[pred_key]) > 0:
                actual_returns = test_data['close'].pct_change().iloc[1:].values
                pred_returns = predictions[pred_key][:len(actual_returns)]

                mse = np.mean((actual_returns - pred_returns) ** 2)
                mae = np.mean(np.abs(actual_returns - pred_returns))

                results[name] = {
                    'mse': mse,
                    'mae': mae,
                    'predictions': len(pred_returns)
                }

                print(f"   MSE: {mse:.8f}")
                print(f"   MAE: {mae:.8f}")

    # 比较结果
    print("\n3. 模型性能比较:")
    for model_name, metrics in results.items():
        print(f"   {model_name:12s}: MSE={metrics['mse']:.8f}, MAE={metrics['mae']:.8f}")


def demo_backtest():
    """演示回测"""
    print("\n" + "="*60)
    print("演示4: 策略回测")
    print("="*60)

    # 生成数据
    print("\n1. 生成模拟数据...")
    data = generate_sample_data(days=500)

    # 初始化系统
    print("\n2. 初始化ML系统...")
    ml_system = MLPredictionSystem(models=['rf'])

    # 回测
    print("\n3. 执行回测...")
    start_date = data['timestamp'].iloc[200].strftime('%Y-%m-%d')
    end_date = data['timestamp'].iloc[-1].strftime('%Y-%m-%d')

    backtest_results = ml_system.backtest_strategy(
        data=data,
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000
    )

    # 显示结果
    print("\n4. 回测结果:")
    if backtest_results:
        print(f"   总收益率: {backtest_results['total_return']:.2%}")
        print(f"   年化波动率: {backtest_results['volatility']:.2%}")
        print(f"   夏普比率: {backtest_results['sharpe_ratio']:.2f}")
        print(f"   最大回撤: {backtest_results['max_drawdown']:.2%}")
        print(f"   总交易次数: {backtest_results['total_trades']}")
        print(f"   最终价值: ${backtest_results['final_value']:,.2f}")
    else:
        print("   回测失败")


def demo_feature_importance():
    """演示特征重要性分析"""
    print("\n" + "="*60)
    print("演示5: 特征重要性分析")
    print("="*60)

    # 生成数据
    print("\n1. 生成模拟数据...")
    data = generate_sample_data(days=300)

    # 初始化系统
    print("\n2. 初始化ML系统...")
    ml_system = MLPredictionSystem(models=['rf', 'xgboost'])

    # 训练
    print("\n3. 训练模型...")
    train_results = ml_system.train_all_models(data)

    # 获取特征重要性
    print("\n4. 特征重要性分析:")
    for model_name, model in ml_system.models.items():
        if model.is_trained and hasattr(model, 'get_feature_importance'):
            importance = model.get_feature_importance()
            top_features = list(importance.items())[:10]

            print(f"\n   {model_name} - 前10个重要特征:")
            for i, (feature, score) in enumerate(top_features, 1):
                print(f"   {i:2d}. {feature:30s} {score:.4f}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("机器学习预测系统演示")
    print("="*60)

    try:
        # 演示1: 基本用法
        demo_basic_usage()

        # 演示2: 特征工程
        demo_feature_engineering()

        # 演示3: 多模型比较
        demo_multiple_models()

        # 演示4: 回测
        demo_backtest()

        # 演示5: 特征重要性
        demo_feature_importance()

        print("\n" + "="*60)
        print("所有演示完成!")
        print("="*60)

    except Exception as e:
        logger.error(f"演示过程中出错: {e}", exc_info=True)
        print(f"\n错误: {e}")


if __name__ == "__main__":
    main()
