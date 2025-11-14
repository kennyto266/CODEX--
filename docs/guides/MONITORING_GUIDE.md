# BMAD 监控系统部署指南

## 📊 概述

BMAD量化交易系统监控基于Prometheus + Grafana + Alertmanager技术栈，提供全方位的系统监控、告警和可视化能力。

## 🏗️ 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    BMAD 监控系统架构                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Grafana    │    │ Prometheus   │    │ Alertmanager │  │
│  │   (可视化)    │    │   (收集)      │    │   (告警)      │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │            监控指标来源                               │  │
│  │                                                          │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │  │
│  │  │ API      │ │ Data     │ │ Redis    │ │PostgreSQL│  │  │
│  │  │ Server   │ │ Adapter  │ │          │ │          │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │  │
│  │                                                          │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │  │
│  │  │Node      │ │cAdvisor  │ │ Custom   │ │ System   │  │  │
│  │  │Exporter  │ │          │ │ Metrics  │ │ Metrics  │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📦 组件说明

### 1. Prometheus (指标收集)
- **版本**: v2.45.0
- **端口**: 9090
- **功能**:
  - 定期抓取各服务指标
  - 存储时序数据
  - 支持PromQL查询语言
  - 告警规则评估

### 2. Grafana (可视化)
- **版本**: 10.0.0
- **端口**: 3000
- **功能**:
  - 实时数据可视化
  - 预配置仪表板
  - 多数据源支持
  - 告警集成

### 3. Alertmanager (告警)
- **版本**: v0.26.0
- **端口**: 9093
- **功能**:
  - 告警去重和分组
  - 多渠道通知 (邮件、Slack)
  - 告警抑制和静默

### 4. Exporters (指标导出器)
- **Redis Exporter**: v1.53.0 (端口 9121)
- **PostgreSQL Exporter**: v0.13.2 (端口 9187)
- **Node Exporter**: v1.6.0 (端口 9100)
- **cAdvisor**: v0.47.0 (端口 8080)

## 🚀 快速部署

### 前置条件

1. **Kubernetes集群已部署**
   ```bash
   kubectl cluster-info
   ```

2. **Helm已安装**
   ```bash
   helm version
   ```

3. **Ingress Controller已配置**
   ```bash
   kubectl get pods -n ingress-nginx
   ```

4. **Cert-Manager已安装**
   ```bash
   kubectl get pods -n cert-manager
   ```

### 执行部署

```bash
# 运行部署脚本
./scripts/deploy-monitoring.sh

# 脚本会自动执行以下步骤：
# 1. 创建 monitoring 命名空间
# 2. 部署 Prometheus
# 3. 部署 Grafana
# 4. 部署 Alertmanager
# 5. 部署 Exporters
# 6. 配置 Ingress
```

### 部署输出示例

```
==========================================
BMAD Monitoring System Deployment Script
==========================================

[1/6] Creating namespace: monitoring
✓ Namespace created
[2/6] Deploying Prometheus...
✓ Prometheus deployed
[3/6] Deploying Grafana...
✓ Grafana deployed
[4/6] Deploying Alertmanager...
✓ Alertmanager deployed
[5/6] Deploying Exporters...
✓ Exporters deployed
[6/6] Setting up Ingress...
Enter your domain (e.g., yourdomain.com): yourdomain.com
✓ Ingress configured

==========================================
Monitoring System Deployed Successfully!
==========================================

Access URLs:
  - Prometheus:  https://prometheus.yourdomain.com
  - Grafana:     https://grafana.yourdomain.com
  - Alertmanager: https://alertmanager.yourdomain.com

Grafana Credentials:
  Username: admin
  Password: admin123
```

## 📊 监控指标

### API Server指标

| 指标名称 | 类型 | 描述 |
|---------|------|------|
| `http_requests_total` | Counter | HTTP请求总数 |
| `http_request_duration_seconds` | Histogram | HTTP请求延迟 |
| `http_requests_errors_total` | Counter | HTTP错误总数 |
| `process_cpu_seconds_total` | Counter | CPU使用时间 |
| `process_resident_memory_bytes` | Gauge | 内存使用量 |

### Data Adapter指标

| 指标名称 | 类型 | 描述 |
|---------|------|------|
| `data_fetch_duration_seconds` | Histogram | 数据获取延迟 |
| `data_fetch_errors_total` | Counter | 数据获取错误 |
| `bmad_trade_volume_5m` | Gauge | 5分钟交易量 |
| `bmad_strategy_returns_1h` | Gauge | 1小时策略收益 |

### 系统指标

| 指标名称 | 类型 | 描述 |
|---------|------|------|
| `up` | Gauge | 服务健康状态 |
| `redis_connected_clients` | Gauge | Redis连接数 |
| `pg_stat_database_numbackends` | Gauge | PostgreSQL连接数 |
| `node_cpu_seconds_total` | Counter | CPU使用率 |
| `node_memory_MemAvailable_bytes` | Gauge | 可用内存 |

## 📈 预配置仪表板

### 1. BMAD系统概览
- **路径**: `/var/lib/grafana/dashboards/bmad-overview.json`
- **面板**:
  - API请求率
  - 响应时间 (95th percentile)
  - CPU使用率
  - 内存使用
  - 错误率
  - 活跃连接数
  - 数据库连接数
  - 数据适配器状态
  - 交易量 (24小时)
  - 策略收益 (1小时)

### 2. Kubernetes仪表板
- 集群资源使用
- Pod状态
- 服务网格
- 网络指标

### 3. 应用仪表板
- 业务指标
- 自定义指标
- 性能分析

## ⚠️ 告警规则

### 关键告警 (Critical)

1. **API服务下线**
   ```yaml
   expr: up{job="bmad-api-server"} == 0
   for: 1m
   severity: critical
   ```

2. **数据库连接失败**
   ```yaml
   expr: pg_up == 0
   for: 1m
   severity: critical
   ```

3. **Redis连接丢失**
   ```yaml
   expr: redis_connected_clients == 0
   for: 1m
   severity: critical
   ```

### 警告告警 (Warning)

1. **高CPU使用率**
   ```yaml
   expr: (100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)) > 80
   for: 2m
   severity: warning
   ```

2. **高内存使用率**
   ```yaml
   expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
   for: 2m
   severity: warning
   ```

3. **高错误率**
   ```yaml
   expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
   for: 2m
   severity: warning
   ```

4. **高响应时间**
   ```yaml
   expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
   for: 5m
   severity: warning
   ```

### 业务告警

1. **策略性能下降**
   ```yaml
   expr: bmad_strategy_returns_1h < -0.05
   for: 5m
   severity: warning
   ```

2. **高交易量**
   ```yaml
   expr: bmad_trade_volume_5m > 1000
   for: 1m
   severity: info
   ```

## 📧 通知配置

### 邮件通知

在 `config/alertmanager/alertmanager.yml` 中配置：

```yaml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@bmad-system.com'
  smtp_auth_username: 'alerts@bmad-system.com'
  smtp_auth_password: 'password'
```

### Slack通知

```yaml
slack_configs:
- api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
  channel: '#bmad-alerts'
  title: 'BMAD Alert'
  text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

## 🔧 常用操作

### 查看服务状态

```bash
# 查看所有监控Pod
kubectl get pods -n monitoring

# 查看监控服务
kubectl get svc -n monitoring

# 查看Prometheus Target
kubectl exec -it prometheus-<pod> -n monitoring -- wget -qO- localhost:9090/targets
```

### 访问Web界面

```bash
# 通过端口转发访问
kubectl port-forward svc/prometheus 9090:9090 -n monitoring
kubectl port-forward svc/grafana 3000:3000 -n monitoring
kubectl port-forward svc/alertmanager 9093:9093 -n monitoring

# 访问地址
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin123)
# Alertmanager: http://localhost:9093
```

### 查询指标

```promql
# API请求率
rate(http_requests_total[5m])

# 95th percentile响应时间
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# 错误率
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# 内存使用
process_resident_memory_bytes / 1024 / 1024

# CPU使用率
rate(process_cpu_seconds_total[5m]) * 100
```

### 告警管理

```bash
# 查看告警状态
kubectl exec -it alertmanager-<pod> -n monitoring -- amtool alert query

# 静默告警
kubectl exec -it alertmanager-<pod> -n monitoring -- amtool silence add alertname=HighCPUUsage
```

## 🎨 自定义仪表板

### 添加新面板

1. 访问 Grafana Web界面
2. 进入 "BMAD System Overview" 仪表板
3. 点击 "Add panel" 按钮
4. 配置指标查询
5. 设置显示选项
6. 保存仪表板

### 导出仪表板配置

```bash
# 导出JSON配置
curl -H "Authorization: Bearer <token>" \
  http://grafana:3000/api/dashboards/uid/<dashboard-uid> > my-dashboard.json
```

## 📝 日志查看

```bash
# 查看Prometheus日志
kubectl logs -f deployment/prometheus -n monitoring

# 查看Grafana日志
kubectl logs -f deployment/grafana -n monitoring

# 查看Alertmanager日志
kubectl logs -f deployment/alertmanager -n monitoring
```

## 🔍 故障排除

### 问题1: Prometheus无法抓取指标

**症状**: Targets状态为DOWN

**解决方法**:
```bash
# 检查服务是否暴露正确端口
kubectl get svc -n monitoring

# 检查指标端点
kubectl exec -it <pod> -n monitoring -- wget -qO- <service>:<port>/metrics

# 检查网络策略
kubectl get networkpolicies -n monitoring
```

### 问题2: Grafana无法连接数据源

**症状**: 仪表板显示"No data"

**解决方法**:
```bash
# 检查数据源配置
kubectl describe configmap grafana-datasources -n monitoring

# 检查Prometheus服务
kubectl get svc prometheus -n monitoring

# 重启Grafana
kubectl rollout restart deployment/grafana -n monitoring
```

### 问题3: 告警未发送

**症状**: Alertmanager收到告警但未通知

**解决方法**:
```bash
# 检查告警路由
kubectl exec -it alertmanager-<pod> -n monitoring -- amtool config routes

# 检查通知渠道配置
kubectl describe configmap alertmanager-config -n monitoring

# 查看Alertmanager日志
kubectl logs -f deployment/alertmanager -n monitoring | grep notify
```

## 🔐 安全配置

### 1. Grafana认证

```yaml
# 禁用匿名访问
GF_AUTH_ANONYMOUS_ENABLED: "false"

# 启用LDAP认证
GF_AUTH_LDAP_ENABLED: "true"
GF_AUTH_LDAP_CONFIG_FILE: "/etc/grafana/ldap.toml"
```

### 2. Ingress TLS

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: monitoring-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - prometheus.yourdomain.com
    secretName: monitoring-tls
```

### 3. RBAC权限

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: prometheus
  namespace: monitoring
rules:
- apiGroups: [""]
  resources: ["services", "endpoints", "pods"]
  verbs: ["get", "list", "watch"]
```

## 📚 扩展阅读

- [Prometheus文档](https://prometheus.io/docs/)
- [Grafana文档](https://grafana.com/docs/)
- [Alertmanager文档](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Kubernetes监控最佳实践](https://kubernetes.io/docs/tasks/debug-application-cluster/resource-usage-monitoring/)

## 🆘 获取帮助

如遇问题，请：

1. 查看日志: `kubectl logs -f <pod> -n monitoring`
2. 检查配置: `kubectl describe <resource> -n monitoring`
3. 查阅文档: [监控指南](../)
4. 提交Issue: [GitHub Issues](https://github.com/your-repo/issues)

---

**文档版本**: 1.0.0
**最后更新**: 2025-11-06
**维护者**: BMAD DevOps Team
