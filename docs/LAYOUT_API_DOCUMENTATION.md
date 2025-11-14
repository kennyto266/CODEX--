# LayoutConfig API Documentation

## 概述

LayoutConfig API提供了完整的布局配置管理功能，支持创建、读取、更新、删除和应用布局配置。API基于RESTful设计，使用JSON格式进行数据交换。

**API版本**: v1
**基础URL**: `http://localhost:8001/api/v1`

---

## 数据模型

### LayoutComponent

布局组件模型

```json
{
  "id": "string",                    // 组件唯一标识
  "type": "string",                  // 组件类型 (chart, indicator, portfolio, etc.)
  "title": "string",                 // 组件标题
  "position": {                      // 位置信息
    "x": "number",                   // X坐标
    "y": "number",                   // Y坐标
    "w": "number",                   // 宽度
    "h": "number"                    // 高度
  },
  "properties": "object",            // 组件自定义属性
  "visible": "boolean"               // 是否显示
}
```

### LayoutConfig

布局配置模型

```json
{
  "id": "string",                    // 布局唯一标识 (UUID)
  "name": "string",                  // 布局名称
  "description": "string",           // 布局描述
  "components": "array",             // 组件列表
  "theme": "object",                 // 主题配置
  "version": "string",               // 版本号 (x.y.z)
  "is_default": "boolean",           // 是否默认布局
  "is_active": "boolean",            // 是否激活
  "user_id": "string",               // 用户ID
  "usage_count": "number",           // 使用次数
  "created_at": "string",            // 创建时间 (ISO 8601)
  "updated_at": "string"             // 更新时间 (ISO 8601)
}
```

---

## API端点

### 1. 获取所有布局 (T214)

#### 请求

```http
GET /api/v1/layout
```

#### 查询参数

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `user_id` | string | 否 | - | 按用户ID过滤 |
| `is_active` | boolean | 否 | - | 按激活状态过滤 |
| `is_default` | boolean | 否 | - | 按默认状态过滤 |
| `page` | integer | 否 | 1 | 页码 (从1开始) |
| `size` | integer | 否 | 20 | 每页数量 (1-100) |
| `sort_by` | string | 否 | created_at | 排序字段 |
| `sort_order` | string | 否 | desc | 排序方向 (asc/desc) |

#### 响应

```json
{
  "total": 10,                       // 总数
  "items": [                         // 布局列表
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "version": "string",
      "is_default": "boolean",
      "is_active": "boolean",
      "user_id": "string",
      "usage_count": "number",
      "created_at": "string",
      "updated_at": "string"
    }
  ],
  "page": 1,
  "size": 20
}
```

#### 状态码

- `200` - 成功
- `500` - 服务器内部错误

---

### 2. 创建新布局 (T215)

#### 请求

```http
POST /api/v1/layout
Content-Type: application/json
```

#### 请求体

```json
{
  "name": "string",                  // 必填：布局名称
  "description": "string",           // 可选：布局描述
  "components": [                    // 可选：组件列表
    {
      "id": "comp1",
      "type": "chart",
      "title": "价格图表",
      "position": {
        "x": 0,
        "y": 0,
        "w": 6,
        "h": 4
      },
      "properties": {
        "symbol": "0700.HK"
      },
      "visible": true
    }
  ],
  "theme": {                         // 可选：主题配置
    "primary_color": "#1976d2",
    "background_color": "#ffffff"
  },
  "version": "string",               // 可选：版本号 (默认: "1.0.0")
  "user_id": "string",               // 可选：用户ID
  "is_default": "boolean"            // 可选：是否默认 (默认: false)
}
```

#### 响应

```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "components": [...],
  "theme": {...},
  "version": "string",
  "is_default": "boolean",
  "is_active": "boolean",
  "user_id": "string",
  "usage_count": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### 状态码

- `201` - 创建成功
- `422` - 验证失败
- `500` - 服务器内部错误

---

### 3. 获取指定布局

#### 请求

```http
GET /api/v1/layout/{layout_id}
```

#### 路径参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `layout_id` | string | 是 | 布局ID (UUID格式) |

#### 响应

完整布局配置信息（参见LayoutConfig模型）

#### 状态码

- `200` - 成功
- `404` - 布局不存在
- `500` - 服务器内部错误

---

### 4. 更新布局 (T216)

#### 请求

```http
PUT /api/v1/layout/{layout_id}
Content-Type: application/json
```

#### 路径参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `layout_id` | string | 是 | 布局ID (UUID格式) |

#### 请求体

```json
{
  "name": "string",                  // 可选：新名称
  "description": "string",           // 可选：新描述
  "components": [...],               // 可选：新组件列表
  "theme": {...},                    // 可选：新主题
  "version": "string",               // 可选：新版本
  "is_default": "boolean",           // 可选：是否默认
  "is_active": "boolean"             // 可选：是否激活
}
```

#### 响应

更新后的布局配置信息

#### 状态码

- `200` - 成功
- `400` - 请求无效（如尝试更新默认布局）
- `404` - 布局不存在
- `500` - 服务器内部错误

---

### 5. 删除布局 (T217)

#### 请求

```http
DELETE /api/v1/layout/{layout_id}
```

#### 路径参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `layout_id` | string | 是 | 布局ID (UUID格式) |

#### 响应

```json
{
  "success": "true",
  "message": "布局 'uuid' 已成功删除",
  "layout_id": "uuid"
}
```

#### 状态码

- `200` - 成功
- `400` - 请求无效（如尝试删除默认布局）
- `404` - 布局不存在
- `500` - 服务器内部错误

#### 备注

使用软删除，设置`is_active`为`false`而不是物理删除。

---

### 6. 应用布局 (T218)

#### 请求

```http
POST /api/v1/layout/{layout_id}/apply
```

#### 路径参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `layout_id` | string | 是 | 布局ID (UUID格式) |

#### 响应

```json
{
  "success": "boolean",
  "message": "string",
  "layout_id": "uuid",
  "usage_count": "number"
}
```

#### 状态码

- `200` - 成功
- `400` - 布局未激活
- `404` - 布局不存在
- `500` - 服务器内部错误

#### 备注

应用布局会增加`usage_count`，并返回当前使用次数。

---

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误码

| 状态码 | 描述 | 示例 |
|--------|------|------|
| 400 | Bad Request | 尝试删除默认布局 |
| 404 | Not Found | 布局ID不存在 |
| 422 | Unprocessable Entity | 数据验证失败 |
| 500 | Internal Server Error | 服务器内部错误 |

---

## 示例

### 创建布局

```bash
curl -X POST http://localhost:8001/api/v1/layout \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的仪表板",
    "description": "自定义布局",
    "components": [...],
    "theme": {...}
  }'
```

### 获取所有布局

```bash
curl http://localhost:8001/api/v1/layout \
  -G -d page=1 -d size=10
```

### 更新布局

```bash
curl -X PUT http://localhost:8001/api/v1/layout/{id} \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新的名称",
    "version": "1.1.0"
  }'
```

### 删除布局

```bash
curl -X DELETE http://localhost:8001/api/v1/layout/{id}
```

### 应用布局

```bash
curl -X POST http://localhost:8001/api/v1/layout/{id}/apply
```

---

## 数据验证规则

### 布局名称
- 长度：1-255字符
- 必填

### 版本号
- 格式：x.y.z (三段式)
- 示例：1.0.0, 2.1.3

### 组件位置
- 必须包含：x, y, w, h 四个字段
- 类型：整数

### 组件ID
- 唯一标识
- 字符串类型

---

## 最佳实践

1. **分页**：大量数据时使用分页
2. **过滤**：使用过滤参数减少数据传输
3. **错误处理**：始终检查响应状态码
4. **验证**：客户端发送前验证数据格式
5. **默认布局**：每个用户最多一个默认布局
6. **软删除**：使用软删除保留历史记录

---

## 性能建议

1. **缓存**：对常用布局进行缓存
2. **索引**：数据库对user_id、is_active、created_at建立索引
3. **分页**：限制单页返回数量（默认20，最大100）
4. **字段选择**：列表接口仅返回必要字段

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2024-11-09 | 初始版本，包含5个CRUD端点 |

---

## 联系信息

如有问题或建议，请联系开发团队。
