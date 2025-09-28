# 🚀 Windows环境运行指南

## 🔍 问题诊断

您遇到的 `ModuleNotFoundError: No module named 'pydantic'` 错误是因为缺少必要的依赖包。

## 🛠️ 解决方案

### 方案1: 使用演示模式 (推荐)

**最简单的方式，无需安装依赖**

```powershell
python demo.py
```

这个命令应该可以正常工作，因为它不依赖外部包。

### 方案2: 安装依赖包

在PowerShell中运行：

```powershell
# 安装基本依赖
pip install pydantic fastapi uvicorn

# 或者安装所有依赖
pip install -r requirements.txt
```

### 方案3: 使用虚拟环境 (推荐)

```powershell
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行系统
python start_dashboard.py dashboard
```

## 🎯 推荐运行顺序

### 1. 首先测试演示模式

```powershell
python demo.py
```

这应该可以正常工作，展示7个AI Agent的功能。

### 2. 如果需要Web界面

```powershell
# 安装Web依赖
pip install fastapi uvicorn

# 启动Web界面
python start_web.py
```

### 3. 完整系统

```powershell
# 安装所有依赖
pip install -r requirements.txt

# 启动完整系统
python start_dashboard.py dashboard
```

## 🔧 故障排除

### 问题1: "pip不是内部或外部命令"

**解决方案**:
```powershell
# 使用python -m pip
python -m pip install pydantic fastapi uvicorn
```

### 问题2: "权限被拒绝"

**解决方案**:
```powershell
# 以管理员身份运行PowerShell
# 或者使用用户安装
pip install --user pydantic fastapi uvicorn
```

### 问题3: "虚拟环境激活失败"

**解决方案**:
```powershell
# 检查执行策略
Get-ExecutionPolicy

# 如果受限，设置策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 重新激活虚拟环境
.venv\Scripts\activate
```

## 📋 依赖包列表

如果手动安装，需要这些包：

```powershell
pip install pydantic
pip install fastapi
pip install uvicorn
pip install numpy
pip install pandas
pip install scikit-learn
pip install redis
pip install celery
pip install pytest
```

## 🎮 测试命令

### 测试演示模式
```powershell
python demo.py
```

### 测试Web依赖
```powershell
python -c "import fastapi, uvicorn; print('Web依赖已安装')"
```

### 测试完整依赖
```powershell
python -c "import pydantic, fastapi, uvicorn, numpy, pandas; print('所有依赖已安装')"
```

## 💡 建议

1. **首次使用**: 先运行 `python demo.py` 体验功能
2. **Web界面**: 安装fastapi和uvicorn后运行Web版本
3. **完整系统**: 安装所有依赖后运行完整版本

## 🆘 如果仍有问题

如果上述方法都不行，请尝试：

1. **检查Python版本**
   ```powershell
   python --version
   ```

2. **检查pip版本**
   ```powershell
   pip --version
   ```

3. **使用conda环境**
   ```powershell
   conda create -n hk_quant python=3.10
   conda activate hk_quant
   pip install -r requirements.txt
   ```

4. **查看详细错误**
   ```powershell
   python start_dashboard.py dashboard --verbose
   ```

## 🎉 成功运行后

一旦成功运行，您将看到：

- **演示模式**: 控制台显示7个AI Agent的状态和绩效
- **Web模式**: 浏览器打开 http://localhost:8000 显示仪表板
- **完整模式**: 所有功能正常运行，包括Redis连接

祝您使用愉快！ 🚀