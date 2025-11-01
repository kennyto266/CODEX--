@echo off
REM === 快速任務狀態更新命令 ===

REM 檢查參數
if "%1"=="" goto usage
if "%2"=="" goto usage

set TASK_ID=%1
set NEW_STATUS=%2

echo 更新任務 %TASK_ID% 狀態為: %NEW_STATUS%

python -c "import requests; r = requests.put('http://localhost:8000/tasks/%TASK_ID%/status', params={'new_status': '%NEW_STATUS%'}); print('更新成功!' if r.status_code == 200 else '更新失敗!')"

goto end

:usage
echo.
echo === 快速任務更新命令 ===
echo.
echo 用法:
echo   quick_task_commands.bat ^<任務ID^> ^<新狀態^>
echo.
echo 示例:
echo   quick_task_commands.bat TASK-100 進行中
echo   quick_task_commands.bat TASK-100 已完成
echo   quick_task_commands.bat TASK-100 待驗收
echo   quick_task_commands.bat TASK-100 已阻塞
echo.
echo 支持的狀態:
echo   - 待開始
echo   - 進行中
echo   - 待驗收
echo   - 已完成
echo   - 已阻塞
echo.

:end
