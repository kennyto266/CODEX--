/**
 * 任務管理Store
 * 使用Pinia管理任務狀態和操作
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useTaskStore = defineStore('task', () => {
  // 狀態
  const tasks = ref([])
  const sprints = ref([])
  const loading = ref(false)
  const error = ref(null)
  const filters = ref({
    status: null,
    priority: null,
    assignee: null,
    sprint: null,
    search: ''
  })

  // 計算屬性
  const filteredTasks = computed(() => {
    let result = tasks.value

    if (filters.value.status) {
      result = result.filter(t => t.status === filters.value.status)
    }

    if (filters.value.priority) {
      result = result.filter(t => t.priority === filters.value.priority)
    }

    if (filters.value.assignee) {
      result = result.filter(t => t.assignee === filters.value.assignee)
    }

    if (filters.value.sprint) {
      result = result.filter(t => t.sprint === filters.value.sprint)
    }

    if (filters.value.search) {
      const search = filters.value.search.toLowerCase()
      result = result.filter(t =>
        t.title.toLowerCase().includes(search) ||
        t.description?.toLowerCase().includes(search) ||
        t.id.toLowerCase().includes(search)
      )
    }

    return result
  })

  const tasksByStatus = computed(() => {
    const grouped = {
      '待開始': [],
      '進行中': [],
      '待驗收': [],
      '已完成': [],
      '已阻塞': []
    }

    filteredTasks.value.forEach(task => {
      const status = task.status || '待開始'
      if (grouped[status]) {
        grouped[status].push(task)
      }
    })

    return grouped
  })

  const taskStatistics = computed(() => {
    const total = tasks.value.length
    const completed = tasks.value.filter(t => t.status === '已完成').length
    const inProgress = tasks.value.filter(t => t.status === '進行中').length
    const blocked = tasks.value.filter(t => t.status === '已阻塞').length

    return {
      total,
      completed,
      inProgress,
      blocked,
      completionRate: total > 0 ? ((completed / total) * 100).toFixed(1) : 0
    }
  })

  // 動作
  async function fetchTasks() {
    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams()
      if (filters.value.status) params.append('status', filters.value.status)
      if (filters.value.priority) params.append('priority', filters.value.priority)
      if (filters.value.assignee) params.append('assignee', filters.value.assignee)
      if (filters.value.sprint) params.append('sprint', filters.value.sprint)
      if (filters.value.search) params.append('search', filters.value.search)

      const response = await fetch(`/api/v1/tasks?${params.toString()}`)
      const data = await response.json()

      if (data.success) {
        tasks.value = data.data
      } else {
        throw new Error(data.error || '獲取任務失敗')
      }
    } catch (err) {
      error.value = err.message
      console.error('獲取任務失敗:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchSprints() {
    try {
      const response = await fetch('/api/v1/sprints')
      const data = await response.json()

      if (data.success) {
        sprints.value = data.data
      }
    } catch (err) {
      console.error('獲取Sprint失敗:', err)
    }
  }

  async function createTask(taskData) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch('/api/v1/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData)
      })

      const data = await response.json()

      if (data.success) {
        tasks.value.unshift(data.data)
        return data.data
      } else {
        throw new Error(data.error || '創建任務失敗')
      }
    } catch (err) {
      error.value = err.message
      console.error('創建任務失敗:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateTask(taskId, updates) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/v1/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      })

      const data = await response.json()

      if (data.success) {
        const index = tasks.value.findIndex(t => t.id === taskId)
        if (index !== -1) {
          tasks.value[index] = data.data
        }
        return data.data
      } else {
        throw new Error(data.error || '更新任務失敗')
      }
    } catch (err) {
      error.value = err.message
      console.error('更新任務失敗:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function transitionTask(taskId, newStatus, comment = null) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/v1/tasks/${taskId}/transition`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_status: newStatus, comment })
      })

      const data = await response.json()

      if (data.success) {
        const index = tasks.value.findIndex(t => t.id === taskId)
        if (index !== -1) {
          tasks.value[index] = data.data
        }
        return data.data
      } else {
        throw new Error(data.error || '狀態轉換失敗')
      }
    } catch (err) {
      error.value = err.message
      console.error('狀態轉換失敗:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function assignTask(taskId, assignee) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/v1/tasks/${taskId}/assign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assignee })
      })

      const data = await response.json()

      if (data.success) {
        const index = tasks.value.findIndex(t => t.id === taskId)
        if (index !== -1) {
          tasks.value[index] = data.data
        }
        return data.data
      } else {
        throw new Error(data.error || '分配任務失敗')
      }
    } catch (err) {
      error.value = err.message
      console.error('分配任務失敗:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteTask(taskId) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/v1/tasks/${taskId}`, {
        method: 'DELETE'
      })

      const data = await response.json()

      if (data.success) {
        tasks.value = tasks.value.filter(t => t.id !== taskId)
        return true
      } else {
        throw new Error(data.error || '刪除任務失敗')
      }
    } catch (err) {
      error.value = err.message
      console.error('刪除任務失敗:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function handleDragEnd(evt, newStatus) {
    // 獲取被拖拽的任務
    const task = evt.item.__vueParentComponent.props.element
    const taskId = task.id

    // 如果狀態有變化，則更新
    if (task.status !== newStatus) {
      try {
        await transitionTask(taskId, newStatus)
        console.log(`任務 ${taskId} 狀態已更新為 ${newStatus}`)
      } catch (err) {
        // 如果更新失敗，可能需要回滾UI
        console.error('狀態更新失敗:', err)
        // 重新獲取數據以恢復UI狀態
        await fetchTasks()
      }
    }
  }

  function setFilter(key, value) {
    filters.value[key] = value
  }

  function clearFilters() {
    filters.value = {
      status: null,
      priority: null,
      assignee: null,
      sprint: null,
      search: ''
    }
  }

  return {
    // 狀態
    tasks,
    sprints,
    loading,
    error,
    filters,

    // 計算屬性
    filteredTasks,
    tasksByStatus,
    taskStatistics,

    // 動作
    fetchTasks,
    fetchSprints,
    createTask,
    updateTask,
    transitionTask,
    assignTask,
    deleteTask,
    handleDragEnd,
    setFilter,
    clearFilters
  }
})
