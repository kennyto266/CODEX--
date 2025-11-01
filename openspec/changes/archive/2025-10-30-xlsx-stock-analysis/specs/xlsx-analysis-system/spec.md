# xlsx Stock Analysis System Specification

## Overview
This specification defines the requirements for implementing an xlsx-based stock analysis system that generates professional Excel reports with comprehensive quantitative analysis.

## ADDED Requirements

### Data Processing Capability
The system shall process stock data and generate Excel reports with multiple worksheets.

#### Scenario: Processing 252 trading days of HKEX stock data
Given: A CSV file containing daily OHLCV data for 0001.HK from 2020-01-02 to 2021-01-07
When: The system runs the analysis engine
Then: It shall generate an analysis_results.json file with 15+ quantitative metrics

#### Scenario: Creating multi-worksheet Excel report
Given: Valid analysis results in JSON format
When: The create_xlsx_report.py script is executed
Then: It shall create an Excel file with 9 worksheets containing structured data

### Excel Formatting Capability
The system shall apply professional formatting to Excel reports.

#### Scenario: Applying conditional formatting to performance metrics
Given: A worksheet with stock performance data
When: The simple_enhance_xlsx.py script runs
Then: It shall apply color scaling and professional styling to the data

#### Scenario: Creating executive summary
Given: Analysis results with key metrics
When: The enhancement script executes
Then: It shall create an Executive Summary worksheet with formatted tables

### xlsx Skill Integration
The system shall utilize xlsx skills for advanced Excel manipulation.

#### Scenario: Multi-sheet management
Given: 9 categories of analysis data
When: Creating the Excel report
Then: The system shall create separate worksheets for each data category

#### Scenario: Professional report generation
Given: Raw analysis data
When: Enhancement script runs
Then: The system shall produce enterprise-grade Excel reports ready for business use

### API Integration
The system shall provide RESTful API endpoints for report generation.

#### Scenario: Starting analysis via API
Given: Valid analysis request with symbol and date range
When: POST /api/xlsx/analyze is called
Then: The system shall return a task_id and start processing asynchronously

#### Scenario: Checking analysis status
Given: A valid task_id
When: GET /api/xlsx/status/{task_id} is called
Then: The system shall return the current status and progress

#### Scenario: Downloading Excel report
Given: A completed analysis task
When: GET /api/xlsx/download/{task_id} is called
Then: The system shall return the Excel file as a download

### Multi-Agent System Integration
The system shall integrate with the existing multi-agent architecture.

#### Scenario: Agent-based report generation
Given: A message to generate a report
When: XlsxReportAgent receives the message
Then: The agent shall process the request and generate the report

#### Scenario: Automatic report generation
Given: A backtest completion signal
When: The signal is broadcast to agents
Then: XlsxReportAgent shall automatically generate a report

### Telegram Bot Integration
The system shall provide Telegram Bot interface for report generation.

#### Scenario: User requests report via Bot
Given: User sends /report command
When: Bot processes the command
Then: Bot shall guide user through report generation steps

#### Scenario: Receiving Excel file via Bot
Given: Report generation is complete
When: Bot sends the file to user
Then: User shall receive the enhanced Excel report

## MODIFIED Requirements

### Performance Metrics Calculation
The original system calculated basic metrics. The system shall now calculate enhanced metrics.

#### Scenario: Calculating Sharpe ratio
Given: Stock returns data
When: Running performance analysis
Then: The system shall compute Sharpe ratio with risk-free rate adjustment

#### Scenario: Computing maximum drawdown
Given: Cumulative return series
When: Running risk analysis
Then: The system shall identify the largest peak-to-trough decline

### Strategy Comparison
The system shall compare multiple trading strategies.

#### Scenario: BOLL vs RSI comparison
Given: Backtest results for BOLL and RSI strategies
When: Generating strategy comparison
Then: The system shall display side-by-side performance metrics

#### Scenario: Excess return calculation
Given: Strategy returns and buy-and-hold returns
When: Computing strategy performance
Then: The system shall calculate strategy excess returns over benchmark

## REMOVED Requirements

### Basic CSV Export
The system no longer requires simple CSV export functionality.

#### Scenario: Legacy CSV export
Given: Analysis results
When: System generates output
Then: It shall NOT export basic CSV files (replaced by Excel)

## RENAMED Requirements

### Analysis Engine → xlsx Stock Analyzer
The component formerly known as "analysis engine" is now the "xlsx Stock Analyzer".

#### Scenario: Component identification
Given: Source code references
When: Looking for analysis functionality
Then: The system shall use the term "XlsxStockAnalyzer" class

### Excel Report → Enhanced Excel Report
The output format is now called "Enhanced Excel Report" to distinguish from basic reports.

#### Scenario: File naming
Given: Generated Excel files
When: Creating output
Then: The system shall use "xlsx_stock_analysis_enhanced.xlsx" naming convention

## Implementation Details

### File Structure
```
xlsx_stock_analyzer.py          # Main analysis engine
create_xlsx_report.py           # Report generator
simple_enhance_xlsx.py          # Format enhancer
xlsx_stock_analysis_enhanced.xlsx  # Final output
src/dashboard/api_xlsx_analysis.py  # API endpoints
src/agents/xlsx_report_agent.py      # Agent integration
src/telegram_bot/xlsx_report_handler.py  # Bot integration
```

### Data Flow
1. CSV data → pandas DataFrame
2. DataFrame → analysis_results.json
3. JSON → Excel multi-worksheet
4. Excel → professional formatting
5. Formatted Excel → final report

### Technical Stack
- Python 3.10+
- pandas (data processing)
- openpyxl (Excel manipulation)
- xlsx skills (advanced features)
- FastAPI (API layer)
- asyncio (async processing)

## Validation Criteria

### Functional Requirements
- [x] Process 252+ trading days of data
- [x] Calculate 15+ quantitative metrics
- [x] Generate 9-worksheet Excel report
- [x] Apply professional formatting
- [x] Create executive summary
- [x] Produce enterprise-ready output
- [x] Provide RESTful API endpoints
- [x] Integrate with multi-agent system
- [x] Support Telegram Bot interface

### Quality Requirements
- [x] Execution time < 60 seconds
- [x] File size < 20KB
- [x] 100% data validation
- [x] Error-free report generation
- [x] Async task processing
- [x] Proper error handling

### Performance Requirements
- [x] API response time < 2 seconds
- [x] Support 5 concurrent tasks
- [x] Memory usage < 200MB
- [x] File I/O optimization

## Testing Scenarios

### Unit Test Scenario
Given: Individual components
When: Running isolated tests
Then: Each function shall pass its unit tests

### Integration Test Scenario
Given: Complete workflow
When: Running full analysis pipeline
Then: All steps shall execute successfully

### End-to-End Test Scenario
Given: CSV input file
When: Executing entire system
Then: Final Excel report shall match expected format and content

### API Test Scenario
Given: HTTP client
When: Calling API endpoints
Then: The system shall respond with correct data and status codes

### Agent Integration Test Scenario
Given: Multi-agent system
When: Sending report request to agent
Then: The agent shall process and respond correctly

### Telegram Bot Test Scenario
Given: Bot user
When: Sending commands to bot
Then: The bot shall guide user and deliver reports
