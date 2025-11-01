@echo off
REM ================================================================
REM Daily Project Management Automation
REM This script runs automated project management tasks daily
REM ================================================================

echo.
echo ================================================================
echo   Daily Project Automation
echo   Date: %date% %time%
echo ================================================================
echo.

REM Run the automation workflow
python production_automation_workflow.py

REM Check if automation was successful
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================
    echo   Automation completed successfully
    echo ================================================================
    echo.
    echo Report saved to: automation_report_%date:~0,4%%date:~5,2%%date:~8,2%.txt
    echo.
) else (
    echo.
    echo ================================================================
    echo   ERROR: Automation failed
    echo ================================================================
    echo.
)

REM Optional: Send notification (uncomment if needed)
REM curl -X POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK -d '{"text":"Daily automation completed"}'

echo Automation script finished.
echo.
