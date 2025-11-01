/**
 * 任務看板路由配置
 */

import TaskBoard from '../components/TaskBoard.vue'

export const taskRoutes = [
  {
    path: '/tasks',
    name: 'TaskBoard',
    component: TaskBoard,
    meta: {
      title: '任務看板',
      icon: '📋',
      requiresAuth: true
    }
  },
  {
    path: '/tasks/board',
    name: 'TaskBoardFull',
    component: TaskBoard,
    meta: {
      title: '完整看板',
      icon: '📋',
      requiresAuth: true
    }
  }
]
