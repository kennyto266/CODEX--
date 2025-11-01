# Frontend Architecture Optimization Proposal

## Why
当前的港股量化交易系统前端存在以下问题，影响开发效率和系统性能：

1. **组件重复问题**：同时存在 `.vue` 和 `.js` 组件文件（38个组件），导致代码维护困难
2. **工具类不完整**：缺少核心工具如 API 客户端、缓存管理、错误处理等
3. **架构不规范**：前端代码组织结构混乱，缺少统一的架构标准
4. **性能未优化**：虽有 Vite 配置但未充分利用代码分割和懒加载优势

## What Changes

### 阶段一：架构整合
- 移除重复的 `.js` 组件文件，统一使用 `.vue` 组件
- 重构 Pinia Store，添加完整的类型支持
- 建立统一的工具库（API、缓存、错误处理、格式化）

### 阶段二：功能增强
- 添加完整的 API 客户端（支持请求重试、拦截器、超时处理）
- 实现智能缓存系统（LRU、TTL、预取）
- 添加全局错误处理和用户通知系统
- 实现实时数据订阅管理（WebSocket）

### 阶段三：性能优化
- 完善代码分割策略，按路由和功能模块分割
- 实现组件懒加载和预加载策略
- 优化打包配置，添加 Tree Shaking
- 实现虚拟滚动优化大列表性能

### 阶段四：用户体验
- 添加加载状态管理（Skeleton、Spinner）
- 实现响应式设计优化
- 添加键盘快捷键支持
- 实现暗色/亮色主题切换

## Impact

### 影响的规格
- **dashboard-ui** - UI 组件和交互
- **data-management** - 数据获取和缓存
- **real-time-updates** - 实时数据更新机制

### 影响的代码文件
- `src/dashboard/static/js/components/` - 组件重构
- `src/dashboard/static/js/stores/` - Store 优化
- `src/dashboard/static/js/utils/` - 工具库完善
- `src/dashboard/static/js/main.js` - 主应用入口
- `src/dashboard/static/vite.config.js` - 构建优化

### 预期收益
- **代码量减少** ~40%（移除重复文件）
- **加载性能提升** 30-50%（代码分割 + 懒加载）
- **开发效率提升** 50%（统一架构 + 完整工具库）
- **用户体验提升**（更好的加载状态、错误处理、响应式设计）

## Rollback Plan
- 使用 Git 标签标记优化前版本
- 分阶段实施，每阶段可独立回滚
- 保留完整的备份和迁移文档
