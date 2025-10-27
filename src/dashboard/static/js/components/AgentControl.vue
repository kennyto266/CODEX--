<template>
  <div v-if="agent" class="space-y-6">
    <!-- Agent 信息 -->
    <div class="bg-gradient-to-r from-blue-50 to-blue-100 p-6 rounded-lg border border-blue-200">
      <h3 class="text-2xl font-bold text-blue-900 mb-4">⚙️ {{ agent.name || agent.id }}</h3>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <p class="text-sm text-blue-700 font-medium">Agent ID</p>
          <p class="text-lg font-mono text-gray-800">{{ agent.id.substring(0, 16) }}...</p>
        </div>
        <div>
          <p class="text-sm text-blue-700 font-medium">目前狀態</p>
          <p class="text-lg font-bold" :class="statusColorClass(agent.status)">
            {{ statusLabel(agent.status) }}
          </p>
        </div>
        <div>
          <p class="text-sm text-blue-700 font-medium">健康狀態</p>
          <p class="text-lg font-bold" :class="healthColorClass(agent.health)">
            {{ healthLabel(agent.health) }}
          </p>
        </div>
      </div>
    </div>

    <!-- 控制命令 -->
    <div class="bg-white rounded-lg shadow-md p-6">
      <h4 class="text-xl font-bold mb-4 text-gray-800">🎮 控制命令</h4>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <!-- 啟動 -->
        <button
          @click="executeAction('start')"
          :disabled="agent.status === 'running' || isLoading"
          class="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-md transition"
        >
          <span v-if="!isLoading">▶️ 啟動</span>
          <span v-else>⏳ 啟動中...</span>
        </button>

        <!-- 停止 -->
        <button
          @click="executeAction('stop')"
          :disabled="agent.status === 'stopped' || isLoading"
          class="bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-md transition"
        >
          <span v-if="!isLoading">⏹️ 停止</span>
          <span v-else>⏳ 停止中...</span>
        </button>

        <!-- 暫停 -->
        <button
          @click="executeAction('pause')"
          :disabled="agent.status !== 'running' || isLoading"
          class="bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-md transition"
        >
          <span v-if="!isLoading">⏸️ 暫停</span>
          <span v-else>⏳ 暫停中...</span>
        </button>

        <!-- 重啟 -->
        <button
          @click="executeAction('restart')"
          :disabled="isLoading"
          class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-md transition"
        >
          <span v-if="!isLoading">🔄 重啟</span>
          <span v-else>⏳ 重啟中...</span>
        </button>
      </div>

      <!-- 操作反饋 -->
      <div v-if="actionMessage" :class="actionMessageClass" class="mt-4 p-4 rounded-md">
        {{ actionMessage }}
      </div>
    </div>

    <!-- Agent 詳細信息 -->
    <div class="bg-white rounded-lg shadow-md p-6">
      <h4 class="text-xl font-bold mb-4 text-gray-800">📊 詳細信息</h4>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- 基本信息 -->
        <div class="space-y-3">
          <h5 class="font-semibold text-gray-800 mb-3">基本信息</h5>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-gray-600">類型</span>
            <span class="font-semibold text-gray-800">{{ agent.type || '未指定' }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-gray-600">版本</span>
            <span class="font-semibold text-gray-800">{{ agent.version || '未知' }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-gray-600">啟動時間</span>
            <span class="font-semibold text-gray-800">{{ formatTime(agent.started_at) }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-gray-600">最後更新</span>
            <span class="font-semibold text-gray-800">{{ formatTime(agent.updated_at) }}</span>
          </div>
        </div>

        <!-- 性能信息 -->
        <div class="space-y-3">
          <h5 class="font-semibold text-gray-800 mb-3">性能信息</h5>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-gray-600">吞吐量</span>
            <span class="font-semibold text-blue-600">{{ (agent.metrics?.throughput || 0).toFixed(2) }} req/s</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-gray-600">平均延遲</span>
            <span class="font-semibold text-purple-600">{{ (agent.metrics?.latency || 0).toFixed(1) }} ms</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-gray-600">已處理任務</span>
            <span class="font-semibold text-green-600">{{ agent.metrics?.processed_tasks || 0 }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-gray-600">失敗任務</span>
            <span class="font-semibold text-red-600">{{ agent.metrics?.error_count || 0 }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 資源使用情況 -->
    <div class="bg-white rounded-lg shadow-md p-6">
      <h4 class="text-xl font-bold mb-4 text-gray-800">💾 資源使用</h4>

      <div class="space-y-4">
        <!-- CPU 使用 -->
        <div>
          <div class="flex justify-between mb-2">
            <span class="text-gray-700 font-semibold">CPU 使用率</span>
            <span class="text-lg font-bold" :class="cpuColorClass(agent.metrics?.cpu_usage || 0)">
              {{ (agent.metrics?.cpu_usage || 0).toFixed(1) }}%
            </span>
          </div>
          <div class="w-full bg-gray-300 rounded-full h-3">
            <div
              :style="{ width: (agent.metrics?.cpu_usage || 0) + '%' }"
              :class="cpuColorClass(agent.metrics?.cpu_usage || 0).replace('text', 'bg')"
              class="h-3 rounded-full transition-all"
            ></div>
          </div>
        </div>

        <!-- 記憶體使用 -->
        <div>
          <div class="flex justify-between mb-2">
            <span class="text-gray-700 font-semibold">記憶體使用</span>
            <span class="text-lg font-bold" :class="memoryColorClass(agent.metrics?.memory_usage || 0)">
              {{ (agent.metrics?.memory_usage || 0).toFixed(0) }} MB
            </span>
          </div>
          <div class="w-full bg-gray-300 rounded-full h-3">
            <div
              :style="{ width: Math.min((agent.metrics?.memory_usage || 0) / 10, 100) + '%' }"
              :class="memoryColorClass(agent.metrics?.memory_usage || 0).replace('text', 'bg')"
              class="h-3 rounded-full transition-all"
            ></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 空狀態 -->
  <div v-else class="bg-white rounded-lg shadow-md p-12 text-center text-gray-500">
    <p class="text-lg mb-2">📭 請先選擇一個 Agent</p>
    <p class="text-sm">在左側列表中點擊要控制的 Agent</p>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  agent: Object
});

const emit = defineEmits(['action']);

const isLoading = ref(false);
const actionMessage = ref('');
const actionMessageClass = ref('');

const executeAction = async (action) => {
  isLoading.value = true;
  actionMessage.value = '';

  try {
    // 發送動作到父組件
    emit('action', action);

    // 顯示成功消息
    actionMessage.value = `✅ 命令已發送: ${actionLabel(action)}`;
    actionMessageClass.value = 'bg-green-100 border border-green-300 text-green-800';
  } catch (error) {
    actionMessage.value = `❌ 執行失敗: ${error.message}`;
    actionMessageClass.value = 'bg-red-100 border border-red-300 text-red-800';
  } finally {
    isLoading.value = false;

    // 3 秒後清除消息
    setTimeout(() => {
      actionMessage.value = '';
    }, 3000);
  }
};

const statusLabel = (status) => {
  if (status === 'running') return '✅ 運行中';
  if (status === 'stopped') return '⏹️ 已停止';
  if (status === 'paused') return '⏸️ 已暫停';
  if (status === 'error') return '❌ 錯誤';
  return status;
};

const statusColorClass = (status) => {
  if (status === 'running') return 'text-green-600';
  if (status === 'stopped') return 'text-gray-600';
  if (status === 'paused') return 'text-yellow-600';
  if (status === 'error') return 'text-red-600';
  return 'text-gray-600';
};

const healthLabel = (health) => {
  if (health === 'healthy') return '💚 健康';
  if (health === 'warning') return '⚠️ 警告';
  if (health === 'error') return '🔴 異常';
  return health;
};

const healthColorClass = (health) => {
  if (health === 'healthy') return 'text-green-600';
  if (health === 'warning') return 'text-yellow-600';
  if (health === 'error') return 'text-red-600';
  return 'text-gray-600';
};

const cpuColorClass = (cpu) => {
  if (cpu > 80) return 'text-red-600';
  if (cpu > 50) return 'text-yellow-600';
  return 'text-green-600';
};

const memoryColorClass = (memory) => {
  if (memory > 800) return 'text-red-600';
  if (memory > 500) return 'text-yellow-600';
  return 'text-green-600';
};

const actionLabel = (action) => {
  const labels = {
    start: '啟動',
    stop: '停止',
    pause: '暫停',
    restart: '重啟'
  };
  return labels[action] || action;
};

const formatTime = (timestamp) => {
  if (!timestamp) return '未知';
  const date = new Date(timestamp);
  const now = new Date();
  const diff = (now - date) / 1000; // 秒

  if (diff < 60) return '剛剛';
  if (diff < 3600) return `${Math.floor(diff / 60)}分鐘前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}小時前`;
  return date.toLocaleString();
};
</script>
