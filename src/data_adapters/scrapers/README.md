# Web Scrapers for Alternative Data Collection

使用 chrome-devtools-mcp 加速开发的爬虫模块

## 使用工作流

### 1. 网页分析 (Chrome DevTools)
- 打开目标网站
- 检查DOM结构找数据位置
- 识别选择器和XPath

### 2. 爬虫开发 (Python)
- 编写BeautifulSoup/Selenium爬虫
- 使用找到的选择器
- 本地测试数据提取

### 3. 集成测试
- 集成到HKEXDataCollector
- 测试缓存和错误处理
- 性能优化

## 目标网站

### HKEX (hkex.com.hk)
- 期货成交量数据
- 期权市场数据  
- 市场动态指标

### 政府数据 (data.gov.hk)
- HIBOR利率数据
- 入境人数统计
- 贸易数据

### 旅游局 (tourism.gov.hk)
- 访港旅客数据
- 按来源地统计

## 快速开始

1. 使用chrome-devtools打开网站
2. 找到数据容器的CSS选择器
3. 生成爬虫代码
4. 在HKEXDataCollector/GovDataCollector中集成
