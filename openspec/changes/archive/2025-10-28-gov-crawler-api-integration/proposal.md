# Gov Crawler API 集成提案

## 概述

本提案旨在移除 HKEX Mock 数据回退机制，实现 gov_crawler 数据 API 端点，并区分两个独立的数据源项目。

## 目标

1. **移除 HKEX Mock 数据回退机制**
   - 移除 run_dashboard.py 中的 Mock 数据回退代码
   - 错误时返回明确的 HTTP 503 错误信息
   - 确保数据透明性，不混淆真实数据和 Mock 数据

2. **实现 gov_crawler 数据 API**
   - 创建 3 个新的 API 端点：
     - `GET /api/gov/data` - 获取政府数据
     - `GET /api/gov/indicators` - 获取指标列表
     - `GET /api/gov/status` - 获取系统状态
   - 支持 35 个政府数据指标，9 个数据分类

3. **修复 API 端点位置错误**
   - 将 gov_crawler 端点从 `create_app()` 外部移动到内部
   - 解决 `NameError: name 'app' is not defined` 错误

4. **区分数据源为独立项目**
   - HKEX 数据源: `/api/stock/data` (股票数据)
   - gov_crawler 数据源: `/api/gov/data` (政府数据)
   - 确保两个数据源清晰分离

## 变更内容

### 修改的文件

1. `run_dashboard.py`
   - 行 416-502: 移除 HKEX Mock 数据回退机制
   - 行 508-786: 实现 gov_crawler API 端点
   - 行 812-813: 更新端口配置为 8002

2. `test_gov_crawler_api.py` (新文件)
   - 创建自动化测试脚本
   - 6 个测试用例

## 预期结果

- ✅ HKEX API 在失败时返回明确的错误信息
- ✅ gov_crawler API 提供 35 个政府数据指标
- ✅ 所有 API 端点正常工作
- ✅ 测试通过率 100%

## 状态

**完成状态**: ✅ 已完成  
**测试状态**: ✅ 全部通过  
**文档状态**: ✅ 已完成  

---

**创建日期**: 2025-10-28  
**负责人**: Claude Code AI  
**提案 ID**: 4246
