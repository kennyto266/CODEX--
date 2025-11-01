<template>
  <div class="task-board">
    <!-- 標題和操作欄 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">📋 任務看板</h1>
        <p class="text-sm text-gray-600 mt-1">
          總計 {{ taskStore.taskStatistics.total }} 個任務，
          完成率 {{ taskStore.taskStatistics.completionRate }}%
        </p>
      </div>

      <div class="flex items-center gap-3">
        <!-- 刷新按鈕 -->
        <button
          @click="refresh"
          :disabled="taskStore.loading"
          class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <span v-if="taskStore.loading">🔄</span>
          <span v-else>↻</span>
          {{ taskStore.loading ? '載入中...' : '刷新' }}
        </button>

        <!-- 新增任務按鈕 -->
        <button
          @click="showCreateDialog = true"
          class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 flex items-center gap-2"
        >
          ➕ 新增任務
        </button>
      </div>
    </div>

    <!-- 統計卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div
        v-for="stat in statisticsCards"
        :key="stat.label"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-4"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-600">{{ stat.label }}</p>
            <p class="text-2xl font-bold text-gray-800 mt-1">{{ stat.value }}</p>
          </div>
          <div class="text-3xl">{{ stat.icon }}</div>
        </div>

        <!-- 進度條 -->
        <div v-if="stat.progress !== undefined" class="mt-3">
          <div class="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>進度</span>
            <span>{{ stat.progress }}%</span>
          </div>
          <div class="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              class="h-full transition-all"
              :class="stat.progressColor"
              :style="{ width: stat.progress + '%' }"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 過濾器 -->
    <TaskFilters />

    <!-- 看板區域 -->
    <div class="task-board-columns flex gap-4 overflow-x-auto pb-6">
      <!-- 待開始列 -->
      <TaskColumn
        status="待開始"
        title="⏸️ 待開始"
        :tasks="taskStore.tasksByStatus['待開始']"
        :allow-create="true"
        @create-task="openCreateDialog"
      />

      <!-- 進行中列 -->
      <TaskColumn
        status="進行中"
        title="🔄 進行中"
        :tasks="taskStore.tasksByStatus['進行中']"
        :allow-create="true"
        @create-task="openCreateDialog"
      />

      <!-- 待驗收列 -->
      <TaskColumn
        status="待驗收"
        title="👀 待驗收"
        :tasks="taskStore.tasksByStatus['待驗收']"
      />

      <!-- 已完成列 -->
      <TaskColumn
        status="已完成"
        title="✅ 已完成"
        :tasks="taskStore.tasksByStatus['已完成']"
      />

      <!-- 已阻塞列 -->
      <TaskColumn
        status="已阻塞"
        title="🚫 已阻塞"
        :tasks="taskStore.tasksByStatus['已阻塞']"
      />
    </div>

    <!-- 創建任務對話框 -->
    <div
      v-if="showCreateDialog"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="showCreateDialog = false"
    >
      <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">➕ 創建新任務</h2>

        <form @submit.prevent="createTask">
          <div class="space-y-4">
            <!-- 任務標題 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                任務標題 *
              </label>
              <input
                v-model="newTask.title"
                type="text"
                required
                placeholder="輸入任務標題..."
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <!-- 任務描述 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                任務描述
              </label>
              <textarea
                v-model="newTask.description"
                rows="3"
                placeholder="輸入任務描述..."
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <!-- 優先級 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                優先級
              </label>
              <select
                v-model="newTask.priority"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="P2">P2 - 普通</option>
                <option value="P1">P1 - 高</option>
                <option value="P0">P0 - 最高</option>
              </select>
            </div>

            <!-- 預估工時 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                預估工時 (小時) *
              </label>
              <input
                v-model.number="newTask.estimated_hours"
                type="number"
                required
                min="1"
                max="100"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <!-- 被分配者 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                被分配者
              </label>
              <input
                v-model="newTask.assignee"
                type="text"
                placeholder="輸入被分配者姓名..."
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <!-- Sprint -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Sprint
              </label>
              <select
                v-model="newTask.sprint"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">無</option>
                <option v-for="sprint in taskStore.sprints" :key="sprint.id" :value="sprint.id">
                  {{ sprint.name }}
                </option>
              </select>
            </div>
          </div>

          <!-- 按鈕 -->
          <div class="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-gray-200">
            <button
              type="button"
              @click="showCreateDialog = false"
              class="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="taskStore.loading || !newTask.title || !newTask.estimated_hours"
              class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ taskStore.loading ? '創建中...' : '創建任務' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 錯誤提示 -->
    <div
      v-if="taskStore.error"
      class="fixed bottom-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg"
    >
      ❌ {{ taskStore.error }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTaskStore } from '../stores/taskStore'
import TaskColumn from './TaskColumn.vue'
import TaskFilters from './TaskFilters.vue'

const taskStore = useTaskStore()

// 顯示/隱藏創建對話框
const showCreateDialog = ref(false)

// 新任務數據
const newTask = ref({
  title: '',
  description: '',
  priority: 'P2',
  estimated_hours: 2,
  assignee: '',
  sprint: ''
})

// 統計卡片數據
const statisticsCards = computed(() => {
  const stats = taskStore.taskStatistics
  return [
    {
      label: '總任務數',
      value: stats.total,
      icon: '📋',
      progressColor: 'bg-blue-500'
    },
    {
      label: '已完成',
      value: stats.completed,
      icon: '✅',
      progress: stats.completionRate,
      progressColor: 'bg-green-500'
    },
    {
      label: '進行中',
      value: stats.inProgress,
      icon: '🔄',
      progressColor: 'bg-yellow-500'
    },
    {
      label: '已阻塞',
      value: stats.blocked,
      icon: '🚫',
      progressColor: 'bg-red-500'
    }
  ]
})

// 打開創建對話框
function openCreateDialog(status) {
  if (status) {
    newTask.value.sprint = status
  }
  showCreateDialog.value = true
}

// 創建任務
async function createTask() {
  try {
    await taskStore.createTask({
      ...newTask.value,
      status: '待開始'
    })

    // 重置表單
    newTask.value = {
      title: '',
      description: '',
      priority: 'P2',
      estimated_hours: 2,
      assignee: '',
      sprint: ''
    }

    showCreateDialog.value = false

    // 重新獲取數據以更新看板
    await taskStore.fetchTasks()
  } catch (error) {
    console.error('創建任務失敗:', error)
  }
}

// 刷新數據
async function refresh() {
  await taskStore.fetchTasks()
  await taskStore.fetchSprints()
}

// 初始化
onMounted(async () => {
  await refresh()
})
</script>

<style scoped>
.task-board {
  padding: 24px;
  background: #f7fafc;
  min-height: 100vh;
}

/* 看板列容器 */
.task-board-columns {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 24px;
}

/* 滾動條樣式 */
.task-board-columns::-webkit-scrollbar {
  height: 8px;
}

.task-board-columns::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.task-board-columns::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 4px;
}

.task-board-columns::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

/* 對話框動畫 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}
</style>
