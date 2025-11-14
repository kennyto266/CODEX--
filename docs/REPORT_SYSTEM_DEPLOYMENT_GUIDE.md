# 自动化报告调度和邮件发送系统 - 部署指南

## 目录
1. [系统概述](#系统概述)
2. [依赖安装](#依赖安装)
3. [配置说明](#配置说明)
4. [部署步骤](#部署步骤)
5. [使用指南](#使用指南)
6. [监控和维护](#监控和维护)
7. [故障排除](#故障排除)
8. [最佳实践](#最佳实践)

## 系统概述

自动化报告调度和邮件发送系统提供以下功能：

### 核心模块

1. **参数配置 (params.py)**
   - 灵活的参数配置系统
   - 支持模板、数据源、图表、邮件和调度参数
   - YAML/JSON格式配置管理
   - 参数验证和克隆

2. **调度器 (scheduler.py)**
   - 基于APScheduler的定时任务调度
   - 支持Cron表达式
   - 任务状态监控
   - 失败重试机制
   - 执行历史记录

3. **邮件发送 (email_delivery.py)**
   - SMTP邮件发送
   - HTML邮件模板
   - 附件支持
   - 批量发送
   - 告警管理

4. **归档管理 (archive.py)**
   - 自动归档旧报告
   - 多种压缩格式
   - 版本控制
   - 存储空间管理
   - 快速检索

## 依赖安装

### 1. 基础依赖

确保已安装以下依赖：

```bash
pip install apscheduler==3.10.4
pip install jinja2==3.1.2
pip install python-multipart==0.0.6
```

### 2. 检查requirements.txt

确认项目根目录的requirements.txt包含：

```txt
# 调度器
APScheduler==3.10.4

# 邮件
jinja2==3.1.2
email-validator==2.1.0

# 数据处理
pydantic==2.9.2
pydantic-settings==2.6.0

# 其他依赖（已在项目中）
fastapi==0.115.0
uvicorn[standard]==0.30.6
pandas==2.2.3
numpy==2.1.3
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 配置说明

### 1. 创建配置文件

在项目根目录创建 `.env` 文件：

```env
# 邮件配置
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true

# 报告配置
REPORTS_DIR=reports
ARCHIVE_DIR=archive/reports
MAX_ARCHIVE_SIZE_GB=10.0
DEFAULT_RETENTION_DAYS=365

# 调度配置
SCHEDULER_TIMEZONE=Asia/Hong_Kong
MAX_WORKERS=4
```

### 2. 创建目录结构

```bash
mkdir -p reports
mkdir -p archive/reports
mkdir -p data/scheduler
mkdir -p data/archive
mkdir -p templates/email
mkdir -p config/reports
```

### 3. 配置邮件服务

#### Gmail配置

1. 开启两步验证
2. 生成应用专用密码
3. 使用应用密码而非账户密码

```python
from reports import EmailConfig

email_config = EmailConfig(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your_email@gmail.com",
    password="your_16_digit_app_password",
    recipients=["recipient@example.com"],
    use_tls=True
)
```

#### QQ邮箱配置

```python
email_config = EmailConfig(
    smtp_server="smtp.qq.com",
    smtp_port=587,
    username="your_email@qq.com",
    password="your_authorization_code",
    recipients=["recipient@example.com"],
    use_tls=True
)
```

## 部署步骤

### 步骤1: 准备环境

```bash
# 1. 克隆或更新项目
git pull origin main

# 2. 创建虚拟环境（如果需要）
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt
```

### 步骤2: 配置系统

创建配置文件 `config/reports/your_report.yaml`：

```yaml
report_id: "daily_portfolio"
name: "每日投资组合报告"
description: "每日生成投资组合表现报告"
template:
  name: "portfolio_template"
  path: "templates/portfolio.html"
  format: "html"
  variables:
    title: "投资组合日报"
data_source:
  type: "hkex"
  symbols: ["0700.HK", "0388.HK"]
  start_date: "2020-01-01"
  end_date: "2024-01-01"
  fields: ["open", "high", "low", "close", "volume"]
chart:
  width: 1200
  height: 800
  theme: "plotly_white"
email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  username: "your_email@gmail.com"
  password: "your_app_password"
  recipients:
    - "trader@example.com"
    - "manager@example.com"
  subject_template: "【日报】{name} - {report_date}"
  signature: "量化交易系统"
schedule:
  cron_expression: "0 9 * * 1-5"  # 每工作日上午9点
  timezone: "Asia/Hong_Kong"
  enabled: true
  max_retries: 3
  retry_delay: 60
output_path: "reports/daily_portfolio.html"
```

### 步骤3: 启动系统

#### 选项1: 集成到现有系统

```python
from src.reports import get_report_system

# 创建并启动报告系统
report_system = get_report_system()
report_system.start()

# 系统会自动加载所有计划任务
# ...
```

#### 选项2: 独立服务

创建文件 `report_service.py`：

```python
import asyncio
from src.reports import start_scheduler, get_params_manager

async def main():
    # 启动调度器
    scheduler = start_scheduler()

    # 保持运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

运行服务：

```bash
python report_service.py
```

### 步骤4: 创建systemd服务 (Linux)

创建文件 `/etc/systemd/system/quant-report.service`：

```ini
[Unit]
Description=Quant Report Scheduler
After=network.target

[Service]
Type=simple
User=quant
WorkingDirectory=/opt/quant-system
ExecStart=/opt/quant-system/.venv/bin/python report_service.py
Restart=always
RestartSec=10
Environment=PATH=/opt/quant-system/.venv/bin

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable quant-report
sudo systemctl start quant-report
sudo systemctl status quant-report
```

## 使用指南

### 1. 创建每日报告

```python
from reports import setup_daily_report

# 设置每日报告
setup_daily_report(
    report_id="daily_summary",
    name="每日摘要",
    symbol="0700.HK",
    recipients=["trader@example.com"]
)
```

### 2. 创建每周报告

```python
from reports import setup_weekly_report

setup_weekly_report(
    report_id="weekly_analysis",
    name="每周分析",
    symbol="0388.HK",
    recipients=["analyst@example.com"]
)
```

### 3. 立即执行报告

```python
from reports.scheduler import get_scheduler

scheduler = get_scheduler()
execution = scheduler.run_report_now("daily_summary")

if execution:
    print(f"执行ID: {execution.execution_id}")
```

### 4. 发送测试邮件

```python
from reports import send_test_email

send_test_email(
    smtp_server="smtp.gmail.com",
    username="your_email@gmail.com",
    password="your_app_password",
    recipients=["test@example.com"]
)
```

### 5. 管理归档

```python
from reports.archive import get_archive_manager

archive_manager = get_archive_manager()

# 列出所有归档
reports = archive_manager.list_archived_reports()
print(f"归档报告数: {len(reports)}")

# 清理过期报告
cleaned = archive_manager.cleanup_expired_reports()
print(f"已清理 {cleaned} 个过期报告")

# 检查存储使用
storage = archive_manager.check_storage_limit()
print(f"存储使用: {storage['usage_percent']}%")
```

## 监控和维护

### 1. 查看调度状态

```python
from reports.scheduler import get_scheduler

scheduler = get_scheduler()

# 列出所有任务
jobs = scheduler.list_scheduled_jobs()
for job in jobs:
    print(f"任务: {job['report_id']}, 下次运行: {job['next_run_time']}")

# 获取执行历史
history = scheduler.get_execution_history("daily_summary", limit=10)
for record in history:
    print(f"执行时间: {record.start_time}, 状态: {record.status.value}")

# 获取统计信息
stats = scheduler.get_statistics()
print(f"总任务数: {stats['total_scheduled_jobs']}")
print(f"成功率: {(stats['status_distribution']['SUCCESS'] / stats['total_executions'] * 100):.1f}%")
```

### 2. 查看邮件发送统计

```python
from reports.email_delivery import get_email_delivery

email_delivery = get_email_delivery()

# 获取发送历史
history = email_delivery.get_send_history(limit=50)
for result in history:
    print(f"邮件: {result.message}, 状态: {'成功' if result.success else '失败'}")

# 获取统计
stats = email_delivery.get_statistics()
print(f"发送成功率: {stats['success_rate']}%")
```

### 3. 设置日志

创建 `logging.conf`：

```ini
[loggers]
keys=root,reports

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler,fileHandler

[logger_reports]
level=INFO
handlers=consoleHandler,fileHandler
qualname=reports
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=INFO
formatter=simpleFormatter
args=('logs/reports.log',)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

配置日志：

```python
import logging
import logging.config

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('reports')
```

## 故障排除

### 问题1: 调度器不执行

**可能原因:**
- 调度器未启动
- Cron表达式错误
- 任务配置错误

**解决方法:**

```python
# 检查调度器状态
scheduler = get_scheduler()
print(f"调度器运行状态: {scheduler.scheduler.running}")

# 查看计划任务
jobs = scheduler.list_scheduled_jobs()
print(f"计划任务数: {len(jobs)}")

# 检查参数
params_manager = get_params_manager()
params = params_manager.get_params("your_report_id")
print(f"参数有效: {params is not None}")
```

### 问题2: 邮件发送失败

**可能原因:**
- SMTP配置错误
- 密码错误
- 防火墙阻止
- 收件人地址无效

**解决方法:**

```python
# 测试SMTP连接
email_delivery = get_email_delivery()
if email_delivery.test_connection():
    print("SMTP连接成功")
else:
    print("SMTP连接失败 - 检查配置")

# 查看发送错误
history = email_delivery.get_send_history(limit=1)
if history and not history[0].success:
    print(f"错误: {history[0].error}")
```

### 问题3: 归档失败

**可能原因:**
- 磁盘空间不足
- 权限不足
- 文件不存在

**解决方法:**

```python
# 检查存储空间
archive_manager = get_archive_manager()
storage = archive_manager.check_storage_limit()
print(f"存储使用: {storage['usage_percent']}%")

# 检查权限
import os
print(f"归档目录权限: {oct(os.stat('archive/reports').st_mode)}")
```

### 问题4: 任务卡住

**解决方法:**

```python
# 重启调度器
scheduler = get_scheduler()
scheduler.shutdown()
scheduler = get_scheduler()  # 获取新实例
scheduler.start()
```

## 最佳实践

### 1. 报告设计

- 保持报告简洁明了
- 使用一致的颜色方案
- 包含关键指标
- 添加时间戳

```python
chart_config = ChartConfig(
    width=1200,
    height=800,
    theme="plotly_white",
    color_scheme="Viridis",
    font_size=12,
    title_size=16
)
```

### 2. 邮件设置

- 使用HTML邮件提高可读性
- 设置清晰的主题
- 添加签名
- 控制收件人数量

```python
email_config = EmailConfig(
    subject_template="【{name}】{report_date}",
    signature="量化交易系统 - 自动发送",
    use_tls=True
)
```

### 3. 调度策略

- 避免高峰时段执行
- 合理设置重试次数
- 设置合适的超时时间
- 使用多个工作进程

```python
schedule_config = ScheduleConfig(
    cron_expression="0 9 * * 1-5",  # 避开市场开盘时间
    max_retries=3,
    retry_delay=60,
    timeout=3600
)
```

### 4. 归档管理

- 设置合理的保留期
- 定期清理过期报告
- 压缩旧报告节省空间
- 备份重要报告

```python
archive_manager = ArchiveManager(
    max_size_gb=10.0,
    default_retention_days=365
)

# 每月清理一次
import schedule
import time

schedule.every().month.do(archive_manager.cleanup_expired_reports)
```

### 5. 监控告警

- 监控任务执行状态
- 监控邮件发送失败
- 监控磁盘空间
- 设置告警通知

```python
from reports.email_delivery import EmailAlertManager

alert_manager = EmailAlertManager(email_delivery)

# 发送错误告警
alert_manager.send_error_alert(
    title="报告生成失败",
    error=str(error),
    context=context
)
```

## 总结

自动化报告调度和邮件发送系统提供了一套完整的报告自动化解决方案。通过合理配置和使用，可以显著提高报告生成和分发的效率。

如有问题，请参考故障排除部分或联系技术支持。
