# 🚀 港股量化交易 AI Agent 系统 - 运行指南

## 📋 系统要求

- **Python**: 3.9+ (推荐 3.10 或 3.11)
- **操作系统**: Windows 10/11, Linux, macOS
- **内存**: 至少 4GB RAM
- **磁盘空间**: 至少 2GB 可用空间

## 🎯 三种运行方式

### 方式1: 演示模式 ⭐⭐⭐ (推荐新手)

**最简单的方式，无需任何配置**

```bash
python demo.py
```

**特点**:
- ✅ 无需安装依赖
- ✅ 展示7个AI Agent功能
- ✅ 包含绩效分析和策略展示
- ✅ 适合快速体验系统

### 方式2: Web仪表板 ⭐⭐ (推荐日常使用)

**完整的Web界面，实时监控**

```bash
python start_web.py
```

**特点**:
- ✅ 现代化Web界面
- ✅ 实时监控Agent状态
- ✅ 远程控制功能
- ✅ 自动打开浏览器 (http://localhost:8000)

### 方式3: 完整系统 ⭐ (生产环境)

**需要Redis服务，功能最完整**

```bash
python start_dashboard.py dashboard
```

**特点**:
- ✅ 所有功能完整运行
- ✅ 需要Redis服务
- ✅ 适合生产环境

## 🔧 详细安装步骤

### 步骤1: 检查环境

```bash
# 检查Python版本
python --version

# 检查pip
pip --version
```

### 步骤2: 自动安装 (推荐)

```bash
python install.py
```

这个脚本会自动:
- 检查Python版本
- 安装所有依赖包
- 配置系统环境
- 验证安装结果

### 步骤3: 手动安装 (可选)

```bash
# 创建虚拟环境 (推荐)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

## 🚀 启动系统

### 快速启动 (推荐)

```bash
# 演示模式 - 无需配置
python demo.py

# Web仪表板 - 自动打开浏览器
python start_web.py

# 完整系统 - 需要Redis
python start_dashboard.py dashboard
```

### 手动启动

```bash
# 启动演示
python demo.py

# 启动简单Web服务器
python simple_web_dashboard.py

# 启动完整仪表板
python start_dashboard.py dashboard

# 启动真实系统
python start_real_system.py
```

## 🌐 访问界面

启动成功后，可以通过以下地址访问:

- **主仪表板**: http://localhost:8000
- **Agent详情**: http://localhost:8000/agent/{agent_id}
- **绩效分析**: http://localhost:8000/performance
- **系统状态**: http://localhost:8000/system

## 🔍 故障排除

### 问题1: "ModuleNotFoundError"

**解决方案**:
```bash
# 安装缺失的依赖
pip install fastapi uvicorn

# 或重新安装所有依赖
pip install -r requirements.txt
```

### 问题2: "localhost 拒絕連線"

**解决方案**:
1. **使用演示模式** (最简单)
   ```bash
   python demo.py
   ```

2. **检查端口占用**
   ```bash
   # Linux/macOS
   lsof -i :8000
   
   # Windows
   netstat -ano | findstr :8000
   ```

3. **使用不同端口**
   ```bash
   python start_web_port.py --port 8080
   ```

### 问题3: "Redis连接失败"

**解决方案**:
1. **使用演示模式** (无需Redis)
   ```bash
   python demo.py
   ```

2. **安装Redis** (Ubuntu/Debian)
   ```bash
   sudo apt update
   sudo apt install redis-server
   sudo systemctl start redis
   ```

3. **安装Redis** (Windows)
   ```bash
   # 使用WSL或Docker
   docker run -d -p 6379:6379 redis:alpine
   ```

### 问题4: "权限错误"

**解决方案**:
```bash
# Linux/macOS
chmod +x *.py

# Windows PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📊 系统组件说明

### AI Agent 组件

1. **量化分析师** - 技术分析和策略研究
2. **量化交易员** - 执行交易决策
3. **风险管理师** - 风险控制和监控
4. **投资组合经理** - 资产配置优化
5. **数据科学家** - 数据分析和建模
6. **研究分析师** - 市场研究和预测
7. **量化工程师** - 系统维护和优化

### 核心功能

- **实时监控**: WebSocket实时数据推送
- **策略管理**: 多策略并行运行
- **风险管理**: Sharpe比率和最大回撤计算
- **绩效分析**: 详细的绩效指标展示
- **系统控制**: 远程启动/停止Agent

## 🎮 使用示例

### 启动演示

```bash
python demo.py
```

输出示例:
```
🚀 港股量化交易 AI Agent 系统演示
=====================================

📊 Agent状态概览:
- 量化分析师: 运行中 (Sharpe: 1.85)
- 量化交易员: 运行中 (Sharpe: 2.10)
- 风险管理师: 运行中 (Sharpe: 1.95)
...

📈 系统绩效:
- 总收益率: 12.5%
- 夏普比率: 1.98
- 最大回撤: 5.2%
```

### 启动Web仪表板

```bash
python start_web.py
```

输出示例:
```
🌐 启动Web仪表板...
✅ 依赖检查通过
🚀 启动服务器: http://localhost:8000
🌍 自动打开浏览器...
✅ 仪表板已启动
```

## 📝 配置文件

### 环境配置

```bash
# 复制环境配置文件
cp env.example .env

# 编辑配置
nano .env
```

### 数据适配器配置

```bash
# 编辑数据适配器配置
nano config/data_adapters.json
```

## 🔄 更新系统

```bash
# 更新依赖
pip install -r requirements.txt --upgrade

# 重新安装
python install.py
```

## 📞 获取帮助

如果遇到问题，可以:

1. **查看日志文件**
   ```bash
   tail -f logs/system.log
   ```

2. **运行诊断脚本**
   ```bash
   python diagnose_imports.py
   ```

3. **查看详细文档**
   - `README.md` - 项目概述
   - `QUICK_START.md` - 快速开始
   - `TROUBLESHOOTING.md` - 故障排除

## 🎉 成功运行后

恭喜！您已经成功运行了港股量化交易 AI Agent 系统！

现在您可以:
- 📊 查看实时Agent状态
- 📈 分析交易绩效
- 🎛️ 控制Agent启停
- 📱 通过Web界面管理系统
- 🤖 体验7个AI Agent的协作

享受您的量化交易之旅！ 🚀