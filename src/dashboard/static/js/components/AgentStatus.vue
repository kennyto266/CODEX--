<template>
  <div class="space-y-6">
    <!-- 健康狀態概覽 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <!-- 全部 Agents -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <p class="text-gray-600 text-sm font-medium mb-2">全部 Agents</p>
        <p class="text-4xl font-bold text-gray-600">{{ agents.length }}</p>
      </div>

      <!-- 健康 -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <p class="text-gray-600 text-sm font-medium mb-2">💚 健康</p>
        <p class="text-4xl font-bold text-green-600">{{ healthyCount }}</p>
        <p class="text-xs text-gray-500 mt-2">{{ healthyPercentage.toFixed(1) }}%</p>
      </div>

      <!-- 警告 -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <p class="text-gray-600 text-sm font-medium mb-2">⚠️ 警告</p>
        <p class="text-4xl font-bold text-yellow-600">{{ warningCount }}</p>
        <p class="text-xs text-gray-500 mt-2">{{ warningPercentage.toFixed(1) }}%</p>
      </div>

      <!-- 異常 -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <p class="text-gray-600 text-sm font-medium mb-2">🔴 異常</p>
        <p class="text-4xl font-bold text-red-600">{{ errorCount }}</p>
        <p class="text-xs text-gray-500 mt-2">{{ errorPercentage.toFixed(1) }}%</p>
      </div>
    </div>

    <!-- Agent 健康狀態詳情 -->
    <div class="bg-white rounded-lg shadow-md p-6">
      <h3 class="text-2xl font-bold mb-6 text-gray-800">🏥 Agent 健康狀態詳情</h3>

      <div class="space-y-4">
        <div v-for="agent in agents" :key="agent.id" class="border border-gray-200 rounded-lg p-4">
          <!-- Agent 信息和狀態 -->
          <div class="flex justify-between items-start mb-3">
            <div>
              <h4 class="text-lg font-bold text-gray-800">{{ agent.name || agent.id }}</h4>
              <p class="text-xs text-gray-500 font-mono">{{ agent.id.substring(0, 16) }}...</p>
            </div>
            <div class="text-right">
              <span :class="healthBadgeClass(agent.health)" class="px-3 py-1 rounded-full text-xs font-bold">
                {{ healthLabel(agent.health) }}
              </span>
              <p class="text-xs text-gray-500 mt-1">{{ formatTime(agent.last_heartbeat) }}</p>
            </div>
          </div>

          <!-- 健康指標 -->
          <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
            <!-- CPU -->
            <div>
              <p class="text-xs text-gray-600 mb-1">CPU</p>
              <div class="flex items-center gap-2">
                <div class="flex-1 bg-gray-300 rounded-full h-2">
                  <div
                    :style="{ width: (agent.metrics?.cpu_usage || 0) + '%' }"
                    :class="cpuColorClass(agent.metrics?.cpu_usage || 0)"
                    class="h-2 rounded-full"
                  ></div>
                </div>
                <span class="text-xs font-semibold w-12 text-right">
                  {{ (agent.metrics?.cpu_usage || 0).toFixed(0) }}%
                </span>
              </div>
            </div>

            <!-- 記憶體 -->
            <div>
              <p class="text-xs text-gray-600 mb-1">記憶體</p>
              <div class="flex items-center gap-2">
                <div class="flex-1 bg-gray-300 rounded-full h-2">
                  <div
                    :style="{ width: Math.min((agent.metrics?.memory_usage || 0) / 10, 100) + '%' }"
                    :class="memoryColorClass(agent.metrics?.memory_usage || 0)"
                    class="h-2 rounded-full"
                  ></div>
                </div>
                <span class="text-xs font-semibold w-12 text-right">
                  {{ (agent.metrics?.memory_usage || 0).toFixed(0) }}M
                </span>
              </div>
            </div>

            <!-- 吞吐量 -->
            <div>
              <p class="text-xs text-gray-600 mb-1">吞吐量</p>
              <p class="text-sm font-bold text-blue-600">{{ (agent.metrics?.throughput || 0).toFixed(2) }} req/s</p>
            </div>

            <!-- 延遲 -->
            <div>
              <p class="text-xs text-gray-600 mb-1">延遲</p>
              <p class="text-sm font-bold" :class="latencyColorClass(agent.metrics?.latency || 0)">
                {{ (agent.metrics?.latency || 0).toFixed(1) }} ms
              </p>
            </div>

            <!-- 錯誤率 -->
            <div>
              <p class="text-xs text-gray-600 mb-1">錯誤率</p>
              <p class="text-sm font-bold" :class="errorRateColorClass(agent.metrics)">
                {{ calculateErrorRate(agent.metrics).toFixed(2) }}%
              </p>
            </div>
          </div>

          <!-- 狀態指示器 -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
            <div class="bg-gray-50 p-2 rounded">
              <p class="text-gray-600">狀態</p>
              <p class="font-semibold text-gray-800">{{ statusLabel(agent.status) }}</p>
            </div>
            <div class="bg-gray-50 p-2 rounded">
              <p class="text-gray-600">運行時間</p>
              <p class="font-semibold text-gray-800">{{ formatUptime(agent.uptime) }}</p>
            </div>
            <div class="bg-gray-50 p-2 rounded">
              <p class="text-gray-600">已完成任務</p>
              <p class="font-semibold text-gray-800">{{ agent.metrics?.processed_tasks || 0 }}</p>
            </div>
            <div class="bg-gray-50 p-2 rounded">
              <p class="text-gray-600">失敗任務</p>
              <p class="font-semibold text-red-600">{{ agent.metrics?.error_count || 0 }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

defineProps({
  agents: {
    type: Array,
    default: () => []
  }
});

const healthyCount = computed(() => {
  return props.agents.filter(a => a.health === 'healthy').length;
});

const warningCount = computed(() => {
  return props.agents.filter(a => a.health === 'warning').length;
});

const errorCount = computed(() => {
  return props.agents.filter(a => a.health === 'error').length;
});

const healthyPercentage = computed(() => {
  return props.agents.length > 0 ? (healthyCount.value / props.agents.length) * 100 : 0;
});

const warningPercentage = computed(() => {
  return props.agents.length > 0 ? (warningCount.value / props.agents.length) * 100 : 0;
});

const errorPercentage = computed(() => {
  return props.agents.length > 0 ? (errorCount.value / props.agents.length) * 100 : 0;
});

const healthLabel = (health) => {
  if (health === 'healthy') return '💚 健康';
  if (health === 'warning') return '⚠️ 警告';
  if (health === 'error') return '🔴 異常';
  return health;
};

const healthBadgeClass = (health) => {
  if (health === 'healthy') return 'bg-green-100 text-green-800';
  if (health === 'warning') return 'bg-yellow-100 text-yellow-800';
  if (health === 'error') return 'bg-red-100 text-red-800';
  return 'bg-gray-100 text-gray-800';
};

const statusLabel = (status) => {
  if (status === 'running') return '✅ 運行中';
  if (status === 'stopped') return '⏹️ 已停止';
  if (status === 'paused') return '⏸️ 已暫停';
  if (status === 'error') return '❌ 錯誤';
  return status;
};

const cpuColorClass = (cpu) => {
  if (cpu > 80) return 'bg-red-600';
  if (cpu > 50) return 'bg-yellow-600';
  return 'bg-green-600';
};

const memoryColorClass = (memory) => {
  if (memory > 800) return 'bg-red-600';
  if (memory > 500) return 'bg-yellow-600';
  return 'bg-green-600';
};

const latencyColorClass = (latency) => {
  if (latency > 500) return 'text-red-600';
  if (latency > 200) return 'text-yellow-600';
  return 'text-green-600';
};

const errorRateColorClass = (metrics) => {
  const errorRate = calculateErrorRate(metrics);
  if (errorRate > 5) return 'text-red-600';
  if (errorRate > 1) return 'text-yellow-600';
  return 'text-green-600';
};

const calculateErrorRate = (metrics) => {
  if (!metrics || !metrics.request_count || metrics.request_count === 0) return 0;
  return (metrics.error_count / metrics.request_count) * 100;
};

const formatUptime = (uptime) => {
  if (!uptime) return '0 秒';
  const days = Math.floor(uptime / 86400);
  const hours = Math.floor((uptime % 86400) / 3600);
  const minutes = Math.floor((uptime % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
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
