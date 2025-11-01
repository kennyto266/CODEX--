# 英超聯賽官網數據源整合規範

## 概述

本規範定義了如何將英超聯賽官方網站 (`https://www.premierleague.com/en/matches`) 整合為 Telegram bot 足球賽程功能的專用數據源。

## Why

目前足球比分功能依賴 ESPN API 和模擬數據，無法提供準確和實時的英超聯賽信息。用戶需要更可靠的數據源來獲取英超比分、賽程和比賽狀態。英超聯賽官網作為官方數據源，提供最準確和最新的比賽信息，是理想的選擇。

## ADDED Requirements

### Requirement: System MUST integrate Premier League official website as primary data source
The system SHALL integrate the official Premier League website as the primary data source for football scores and schedules.

#### Scenario: 获取英超比分数据
- **WHEN** 用户执行 `/score soccer` 命令时
- **THEN** 系统访问 `https://www.premierleague.com/en/matches?competition=8&season=2025&matchweek=X&month=Y`
  - 自动检测当前赛季、轮次和月份
  - 提取所有英超比赛数据
  - 包括已完成、进行中和未开始的比赛
  - 支持历史比分查询（指定轮次）

#### Scenario: 处理动态网页内容
- **WHEN** 英超官网使用动态加载时
- **THEN** 系统通过 Chrome MCP 执行：
  - 等待 JavaScript 渲染完成
  - 等待 AJAX 请求完成
  - 滚动页面加载所有比赛
  - 等待内容稳定后再提取

#### Scenario: 失败回退机制
- **WHEN** 英超官网不可访问时
- **THEN** 系统自动切换到备用数据源：
  1. ESPN API (英超数据)
  2. 模拟数据（基于当前时间）

### Requirement: System MUST extract comprehensive match information
The system SHALL extract comprehensive match information from the Premier League website.

#### Scenario: 提取比赛基本信息
- **WHEN** 获取英超比赛数据时
- **THEN** 系统提取以下信息：
  - 比赛日期和时间 (GMT)
  - 主队和客队名称（英文和中文）
  - 实时比分（如果比赛进行中）
  - 最终比分（如果比赛已结束）
  - 比赛状态（scheduled/live/halftime/finished）
  - 比赛分钟（例如：67'+3）
  - 球场名称
  - 轮次信息

#### Scenario: 处理比赛状态
- **WHEN** 比赛处于不同状态时
- **THEN** 系统正确处理：
  - `scheduled`: 显示开赛时间，状态为"未开始"
  - `live`: 显示当前分钟数和补时，状态为"进行中"
    - 上半场: 0-45 分钟
    - 中场休息: 45 分钟，显示"半场"
    - 下半场: 46-90 分钟
    - 伤停补时: 90'+X 分钟
  - `finished`: 显示最终比分，状态为"已结束"
  - `postponed`: 显示延期信息
  - `cancelled`: 显示取消信息

#### Scenario: 处理伤停补时
- **WHEN** 比赛进入伤停补时阶段时
- **THEN** 系统显示：
  - 补时分钟数（例如：90'+3）
  - 计算预计结束时间
  - 更新比赛状态为"进行中"

### Requirement: System MUST implement timezone conversion
The system SHALL implement proper timezone conversion from GMT to HKT.

#### Scenario: GMT 转换为 HKT
- **WHEN** 显示比赛时间时
- **THEN** 系统执行：
  - 接收 GMT 时间戳
  - 转换为香港时间（UTC+8）
  - 处理夏令时（GMT+1）
  - 格式化为 `HH:MM (HKT)`

#### Scenario: 显示多时区时间
- **WHEN** 显示重要比赛信息时
- **THEN** 系统可以显示：
  - 本地开赛时间（主要）
  - 原 GMT 时间（可选）
  - 比赛地当地时间（可选）

#### Scenario: 处理跨日比赛
- **WHEN** 比赛时间跨日时
- **THEN** 系统正确处理：
  - 显示正确的日期
  - 例如：GMT 22:00 → HKT 次日 06:00

### Requirement: System MUST support comprehensive team name mapping
The system SHALL support comprehensive team name mapping from English to Chinese.

#### Scenario: 球队名称中文化
- **WHEN** 显示英超球队时
- **THEN** 系统显示中文球队名称：
  - Arsenal → 阿仙奴
  - Manchester City → 曼城
  - Liverpool → 利物浦
  - Chelsea → 車路士
  - Tottenham → 熱刺
  - Manchester United → 曼聯
  - 全部 20 支英超球队

#### Scenario: 处理未知球队
- **WHEN** 遇到未映射的球队名称时
- **THEN** 系统执行：
  - 使用原始英文名称
  - 记录到日志中
  - 更新映射表（如果需要）

#### Scenario: 球队名称变体处理
- **WHEN** 球队名称有变体时
- **THEN** 系统正确处理：
  - "Brighton & Hove Albion" → 白禮頓
  - "Tottenham Hotspur" → 熱刺
  - "West Ham United" → 韋斯咸

### Requirement: System MUST implement caching mechanism
The system SHALL implement an efficient caching mechanism to improve performance.

#### Scenario: 内存缓存
- **WHEN** 获取数据时
- **THEN** 系统：
  - 检查 5 分钟内存缓存
  - 缓存键格式：`pl_scores_{YYYY-MM-DD}_{matchweek}`
  - 如果缓存存在且未过期，返回缓存数据
  - 缓存命中率应 > 70%

#### Scenario: 缓存更新策略
- **WHEN** 缓存过期或需要更新时
- **THEN** 系统：
  - 自动重新获取数据
  - 更新缓存
  - 保持数据一致性
  - 记录缓存命中率

#### Scenario: 强制刷新缓存
- **WHEN** 用户请求强制刷新时
- **THEN** 系统：
  - 忽略现有缓存
  - 立即获取最新数据
  - 更新缓存
  - 返回最新数据

### Requirement: System MUST handle concurrency properly
The system SHALL handle concurrent requests properly using appropriate synchronization mechanisms.

#### Scenario: 多用户并发查询
- **WHEN** 多个用户同时查询比分时
- **THEN** 系统：
  - 使用信号量限制并发请求（最多 5 个）
  - 共享缓存数据
  - 避免重复请求
  - 保持响应时间 < 3 秒

#### Scenario: 并发数据更新
- **WHEN** 多个请求同时更新数据时
- **THEN** 系统：
  - 使用异步锁确保数据一致性
  - 最后一个写入者获胜
  - 避免数据竞争
  - 保持缓存同步

### Requirement: System MUST implement robust error handling
The system SHALL implement robust error handling and fallback mechanisms.

#### Scenario: 网站不可访问
- **WHEN** 英超官网返回错误时
- **THEN** 系统：
  - 记录详细错误日志
  - 自动切换到备用数据源
  - 向用户显示备用源提示
  - 继续监控系统状态

#### Scenario: 数据解析错误
- **WHEN** 无法解析返回的数据时
- **THEN** 系统：
  - 记录解析错误详情
  - 尝试使用备用解析器
  - 返回部分数据（如果可能）
  - 通知管理员

#### Scenario: 网络超时
- **WHEN** 请求超时时
- **THEN** 系统：
  - 记录超时错误
  - 重新尝试（最多 3 次）
  - 每次重试增加延迟（1s, 2s, 4s）
  - 最后切换到备用源

### Requirement: System MUST implement rate limiting
The system SHALL implement rate limiting to prevent abuse and ensure fair usage.

#### Scenario: 请求限流
- **WHEN** 检测到高频请求时
- **THEN** 系统：
  - 限制每个 IP 每分钟最多 20 次请求
  - 限制每个用户每分钟最多 5 次查询
  - 返回 429 Too Many Requests 状态
  - 提示用户稍后重试

#### Scenario: 避免被封
- **WHEN** 请求过于频繁时
- **THEN** 系统：
  - 在请求之间添加随机延迟（1-3 秒）
  - 使用 User-Agent 轮换
  - 保持请求模式自然
  - 监控 HTTP 状态码

### Requirement: System MUST support schedule queries
The system SHALL support querying and displaying future Premier League schedules.

#### Scenario: 获取未来赛程
- **WHEN** 用户执行 `/schedule soccer` 时
- **THEN** 系统：
  - 获取未来 7 天的英超赛程
  - 显示比赛日期、时间、对阵双方
  - 按日期分组显示
  - 标注重要比赛（德比、榜首大战等）

#### Scenario: 赛程分类显示
- **WHEN** 显示英超赛程时
- **THEN** 系统按以下方式组织：
  - 按日期分组
  - 按轮次分类
  - 标记重要比赛
  - 显示是否有直播

#### Scenario: 赛程详情查询
- **WHEN** 用户查询特定比赛详情时
- **THEN** 系统显示：
  - 对阵双方（中文名称）
  - 开赛时间（HKT）
  - 球场信息
  - 当前排名对比
  - 历史交锋记录（如果可用）

### Requirement: System MUST format messages clearly
The system SHALL format Telegram messages clearly and user-friendly.

#### Scenario: 格式化当日比分
- **WHEN** 格式化英超比分消息时
- **THEN** 系统生成以下格式：

```
⚽ 英超联赛比分 (2025-10-31)

🥇 第 10 轮

✅ 已结束
🏟️ 伊蒂哈德球场
⚡ 曼城 3 - 1 利物浦
   📅 22:00 (GMT) → 06:00 (HKT)
   📊 观众: 54,000

🔴 进行中
⏱️ 阿森纳 vs 切尔西 (第 42 分钟)
   💯 比分: 2 - 0
   📊 进度: 47%
   🕖 预计结束: 21:42 (HKT)

⏸️ 即将开始
🕗 20:30 热刺 vs 曼联
   📅 20:30 (GMT) → 次日 04:30 (HKT)
   🏟️ 托特纳姆热刺球场
```

#### Scenario: 格式化赛程消息
- **WHEN** 格式化英超赛程消息时
- **THEN** 系统生成：

```
📅 英超赛程 (未来 7 天)

11 月 1 日 (周五)
🥇 第 11 轮
🕖 20:30 阿森纳 vs 切尔西
   🏟️ 酋长球场

🕗 21:00 曼城 vs 利物浦
   🏟️ 伊蒂哈德球场

11 月 2 日 (周六)
🕖 20:30 热刺 vs 曼联
   🏟️ 托特纳姆热刺球场
...

⭐ 重点赛事
11 月 3 日 (周日) 21:00
🔥 曼联 vs 曼城 (曼市德比)
🏟️ 老特拉福德球场
```

### Requirement: System MUST implement monitoring
The system SHALL implement comprehensive monitoring and alerting.

#### Scenario: 性能监控
- **WHEN** 系统运行时
- **THEN** 系统监控：
  - 请求总数
  - 成功率（目标 > 95%）
  - 平均响应时间（目标 < 3 秒）
  - 缓存命中率（目标 > 70%）
  - 并发请求数

#### Scenario: 错误监控
- **WHEN** 发生错误时
- **THEN** 系统：
  - 记录详细错误日志
  - 分类错误类型
  - 统计错误频率
  - 设置告警阈值
  - 自动通知管理员

#### Scenario: 数据质量监控
- **WHEN** 获取数据时
- **THEN** 系统检查：
  - 数据完整性
  - 数据一致性
  - 数据时效性
  - 数据准确性

### Requirement: System MUST support historical data
The system SHALL support querying historical match data for the current season.

#### Scenario: 查询历史比分
- **WHEN** 用户查询历史轮次时
- **THEN** 系统：
  - 支持查询任意历史轮次（当前赛季）
  - 显示该轮次的完整比分
  - 按轮次分组显示
  - 包含比赛详情

#### Scenario: 查询整个赛季数据
- **WHEN** 用户查询整个赛季时
- **THEN** 系统：
  - 按轮次分组显示所有比赛
  - 显示积分榜（如果可用）
  - 显示射手榜（如果可用）
  - 支持分页显示

### Requirement: System MUST handle updates gracefully
The system SHALL handle live match updates gracefully and efficiently.

#### Scenario: 实时比分更新
- **WHEN** 比赛进行中时
- **THEN** 系统：
  - 每 30 秒检查比分变化
  - 如果进球，立即更新
  - 中场休息时暂停更新
  - 补时阶段增加更新频率

#### Scenario: 比赛状态变更
- **WHEN** 比赛状态发生变化时
- **THEN** 系统：
  - 检测状态变化
  - 更新缓存
  - 通知相关用户（如果适用）
  - 记录变更日志

## MODIFIED Requirements

### Modified Requirement: System MUST prioritize Premier League data source
The system SHALL prioritize Premier League official website over ESPN API as the primary data source.

**BEFORE**: ESPN API is the primary data source
**AFTER**: Premier League official website is primary, ESPN is fallback
**IMPACT**: `real_data_fetcher.py` data source priority order changes
**MIGRATION**: Existing code needs update to data source selection logic

### Modified Requirement: System MUST enhance error recovery
The system SHALL enhance error recovery capabilities with multi-layer fallback.

**BEFORE**: Simple error handling and fallback
**AFTER**: Multi-layer error handling (website → ESPN → mock)
**IMPACT**: Requires more complex error handling logic
**MIGRATION**: Update exception handling classes and recovery strategies

### Modified Requirement: System MUST improve caching efficiency
The system SHALL improve caching efficiency with multi-tier architecture.

**BEFORE**: Simple in-memory caching
**AFTER**: Multi-tier cache architecture (memory → file → Redis)
**IMPACT**: Requires implementing cache management interface
**MIGRATION**: Update cache-related code

## REMOVED Requirements

### Removed Requirement: Direct ESPN API dependency
The direct dependency on ESPN API as primary data source SHALL be removed.

**REASON**: Premier League official website is the primary data source, ESPN is demoted to fallback
**IMPACT**: Reduced dependency on external API
**MIGRATION**: Update data fetching logic

## 性能要求

- **响应时间**: < 3 秒（95% 的请求）
- **成功率**: > 95%
- **缓存命中率**: > 70%
- **并发处理**: 支持 15 个并发请求
- **数据新鲜度**: 缓存过期时间 5 分钟
- **错误恢复时间**: < 10 秒

## 安全要求

- **请求限流**: 每 IP 每分钟 20 次
- **用户限流**: 每用户每分钟 5 次
- **数据验证**: 所有输入参数验证
- **错误信息**: 不暴露敏感信息
- **日志脱敏**: 不记录个人敏感信息

## 兼容性要求

- **向后兼容**: 保持现有 API 不变
- **多数据源**: 支持多个数据源同时存在
- **配置灵活**: 支持通过配置启用/禁用数据源
- **版本兼容**: 与现有 Telegram bot 框架兼容

## 监控指标

1. **请求指标**:
   - 总请求数
   - 成功请求数
   - 失败请求数
   - 平均响应时间

2. **缓存指标**:
   - 缓存命中率
   - 缓存大小
   - 缓存过期率

3. **数据质量指标**:
   - 数据完整性
   - 数据准确性
   - 数据时效性

4. **错误指标**:
   - 错误类型分布
   - 错误频率
   - 恢复成功率

## 相关规格

- `specs/sports-scoring` - 体育比分核心框架
- `specs/football-scoring` - 足球比分功能规格
- `specs/sports-schedule` - 赛程查询功能
- `specs/telegram-bot` - Telegram Bot 集成

## 测试要求

1. **单元测试**: 测试所有组件功能
2. **集成测试**: 测试多数据源场景
3. **性能测试**: 测试并发和负载
4. **错误测试**: 测试错误场景和恢复
5. **用户验收测试**: 验证用户体验

---

**规范版本**: 1.0
**创建时间**: 2025-10-31
**状态**: 待实施
**负责人**: Claude Code
