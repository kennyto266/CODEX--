# 🚀 港股量化交易 AI Agent 系统 - 快速开始

## 一分钟快速体验

### 步骤1: 自动安装
```bash
python install.py
```

### 步骤2: 启动演示
```bash
python start_dashboard.py demo
```

### 步骤3: 启动仪表板
```bash
python start_dashboard.py dashboard
```

### 步骤4: 访问界面
打开浏览器访问: http://localhost:8000

---

## 🎯 三种使用模式

### 模式1: 演示模式 ⭐ (推荐新手)
```bash
python start_dashboard.py demo
```
- ✅ 无需外部依赖
- ✅ 快速体验系统功能
- ✅ 展示7个AI Agent交互

### 模式2: 仪表板模式 ⭐⭐ (推荐日常使用)
```bash
python start_dashboard.py dashboard
```
- ✅ 完整的Web界面
- ✅ 实时监控Agent状态
- ✅ 查看策略和绩效指标
- ✅ 远程控制Agent

### 模式3: 完整系统模式 ⭐⭐⭐ (生产环境)
```bash
python -m src.main
```
- ✅ 所有功能完整运行
- ✅ 需要Redis服务
- ✅ 适合生产环境

---

## 📊 仪表板功能介绍

### 主界面功能
- **Agent状态监控**: 实时查看7个AI Agent运行状态
- **策略信息展示**: 查看每个Agent的交易策略
- **绩效指标**: 夏普比率、收益率、回撤等关键指标
- **控制操作**: 启动/停止/重启Agent

### 访问地址
- 🏠 **主仪表板**: http://localhost:8000/
- 📈 **绩效分析**: http://localhost:8000/performance
- 🔧 **系统状态**: http://localhost:8000/system
- 📚 **API文档**: http://localhost:8000/docs

---

## 🔧 环境配置

### 最小配置 (演示模式)
```bash
# 无需额外配置，直接运行
python start_dashboard.py demo
```

### 标准配置 (仪表板模式)
```bash
# 可选：启动Redis (推荐)
docker run -d -p 6379:6379 redis:latest

# 启动仪表板
python start_dashboard.py dashboard
```

### 完整配置 (生产模式)
```bash
# 1. 启动Redis
docker run -d -p 6379:6379 redis:latest

# 2. 配置环境变量
cp env.example .env
# 编辑.env文件

# 3. 启动完整系统
python -m src.main
```

---

## 🎮 使用示例

### 查看Agent状态
```bash
curl http://localhost:8000/api/dashboard/agents
```

### 控制Agent
```bash
# 启动Agent
curl -X POST http://localhost:8000/api/dashboard/agents/quant_analyst_001/control/start

# 停止Agent
curl -X POST http://localhost:8000/api/dashboard/agents/quant_analyst_001/control/stop
```

### 查看绩效数据
```bash
curl http://localhost:8000/api/dashboard/performance
```

---

## 🆘 常见问题

### Q: 启动失败怎么办？
```bash
# 检查Python版本 (需要3.9+)
python --version

# 重新安装依赖
python install.py

# 查看日志
tail -f logs/dashboard.log
```

### Q: 端口被占用怎么办？
```bash
# 更改端口
export PORT=8001
python start_dashboard.py dashboard

# 或查找占用进程
netstat -ano | findstr :8000
```

### Q: Redis连接失败怎么办？
```bash
# 启动Redis (Docker)
docker run -d -p 6379:6379 redis:latest

# 或使用演示模式 (无需Redis)
python start_dashboard.py demo
```

---

## 📚 更多资源

- 📖 **详细使用指南**: [USAGE_GUIDE.md](USAGE_GUIDE.md)
- 🔧 **API文档**: [docs/api_reference.md](docs/api_reference.md)
- 👨‍💻 **开发指南**: [docs/developer_guide.md](docs/developer_guide.md)
- 🧪 **测试运行**: `pytest tests/`

---

## 🎉 开始使用

选择适合您的模式，立即开始体验港股量化交易AI Agent系统！

```bash
# 新手推荐
python start_dashboard.py demo

# 日常使用
python start_dashboard.py dashboard
```

**祝您使用愉快！** 🚀
