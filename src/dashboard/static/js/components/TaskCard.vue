<template>
  <div
    class="task-card bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-3 cursor-move hover:shadow-md transition-shadow"
    :class="{
      'border-l-4 border-l-red-500': task.priority === 'P0',
      'border-l-4 border-l-yellow-500': task.priority === 'P1',
      'border-l-4 border-l-blue-500': task.priority === 'P2'
    }"
    :draggable="true"
  >
    <!-- 任務ID和優先級 -->
    <div class="flex justify-between items-start mb-2">
      <span class="text-xs font-mono text-gray-500">{{ task.id }}</span>
      <span
        class="px-2 py-1 rounded text-xs font-bold"
        :class="priorityClass(task.priority)"
      >
        {{ task.priority }}
      </span>
    </div>

    <!-- 任務標題 -->
    <h3 class="text-sm font-semibold text-gray-800 mb-2 line-clamp-2">
      {{ task.title }}
    </h3>

    <!-- 任務描述 -->
    <p
      v-if="task.description"
      class="text-xs text-gray-600 mb-3 line-clamp-3"
    >
      {{ task.description }}
    </p>

    <!-- 任務標籤 -->
    <div class="flex flex-wrap gap-2 mb-3">
      <span
        v-if="task.assignee"
        class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700"
      >
        👤 {{ task.assignee }}
      </span>

      <span
        v-if="task.sprint"
        class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-700"
      >
        🏃 {{ task.sprint }}
      </span>

      <span
        v-if="task.story_points"
        class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-purple-100 text-purple-700"
      >
        ⭐ {{ task.story_points }}pt
      </span>
    </div>

    <!-- 工時信息 -->
    <div class="flex items-center justify-between text-xs text-gray-500 mb-3">
      <div class="flex items-center gap-4">
        <span v-if="task.estimated_hours">
          ⏱️ 預估: {{ task.estimated_hours }}h
        </span>
        <span v-if="task.actual_hours">
          ⏱️ 實際: {{ task.actual_hours }}h
        </span>
      </div>

      <div class="flex items-center">
        <span class="text-xs">{{ task.progress_percentage }}%</span>
        <div class="w-12 h-2 bg-gray-200 rounded-full ml-2 overflow-hidden">
          <div
            class="h-full bg-green-500 transition-all"
            :style="{ width: task.progress_percentage + '%' }"
          />
        </div>
      </div>
    </div>

    <!-- 底部操作區 -->
    <div class="flex items-center justify-between pt-2 border-t border-gray-100">
      <div class="flex items-center gap-2">
        <!-- 被阻塞圖標 -->
        <span v-if="task.is_blocked" title="被阻塞" class="text-red-500">
          🚫
        </span>

        <!-- 已完成圖標 -->
        <span v-if="task.is_completed" title="已完成" class="text-green-500">
          ✅
        </span>

        <!-- 有依賴圖標 -->
        <span
          v-if="task.dependencies && task.dependencies.length > 0"
          title="有前置依賴"
          class="text-orange-500"
        >
          🔗
        </span>
      </div>

      <!-- 創建時間 -->
      <span class="text-xs text-gray-400">
        {{ formatDate(task.created_at) }}
      </span>
    </div>

    <!-- 內嵌操作菜單（點擊時顯示） -->
    <div
      v-if="showMenu"
      class="absolute top-2 right-2 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-10"
    >
      <button
        @click="editTask"
        class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
      >
        ✏️ 編輯
      </button>
      <button
        @click="assignTask"
        class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
      >
        👤 分配
      </button>
      <button
        @click="deleteTaskConfirm"
        class="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
      >
        🗑️ 刪除
      </button>
    </div>

    <!-- 菜單按鈕 -->
    <button
      @click="showMenu = !showMenu"
      class="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
    >
      ⋯
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  task: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['edit', 'assign', 'delete'])

const showMenu = ref(false)

// 優先級樣式
function priorityClass(priority) {
  const classes = {
    'P0': 'bg-red-100 text-red-800',
    'P1': 'bg-yellow-100 text-yellow-800',
    'P2': 'bg-blue-100 text-blue-800'
  }
  return classes[priority] || 'bg-gray-100 text-gray-800'
}

// 格式化日期
function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diffTime = Math.abs(now - date)
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays === 0) {
    return '今天'
  } else if (diffDays === 1) {
    return '昨天'
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return date.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' })
  }
}

// 操作方法
function editTask() {
  showMenu.value = false
  emit('edit', props.task)
}

function assignTask() {
  showMenu.value = false
  emit('assign', props.task)
}

function deleteTaskConfirm() {
  showMenu.value = false
  if (confirm(`確定要刪除任務 "${props.task.title}" 嗎？`)) {
    emit('delete', props.task)
  }
}

// 點擊外部關閉菜單
document.addEventListener('click', (e) => {
  if (!e.target.closest('.task-card')) {
    showMenu.value = false
  }
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.task-card {
  position: relative;
}
</style>
