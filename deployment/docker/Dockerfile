# 多阶段Dockerfile - 生产级CODEX交易系统
# 阶段1: 构建阶段 (Build Stage)
FROM python:3.13-slim as builder

# 设置构建参数
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# 添加标签
LABEL maintainer="CODEX Team <team@codex.trading>"
LABEL org.label-schema.build-date=$BUILD_DATE
LABEL org.label-schema.name="CODEX Trading System"
LABEL org.label-schema.description="Enterprise-grade Hong Kong Stock Quantitative Trading System"
LABEL org.label-schema.url="https://github.com/codex/trading-system"
LABEL org.label-schema.vcs-ref=$VCS_REF
LABEL org.label-schema.vcs-url="https://github.com/codex/trading-system"
LABEL org.label-schema.vendor="CODEX"
LABEL org.label-schema.version=$VERSION
LABEL org.label-schema.schema-version="1.0"

# 设置工作目录
WORKDIR /build

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 升级pip和安装构建工具
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 复制依赖文件
COPY requirements.txt requirements-dev.txt ./

# 安装Python依赖（仅构建所需）
RUN pip install --no-cache-dir -r requirements.txt

# 阶段2: 运行环境 (Runtime Stage)
FROM python:3.13-slim as runtime

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 创建非root用户
RUN groupadd -r codex && useradd -r -g codex -m -s /bin/bash codex

# 安装运行时系统依赖
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 设置工作目录
WORKDIR /app

# 从构建阶段复制Python包
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY --chown=codex:codex src/ /app/src/
COPY --chown=codex:codex openspec/ /app/openspec/
COPY --chown=codex:codex run_dashboard.py /app/
COPY --chown=codex:codex *.md /app/

# 创建必要的目录
RUN mkdir -p /app/logs /app/data /app/temp && \
    chown -R codex:codex /app

# 切换到非root用户
USER codex

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# 暴露端口
EXPOSE 8001

# 设置默认命令
CMD ["python", "run_dashboard.py", "--host", "0.0.0.0", "--port", "8001"]

# 阶段3: 开发环境 (Development Stage)
FROM runtime as development

# 切换回root安装开发依赖
USER root

# 复制开发依赖文件
COPY --chown=codex:codex requirements-dev.txt /app/

# 安装开发依赖
RUN pip install --no-cache-dir -r requirements-dev.txt

# 安装测试工具
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-asyncio \
    pytest-xdist \
    httpx \
    factory-boy

# 切换回codex用户
USER codex

# 设置开发环境变量
ENV ENVIRONMENT=development

# 开发阶段默认命令
CMD ["python", "run_dashboard.py", "--host", "0.0.0.0", "--port", "8001", "--reload"]

# 阶段4: 测试环境 (Testing Stage)
FROM builder as testing

# 复制测试代码
COPY --chown=codex:codex tests/ /app/tests/
COPY --chown=codex:codex src/ /app/src/
COPY --chown=codex:codex pytest.ini /app/
COPY --chown=codex:codex .coveragerc /app/

# 设置测试环境变量
ENV ENVIRONMENT=testing
ENV PYTEST_CURRENT_TEST=1

# 运行测试
CMD ["pytest", "tests/", "-v", "--cov=src", "--cov-report=term-missing", "--cov-fail-under=90"]
