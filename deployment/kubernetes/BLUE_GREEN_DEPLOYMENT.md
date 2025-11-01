# 蓝绿部署策略指南

## 概述

蓝绿部署是一种零停机时间的部署策略，通过维护两套完全相同的生产环境（"蓝"和"绿"），实现快速、安全的版本切换。

## 优势

- ✅ **零停机时间**: 切换过程用户无感知
- ✅ **快速回滚**: 如果新版本出现问题，可立即回滚
- ✅ **风险降低**: 先在小流量下验证，再全量切换
- ✅ **完整测试**: 新版本在生产环境完全验证后再切换
- ✅ **环境隔离**: 新旧版本完全独立，互不影响

## 工作原理

```
时间线:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  蓝环境      │    │  蓝环境      │    │  绿环境      │    │  绿环境      │
│   v1.0      │    │   v1.0      │    │   v1.1      │    │   v1.1      │
│   100%流量   │───▶│   90%流量   │───▶│   10%流量   │───▶│   100%流量  │
│  (当前生产)  │    │   (金丝雀)   │    │   (新版本)   │    │  (新生产)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                            │            │            │
                            └────────────┴────────────┘
                                   回滚选项
```

## 快速开始

### 1. 基础蓝绿部署

```bash
# 部署v2.0.0版本
./blue-green-deploy.sh \
  --new-version v2.0.0 \
  --new-image codex/trading-system:v2.0.0

# 验证部署
./blue-green-deploy.sh --new-version v2.0.0 --verify-only
```

### 2. 金丝雀部署 (推荐)

分阶段验证新版本，降低风险：

```bash
# 步骤1: 部署新版本并分流10%流量
./blue-green-deploy.sh \
  --new-version v2.0.0 \
  --new-image codex/trading-system:v2.0.0 \
  --traffic-percentage 10

# 步骤2: 观察5-10分钟，检查指标
# - 错误率
# - 响应时间
# - CPU/内存使用率
# - 业务指标

# 步骤3: 如果一切正常，切换100%流量
./blue-green-deploy.sh \
  --new-version v2.0.0 \
  --traffic-percentage 100
```

### 3. 快速回滚

```bash
# 一键回滚到上一个版本
./blue-green-deploy.sh --rollback-only
```

## 详细使用指南

### 准备阶段

#### 1. 验证新版本
```bash
# 在开发环境测试
kubectl run --rm -it test-pod --image=codex/trading-system:v2.0.0

# 运行自动化测试
pytest tests/e2e/ -v
```

#### 2. 检查数据库迁移
```bash
# 如果有数据库迁移，需要确保：
# 1. 向后兼容性 (旧版本可以读取新版本创建的字段)
# 2. 迁移脚本已测试
# 3. 回滚脚本已准备
```

#### 3. 准备回滚计划
```bash
# 记录当前版本
CURRENT_VERSION=$(kubectl get deployment codex-trading-app -n codex-trading -o jsonpath='{.spec.template.spec.containers[0].image}')

# 准备回滚命令
echo "回滚命令: $CURRENT_VERSION"
```

### 执行部署

#### 步骤1: 部署新版本

```bash
./blue-green-deploy.sh \
  --namespace codex-trading \
  --new-version v2.0.0 \
  --new-image codex/trading-system:v2.0.0 \
  --timeout 600 \
  --health-check-url /health \
  --traffic-percentage 10
```

**脚本执行过程**:
1. ✅ 检查当前环境 (蓝或绿)
2. ✅ 部署到新环境 (绿或蓝)
3. ✅ 等待Pod准备就绪
4. ✅ 执行健康检查
5. ✅ 分流流量到新版本
6. ✅ 显示验证说明

#### 步骤2: 验证指标

监控以下指标5-10分钟：

**系统指标**:
```bash
# 检查Pod状态
kubectl get pods -n codex-trading

# 查看资源使用
kubectl top pods -n codex-trading

# 查看错误日志
kubectl logs -f deployment/codex-trading-app-green -n codex-trading
```

**业务指标** (通过Grafana/Prometheus):
- 请求错误率 < 0.1%
- P95响应时间 < 200ms
- CPU使用率 < 80%
- 内存使用率 < 80%

**业务功能**:
- API响应正确
- 数据库连接正常
- 缓存读写正常
- 交易信号生成正常

#### 步骤3: 切换流量

如果所有指标正常：

```bash
# 切换100%流量
./blue-green-deploy.sh \
  --new-version v2.0.0 \
  --traffic-percentage 100
```

#### 步骤4: 清理旧版本

```bash
# 脚本会自动清理旧版本，也可以手动执行
kubectl delete deployment codex-trading-app-blue -n codex-trading
```

### 监控面板

#### Grafana仪表板

创建蓝绿部署监控面板：

```yaml
面板1: 金丝雀 vs 稳定版本对比
- 请求量 (蓝色)
- 错误率 (绿色)
- 响应时间P95 (红色)

面板2: 蓝绿环境Pod状态
- Blue环境Pod数量
- Green环境Pod数量
- 各环境CPU/内存使用率

面板3: 业务指标
- 交易量
- 订单处理时间
- 策略信号生成
```

### 回滚流程

#### 自动回滚触发条件

如果新版本出现以下情况，自动回滚：

1. **错误率过高**
   ```bash
   # 错误率 > 1% 持续5分钟
   ```

2. **响应时间过长**
   ```bash
   # P95响应时间 > 500ms 持续5分钟
   ```

3. **健康检查失败**
   ```bash
   # 健康检查端点返回错误
   ```

4. **手动触发**
   ```bash
   # 执行回滚命令
   ./blue-green-deploy.sh --rollback-only
   ```

#### 回滚命令

```bash
# 方法1: 使用脚本回滚
./blue-green-deploy.sh --rollback-only

# 方法2: 手动回滚到指定版本
kubectl set image deployment/codex-trading-app-green \
  api=codex/trading-system:v1.9.0 \
  -n codex-trading

# 切换流量
kubectl patch service codex-trading-service \
  -n codex-trading \
  -p '{"spec":{"selector":{"environment":"green"}}}'
```

#### 验证回滚

```bash
# 检查Pod状态
kubectl get pods -n codex-trading

# 验证应用功能
curl https://api.codex.trading.com/health

# 检查业务指标
# 确认错误率恢复正常
# 确认响应时间恢复正常
```

## 故障排除

### 问题1: 新版本Pod启动失败

**症状**:
```bash
kubectl get pods -n codex-trading
# 显示 ImagePullBackOff 或 CrashLoopBackOff
```

**解决方案**:
1. 检查镜像是否存在:
   ```bash
   docker pull codex/trading-system:v2.0.0
   ```

2. 检查镜像标签:
   ```bash
   # 确保版本号正确
   ```

3. 检查镜像拉取权限:
   ```bash
   # 如果是私有仓库，需要配置imagePullSecrets
   kubectl get secret regcred -n codex-trading -o yaml
   ```

### 问题2: 健康检查失败

**症状**:
```bash
kubectl describe pod <pod-name> -n codex-trading
# 显示 Liveness probe failed
```

**解决方案**:
1. 检查健康检查端点:
   ```bash
   curl http://<pod-ip>:8001/health
   ```

2. 调整探针参数:
   ```yaml
   # 在deployment.yaml中调整
   livenessProbe:
     initialDelaySeconds: 60  # 增加延迟
     periodSeconds: 30        # 增加检查间隔
   ```

### 问题3: 数据库迁移失败

**症状**:
```bash
# 应用日志显示数据库错误
ERROR: column "new_field" does not exist
```

**解决方案**:
1. **预防**: 确保向后兼容性
   ```sql
   -- 迁移脚本示例
   ALTER TABLE trades ADD COLUMN new_field VARCHAR(50) DEFAULT NULL;
   ```

2. **修复**: 回滚迁移
   ```sql
   ALTER TABLE trades DROP COLUMN new_field;
   ```

### 问题4: 流量切换后出现502错误

**症状**:
```bash
# 用户访问返回502 Bad Gateway
```

**解决方案**:
1. 检查服务选择器:
   ```bash
   kubectl describe service codex-trading-service -n codex-trading
   ```

2. 检查Endpoint:
   ```bash
   kubectl get endpoints codex-trading-service -n codex-trading
   ```

3. 临时回滚:
   ```bash
   ./blue-green-deploy.sh --rollback-only
   ```

## 最佳实践

### 1. 数据库迁移策略

- ✅ 使用向前兼容的模式变更
- ✅ 先添加字段，后填充数据
- ✅ 保持临时字段一段时间
- ✅ 准备回滚脚本
- ✅ 在非高峰时间执行迁移

### 2. 监控和告警

```yaml
# 设置关键告警
- 错误率 > 1% (立即告警)
- 响应时间P95 > 500ms (5分钟)
- 健康检查失败 (立即告警)
- Pod重启次数过多 (立即告警)
```

### 3. 部署时机

- ✅ 选择业务低峰期 (周末、凌晨)
- ✅ 确保关键人员在岗
- ✅ 准备回滚计划
- ✅ 通知相关方

### 4. 测试策略

```bash
# 金丝雀期间重点测试
- 新功能正确性
- 性能指标
- 错误率
- 业务关键路径
- 边界条件
```

### 5. 文档记录

```bash
# 每次部署后记录
- 部署时间
- 版本号
- 变更内容
- 测试结果
- 性能指标
- 任何问题
```

## 常见问题FAQ

### Q: 蓝绿部署需要多少额外资源？

A: 至少需要额外100%的资源，因为要同时运行两套环境。对于生产环境，建议分配1.5-2倍的资源。

### Q: 数据库如何处理蓝绿部署？

A: 推荐方案：
- 模式变更向前兼容
- 数据迁移在切换前完成
- 共享数据库实例
- 使用特性开关控制数据写入

### Q: 如何处理状态数据？

A: 对于无状态应用，切换简单。对于有状态应用：
- 使用外部状态存储 (Redis, 数据库)
- 同步状态数据
- 或容忍短暂数据丢失

### Q: 金丝雀阶段流量百分比多少合适？

A: 根据业务特点：
- **关键系统**: 1-5%
- **中等风险**: 10-20%
- **低风险**: 50%
- **经过充分测试**: 可直接100%

### Q: 多久可以清理旧版本？

A: 建议：
- 观察1-24小时确保稳定
- 检查所有监控指标
- 确认没有异常报警
- 执行手动清理

## 高级用法

### 1. 基于指标的自动切换

```bash
# 结合Prometheus实现自动切换
if error_rate < 0.1% && response_time_p95 < 200ms; then
  switch_to_green()
fi
```

### 2. 细粒度流量控制

```bash
# 按用户ID分流
nginx.ingress.kubernetes.io/canary-by-header: "X-User-ID"
nginx.ingress.kubernetes.io/canary-by-header-value: ".*"

# 按地理位置分流
nginx.ingress.kubernetes.io/canary-by-header: "X-Region"
```

### 3. 多阶段金丝雀

```bash
# 第一阶段: 5%
./blue-green-deploy.sh --traffic-percentage 5

# 观察30分钟后
# 第二阶段: 25%
./blue-green-deploy.sh --traffic-percentage 25

# 观察1小时后
# 第三阶段: 100%
./blue-green-deploy.sh --traffic-percentage 100
```

## 总结

蓝绿部署是生产环境的安全部署策略，通过零停机时间、快速回滚和金丝雀验证，确保应用更新的安全性和可靠性。

**关键要点**:
1. ✅ 始终准备回滚计划
2. ✅ 使用金丝雀验证降低风险
3. ✅ 密切监控关键指标
4. ✅ 在低峰期执行部署
5. ✅ 自动化减少人为错误

**联系方式**: 如有问题，请联系DevOps团队
- 邮箱: devops@company.com
- Slack: #deployments
