# 項目計劃優化 - 設計文檔

## 設計理念

本設計遵循以下核心原則，確保項目管理系統的高效性、可擴展性和可維護性：

### 1. 小步快跑 (Small Batches)
**設計原則**: 將大型任務拆分為2-4小時的小任務
**理由**: 降低認知負擔、提高完成率、便於追蹤進度、減少風險

**實施方式**:
```python
# ❌ 大任務：重構API (40小時)
# ✅ 小任務：每個API端點重構 (3小時)
tasks = [
    "TASK-101: 重構api_agents.py使用Repository (3h)",
    "TASK-102: 重構api_strategies.py使用Repository (3h)",
    "TASK-103: 重構api_trading.py使用Repository (3h)",
    "TASK-104: 重構api_risk.py使用Repository (3h)",
    "TASK-105: 重構api_backtest.py使用Repository (3h)",
]
```

### 2. 可視化管理 (Visibility)
**設計原則**: 實時可視化項目進度和團隊狀態
**理由**: 提高透明度、及早發現問題、提升決策質量

**實施方式**:
```python
# 任務看板視圖
class TaskBoardView:
    """Kanban-style 任務板"""
    columns = {
        "TODO": "待開始",
        "IN_PROGRESS": "進行中",
        "REVIEW": "待驗收",
        "DONE": "已完成"
    }

    def get_real_time_metrics(self):
        """實時指標"""
        return {
            "completion_rate": 0.75,  # 75%
            "velocity_trend": "↗ +15%",
            "blocked_tasks": 3,
            "team_capacity": 0.85
        }
```

### 3. 自動化優先 (Automation First)
**設計原則**: 自動化所有可自動化的流程
**理由**: 減少手工錯誤、節省時間、確保一致性

**自動化場景**:
- Git提交自動關聯任務
- 任務狀態自動更新
- 自動化測試觸發
- 進度報告自動生成
- 依賴關係自動檢查

### 4. 數據驅動 (Data-Driven)
**設計原則**: 基於數據做決策，而非主觀判斷
**理由**: 客觀評估、持續改進、可預測性

**關鍵指標**:
```python
class ProjectMetrics:
    """項目關鍵指標"""

    # 交付指標
    sprint_completion_rate: float  # Sprint完成率
    velocity: float  # 團隊速度
    lead_time: float  # 任務流轉時間

    # 質量指標
    defect_rate: float  # 缺陷率
    code_coverage: float  # 代碼覆蓋率
    rework_ratio: float  # 返工比例

    # 流程指標
    wait_time: float  # 等待時間
    bottleneck_count: int  # 瓶頸數量
    dependency_resolution_time: float  # 依賴解決時間
```

## 系統架構設計

### 整體架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                     任務管理系統架構                         │
├─────────────────────────────────────────────────────────────┤
│  前端層 (Frontend Layer)                                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ TaskBoard    │ │ SprintBoard  │ │ Metrics      │        │
│  │ (Vue.js)     │ │ (Vue.js)     │ │ (Chart.js)   │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│               │               │               │             │
│               └───────────────┼───────────────┘             │
│                           WebSocket                         │
├─────────────────────────────────────────────────────────────┤
│  API層 (API Layer)                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │ FastAPI Routes                                       │    │
│  │  - /api/tasks (CRUD)                                │    │
│  │  - /api/sprints (Sprint管理)                       │    │
│  │  - /api/metrics (指標)                             │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                 │
├─────────────────────────────────────────────────────────────┤
│  服務層 (Service Layer)                                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ TaskService  │ │ SprintSvc    │ │ MetricsSvc   │        │
│  │ 任務服務     │ │ Sprint服務   │ │ 指標服務     │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ AutoSvc      │ │ ReportSvc    │ │ NotifySvc    │        │
│  │ 自動化服務   │ │ 報告服務     │ │ 通知服務     │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  數據層 (Data Layer)                                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Task Model   │ │ Sprint Model │ │ Metrics Data │        │
│  │ (SQLAlchemy) │ │ (SQLAlchemy) │ │ (Redis)      │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│                           │                                 │
│                    PostgreSQL                              │
└─────────────────────────────────────────────────────────────┘
```

### 核心組件設計

#### 1. 任務數據模型

```python
from sqlalchemy import Column, String, DateTime, Enum, Integer, Text
from sqlalchemy.dialects.postgresql import ARRAY
from enum import Enum as PyEnum

class TaskStatus(PyEnum):
    TODO = "待開始"
    IN_PROGRESS = "進行中"
    REVIEW = "待驗收"
    DONE = "已完成"
    BLOCKED = "已阻塞"

class Priority(PyEnum):
    P0 = "P0"  # 關鍵路徑
    P1 = "P1"  # 重要
    P2 = "P2"  # 一般

class Task(Base):
    __tablename__ = "tasks"

    # 基本信息
    id = Column(String, primary_key=True)  # TASK-001
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # 狀態管理
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(Enum(Priority), default=Priority.P2)

    # 時間管理
    estimated_hours = Column(Integer, nullable=False)
    actual_hours = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # 人員管理
    assignee = Column(String(100))
    reporter = Column(String(100))
    watchers = Column(ARRAY(String))

    # 關係管理
    dependencies = Column(ARRAY(String))  # 任務ID列表
    dependents = Column(ARRAY(String))    # 依賴此任務的任務

    # 驗收標準
    acceptance_criteria = Column(ARRAY(Text))
    deliverables = Column(ARRAY(String))

    # Sprint管理
    sprint = Column(String(50))
    story_points = Column(Integer, default=1)

    # 自動化字段
    automation_metadata = Column(JSON)
```

**設計決策說明**:
- **String ID**: 使用"TASK-001"格式，易於閱讀和追踪
- **時間管理**: 區分預估時間和實際時間，用於持續改進估時
- **依賴管理**: 顯式存儲依賴關係，支持自動檢查
- **自動化元數據**: JSON字段存儲Git提交ID、自動化檢查結果等

#### 2. 任務狀態流轉

```python
class TaskStateMachine:
    """任務狀態機，確保狀態變更的合法性"""

    ALLOWED_TRANSITIONS = {
        TaskStatus.TODO: [TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED],
        TaskStatus.IN_PROGRESS: [TaskStatus.REVIEW, TaskStatus.BLOCKED, TaskStatus.TODO],
        TaskStatus.REVIEW: [TaskStatus.DONE, TaskStatus.IN_PROGRESS],
        TaskStatus.BLOCKED: [TaskStatus.TODO, TaskStatus.IN_PROGRESS],
        TaskStatus.DONE: []  # 已完成任務不允許變更
    }

    def can_transition(self, from_status: TaskStatus, to_status: TaskStatus) -> bool:
        """檢查狀態變更是否合法"""
        return to_status in self.ALLOWED_TRANSITIONS[from_status]

    async def transition(self, task_id: str, to_status: TaskStatus, comment: str = None):
        """執行狀態變更"""
        task = await self.get_task(task_id)
        if not self.can_transition(task.status, to_status):
            raise InvalidTransitionError(f"不能從 {task.status} 變更到 {to_status}")

        # 記錄狀態變更日誌
        await self.log_transition(task_id, task.status, to_status, comment)

        # 更新任務狀態
        task.status = to_status
        if to_status == TaskStatus.DONE:
            task.completed_at = datetime.utcnow()

        await self.save_task(task)
```

**設計決策說明**:
- **狀態機模式**: 防止非法狀態變更，確保數據一致性
- **變更日誌**: 記錄所有狀態變更，用於審計和問題追踪
- **完成時間**: 自動記錄完成時間，支持性能分析

#### 3. 自動化工作流引擎

```python
class AutomationEngine:
    """自動化工作流引擎"""

    async def handle_git_commit(self, commit: GitCommit):
        """處理Git提交事件"""
        # 提取任務ID
        task_ids = self.extract_task_ids(commit.message)

        for task_id in task_ids:
            # 檢查是否為關閉任務的提交
            if self.is_closing_commit(commit.message):
                await self.transition_task(task_id, TaskStatus.DONE, f"Git提交: {commit.hash}")
                await self.link_commit(task_id, commit.hash)

            # 如果是工作提交，轉為進行中
            elif commit.message.startswith(("feat:", "fix:", "refactor:")):
                await self.transition_task(task_id, TaskStatus.IN_PROGRESS)

    async def check_dependencies(self, task_id: str):
        """檢查任務依賴"""
        task = await self.get_task(task_id)

        for dep_id in task.dependencies:
            dep_task = await self.get_task(dep_id)
            if dep_task.status != TaskStatus.DONE:
                raise DependencyNotMetError(f"依賴任務 {dep_id} 未完成")

        # 所有依賴都已完成，可以開始
        if task.status == TaskStatus.TODO:
            await self.transition_task(task_id, TaskStatus.IN_PROGRESS, "所有依賴已滿足")

    async def detect_blockers(self):
        """檢測阻塞任務"""
        blocked_tasks = []

        for task in await self.get_all_tasks():
            if task.status == TaskStatus.IN_PROGRESS:
                # 檢查依賴是否完成
                try:
                    await self.check_dependencies(task.id)
                except DependencyNotMetError:
                    blocked_tasks.append(task)
                    await self.transition_task(task.id, TaskStatus.BLOCKED)

        return blocked_tasks
```

**設計決策說明**:
- **事件驅動**: 基於Git提交事件自動更新任務狀態
- **語義化提交**: 根據提交信息類型決定狀態變更
- **依賴檢查**: 自動化檢查前置條件，減少手動錯誤
- **阻塞檢測**: 定期掃描並標記阻塞任務

#### 4. Sprint計劃算法

```python
class SprintPlanner:
    """Sprint規劃引擎"""

    def plan_sprint(self, sprint: Sprint, team_capacity: int) -> List[Task]:
        """智能Sprint規劃"""

        # 獲取待分配任務
        backlog = self.get_prioritized_backlog()

        # 按優先級和依賴排序
        sorted_backlog = self.sort_by_priority_and_dependency(backlog)

        selected_tasks = []
        total_hours = 0

        for task in sorted_backlog:
            # 檢查容量
            if total_hours + task.estimated_hours > team_capacity:
                continue

            # 檢查依賴是否在本Sprint內
            if self.has_external_dependency(task, selected_tasks):
                continue

            selected_tasks.append(task)
            total_hours += task.estimated_hours

        return selected_tasks

    def calculate_team_capacity(self, team_members: List[str]) -> int:
        """計算團隊總容量"""
        total_capacity = 0

        for member in team_members:
            # 從歷史數據計算個人速度
            velocity = self.get_member_velocity(member)
            # 考慮休假、會議等時間
            available_hours = self.get_available_hours(member)

            total_capacity += min(velocity, available_hours)

        return total_capacity

    def get_member_velocity(self, member: str) -> int:
        """計算成員歷史平均速度"""
        # 獲取過去3個Sprint的數據
        sprints = self.get_recent_sprints(member, 3)

        completed_hours = sum(s.actual_hours for s in sprints)
        sprint_count = len(sprints)

        if sprint_count == 0:
            return 40  # 默認每Sprint 40小時

        return int(completed_hours / sprint_count)
```

**設計決策說明**:
- **智能規劃**: 考慮優先級、依賴、團隊容量多個因素
- **歷史數據**: 基於歷史速度預測，更準確
- **依賴管理**: 避免選擇依賴外部Sprint的任務
- **個人化速度**: 考慮每個成員的不同能力

#### 5. 指標計算引擎

```python
class MetricsEngine:
    """項目指標計算引擎"""

    def calculate_velocity(self, sprint: Sprint) -> float:
        """計算Sprint速度 (完成的Story Points)"""
        completed_tasks = [
            t for t in sprint.tasks
            if t.status == TaskStatus.DONE
        ]

        return sum(t.story_points for t in completed_tasks)

    def calculate_burndown(self, sprint: Sprint) -> Dict[date, float]:
        """計算燃盡圖數據"""
        start_date = sprint.start_date
        end_date = sprint.end_date

        # 理想燃盡線
        total_points = sum(t.story_points for t in sprint.tasks)
        days = (end_date - start_date).days
        ideal_burndown = {}

        for i in range(days + 1):
            date = start_date + timedelta(days=i)
            remaining = total_points - (total_points * i / days)
            ideal_burndown[date] = remaining

        # 實際燃盡線
        actual_burndown = {}
        current_remaining = total_points

        for task in sprint.tasks:
            if task.completed_at:
                date = task.completed_at.date()
                if date not in actual_burndown:
                    actual_burndown[date] = current_remaining
                actual_burndown[date] -= task.story_points
                current_remaining -= task.story_points

        return {
            "ideal": ideal_burndown,
            "actual": actual_burndown
        }

    def detect_bottlenecks(self, sprint: Sprint) -> List[Bottleneck]:
        """檢測流程瓶頸"""
        bottlenecks = []

        # 檢查在制品 (WIP)
        wip_by_member = defaultdict(int)
        for task in sprint.tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                wip_by_member[task.assignee] += 1

        for member, wip_count in wip_by_member.items():
            if wip_count > 3:  # 每人同時超過3個任務視為瓶頸
                bottlenecks.append(Bottleneck(
                    type="WIP_LIMIT",
                    member=member,
                    severity="WARNING",
                    message=f"{member} 有 {wip_count} 個同時進行的任務"
                ))

        # 檢查長時間未更新的任務
        stale_tasks = [
            t for t in sprint.tasks
            if t.status == TaskStatus.IN_PROGRESS
            and (datetime.utcnow() - t.updated_at).days > 3
        ]

        for task in stale_tasks:
            bottlenecks.append(Bottleneck(
                type="STALE_TASK",
                task_id=task.id,
                severity="ERROR",
                message=f"任務 {task.id} 已超過3天未更新"
            ))

        return bottlenecks
```

**設計決策說明**:
- **多維度指標**: 速度、燃盡圖、在制品等多個角度
- **實時檢測**: 自動檢測瓶頸並預警
- **歷史對比**: 與歷史數據對比，提供趨勢分析
- **可視化支持**: 計算結果直接用於圖表渲染

## 數據庫設計

### 表結構設計

```sql
-- 任務表
CREATE TABLE tasks (
    id VARCHAR(20) PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL,
    priority VARCHAR(5) NOT NULL,
    estimated_hours INTEGER NOT NULL,
    actual_hours INTEGER,
    assignee VARCHAR(100),
    sprint VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Sprint表
CREATE TABLE sprints (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    goal TEXT,
    status VARCHAR(20) NOT NULL
);

-- 任務狀態變更日誌表
CREATE TABLE task_transitions (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(20) REFERENCES tasks(id),
    from_status VARCHAR(20),
    to_status VARCHAR(20),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sprint任務關聯表
CREATE TABLE sprint_tasks (
    sprint_id VARCHAR(50) REFERENCES sprints(id),
    task_id VARCHAR(20) REFERENCES tasks(id),
    PRIMARY KEY (sprint_id, task_id)
);

-- 團隊成員表
CREATE TABLE team_members (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    velocity_avg INTEGER DEFAULT 40,
    capacity_hours INTEGER DEFAULT 40
);

-- 項目指標表
CREATE TABLE project_metrics (
    id SERIAL PRIMARY KEY,
    sprint_id VARCHAR(50),
    metric_name VARCHAR(50),
    metric_value NUMERIC,
    calculated_at TIMESTAMP DEFAULT NOW()
);
```

### 索引設計

```sql
-- 任務查詢優化
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_assignee ON tasks(assignee);
CREATE INDEX idx_tasks_sprint ON tasks(sprint);
CREATE INDEX idx_tasks_priority ON tasks(priority);

-- Sprint查詢優化
CREATE INDEX idx_sprints_dates ON sprints(start_date, end_date);

-- 日誌查詢優化
CREATE INDEX idx_transitions_task_id ON task_transitions(task_id);
CREATE INDEX idx_transitions_created_at ON task_transitions(created_at);
```

## API設計

### RESTful API設計原則

1. **資源導向**: URL代表資源，使用名詞而非動詞
2. **HTTP方法**: GET(查詢)、POST(創建)、PUT(更新)、DELETE(刪除)
3. **狀態碼**: 正確使用HTTP狀態碼 (200, 201, 400, 404, 500)
4. **版本控制**: API版本控制 (/api/v1/tasks)
5. **分頁**: 列表端點支持分頁 (page, limit)
6. **過濾**: 支持查詢參數過濾 (?status=TODO&priority=P0)

### 關鍵API端點

```python
# 任務管理API
@router.get("/api/v1/tasks")
async def list_tasks(
    status: Optional[TaskStatus] = None,
    assignee: Optional[str] = None,
    sprint: Optional[str] = None,
    priority: Optional[Priority] = None,
    page: int = 1,
    limit: int = 20
):
    """獲取任務列表，支持過濾和分頁"""

@router.post("/api/v1/tasks")
async def create_task(task: TaskCreate):
    """創建新任務"""

@router.put("/api/v1/tasks/{task_id}")
async def update_task(task_id: str, task: TaskUpdate):
    """更新任務"""

@router.post("/api/v1/tasks/{task_id}/transition")
async def transition_task(
    task_id: str,
    new_status: TaskStatus,
    comment: Optional[str] = None
):
    """任務狀態流轉"""

# Sprint管理API
@router.get("/api/v1/sprints")
async def list_sprints():
    """獲取Sprint列表"""

@router.post("/api/v1/sprints/{sprint_id}/plan")
async def plan_sprint(sprint_id: str, plan: SprintPlan):
    """規劃Sprint任務"""

# 指標API
@router.get("/api/v1/metrics/sprint/{sprint_id}")
async def get_sprint_metrics(sprint_id: str):
    """獲取Sprint指標"""

@router.get("/api/v1/metrics/burndown/{sprint_id}")
async def get_burndown_chart(sprint_id: str):
    """獲取燃盡圖數據"""
```

### API響應格式標準化

```python
class APIResponse(BaseModel):
    """標準API響應格式"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    meta: Optional[Dict] = None
    timestamp: datetime

    @classmethod
    def success(cls, data=None, meta=None):
        return cls(success=True, data=data, meta=meta)

    @classmethod
    def error(cls, error_message):
        return cls(success=False, error=error_message)

# 使用示例
@router.get("/api/v1/tasks/{task_id}")
async def get_task(task_id: str):
    task = await task_service.get_task(task_id)
    return APIResponse.success(
        data=task,
        meta={"fetch_time": "2025-10-29T10:00:00Z"}
    )
```

## 前端架構設計

### Vue.js組件層次

```
src/components/
├── TaskBoard/
│   ├── TaskBoard.vue          # 主看板組件
│   ├── TaskColumn.vue         # 狀態列組件
│   ├── TaskCard.vue           # 任務卡片組件
│   ├── TaskCardDrag.vue       # 拖拽處理
│   └── TaskFilters.vue        # 過濾器組件
├── Sprint/
│   ├── SprintBoard.vue        # Sprint概覽
│   ├── SprintPlanning.vue     # Sprint規劃
│   └── SprintMetrics.vue      # Sprint指標
├── Metrics/
│   ├── MetricsDashboard.vue   # 指標儀表板
│   ├── BurndownChart.vue      # 燃盡圖
│   ├── VelocityChart.vue      # 速度圖
│   └── BottleneckAlert.vue    # 瓶頸警告
└── Common/
    ├── TaskModal.vue          # 任務詳情彈窗
    ├── TaskForm.vue           # 任務表單
    └── DateRangePicker.vue    # 日期範圍選擇器
```

### 狀態管理 (Pinia)

```javascript
// stores/taskStore.js
import { defineStore } from 'pinia'

export const useTaskStore = defineStore('task', {
  state: () => ({
    tasks: [],
    currentSprint: null,
    filters: {
      status: null,
      assignee: null,
      priority: null
    },
    loading: false
  }),

  getters: {
    tasksByStatus: (state) => (status) => {
      return state.tasks.filter(task => task.status === status)
    },
    sprintProgress: (state) => {
      if (!state.currentSprint) return 0
      const completed = state.tasks.filter(
        t => t.sprint === state.currentSprint.id && t.status === 'DONE'
      ).length
      const total = state.tasks.filter(
        t => t.sprint === state.currentSprint.id
      ).length
      return total > 0 ? completed / total : 0
    }
  },

  actions: {
    async fetchTasks() {
      this.loading = true
      try {
        const response = await api.get('/api/v1/tasks', {
          params: this.filters
        })
        this.tasks = response.data
      } finally {
        this.loading = false
      }
    },

    async transitionTask(taskId, newStatus, comment) {
      await api.post(`/api/v1/tasks/${taskId}/transition`, {
        new_status: newStatus,
        comment: comment
      })
      // 更新本地狀態
      const task = this.tasks.find(t => t.id === taskId)
      if (task) task.status = newStatus
    }
  }
})
```

### 實時更新 (WebSocket)

```javascript
// websocket/taskSocket.js
import { io } from 'socket.io-client'

class TaskSocket {
  constructor() {
    this.socket = io('/api/v1/ws/tasks')
  }

  onTaskUpdate(callback) {
    this.socket.on('task:updated', callback)
  }

  onSprintUpdate(callback) {
    this.socket.on('sprint:updated', callback)
  }

  emitTaskTransition(taskId, status) {
    this.socket.emit('task:transition', { taskId, status })
  }
}

// 使用示例
const taskSocket = new TaskSocket()
taskSocket.onTaskUpdate((data) => {
  // 更新任務狀態
  const task = taskStore.tasks.find(t => t.id === data.taskId)
  if (task) {
    task.status = data.newStatus
  }
})
```

## 性能優化設計

### 1. 數據庫優化

```python
# 使用連接池
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)

# 使用索引覆蓋查詢
@router.get("/api/v1/tasks/dashboard")
async def get_dashboard_data():
    """儀表板數據，使用索引覆蓋查詢"""
    query = select([
        Task.status,
        Task.priority,
        func.count(Task.id).label('count')
    ]).group_by(Task.status, Task.priority)

    result = await database.fetch_all(query)
    return result

# 使用分頁查詢
@router.get("/api/v1/tasks")
async def list_tasks(page: int = 1, limit: int = 20):
    """分頁查詢，大偏移量使用鍵集分頁"""
    offset = (page - 1) * limit
    query = select(Task).offset(offset).limit(limit)
    return await database.fetch_all(query)
```

### 2. 緩存策略

```python
# Redis緩存
from functools import wraps

def cached(ttl=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached_result = await redis.get(cache_key)

            if cached_result:
                return json.loads(cached_result)

            result = await func(*args, **kwargs)
            await redis.setex(
                cache_key,
                ttl,
                json.dumps(result, default=str)
            )
            return result
        return wrapper
    return decorator

# 緩存關鍵查詢
@router.get("/api/v1/metrics/sprint/{sprint_id}")
@cached(ttl=600)  # 緩存10分鐘
async def get_sprint_metrics(sprint_id: str):
    """Sprint指標查詢緩存"""
    # 計算指標...
```

### 3. 異步優化

```python
# 批量異步查詢
async def get_multiple_tasks(task_ids: List[str]):
    """批量獲取任務，使用異步併發"""
    tasks = await asyncio.gather(
        *[get_task(task_id) for task_id in task_ids],
        return_exceptions=True
    )
    return [t for t in tasks if not isinstance(t, Exception)]

# 流式處理大數據
@router.get("/api/v1/tasks/export")
async def export_tasks():
    """流式導出任務，支持大數據集"""
    async def generate():
        async for batch in task_service.stream_all_tasks(1000):
            yield json.dumps(batch) + "\n"

    return StreamingResponse(
        generate(),
        media_type="application/json",
        headers={
            "Content-Disposition": "attachment; filename=tasks.json"
        }
    )
```

## 測試策略

### 單元測試

```python
# tests/test_task_service.py
import pytest
from unittest.mock import AsyncMock

class TestTaskService:
    @pytest.fixture
    def task_service(self):
        return TaskService(database=AsyncMock())

    @pytest.mark.asyncio
    async def test_create_task(self, task_service):
        """測試創建任務"""
        task_data = TaskCreate(
            title="測試任務",
            priority=Priority.P0,
            estimated_hours=3
        )

        result = await task_service.create_task(task_data)

        assert result.id.startswith("TASK-")
        assert result.status == TaskStatus.TODO
        assert result.priority == Priority.P0

    @pytest.mark.asyncio
    async def test_transition_task(self, task_service):
        """測試任務狀態流轉"""
        # 準備測試數據
        task = Task(id="TASK-001", status=TaskStatus.TODO)

        # 執行狀態變更
        await task_service.transition_task(
            task.id,
            TaskStatus.IN_PROGRESS
        )

        # 驗證結果
        assert task.status == TaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_invalid_transition(self, task_service):
        """測試非法狀態變更"""
        task = Task(id="TASK-001", status=TaskStatus.DONE)

        with pytest.raises(InvalidTransitionError):
            await task_service.transition_task(
                task.id,
                TaskStatus.IN_PROGRESS
            )
```

### 集成測試

```python
# tests/test_api_integration.py
from fastapi.testclient import TestClient

class TestTaskAPI:
    def setup_method(self):
        self.client = TestClient(app)

    def test_create_and_fetch_task(self):
        """測試創建和獲取任務"""
        # 創建任務
        response = self.client.post("/api/v1/tasks", json={
            "title": "測試任務",
            "priority": "P0",
            "estimated_hours": 3
        })
        assert response.status_code == 201
        task_id = response.json()["data"]["id"]

        # 獲取任務
        response = self.client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["data"]["title"] == "測試任務"

    def test_task_transition(self):
        """測試任務狀態流轉"""
        task_id = "TASK-001"
        response = self.client.post(
            f"/api/v1/tasks/{task_id}/transition",
            json={"new_status": "IN_PROGRESS"}
        )
        assert response.status_code == 200

        # 驗證狀態已更新
        response = self.client.get(f"/api/v1/tasks/{task_id}")
        assert response.json()["data"]["status"] == "IN_PROGRESS"
```

### 性能測試

```python
# tests/test_performance.py
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class TestTaskPerformance:
    def test_create_100_tasks(self):
        """測試批量創建100個任務的性能"""
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(create_test_task)
                for _ in range(100)
            ]
            results = [f.result() for f in futures]

        elapsed = time.time() - start_time

        # 100個任務應在5秒內完成
        assert elapsed < 5.0
        assert len(results) == 100

    def test_query_with_filters(self):
        """測試帶過濾器的查詢性能"""
        # 先創建1000個任務
        create_1000_tasks()

        start_time = time.time()
        response = self.client.get(
            "/api/v1/tasks?status=TODO&priority=P0"
        )
        elapsed = time.time() - start_time

        # 查詢應在200ms內完成
        assert elapsed < 0.2
        assert response.status_code == 200
```

## 部署架構

### Docker部署

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.dashboard.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/tasks
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: tasks
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  postgres_data:
```

### Kubernetes部署

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: task-management
spec:
  replicas: 3
  selector:
    matchLabels:
      app: task-management
  template:
    metadata:
      labels:
        app: task-management
    spec:
      containers:
      - name: app
        image: task-management:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

## 安全設計

### 1. 認證和授權

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """驗證用戶身份"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無效的認證憑據"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的認證憑據"
        )

    user = await get_user(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用戶不存在"
        )
    return user

async def require_permission(permission: str):
    """檢查用戶權限"""
    async def dependency(user = Depends(get_current_user)):
        if permission not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="權限不足"
            )
        return user
    return dependency

# 使用示例
@router.post("/api/v1/tasks")
async def create_task(
    task: TaskCreate,
    user = Depends(require_permission("task:create"))
):
    """創建任務需要task:create權限"""
    return await task_service.create_task(task)
```

### 2. 數據驗證

```python
from pydantic import BaseModel, validator
from typing import Optional

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Priority
    estimated_hours: int

    @validator('title')
    def validate_title(cls, v):
        if len(v) < 3:
            raise ValueError('任務標題至少3個字符')
        if len(v) > 200:
            raise ValueError('任務標題不能超過200個字符')
        return v

    @validator('estimated_hours')
    def validate_hours(cls, v):
        if v <= 0:
            raise ValueError('預估時間必須大於0')
        if v > 100:
            raise ValueError('單個任務預估時間不能超過100小時')
        return v
```

### 3. API速率限制

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/api/v1/tasks")
@limiter.limit("10/minute")  # 每分鐘最多10個請求
async def create_task(request: Request, task: TaskCreate):
    """創建任務速率限制"""
    return await task_service.create_task(task)
```

### 4. 審計日誌

```python
import structlog

logger = structlog.get_logger()

class AuditLogger:
    @staticmethod
    async def log_task_create(task: Task, user: User):
        logger.info(
            "task_created",
            task_id=task.id,
            user_id=user.id,
            timestamp=datetime.utcnow().isoformat()
        )

    @staticmethod
    async def log_task_transition(task_id: str, from_status: str, to_status: str, user: User):
        logger.info(
            "task_transition",
            task_id=task_id,
            from_status=from_status,
            to_status=to_status,
            user_id=user.id,
            timestamp=datetime.utcnow().isoformat()
        )
```

## 監控和告警

### 1. 健康檢查

```python
@router.get("/health")
async def health_check():
    """應用健康檢查"""
    try:
        # 檢查數據庫連接
        await database.fetch_one("SELECT 1")

        # 檢查Redis連接
        await redis.ping()

        # 檢查任務隊列
        queue_size = await get_queue_size()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": "ok",
                "redis": "ok",
                "queue_size": queue_size
            }
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Service Unavailable"
        )
```

### 2. 指標收集

```python
from prometheus_client import Counter, Histogram, Gauge

# 定義指標
task_operations = Counter(
    'task_operations_total',
    'Total task operations',
    ['operation', 'status']
)

task_operation_duration = Histogram(
    'task_operation_duration_seconds',
    'Task operation duration'
)

active_sprints = Gauge(
    'active_sprints_total',
    'Number of active sprints'
)

# 使用示例
@router.post("/api/v1/tasks")
async def create_task(task: TaskCreate):
    start_time = time.time()

    try:
        result = await task_service.create_task(task)
        task_operations.labels(operation='create', status='success').inc()
        return result
    except Exception as e:
        task_operations.labels(operation='create', status='error').inc()
        raise
    finally:
        task_operation_duration.observe(time.time() - start_time)
```

### 3. 告警規則

```yaml
# alerting/rules.yml
groups:
- name: task_management
  rules:
  - alert: HighErrorRate
    expr: rate(task_operations_total{status="error"}[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "任務操作錯誤率過高"

  - alert: SlowResponse
    expr: histogram_quantile(0.95, task_operation_duration_seconds) > 0.5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "API響應時間過慢"

  - alert: TooManyBlockedTasks
    expr: tasks_blocked_total > 10
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "阻塞任務數量過多"
```

## 故障恢復

### 1. 數據備份

```python
# scripts/backup.py
async def backup_database():
    """每日數據庫備份"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_taskdb_{timestamp}.sql"

    # 導出SQL
    subprocess.run([
        "pg_dump",
        "-h", DB_HOST,
        "-U", DB_USER,
        "-d", DB_NAME,
        "-f", backup_file
    ])

    # 上傳到雲存儲
    await upload_to_s3(backup_file, f"backups/{backup_file}")

    # 清理本地文件
    os.remove(backup_file)
```

### 2. 災難恢復

```python
# scripts/restore.py
async def restore_database(backup_file: str):
    """從備份恢復數據庫"""
    # 下載備份文件
    await download_from_s3(f"backups/{backup_file}", backup_file)

    # 恢復數據庫
    subprocess.run([
        "psql",
        "-h", DB_HOST,
        "-U", DB_USER,
        "-d", DB_NAME,
        "-f", backup_file
    ])

    # 驗證恢復
    await verify_database_integrity()

    # 清理
    os.remove(backup_file)
```

## 擴展性設計

### 水平擴展

```python
# 使用Celery處理異步任務
from celery import Celery

celery_app = Celery('task_management')

@celery_app.task
def process_task_automation(task_id: str):
    """異步處理任務自動化"""
    # 檢查依賴、狀態變更等
    pass

@router.post("/api/v1/tasks/{task_id}/transition")
async def transition_task(task_id: str, new_status: TaskStatus):
    """立即返回，異步處理"""
    # 立即更新數據庫
    await update_task_status(task_id, new_status)

    # 提交異步任務
    process_task_automation.delay(task_id)

    return {"status": "accepted", "processing": "async"}
```

### 微服務拆分

```python
# 拆分為獨立服務
services = {
    "task-service": "http://task-service:8001",
    "sprint-service": "http://sprint-service:8002",
    "metrics-service": "http://metrics-service:8003",
    "notification-service": "http://notification-service:8004"
}

# 服務發現
from etcd3 import Etcd3Client

class ServiceRegistry:
    def __init__(self):
        self.client = Etcd3Client()

    async def register_service(self, name: str, url: str):
        await self.client.put(f"/services/{name}", url)

    async def discover_service(self, name: str) -> str:
        value, _ = await self.client.get(f"/services/{name}")
        return value.decode()
```

---

**設計總結**: 本設計採用微服務架構、事件驅動模式、RESTful API、Vue.js前端、PostgreSQL+Redis數據層，確保系統的高性能、高可用性和可擴展性。通過自動化工作流、智能Sprint規劃、實時指標監控，大幅提升項目管理效率。
