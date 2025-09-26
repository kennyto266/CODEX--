# 🔧 故障排除指南

## 🚨 常见问题解决方案

### 1. "localhost 拒絕連線" 或 "无法连接到此页面"

#### 问题原因
- Web服务器没有启动
- 端口被占用
- 防火墙阻止连接
- 依赖包缺失

#### 解决方案

**方案1: 使用演示模式 (推荐)**
```bash
python demo.py
```
- ✅ 无需Web服务器
- ✅ 展示完整功能
- ✅ 无需任何配置

**方案2: 启动Web服务器**
```bash
# 检查依赖
pip install fastapi uvicorn

# 启动Web服务器
python start_web.py
```

**方案3: 检查端口占用**
```bash
# Windows
netstat -ano | findstr :8000

# 如果端口被占用，更改端口
set PORT=8001
python simple_web_dashboard.py
```

### 2. "ModuleNotFoundError" 或依赖包错误

#### 问题原因
- Python包未安装
- 虚拟环境问题
- 版本不兼容

#### 解决方案
```bash
# 安装基础依赖
pip install fastapi uvicorn

# 安装完整依赖
pip install -r requirements.txt

# 如果还有问题，使用自动安装
python install.py
```

### 3. "Permission denied" 或权限错误

#### 问题原因
- 端口权限不足
- 文件权限问题
- 管理员权限需求

#### 解决方案
```bash
# 使用不同端口
set PORT=8080
python simple_web_dashboard.py

# 或使用演示模式
python demo.py
```

### 4. 浏览器无法访问

#### 问题原因
- 服务器未启动
- 错误的URL
- 浏览器缓存问题

#### 解决方案
1. **确认服务器状态**
   ```bash
   # 测试API
   curl http://localhost:8000/api/status
   ```

2. **尝试不同URL**
   - http://127.0.0.1:8000
   - http://localhost:8000
   - http://0.0.0.0:8000

3. **清除浏览器缓存**
   - 按 Ctrl+F5 强制刷新
   - 或使用无痕模式

### 5. 数据不显示或显示错误

#### 问题原因
- API连接失败
- 数据格式错误
- JavaScript错误

#### 解决方案
1. **检查浏览器控制台**
   - 按 F12 打开开发者工具
   - 查看 Console 标签页的错误信息

2. **测试API端点**
   ```bash
   # 测试Agent数据
   curl http://localhost:8000/api/agents
   
   # 测试系统状态
   curl http://localhost:8000/api/status
   ```

3. **使用演示模式**
   ```bash
   python demo.py
   ```

## 🛠️ 诊断工具

### 1. 系统检查脚本
```bash
# 创建诊断脚本
python -c "
import sys
print(f'Python版本: {sys.version}')

try:
    import fastapi
    print('✅ FastAPI已安装')
except ImportError:
    print('❌ FastAPI未安装')

try:
    import uvicorn
    print('✅ Uvicorn已安装')
except ImportError:
    print('❌ Uvicorn未安装')

import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('localhost', 8000))
if result == 0:
    print('❌ 端口8000已被占用')
else:
    print('✅ 端口8000可用')
sock.close()
"
```

### 2. 网络连接测试
```bash
# 测试本地连接
ping localhost

# 测试端口连接
telnet localhost 8000
```

### 3. 日志查看
```bash
# 查看Python错误日志
python simple_web_dashboard.py 2>&1 | tee dashboard.log

# 查看系统日志
tail -f logs/dashboard.log
```

## 🎯 快速解决方案

### 场景1: 完全无法启动
```bash
# 使用演示模式
python demo.py
```

### 场景2: Web界面无法访问
```bash
# 重新安装依赖
pip install fastapi uvicorn

# 启动Web服务器
python start_web.py
```

### 场景3: 端口被占用
```bash
# 使用不同端口
set PORT=8080
python simple_web_dashboard.py
```

### 场景4: 依赖包问题
```bash
# 使用自动安装
python install.py

# 或手动安装
pip install -r requirements.txt
```

## 🔍 详细诊断步骤

### 步骤1: 检查Python环境
```bash
python --version
# 应该显示 Python 3.9 或更高版本
```

### 步骤2: 检查依赖包
```bash
pip list | findstr fastapi
pip list | findstr uvicorn
```

### 步骤3: 测试基础功能
```bash
# 运行演示
python demo.py

# 如果演示成功，说明基础功能正常
```

### 步骤4: 测试Web服务器
```bash
# 启动Web服务器
python simple_web_dashboard.py

# 在另一个终端测试
curl http://localhost:8000/api/status
```

### 步骤5: 检查浏览器
- 尝试不同浏览器
- 清除缓存
- 检查JavaScript是否启用

## 📞 获取帮助

### 1. 查看文档
- **快速开始**: `QUICK_START.md`
- **使用指南**: `USAGE_GUIDE.md`
- **完整说明**: `HOW_TO_USE.md`

### 2. 运行诊断
```bash
# 自动诊断
python install.py

# 手动检查
python -c "import sys; print(sys.version); import fastapi; print('OK')"
```

### 3. 使用替代方案
```bash
# 如果Web界面有问题，使用演示模式
python demo.py

# 演示模式包含所有功能展示
```

## 🎉 成功指标

### 演示模式成功
- 显示7个AI Agent信息
- 显示绩效分析
- 显示策略信息
- 显示风险分析

### Web模式成功
- 浏览器可以访问 http://localhost:8000
- 显示Agent卡片
- 显示实时数据
- 可以执行控制操作

---

**如果以上方法都无法解决问题，请提供具体的错误信息，我会进一步协助您解决。** 🛠️
