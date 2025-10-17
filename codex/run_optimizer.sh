#!/bin/bash
# 股票回測策略優化器 - Linux/Mac Shell腳本
# 快速啟動腳本

echo "========================================"
echo "股票回測策略優化器"
echo "========================================"
echo ""

# 檢查是否提供了數據文件參數
if [ -z "$1" ]; then
    echo "用法: ./run_optimizer.sh [數據文件路徑] [可選:起始週期] [可選:結束週期] [可選:步距]"
    echo ""
    echo "示例:"
    echo "  ./run_optimizer.sh data.csv"
    echo "  ./run_optimizer.sh data.csv 1 100 2"
    echo "  ./run_optimizer.sh ../examples/raw_data_sample.csv"
    echo ""
    exit 1
fi

# 設置參數
DATA_FILE=$1
START_PERIOD=${2:-1}
END_PERIOD=${3:-300}
STEP=${4:-1}

echo "數據文件: $DATA_FILE"
echo "起始週期: $START_PERIOD"
echo "結束週期: $END_PERIOD"
echo "步距: $STEP"
echo ""
echo "開始優化..."
echo "========================================"
echo ""

# 執行優化器
python3 simple_strategy_optimizer.py --data "$DATA_FILE" --start $START_PERIOD --end $END_PERIOD --step $STEP --output results

echo ""
echo "========================================"
echo "優化完成！結果保存在 results/ 目錄"
echo "========================================"
