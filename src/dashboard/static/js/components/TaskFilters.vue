<template>
  <div class="task-filters bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
    <div class="flex flex-wrap gap-4">
      <!-- 搜索框 -->
      <div class="flex-1 min-w-[200px]">
        <label class="block text-sm font-medium text-gray-700 mb-1">
          🔍 搜索任務
        </label>
        <input
          v-model="localFilters.search"
          @input="updateFilters"
          type="text"
          placeholder="搜索標題、描述或ID..."
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
        />
      </div>

      <!-- 狀態過濾 -->
      <div class="min-w-[150px]">
        <label class="block text-sm font-medium text-gray-700 mb-1">
          📊 狀態
        </label>
        <select
          v-model="localFilters.status"
          @change="updateFilters"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
        >
          <option value="">全部狀態</option>
          <option value="待開始">⏸️ 待開始</option>
          <option value="進行中">🔄 進行中</option>
          <option value="待驗收">👀 待驗收</option>
          <option value="已完成">✅ 已完成</option>
          <option value="已阻塞">🚫 已阻塞</option>
        </select>
      </div>

      <!-- 優先級過濾 -->
      <div class="min-w-[150px]">
        <label class="block text-sm font-medium text-gray-700 mb-1">
          🚨 優先級
        </label>
        <select
          v-model="localFilters.priority"
          @change="updateFilters"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
        >
          <option value="">全部優先級</option>
          <option value="P0">🔴 P0 (最高)</option>
          <option value="P1">🟡 P1 (高)</option>
          <option value="P2">🔵 P2 (普通)</option>
        </select>
      </div>

      <!-- 被分配者過濾 -->
      <div class="min-w-[150px]">
        <label class="block text-sm font-medium text-gray-700 mb-1">
          👤 被分配者
        </label>
        <select
          v-model="localFilters.assignee"
          @change="updateFilters"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
        >
          <option value="">全部人員</option>
          <option v-for="person in assignees" :key="person" :value="person">
            {{ person }}
          </option>
        </select>
      </div>

      <!-- Sprint過濾 -->
      <div class="min-w-[150px]">
        <label class="block text-sm font-medium text-gray-700 mb-1">
          🏃 Sprint
        </label>
        <select
          v-model="localFilters.sprint"
          @change="updateFilters"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
        >
          <option value="">全部Sprint</option>
          <option v-for="sprint in sprints" :key="sprint.id" :value="sprint.id">
            {{ sprint.name }}
          </option>
        </select>
      </div>
    </div>

    <!-- 操作按鈕 -->
    <div class="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
      <!-- 統計信息 -->
      <div class="flex items-center gap-4 text-sm text-gray-600">
        <span>
          顯示 {{ filteredCount }} / {{ totalCount }} 個任務
        </span>

        <!-- 快捷過濾按鈕 -->
        <div class="flex gap-2">
          <button
            @click="quickFilter('blocked')"
            class="px-3 py-1 rounded-full text-xs bg-red-100 text-red-700 hover:bg-red-200"
          >
            🚫 只看阻塞
          </button>
          <button
            @click="quickFilter('my')"
            class="px-3 py-1 rounded-full text-xs bg-blue-100 text-blue-700 hover:bg-blue-200"
          >
            👤 我的任務
          </button>
          <button
            @click="quickFilter('todo')"
            class="px-3 py-1 rounded-full text-xs bg-gray-100 text-gray-700 hover:bg-gray-200"
          >
            ⏸️ 待開始
          </button>
        </div>
      </div>

      <!-- 清除過濾 -->
      <button
        @click="clearAllFilters"
        class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
      >
        🔄 清除過濾
      </button>
    </div>

    <!-- 活躍過濾器標籤 -->
    <div v-if="hasActiveFilters" class="flex flex-wrap gap-2 mt-3">
      <span class="text-sm text-gray-600">活躍過濾器:</span>

      <span
        v-if="localFilters.search"
        class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs bg-blue-100 text-blue-700"
      >
        🔍 {{ localFilters.search }}
        <button @click="clearSearch" class="hover:text-blue-900">×</button>
      </span>

      <span
        v-if="localFilters.status"
        class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs bg-green-100 text-green-700"
      >
        📊 {{ localFilters.status }}
        <button @click="clearFilter('status')" class="hover:text-green-900">×</button>
      </span>

      <span
        v-if="localFilters.priority"
        class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs bg-orange-100 text-orange-700"
      >
        🚨 {{ localFilters.priority }}
        <button @click="clearFilter('priority')" class="hover:text-orange-900">×</button>
      </span>

      <span
        v-if="localFilters.assignee"
        class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs bg-purple-100 text-purple-700"
      >
        👤 {{ localFilters.assignee }}
        <button @click="clearFilter('assignee')" class="hover:text-purple-900">×</button>
      </span>

      <span
        v-if="localFilters.sprint"
        class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs bg-indigo-100 text-indigo-700"
      >
        🏃 {{ localFilters.sprint }}
        <button @click="clearFilter('sprint')" class="hover:text-indigo-900">×</button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useTaskStore } from '../stores/taskStore'

const taskStore = useTaskStore()

// 本地過濾器狀態
const localFilters = ref({
  search: '',
  status: '',
  priority: '',
  assignee: '',
  sprint: ''
})

// 計算屬性
const assignees = computed(() => {
  const uniqueAssignees = new Set()
  taskStore.tasks.forEach(task => {
    if (task.assignee) {
      uniqueAssignees.add(task.assignee)
    }
  })
  return Array.from(uniqueAssignees).sort()
})

const sprints = computed(() => {
  return taskStore.sprints || []
})

const totalCount = computed(() => {
  return taskStore.tasks.length
})

const filteredCount = computed(() => {
  return taskStore.filteredTasks.length
})

const hasActiveFilters = computed(() => {
  return Object.values(localFilters.value).some(value => value !== '')
})

// 過濾器更新
function updateFilters() {
  // 同步到 store
  for (const key in localFilters.value) {
    taskStore.setFilter(key, localFilters.value[key] || null)
  }

  // 重新獲取數據
  taskStore.fetchTasks()
}

// 清除單個過濾器
function clearFilter(key) {
  localFilters.value[key] = ''
  updateFilters()
}

// 清除搜索
function clearSearch() {
  localFilters.value.search = ''
  updateFilters()
}

// 清除所有過濾器
function clearAllFilters() {
  localFilters.value = {
    search: '',
    status: '',
    priority: '',
    assignee: '',
    sprint: ''
  }
  taskStore.clearFilters()
  taskStore.fetchTasks()
}

// 快捷過濾
function quickFilter(type) {
  switch (type) {
    case 'blocked':
      localFilters.value.status = '已阻塞'
      break
    case 'my':
      // TODO: 獲取當前用戶
      localFilters.value.assignee = '當前用戶'
      break
    case 'todo':
      localFilters.value.status = '待開始'
      break
  }
  updateFilters()
}

// 初始化時同步過濾器
onMounted(() => {
  // 從 store 同步過濾器狀態
  const storeFilters = taskStore.filters
  for (const key in localFilters.value) {
    localFilters.value[key] = storeFilters[key] || ''
  }
})
</script>

<style scoped>
.task-filters {
  position: sticky;
  top: 0;
  z-index: 10;
}

/* 過濾器動畫 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
