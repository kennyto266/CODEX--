<template>
  <div class="bg-white rounded-lg shadow-md p-6">
    <h2 class="text-2xl font-bold mb-6 text-gray-800">📋 Agent 列表</h2>

    <!-- 搜索和篩選 -->
    <div class="mb-6 flex gap-4">
      <div class="flex-1">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索 Agent ID 或名稱..."
          class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <select
        v-model="filterStatus"
        class="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">全部狀態</option>
        <option value="running">🟢 運行中</option>
        <option value="stopped">⏹️ 已停止</option>
        <option value="paused">⏸️ 已暫停</option>
        <option value="error">❌ 錯誤</option>
      </select>
    </div>

    <!-- Agent 網格 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="agent in filteredAgents"
        :key="agent.id"
        @click="$emit('select', agent)"
        class="bg-gradient-to-br from-gray-50 to-gray-100 p-4 rounded-lg border-2 border-gray-300 hover:border-blue-500 cursor-pointer transition hover:shadow-lg"
      >
        <!-- Agent 狀態 -->
        <div class="flex justify-between items-start mb-3">
          <div>
            <h3 class="text-lg font-bold text-gray-800">{{ agent.name }}</h3>
            <p class="text-xs text-gray-500 font-mono">ID: {{ agent.id.substring(0, 12) }}...</p>
          </div>
          <span
            :class="statusBadgeClass(agent.status)"
            class="px-3 py-1 rounded-full text-xs font-bold"
          >
            {{ statusLabel(agent.status) }}
          </span>
        </div>

        <!-- Agent 信息 -->
        <div class="space-y-2 mb-4">
          <div class="flex justify-between text-sm">
            <span class="text-gray-600">運行時間</span>
            <span class="font-semibold text-gray-800">{{ formatUptime(agent.uptime) }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-gray-600">健康狀態</span>
            <span :class="agent.health === 'healthy' ? 'text-green-600' : 'text-red-600'" class="font-semibold">
              {{ agent.health === 'healthy' ? '✅ 健康' : '⚠️ 異常' }}
            </span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-gray-600">已處理任務</span>
            <span class="font-semibold text-gray-800">{{ agent.metrics?.processed_tasks || 0 }}</span>
          </div>
        </div>

        <!-- 性能條 -->
        <div class="space-y-2">
          <!-- CPU 使用率 -->
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-gray-600">CPU</span>
              <span class="font-semibold">{{ (agent.metrics?.cpu_usage || 0).toFixed(1) }}%</span>
            </div>
            <div class="w-full bg-gray-300 rounded-full h-2">
              <div
                :style="{ width: (agent.metrics?.cpu_usage || 0) + '%' }"
                class="bg-blue-600 h-2 rounded-full"
              ></div>
            </div>
          </div>

          <!-- 記憶體使用率 -->
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-gray-600">記憶體</span>
              <span class="font-semibold">{{ (agent.metrics?.memory_usage || 0).toFixed(0) }}MB</span>
            </div>
            <div class="w-full bg-gray-300 rounded-full h-2">
              <div
                :style="{ width: Math.min((agent.metrics?.memory_usage || 0) / 10, 100) + '%' }"
                class="bg-purple-600 h-2 rounded-full"
              ></div>
            </div>
          </div>
        </div>

        <!-- 最後心跳 -->
        <p class="text-xs text-gray-500 mt-3">
          💓 最後心跳: {{ formatTime(agent.last_heartbeat) }}
        </p>
      </div>
    </div>

    <!-- 空狀態 -->
    <div v-if="filteredAgents.length === 0" class="text-center py-12 text-gray-500">
      <p class="text-lg mb-2">📭 沒有找到匹配的 Agent</p>
      <p class="text-sm">請調整搜索條件或篩選條件</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

defineProps({
  agents: {
    type: Array,
    default: () => []
  }
});

defineEmits(['select']);

const searchQuery = ref('');
const filterStatus = ref('');

const filteredAgents = computed(() => {
  return props.agents.filter(agent => {
    const matchesSearch = !searchQuery.value ||
      agent.id.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      (agent.name && agent.name.toLowerCase().includes(searchQuery.value.toLowerCase()));

    const matchesStatus = !filterStatus.value || agent.status === filterStatus.value;

    return matchesSearch && matchesStatus;
  });
});

const statusLabel = (status) => {
  if (status === 'running') return '✅ 運行中';
  if (status === 'stopped') return '⏹️ 已停止';
  if (status === 'paused') return '⏸️ 已暫停';
  if (status === 'error') return '❌ 錯誤';
  return status;
};

const statusBadgeClass = (status) => {
  if (status === 'running') return 'bg-green-100 text-green-800';
  if (status === 'stopped') return 'bg-gray-100 text-gray-800';
  if (status === 'paused') return 'bg-yellow-100 text-yellow-800';
  if (status === 'error') return 'bg-red-100 text-red-800';
  return 'bg-gray-100 text-gray-800';
};

const formatUptime = (uptime) => {
  if (!uptime) return '0 秒';
  const days = Math.floor(uptime / 86400);
  const hours = Math.floor((uptime % 86400) / 3600);
  const minutes = Math.floor((uptime % 3600) / 60);

  if (days > 0) return `${days}天 ${hours}小時`;
  if (hours > 0) return `${hours}小時 ${minutes}分鐘`;
  return `${minutes}分鐘`;
};

const formatTime = (timestamp) => {
  if (!timestamp) return '未知';
  const date = new Date(timestamp);
  const now = new Date();
  const diff = (now - date) / 1000; // 秒

  if (diff < 60) return '剛剛';
  if (diff < 3600) return `${Math.floor(diff / 60)} 分鐘前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小時前`;
  return date.toLocaleString();
};
</script>
