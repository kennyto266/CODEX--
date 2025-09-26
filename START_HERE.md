# 🚀 港股量化交易 AI Agent 系统 - 开始使用

## 🎯 立即开始 (3种方式)

### 方式1: 演示模式 ⭐⭐⭐ (推荐新手)
```bash
python demo.py
```
**特点**: 
- ✅ 无需任何配置
- ✅ 展示完整功能
- ✅ 包含7个AI Agent信息
- ✅ 绩效分析和策略展示

### 方式2: Web仪表板 ⭐⭐ (推荐日常使用)
```bash
python start_web.py
```
**特点**:
- ✅ 现代化Web界面
- ✅ 实时监控Agent状态
- ✅ 远程控制功能
- ✅ 自动打开浏览器

### 方式3: 简化Web服务器 ⭐ (手动启动)
```bash
python simple_web_dashboard.py
```
**特点**:
- ✅ 手动控制启动
- ✅ 自定义配置
- ✅ 适合开发调试

---

## 🔧 如果遇到问题

### 问题: "localhost 拒絕連線"
**解决方案**:
1. **使用演示模式** (最简单)
   ```bash
   python demo.py
   ```

2. **检查依赖包**
   ```bash
   pip install fastapi uvicorn
   ```

3. **使用不同端口**
   ```bash
   set PORT=8080
   python simple_web_dashboard.py
   ```

### 问题: 依赖包缺失
**解决方案**:
```bash
# 自动安装
python install.py

# 或手动安装
pip install fastapi uvicorn
```

### 问题: 端口被占用
**解决方案**:
```bash
# 查找占用进程
netstat -ano | findstr :8000

# 使用不同端口
set PORT=8080
python simple_web_dashboard.py
```

---

## 📊 系统功能预览

### 🤖 7个AI Agent
- **量化分析师**: 技术分析策略 (夏普比率: 1.85)
- **量化交易员**: 动量策略 (夏普比率: 2.10)
- **投资组合经理**: 风险平价策略 (夏普比率: 1.95)
- **风险分析师**: 对冲策略 (夏普比率: 1.75)
- **数据科学家**: 机器学习策略 (夏普比率: 2.25)
- **量化工程师**: 系统优化策略 (夏普比率: 1.65)
- **研究分析师**: 研究驱动策略 (夏普比率: 1.90)

### 📈 关键指标
- **平均夏普比率**: 1.92 (优秀)
- **平均收益率**: 12.86%
- **平均最大回撤**: 3.86%
- **总交易次数**: 1,095次

---

## 🌐 Web界面功能

### 主仪表板 (http://localhost:8000)
- **Agent状态监控**: 实时查看运行状态
- **资源使用监控**: CPU、内存使用情况
- **绩效指标**: 夏普比率、收益率、回撤
- **控制操作**: 启动/停止/重启Agent

### API接口
- **系统状态**: http://localhost:8000/api/status
- **Agent数据**: http://localhost:8000/api/agents
- **绩效数据**: http://localhost:8000/api/performance

---

## 🎮 使用示例

### 1. 快速体验
```bash
# 运行演示
python demo.py

# 查看7个AI Agent的完整信息
# 包括绩效分析、策略展示、风险控制
```

### 2. Web界面使用
```bash
# 启动Web服务器
python start_web.py

# 浏览器自动打开 http://localhost:8000
# 查看实时Agent状态和绩效指标
```

### 3. API调用示例
```bash
# 获取系统状态
curl http://localhost:8000/api/status

# 获取Agent数据
curl http://localhost:8000/api/agents

# 控制Agent
curl -X POST http://localhost:8000/api/agents/quant_analyst_001/control/start
```

---

## 📚 完整文档

- **🚀 快速开始**: [QUICK_START.md](QUICK_START.md)
- **📖 使用指南**: [USAGE_GUIDE.md](USAGE_GUIDE.md)
- **🎯 使用说明**: [HOW_TO_USE.md](HOW_TO_USE.md)
- **🔧 故障排除**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 🎉 立即开始

### 新手推荐
```bash
python demo.py
```

### 日常使用
```bash
python start_web.py
```

### 开发调试
```bash
python simple_web_dashboard.py
```

---

**您的港股量化交易AI Agent系统已经完全就绪！** 🎉

选择适合您的方式，立即开始体验7个专业AI Agent的量化交易系统！
