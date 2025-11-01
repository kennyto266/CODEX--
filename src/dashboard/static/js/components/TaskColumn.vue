<template>
  <div class="task-column flex-shrink-0 w-80 bg-gray-50 rounded-lg p-4">
    <!-- 列標題 -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <h2 class="text-lg font-semibold text-gray-800">{{ columnTitle }}</h2>
        <span
          class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-200 text-xs font-bold text-gray-700"
        >
          {{ tasks.length }}
        </span>
      </div>

      <!-- 新增任務按鈕 -->
      <button
        v-if="allowCreate"
        @click="createTask"
        class="p-1 rounded-full hover:bg-gray-200 text-gray-600"
        title="新增任務"
      >
        ➕
      </button>
    </div>

    <!-- 拖拽區域 -->
    <draggable
      v-model="localTasks"
      :group="{ name: 'tasks', pull: true, put: true }"
      item-key="id"
      @end="handleDragEnd"
      class="task-list min-h-[500px] space-y-2"
      :animation="200"
      ghost-class="opacity-50"
      chosen-class="bg-blue-100"
      drag-class="shadow-xl"
    >
      <template #item="{ element }">
        <TaskCard
          :task="element"
          @edit="editTask"
          @assign="assignTask"
          @delete="deleteTask"
        />
      </template>

      <!-- 空狀態 -->
      <template #empty>
        <div class="flex flex-col items-center justify-center h-64 text-gray-400">
          <div class="text-4xl mb-2">📭</div>
          <p class="text-sm">沒有任務</p>
        </div>
      </template>
    </draggable>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { VueDraggableNext as draggable } from 'vuedraggable'
import TaskCard from './TaskCard.vue'
import { useTaskStore } from '../stores/taskStore'

const props = defineProps({
  status: {
    type: String,
    required: true
  },
  title: {
    type: String,
    required: true
  },
  tasks: {
    type: Array,
    default: () => []
  },
  allowCreate: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['create-task'])

const taskStore = useTaskStore()
const localTasks = ref([...props.tasks])

// 列標題
const columnTitle = computed(() => {
  return props.title || props.status
})

// 監聽props.tasks的變化
watch(
  () => props.tasks,
  (newTasks) => {
    localTasks.value = [...newTasks]
  },
  { deep: true }
)

// 處理拖拽結束
async function handleDragEnd(evt) {
  try {
    // 如果是跨列拖拽或狀態有變化，則更新任務狀態
    if (evt.added || evt.moved) {
      const task = evt.item.__vueParentComponent.props.element

      // 檢查是否需要更新狀態
      if (task.status !== props.status) {
        await taskStore.handleDragEnd(evt, props.status)
      }
    }
  } catch (error) {
    console.error('處理拖拽結束失敗:', error)
    // 重新獲取數據以恢復UI狀態
    await taskStore.fetchTasks()
  }
}

// 新增任務
function createTask() {
  emit('create-task', props.status)
}

// 編輯任務
function editTask(task) {
  console.log('編輯任務:', task.id)
  // TODO: 打開編輯對話框
}

// 分配任務
function assignTask(task) {
  console.log('分配任務:', task.id)
  // TODO: 打開分配對話框
}

// 刪除任務
async function deleteTask(task) {
  if (confirm(`確定要刪除任務 "${task.title}" 嗎？`)) {
    try {
      await taskStore.deleteTask(task.id)
    } catch (error) {
      console.error('刪除任務失敗:', error)
    }
  }
}
</script>

<style scoped>
.task-list {
  padding: 4px;
}

.task-list:empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 500px;
}

/* 拖拽動畫 */
.task-list .sortable-ghost {
  opacity: 0.5;
  background: #cbd5e0;
}

.task-list .sortable-chosen {
  transform: scale(1.02);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
}

/* 列動畫 */
.task-column {
  transition: transform 0.2s ease;
}

.task-column:hover {
  transform: translateY(-2px);
}
</style>
