# 多阶段构建 Dockerfile
# CODEX Trading Dashboard

# ------------------------------------------------------------------------------
# 构建阶段
# ------------------------------------------------------------------------------
FROM node:18-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY src/dashboard/static/package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY src/dashboard/static/ .

# 构建前端
RUN npm run build

# ------------------------------------------------------------------------------
# 生产阶段
# ------------------------------------------------------------------------------
FROM python:3.10-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 创建应用目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libta-lib-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt ./

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY run_dashboard.py ./

# 复制构建产物
COPY --from=builder /app/dist ./src/dashboard/static/dist/

# 创建非root用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/health || exit 1

# 启动命令
CMD ["uvicorn", "src.dashboard.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
