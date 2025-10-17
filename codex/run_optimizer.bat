@echo off
REM 股票回測策略優化器 - Windows批處理腳本
REM 快速啟動腳本

echo ========================================
echo 股票回測策略優化器
echo ========================================
echo.

REM 檢查是否提供了數據文件參數
if "%1"=="" (
    echo 用法: run_optimizer.bat [數據文件路徑] [可選:起始週期] [可選:結束週期] [可選:步距]
    echo.
    echo 示例:
    echo   run_optimizer.bat data.csv
    echo   run_optimizer.bat data.csv 1 100 2
    echo   run_optimizer.bat ..\examples\raw_data_sample.csv
    echo.
    pause
    exit /b 1
)

REM 設置默認參數
set DATA_FILE=%1
set START_PERIOD=%2
set END_PERIOD=%3
set STEP=%4

REM 如果未提供參數，使用默認值
if "%START_PERIOD%"=="" set START_PERIOD=1
if "%END_PERIOD%"=="" set END_PERIOD=300
if "%STEP%"=="" set STEP=1

echo 數據文件: %DATA_FILE%
echo 起始週期: %START_PERIOD%
echo 結束週期: %END_PERIOD%
echo 步距: %STEP%
echo.
echo 開始優化...
echo ========================================
echo.

REM 執行優化器
python simple_strategy_optimizer.py --data "%DATA_FILE%" --start %START_PERIOD% --end %END_PERIOD% --step %STEP% --output results

echo.
echo ========================================
echo 優化完成！結果保存在 results\ 目錄
echo ========================================
pause
