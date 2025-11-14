# Mini Hedge Fund Sprint 0 開發環境設置指南

**版本**: v1.0
**創建日期**: 2025年11月5日
**適用範圍**: Sprint 0 - 基礎設施與數據層
**文檔類型**: 開發環境設置與新開發者入門指南

---

## 目錄

1. [概述](#概述)
2. [系統要求](#系統要求)
3. [快速開始](#快速開始)
4. [詳細安裝步驟](#詳細安裝步驟)
5. [驗證環境](#驗證環境)
6. [開發工具鏈](#開發工具鏈)
7. [常用操作](#常用操作)
8. [故障排除](#故障排除)

---

## 概述

本指南將幫助您在30分鐘內完成Mini Hedge Fund系統的開發環境設置。Sprint 0專注於基礎設施與數據層建設，包括：

- **多數據庫架構**: PostgreSQL + InfluxDB + Redis
- **5層架構**: 表現層 → API層 → 應用層 → 數據層 → 基礎設施
- **35個宏觀指標**: HIBOR利率、GDP、零售數據等
- **數據適配器框架**: 可擴展的多數據源集成

---

## 系統要求

### 最低要求

- **操作系統**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+
- **Python**: 3.10 或更高版本
- **內存**: 8GB RAM (推薦 16GB)
- **磁盤空間**: 10GB 可用空間
- **網絡**: 穩定的互聯網連接

### 必需軟件

| 軟件 | 版本要求 | 用途 |
|------|----------|------|
| Docker | 24.0+ | 容器化服務 |
| Docker Compose | 2.20+ | 多服務編排 |
| Python | 3.10+ | 開發語言 |
| Git | 2.30+ | 版本控制 |

---

## 快速開始

如果您已安裝所有依賴，可以直接運行：

```bash
# Linux/macOS
./verify-env.sh

# Windows
verify-env.bat

# 如果檢查通過，啟動所有服務
docker-compose up -d
```

完整流程預計時間：**20-30分鐘**

---

## 詳細安裝步驟

### 步驟1: 安裝Docker

#### Windows/macOS

1. 訪問 [Docker官網](https://www.docker.com/products/docker-desktop)
2. 下載並安裝 Docker Desktop
3. 啟動 Docker Desktop
4. 驗證安裝：
```bash
docker --version
docker-compose --version
```

#### Ubuntu/Debian

```bash
# 更新包索引
sudo apt-get update

# 安裝必要包
sudo apt-get install apt-transport-https ca-certificates curl gnupg lsb-release

# 添加Docker官方GPG密鑰
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加軟件源
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安裝Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 啟動Docker
sudo systemctl start docker
sudo systemctl enable docker

# 將用戶添加到docker組
sudo usermod -aG docker $USER

# 重新登錄或運行
newgrp docker
```

### 步驟2: 安裝Python 3.10+

#### Windows

1. 訪問 [Python官網](https://www.python.org/downloads/)
2. 下載 Python 3.10 或更高版本
3. 安裝時勾選 "Add Python to PATH"
4. 驗證：
```cmd
python --version
```

#### macOS

```bash
# 使用 Homebrew
brew install python@3.10

# 或從官網下載安裝包
```

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev python3-pip

# 驗證
python3 --version
```

### 步驟3: 克隆項目

```bash
# 克隆項目
git clone <repository-url>
cd CODEX--

# 或解壓項目包
```

### 步驟4: 創建Python虛擬環境

```bash
# Windows
python -m venv .venv310
.venv310\Scripts\activate

# Linux/macOS
python3 -m venv .venv310
source .venv310/bin/activate

# 驗證虛擬環境
which python
# 應該指向 .venv310/bin/python
```

### 步驟5: 安裝依賴

```bash
# 升級pip
pip install --upgrade pip

# 安裝項目依賴
pip install -r requirements.txt

# 安裝開發依賴 (可選)
pip install -e .[dev]
```

**注意**: 如果TA-Lib安裝失敗，請參考[故障排除](#ta-lib安裝問題)章節。

### 步驟6: 配置環境變量

```bash
# 複製環境變量模板
cp .env.example .env

# 編輯配置文件 (Windows)
notepad .env

# 編輯配置文件 (Linux/macOS)
nano .env
```

編輯 `.env` 文件，設置必要的API密鑰和配置：

```env
# API服務配置
API_HOST=0.0.0.0
API_PORT=8001
ENVIRONMENT=development

# 數據庫配置
POSTGRES_USER=codex
POSTGRES_PASSWORD=codex_password
POSTGRES_DB=codex_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# InfluxDB配置 (Sprint 0新增)
INFLUXDB_HOST=localhost
INFLUXDB_PORT=8086
INFLUXDB_TOKEN=codex-admin-token-12345
INFLUXDB_ORG=codex
INFLUXDB_BUCKET=macro_indicators

# Telegram機器人 (可選)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 步驟7: 啟動服務

```bash
# 使用Docker Compose啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

**預期輸出**:
```
      Name                    Command               State                    Ports
--------------------------------------------------------------------------------------------------
codex-database-1   docker-entrypoint.sh postgres    Up      0.0.0.0:5432->5432/tcp
codex-redis-1      docker-entrypoint.sh redis ...   Up      0.0.0.0:6379->6379/tcp
codex-influxdb-1   /entrypoint.sh influxd           Up      0.0.0.0:8086->8086/tcp
codex-web-1        uvicorn main:app --host 0.0. ...  Up      0.0.0.0:8001->8001/tcp
```

---

## 驗證環境

### 自動驗證

運行環境驗證腳本：

```bash
# Linux/macOS
./verify-env.sh

# Windows
verify-env.bat
```

**預期結果**:
```
================================================
   Mini Hedge Fund 環境驗證
   Sprint 0 - US-001 Task 1.4
================================================

=== 1. 系統基礎檢查 ===
[✓ PASS] Docker 服務運行正常
[✓ PASS] Docker Compose 可用
[✓ PASS] Python3 可用
[✓ PASS] 虛擬環境已激活
[✓ PASS] 所有必需依賴包已安裝

=== 2. Docker 服務檢查 ===
[✓ PASS] 所有必需容器運行正常

=== 3. 數據庫服務檢查 ===
[✓ PASS] PostgreSQL 服務可達
[✓ PASS] Redis 服務可達
[✓ PASS] InfluxDB 服務可達

=== 4. API 端點檢查 ===
[✓ PASS] 主服務 API 響應正常 (HTTP 200)
[✓ PASS] InfluxDB UI 響應正常 (HTTP 200)
[✓ PASS] Grafana 響應正常 (HTTP 200)
[✓ PASS] Prometheus 響應正常 (HTTP 200)

=== 5. 代碼質量工具檢查 ===
[✓ PASS] Black 代碼格式化工具已安裝
[✓ PASS] isort 已安裝
[✓ PASS] flake8 已安裝
[✓ PASS] mypy 類型檢查已安裝
[✓ PASS] pre-commit 鉤子已安裝

================================================
               驗證摘要
================================================

總檢查項目: 16
通過項目: 16
失敗項目: 0

✓ 環境驗證全部通過！
```

### 手動驗證

如果自動驗證失敗，可以手動檢查：

```bash
# 1. 檢查服務端口
netstat -an | grep 5432  # PostgreSQL
netstat -an | grep 6379  # Redis
netstat -an | grep 8086  # InfluxDB
netstat -an | grep 8001  # Web API

# 2. 測試API端點
curl http://localhost:8001/api/health
curl http://localhost:8086/health

# 3. 測試數據庫連接
# PostgreSQL
psql -h localhost -U codex -d codex_db

# Redis
redis-cli ping

# InfluxDB
curl -H "Authorization: Token codex-admin-token-12345" \
     http://localhost:8086/health
```

### 訪問Web界面

驗證成功後，可以訪問以下界面：

| 服務 | URL | 說明 |
|------|-----|------|
| 主儀表板 | http://localhost:8001 | Mini Hedge Fund 主界面 |
| API文檔 | http://localhost:8001/docs | Swagger API文檔 |
| InfluxDB UI | http://localhost:8086 | 時序數據管理 |
| Grafana | http://localhost:3000 | 監控面板 (admin/admin123) |
| Prometheus | http://localhost:9090 | 指標監控 |

---

## 開發工具鏈

### 代碼格式化

項目已配置完整的代碼質量工具鏈：

```bash
# 格式化代碼
black src/ tests/
isort src/ tests/

# 檢查代碼風格
flake8 src/ tests/

# 類型檢查
mypy src/

# 安全檢查
bandit -r src/
```

### Pre-commit鉤子

設置預提交鉤子確保代碼質量：

```bash
# 安裝pre-commit
pip install pre-commit

# 安裝鉤子
pre-commit install

# 測試鉤子
pre-commit run --all-files
```

### 測試框架

運行測試：

```bash
# 運行所有測試
pytest

# 運行特定測試
pytest tests/test_core_functions.py -v

# 生成覆蓋率報告
pytest --cov=src --cov-report=html
# 查看報告: htmlcov/index.html

# 運行特定標記的測試
pytest -m unit          # 單元測試
pytest -m integration   # 集成測試
pytest -m api          # API測試
```

### 代碼審查

提交代碼前確保：

- [ ] 所有測試通過
- [ ] 代碼覆蓋率 > 80%
- [ ] 通過flake8檢查
- [ ] 通過mypy類型檢查
- [ ] 通過pre-commit鉤子

---

## 常用操作

### 啟動系統

```bash
# 激活虛擬環境
source .venv310/bin/activate  # Linux/macOS
# 或
.venv310\Scripts\activate     # Windows

# 啟動所有服務
docker-compose up -d

# 啟動主應用
python complete_project_system.py
```

### 停止系統

```bash
# 停止主應用 (Ctrl+C)

# 停止所有Docker服務
docker-compose down
```

### 查看日誌

```bash# 應用日誌
tail -f logs/quant_system.log

# Docker服務日誌
docker-compose logs -f web
docker-compose logs -f database
docker-compose logs -f redis
docker-compose logs -f influxdb
```

### 數據庫操作

```bash# PostgreSQL
psql -h localhost -U codex -d codex_db

# 創建遷移
alembic revision --autogenerate -m "描述"

# 應用遷移
alembic upgrade head

# 備份數據
pg_dump -h localhost -U codex -d codex_db > backup.sql
```

### 重置環境

```bash# 停止並刪除所有容器和卷
docker-compose down -v

# 重建並啟動
docker-compose up -d --build
```

---

## 故障排除

### 常見問題

#### 問題1: 端口被占用

**錯誤**:
```
ERROR: for web  Cannot start service web: driver failed programming external connectivity on endpoint codex-web-1
```

**解決方案**:
```bash
# 查找占用端口的進程
netstat -tulpn | grep :8001

# Windows
netstat -ano | findstr :8001

# 終止進程
kill -9 <PID>

# 或更改端口
echo "API_PORT=8002" >> .env
```

#### 問題2: Docker權限不足

**錯誤**:
```
Got permission denied while trying to connect to the Docker daemon socket
```

**解決方案**:
```bash
# Linux/macOS: 將用戶添加到docker組
sudo usermod -aG docker $USER

# 重新登錄或運行
newgrp docker

# 或使用sudo
sudo docker-compose up -d
```

#### 問題3: 虛擬環境問題

**錯誤**:
```
ModuleNotFoundError: No module named 'fastapi'
```

**解決方案**:
```bash
# 確認虛擬環境已激活
which python  # 應該指向 .venv310/bin/python

# 重新創建虛擬環境
rm -rf .venv310
python -m venv .venv310
source .venv310/bin/activate
pip install -r requirements.txt
```

#### 問題4: TA-Lib安裝失敗

**錯誤**:
```
ERROR: Failed building wheel for TA-Lib
```

**解決方案**:

**方法1**: 使用conda
```bash
conda install -c conda-forge ta-lib
```

**方法2**: 預編譯wheel
```bash
# 下載對應版本: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
pip install TA_Lib‑0.4.XX‑cpXX‑cpXX‑win_amd64.whl  # Windows
```

**方法3**: 系統級安裝
```bash
# Ubuntu/Debian
sudo apt-get install ta-lib
pip install TA-Lib

# macOS
brew install ta-lib
pip install TA-Lib
```

#### 問題5: InfluxDB連接失敗

**錯誤**:
```
ConnectionError: HTTPConnectionPool(host='localhost', port=8086)
```

**解決方案**:
```bash
# 檢查InfluxDB容器狀態
docker-compose ps influxdb

# 檢查InfluxDB日誌
docker-compose logs influxdb

# 重啟InfluxDB
docker-compose restart influxdb

# 驗證配置
curl -H "Authorization: Token codex-admin-token-12345" \
     http://localhost:8086/api/v2/buckets
```

#### 問題6: 測試失敗

**錯誤**:
```
FAILED tests/test_core_functions.py::test_data_fetch - ConnectionError
```

**解決方案**:
```bash
# 確保所有服務正在運行
docker-compose ps

# 運行集成測試 (需要服務)
pytest tests/integration/ -v

# 運行單元測試 (不需要服務)
pytest tests/unit/ -v

# 跳過慢速測試
pytest -m "not slow"
```

#### 問題7: pre-commit失敗

**錯誤**:
```
black failed
```

**解決方案**:
```bash
# 自動修復
black src/ tests/
isort src/ tests/

# 重新運行檢查
pre-commit run --all-files

# 跳過此次提交
git commit --no-verify
```

### 獲取幫助

如果遇到問題：

1. 查看日誌文件: `logs/quant_system.log`
2. 運行驗證腳本: `./verify-env.sh`
3. 查看故障排除指南: `docs/troubleshooting_guide.md`
4. 提交Issue: [項目Issue頁面]

### 性能優化

#### 加速Docker構建

```bash
# 使用BuildKit
export DOCKER_BUILDKIT=1
docker-compose build --parallel

# 緩存依賴
docker-compose build --no-cache web
```

#### 優化測試運行

```bash
# 並行運行測試
pytest -n auto

# 僅運行失敗的測試
pytest --lf

# 快速測試 (跳過慢速測試)
pytest -m "not slow"
```

---

## 下一步

完成環境設置後，您可以：

1. **閱讀架構文檔**: `docs/architecture.md`
2. **查看API文檔**: http://localhost:8001/docs
3. **運行示例**: `python examples/quick_start.py`
4. **開始開發**: 參考 `docs/new-developer-guide.md`

### Sprint 0 接下來的任務

- [ ] US-002: 建立代碼結構和規範
- [ ] US-003: 實現基礎數據適配器框架
- [ ] US-004: 實現HKMA數據適配器

---

## 參考資源

### 文檔
- [項目架構](docs/architecture.md)
- [API參考](docs/api_reference.md)
- [故障排除指南](docs/troubleshooting_guide.md)
- [新開發者指南](docs/new-developer-guide.md)

### 外部資源
- [FastAPI文檔](https://fastapi.tiangolo.com/)
- [Docker文檔](https://docs.docker.com/)
- [InfluxDB文檔](https://docs.influxdata.com/influxdb/)

---

**文檔版本**: v1.0
**最後更新**: 2025年11月5日
**維護者**: Mini Hedge Fund開發團隊

如果您發現文檔錯誤或有改進建議，請提交Pull Request或Issue。
