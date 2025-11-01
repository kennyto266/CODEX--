# CODEX交易系统 - Kubernetes部署指南

## 概述

本目录包含CODEX交易系统的完整Kubernetes部署配置，支持生产、开发、测试三种环境。

## 文件结构

```
kubernetes/
├── namespace.yaml        # 命名空间定义
├── configmap.yaml        # 配置映射
├── secrets.yaml          # 密钥管理
├── rbac.yaml             # RBAC权限控制
├── pvc.yaml              # 持久化存储
├── deployment.yaml       # 应用部署
├── service.yaml          # 服务定义
├── ingress.yaml          # 入口配置
├── hpa.yaml              # 自动缩放
├── deploy.sh             # 自动化部署脚本
└── README.md             # 本文件
```

## 快速部署

### 前置要求

1. **Kubernetes集群** (v1.20+)
2. **kubectl** 已配置并连接到集群
3. **Ingress Controller** (Nginx或Traefik)
4. **cert-manager** (用于SSL证书管理)

### 一键部署

```bash
# 部署到生产环境
cd deployment/kubernetes
./deploy.sh --env production

# 部署到开发环境
./deploy.sh --env development

# 部署到测试环境
./deploy.sh --env testing
```

### 高级选项

```bash
# 指定命名空间
./deploy.sh --namespace my-namespace --env production

# 试运行模式 (不实际应用变更)
./deploy.sh --dry-run

# 跳过密钥创建 (开发环境)
./deploy.sh --env development --skip-secrets

# 跳过监控组件
./deploy.sh --skip-monitoring

# 自定义超时时间
./deploy.sh --timeout 1200
```

## 部署组件

### 1. 命名空间 (Namespace)

- `codex-trading` - 生产环境
- `codex-trading-dev` - 开发环境
- `codex-trading-test` - 测试环境

### 2. 配置映射 (ConfigMap)

包含应用程序的所有非敏感配置：
- 环境变量
- API配置
- 数据库连接池配置
- Redis配置
- 安全设置
- 交易参数

### 3. 密钥管理 (Secrets)

**敏感信息存储**：
- 数据库密码
- Redis密码
- API密钥
- JWT密钥
- SSL证书
- Telegram Bot Token

**注意**: 部署前请更新 `secrets.yaml` 中的实际密钥值。

### 4. RBAC权限控制

- ServiceAccount定义
- Role和ClusterRole
- RoleBinding和ClusterRoleBinding
- 网络策略 (NetworkPolicy)

### 5. 持久化存储 (PVC)

| 存储类型 | 大小 | 用途 |
|---------|------|------|
| postgres-pvc | 100Gi | PostgreSQL数据 |
| redis-pvc | 20Gi | Redis缓存 |
| grafana-pvc | 10Gi | Grafana配置 |
| prometheus-pvc | 50Gi | Prometheus数据 |
| app-logs-pvc | 30Gi | 应用日志 |
| app-data-pvc | 100Gi | 应用数据 |

### 6. 部署 (Deployment)

#### 应用服务
- **副本数**: 3个 (生产环境)
- **资源限制**:
  - CPU: 250m - 2000m
  - 内存: 512Mi - 2Gi
- **健康检查**: Liveness、Readiness、Startup探针
- **安全上下文**: 非root用户、只读根文件系统

#### 数据库 (PostgreSQL)
- **版本**: PostgreSQL 15 Alpine
- **资源**: 1Gi - 4Gi内存，500m - 2000m CPU
- **持久化**: 100Gi存储

#### 缓存 (Redis)
- **版本**: Redis 7 Alpine
- **资源**: 512Mi - 2Gi内存，250m - 1000m CPU
- **持久化**: 20Gi存储

### 7. 服务 (Service)

- **ClusterIP服务**: 内部访问
- **LoadBalancer服务**: 外部访问
- **NodePort服务**: 开发环境
- **Headless服务**: 无头服务 (用于有状态集合)

### 8. Ingress配置

#### 域名路由

| 域名 | 路径 | 后端服务 |
|------|------|----------|
| codex.trading.com | /api, /ws, /health | codex-trading-service |
| api.codex.trading.com | / | codex-trading-service |
| prometheus.codex.trading.com | / | prometheus-service |
| grafana.codex.trading.com | / | grafana-service |

#### 特性
- SSL/TLS终止 (Let's Encrypt)
- CORS支持
- WebSocket支持
- 速率限制
- Basic Auth (admin.codex.trading.com)

### 9. 自动缩放 (HPA)

#### 缩放触发条件
- **CPU使用率**: 超过70%时扩容
- **内存使用率**: 超过80%时扩容
- **请求率**: 平均每Pod超过1000 QPS时扩容
- **响应时间**: 超过1秒时扩容

#### 缩放范围
- **应用服务**: 3 - 20副本
- **数据库**: 1 - 3副本
- **Redis**: 1 - 3副本

## 环境配置

### 生产环境

```yaml
ENVIRONMENT: production
DEBUG: false
LOG_LEVEL: INFO
API_WORKERS: 4
DB_POOL_SIZE: 10
REDIS_POOL_SIZE: 10
TRADING_ENABLE_PAPER_TRADING: false
```

### 开发环境

```yaml
ENVIRONMENT: development
DEBUG: true
LOG_LEVEL: DEBUG
API_WORKERS: 1
DB_POOL_SIZE: 5
REDIS_POOL_SIZE: 5
TRADING_ENABLE_PAPER_TRADING: true
```

## 监控和告警

### Prometheus
- **端口**: 9090
- **访问**: https://prometheus.codex.trading.com
- **保留期**: 30天

### Grafana
- **端口**: 3000
- **访问**: https://grafana.codex.trading.com
- **管理员密码**: 通过secrets管理

### 告警管理器 (AlertManager)
- **端口**: 9093
- **配置**: 支持邮件、Slack、PagerDuty

## 安全配置

### 网络策略
- 只允许必要的网络流量
- 禁止Pod间任意通信
- 限制外部访问

### 容器安全
- 非root用户运行
- 只读根文件系统
- 禁用所有capabilities
- 只读挂载点

### SSL/TLS
- Let's Encrypt自动证书
- 强制HTTPS重定向
- 安全标头配置

## 滚动更新

部署使用滚动更新策略：
- **maxUnavailable**: 1 (一次最多不可用1个Pod)
- **maxSurge**: 1 (一次最多额外创建1个Pod)
- **健康检查**: 更新期间保持服务可用

## 蓝绿部署

### 启用蓝绿部署

1. 部署新版本 (绿)：
   ```bash
   kubectl set image deployment/codex-trading-app-blue api=codex/trading-system:v2.0 -n codex-trading
   ```

2. 验证新版本：
   ```bash
   # 访问健康检查端点
   curl https://api.codex.trading.com/health
   ```

3. 切换流量到新版本：
   ```bash
   # 更新Ingress权重或使用服务网格
   ```

4. 清理旧版本 (蓝)：
   ```bash
   kubectl delete deployment codex-trading-app-blue -n codex-trading
   ```

## 故障排除

### 查看Pod状态
```bash
kubectl get pods -n codex-trading
kubectl describe pod <pod-name> -n codex-trading
kubectl logs <pod-name> -n codex-trading
```

### 查看事件
```bash
kubectl get events -n codex-trading --sort-by='.lastTimestamp'
```

### 查看资源使用
```bash
kubectl top pods -n codex-trading
kubectl top nodes
```

### 常见问题

#### Pod无法启动
1. 检查镜像拉取是否成功
2. 检查配置和密钥是否正确
3. 检查资源限制是否合理
4. 查看事件和日志

#### 服务无法访问
1. 检查Service状态
   ```bash
   kubectl get svc -n codex-trading
   kubectl describe svc codex-trading-service -n codex-trading
   ```
2. 检查Ingress配置
   ```bash
   kubectl get ingress -n codex-trading
   kubectl describe ingress codex-trading-ingress -n codex-trading
   ```

#### 数据库连接失败
1. 检查PostgreSQL Pod是否运行正常
2. 验证数据库密码和连接URL
3. 检查网络策略是否允许连接

## 备份和恢复

### 数据库备份
```bash
# 创建备份
kubectl create job --from=cronjob/postgres-backup backup-$(date +%Y%m%d-%H%M%S) -n codex-trading

# 查看备份状态
kubectl get jobs -n codex-trading
```

### 恢复数据库
```bash
# 恢复备份
kubectl create job --from=cronjob/postgres-restore restore-$(date +%Y%m%d-%H%M%S) -n codex-trading
```

## 升级指南

### 应用升级
1. 更新Docker镜像版本
2. 执行部署脚本：
   ```bash
   ./deploy.sh --env production
   ```
3. 监控部署状态：
   ```bash
   kubectl rollout status deployment/codex-trading-app -n codex-trading
   ```

### 回滚
```bash
# 回滚到上一个版本
kubectl rollout undo deployment/codex-trading-app -n codex-trading

# 回滚到指定版本
kubectl rollout undo deployment/codex-trading-app --to-revision=2 -n codex-trading
```

## 清理资源

### 删除命名空间
```bash
kubectl delete namespace codex-trading
```

### 删除特定资源
```bash
kubectl delete -f deployment.yaml -n codex-trading
kubectl delete -f service.yaml -n codex-trading
kubectl delete -f ingress.yaml -n codex-trading
```

## 性能优化

### 资源调优
- 根据监控数据调整HPA参数
- 优化数据库连接池大小
- 调整Redis缓存策略

### 存储优化
- 使用SSD存储类提高IO性能
- 配置适当的PV大小
- 启用压缩减少存储占用

## 参考资料

- [Kubernetes官方文档](https://kubernetes.io/docs/)
- [kubectl命令参考](https://kubernetes.io/docs/reference/kubectl/)
- [Ingress-Nginx文档](https://kubernetes.github.io/ingress-nginx/)
- [cert-manager文档](https://cert-manager.io/docs/)

## 支持

如有问题，请联系运维团队：
- 邮箱: ops-team@company.com
- Slack: #devops
