# BMAD ELK Stack 日志系统部署指南

## 📊 概述

BMAD量化交易系统日志基于ELK (Elasticsearch, Logstash, Kibana) Stack构建，提供集中式日志收集、存储、分析和可视化能力。

## 🏗️ 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                   BMAD ELK Stack 架构                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Kibana     │    │ Elasticsearch│    │   Logstash   │  │
│  │  (可视化)     │    │   (存储)      │    │  (处理)      │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │           │
│         └───────────────────┼───────────────────┘           │
│                             │                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │            Filebeat (日志收集)                          │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │ │
│  │  │ API      │ │ Data     │ │ Redis    │ │PostgreSQL│  │ │
│  │  │ Server   │ │ Adapter  │ │          │ │          │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │ │
│  │                                                          │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │ │
│  │  │Kubernetes│ │ Application│ │ System   │ │ Audit    │  │ │
│  │  │  Logs    │ │  Logs     │ │ Logs     │ │ Logs     │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │ │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📦 组件说明

### 1. Elasticsearch (搜索引擎)
- **版本**: 8.8.0
- **端口**: 9200 (HTTP), 9300 (Transport)
- **功能**:
  - 分布式搜索和分析引擎
  - 实时索引和查询
  - 水平扩展
  - 自动负载均衡

### 2. Logstash (日志处理)
- **版本**: 8.8.0
- **端口**: 5044 (Beats), 8080 (HTTP), 514 (Syslog)
- **功能**:
  - 日志数据处理和转换
  - 支持多种输入源
  - 丰富的过滤和解析插件
  - 输出到多个目标

### 3. Kibana (可视化)
- **版本**: 8.8.0
- **端口**: 5601
- **功能**:
  - 数据可视化和仪表板
  - 实时日志分析
  - 搜索和查询
  - 告警和监控

### 4. Filebeat (日志收集器)
- **版本**: 8.8.0
- **功能**:
  - 轻量级日志收集
  - Kubernetes集成
  - 自动发现日志源
  - 背压处理

## 🚀 快速部署

### 前置条件

1. **Kubernetes集群已部署**
   ```bash
   kubectl cluster-info
   ```

2. **存储类已配置**
   ```bash
   kubectl get storageclass
   ```

3. **Ingress Controller已部署**
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
./scripts/deploy-elk.sh

# 脚本会自动执行以下步骤：
# 1. 创建 logging 命名空间
# 2. 部署 Elasticsearch
# 3. 部署 Logstash
# 4. 部署 Kibana
# 5. 部署 Filebeat (DaemonSet)
# 6. 创建 ILM 策略
# 7. 配置 Ingress
```

### 部署输出示例

```
==========================================
BMAD ELK Stack Deployment Script
==========================================

[1/7] Creating namespace: logging
✓ Namespace created
[2/7] Deploying Elasticsearch...
✓ Elasticsearch deployed
[3/7] Deploying Logstash...
✓ Logstash deployed
[4/7] Deploying Kibana...
✓ Kibana deployed
[5/7] Deploying Filebeat as DaemonSet...
✓ Filebeat DaemonSet deployed
[6/7] Creating Index Lifecycle Management Policy...
✓ ILM Policy created
[7/7] Setting up Ingress...
Enter your domain (e.g., yourdomain.com): yourdomain.com
✓ Ingress configured

==========================================
ELK Stack Deployed Successfully!
==========================================

Access URLs:
  - Elasticsearch: https://elasticsearch.yourdomain.com
  - Kibana: https://kibana.yourdomain.com

Default Credentials (if enabled):
  Username: elastic
  Password: changeme

To view deployment status:
  kubectl get pods -n logging
  kubectl get svc -n logging
```

## 📝 日志数据流

### 1. 日志收集 (Filebeat)
```
容器日志 → Filebeat → Logstash
```

**收集的日志类型**:
- BMAD应用日志 (API Server, Data Adapter)
- Redis日志
- PostgreSQL日志
- Kubernetes系统日志
- 容器运行时日志

### 2. 日志处理 (Logstash)
```
Input → Filter → Output
```

**处理流程**:
1. **Input**: 接收Beat、HTTP、Syslog输入
2. **Filter**:
   - 解析日志格式
   - 提取结构化字段
   - 添加元数据
   - 分类标签 (ERROR, WARNING, INFO)
   - 按服务分类 (trading, api, data)
3. **Output**: 输出到Elasticsearch

### 3. 索引策略

| 索引名称 | 用途 | 保留期 |
|---------|------|--------|
| `bmad-logs-*` | 常规日志 | 90天 |
| `bmad-errors-*` | 错误日志 | 180天 |
| `bmad-health-*` | 健康检查日志 | 30天 |
| `kubernetes-*` | Kubernetes日志 | 60天 |

## 📊 预配置索引模式

### BMAD应用日志

```json
{
  "timestamp": "2025-11-06T10:30:00.000Z",
  "level": "INFO",
  "msg": "Strategy execution started",
  "service": "bmad-api-server",
  "category": "trading",
  "kubernetes": {
    "container_name": "api-server",
    "namespace": "bmad-production",
    "pod_name": "api-server-xyz123"
  },
  "tags": ["bmad", "trading", "info"]
}
```

### 错误日志结构

```json
{
  "timestamp": "2025-11-06T10:30:00.000Z",
  "level": "ERROR",
  "msg": "Database connection failed",
  "service": "postgresql",
  "error_type": "connection_error",
  "stack_trace": "...",
  "tags": ["error", "critical"]
}
```

## 🔍 Kibana仪表板

### 预配置仪表板

1. **BMAD系统日志概览**
   - 总日志量
   - 错误率趋势
   - 按服务分布
   - 按级别分布
   - 实时日志流

2. **错误分析仪表板**
   - 错误类型分布
   - 错误时间线
   - Top错误
   - 错误追踪

3. **性能分析仪表板**
   - API响应时间
   - 数据库查询时间
   - 日志处理延迟
   - Elasticsearch性能

4. **Kubernetes日志仪表板**
   - Pod状态变化
   - 容器重启
   - 资源使用
   - 调度事件

### 搜索查询示例

```sql
# 查找所有ERROR级别日志
level:ERROR

# 查找特定服务的日志
service:bmad-api-server

# 查找交易相关日志
category:trading

# 查找最近1小时的错误
level:ERROR AND @timestamp:[now-1h TO now]

# 查找包含特定关键字的日志
msg:"strategy execution"

# 复合查询
service:bmad-api-server AND level:ERROR AND @timestamp:[now-24h TO now]
```

## 🔧 配置详解

### Elasticsearch配置

```yaml
# 集群配置
cluster.name: bmad-logging-cluster
node.name: bmad-es-node-1
path.data: /usr/share/elasticsearch/data
path.logs: /usr/share/elasticsearch/logs

# 网络配置
network.host: 0.0.0.0
http.port: 9200
transport.port: 9300

# 性能调优
indices.memory.index_buffer_size: 30%
indices.queries.cache.size: 10%
indices.fielddata.cache.size: 20%

# 索引配置
number_of_shards: 1
number_of_replicas: 0
refresh_interval: 1s
```

### Logstash配置

```ruby
input {
  beats { port => 5044 }
  http { port => 8080 }
  syslog { port => 514 }
}

filter {
  if [fields][log_type] == "bmad" {
    grok { match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level}" } }
    date { match => [ "timestamp", "ISO8601" ] }

    if [level] == "ERROR" { mutate { add_tag => [ "error" ] } }
    if [msg] =~ /trade|strategy/i { mutate { add_field => { "category" => "trading" } } }
  }
}

output {
  elasticsearch { hosts => ["elasticsearch:9200"] }
}
```

### Filebeat配置

```yaml
filebeat.inputs:
- type: container
  enabled: true
  paths:
    - /var/log/containers/*bmad*.log
  processors:
  - add_kubernetes_metadata:
      host: ${NODE_NAME}
  - decode_json_fields:
      fields: ["message"]
      target: "json"

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "bmad-logs-%{+yyyy.MM.dd}"

setup.template.name: "bmad-logs"
setup.template.pattern: "bmad-logs-*"
setup.ilm.enabled: true
```

## 📧 告警配置

### Kibana Watcher

```json
{
  "trigger": {
    "schedule": {
      "interval": "5m"
    }
  },
  "actions": {
    "send_email": {
      "email": {
        "to": "admin@bmad-system.com",
        "subject": "BMAD Error Alert",
        "body": "High error rate detected in BMAD logs"
      }
    }
  },
  "input": {
    "search": {
      "request": {
        "search_type": "query_then_fetch",
        "indices": ["bmad-errors-*"],
        "body": {
          "query": {
            "range": {
              "@timestamp": {
                "gte": "now-5m"
              }
            }
          },
          "aggs": {
            "errors_per_minute": {
              "date_histogram": {
                "field": "@timestamp",
                "interval": "minute"
              }
            }
          }
        }
      }
    }
  }
}
```

## 🔍 常用查询

### 检查Elasticsearch集群健康

```bash
curl -s http://elasticsearch.logging.svc.cluster.local:9200/_cluster/health

# 响应示例
{
  "cluster_name": "bmad-logging-cluster",
  "status": "green",
  "timed_out": false,
  "number_of_nodes": 1,
  "number_of_data_nodes": 1,
  "active_primary_shards": 5,
  "active_shards": 5,
  "relocating_shards": 0,
  "initializing_shards": 0,
  "unassigned_shards": 0,
  "delayed_unassigned_shards": 0,
  "number_of_pending_tasks": 0,
  "number_of_in_flight_fetch": 0,
  "task_max_waiting_in_queue_millis": 0,
  "active_shards_percent_as_number": 100.0
}
```

### 查看索引列表

```bash
curl -s http://elasticsearch.logging.svc.cluster.local:9200/_cat/indices?v

# 查看索引大小
curl -s http://elasticsearch.logging.svc.cluster.local:9200/_cat/indices?bytes=mb
```

### 测试日志收集

```bash
# 通过Logstash HTTP接口发送测试日志
echo '{"message":"test log","level":"INFO","service":"test"}' | \
  curl -s -XPOST http://logstash.logging.svc.cluster.local:8080 \
    -H 'Content-Type: application/json'

# 在Kibana中搜索 index:bmad-logs-*
```

### 检查Filebeat状态

```bash
kubectl get pods -n logging -l app=filebeat
kubectl logs -f ds/filebeat -n logging
```

## 🔧 维护操作

### 查看日志

```bash
# Elasticsearch日志
kubectl logs -f statefulset/elasticsearch -n logging

# Logstash日志
kubectl logs -f deployment/logstash -n logging

# Kibana日志
kubectl logs -f deployment/kibana -n logging

# Filebeat日志
kubectl logs -f ds/filebeat -n logging
```

### 扩容操作

```bash
# 扩容Elasticsearch
kubectl scale statefulset elasticsearch --replicas=3 -n logging

# 扩容Logstash
kubectl scale deployment logstash --replicas=2 -n logging
```

### 数据清理

```bash
# 删除旧索引 (保留30天)
curl -X DELETE "elasticsearch.logging.svc.cluster.local:9200/bmad-logs-$(date -d '30 days ago' +%Y.%m.%d)"

# 清理已完成的索引生命周期策略
curl -X DELETE "elasticsearch.logging.svc.cluster.local:9200/_ilm/policy/bmad-logs-policy"

# 强制合并段
for index in $(curl -s http://elasticsearch:9200/_cat/indices?h=i | grep bmad-logs); do
  curl -X POST "elasticsearch:9200/$index/_forcemerge?max_num_segments=1"
done
```

## 📊 性能调优

### Elasticsearch JVM调优

```yaml
# 推荐JVM堆大小为系统内存的50%，不超过32GB
- name: ES_JAVA_OPTS
  value: "-Xms4g -Xmx4g -XX:+UseConcMarkSweepGC"

# 系统配置
vm.max_map_count=262144
fs.file-max=65536
```

### 索引优化

```bash
# 批量索引设置
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "refresh_interval": "30s",
    "index.translog.flush_threshold_ops": 5000,
    "index.store.throttle.type": "merge",
    "index.merge.scheduler.max_thread_count": 1
  }
}
```

### Logstash性能调优

```yaml
# 调整工作线程数
pipeline.workers: 4
pipeline.batch.size: 1000
pipeline.batch.delay: 50
```

## 🔐 安全配置

### 启用X-Pack安全

```yaml
# Elasticsearch
xpack.security.enabled: true
xpack.security.authc.api_key.enabled: true

# Kibana
xpack.security.enabled: true
elasticsearch.username: "elastic"
elasticsearch.password: "${ELASTIC_PASSWORD}"

# 创建用户
curl -X POST "localhost:9200/_security/user/bmad_user" -H 'Content-Type: application/json' -u 'elastic:changeme' -d'{
  "password" : "bmad_password",
  "roles" : ["kibana_user", "logstash_writer"]
}'
```

### TLS加密

```yaml
# Elasticsearch TLS配置
xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.key: /usr/share/elasticsearch/config/elasticsearch.key
xpack.security.http.ssl.certificate: /usr/share/elasticsearch/config/elasticsearch.crt
xpack.security.http.ssl.certificate_authorities: /usr/share/elasticsearch/config/ca.crt
```

## 📚 故障排除

### 问题1: Elasticsearch无法启动

**症状**: Pod CrashLoopBackOff

**解决方法**:
```bash
# 检查JVM堆内存设置
kubectl describe pod elasticsearch-0 -n logging

# 检查系统限制
kubectl exec -it elasticsearch-0 -n logging -- sysctl vm.max_map_count
# 如果小于262144，需要修改节点配置
```

### 问题2: Kibana无法连接Elasticsearch

**症状**: Kibana启动后显示"Unable to connect to Elasticsearch"

**解决方法**:
```bash
# 检查Elasticsearch服务
kubectl get svc elasticsearch -n logging

# 检查网络策略
kubectl get networkpolicies -n logging

# 验证连接
kubectl run test-es --rm -i --restart=Never --image=curlimages/curl:latest -- \
  curl -s http://elasticsearch:9200/_cluster/health
```

### 问题3: Logstash处理延迟

**症状**: 日志到达Elasticsearch延迟超过5分钟

**解决方法**:
```bash
# 检查Logstash队列
kubectl exec -it logstash-<pod> -n logging -- \
  curl -s http://localhost:9600/_node/stats/pipelines

# 调整pipeline参数
# 增加worker数量和batch大小
```

### 问题4: 索引分片未分配

**症状**: Elasticsearch集群状态为yellow或red

**解决方法**:
```bash
# 查看未分配的分片
curl -s http://elasticsearch:9200/_cat/shards?h=index,shard,prirep,state | grep UNASSIGNED

# 强制分配分片
for shard in $(curl -s http://elasticsearch:9200/_cat/shards?h=index,shard | grep UNASSIGNED | awk '{print $2}'); do
  curl -X POST "elasticsearch:9200/_cluster/reroute" -H 'Content-Type: application/json' -d '{
    "commands": [{
      "allocate_stale_primary": {
        "index": "INDEX_NAME",
        "shard": '$shard',
        "node": "NODE_NAME",
        "accept_data_loss": true
      }
    }]
  }'
done
```

## 📚 扩展阅读

- [Elasticsearch官方文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Logstash参考指南](https://www.elastic.co/guide/en/logstash/current/index.html)
- [Kibana用户指南](https://www.elastic.co/guide/en/kibana/current/index.html)
- [Filebeat参考手册](https://www.elastic.co/guide/en/beats/filebeat/current/index.html)

## 🆘 获取帮助

如遇问题，请：

1. 查看日志: `kubectl logs -f <pod> -n logging`
2. 检查状态: `kubectl get pods -n logging`
3. 验证配置: `kubectl describe <resource> -n logging`
4. 查阅文档: [日志指南](../)
5. 提交Issue: [GitHub Issues](https://github.com/your-repo/issues)

---

**文档版本**: 1.0.0
**最后更新**: 2025-11-06
**维护者**: BMAD DevOps Team
