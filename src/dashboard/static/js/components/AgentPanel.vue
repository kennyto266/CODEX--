<template>
  <div class="space-y-6 p-6 bg-gray-50 min-h-screen">
    <!-- 標題 -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-4xl font-bold text-gray-900">🤖 Agent 管理系統</h1>
        <p class="text-gray-600 mt-2">多智能體協作監控和控制</p>
      </div>
      <div class="text-right">
        <p class="text-sm text-gray-500">活躍 Agent 數</p>
        <p class="text-3xl font-bold text-green-600">{{ activeAgents }}</p>
      </div>
    </div>

    <!-- 標籤頁 -->
    <div class="flex gap-2 border-b border-gray-300">
      <button
        @click="activeTab = 'list'"
        :class="activeTab === 'list' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        📋 Agent 列表
      </button>
      <button
        @click="activeTab = 'status'"
        :class="activeTab === 'status' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        💚 健康狀態 ({{ healthyCount }}/{{ agentStore.agents.length }})
      </button>
      <button
        @click="activeTab = 'metrics'"
        :class="activeTab === 'metrics' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        📊 性能指標
      </button>
      <button
        @click="activeTab = 'logs'"
        :class="activeTab === 'logs' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        📜 日誌
      </button>
    </div>

    <!-- Agent 列表 Tab -->
    <div v-if="activeTab === 'list'" class="space-y-6">
      <AgentList :agents="agentStore.agents" @select="selectAgent" />

      <!-- 選中的 Agent 控制面板 -->
      <div v-if="selectedAgent" class="bg-white rounded-lg shadow-md p-6">
        <AgentControl :agent="selectedAgent" @action="handleAgentAction" />
      </div>
    </div>

    <!-- 健康狀態 Tab -->
    <div v-if="activeTab === 'status'" class="space-y-6">
      <AgentStatus :agents="agentStore.agents" />
    </div>

    <!-- 性能指標 Tab -->
    <div v-if="activeTab === 'metrics'" class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- 總吞吐量 -->
        <div class="bg-white p-6 rounded-lg shadow-md">
          <p class="text-gray-600 text-sm font-medium mb-2">總吞吐量 (req/s)</p>
          <p class="text-4xl font-bold text-green-600">{{ totalThroughput.toFixed(2) }}</p>
        </div>

        <!-- 平均延遲 -->
        <div class="bg-white p-6 rounded-lg shadow-md">
          <p class="text-gray-600 text-sm font-medium mb-2">平均延遲 (ms)</p>
          <p class="text-4xl font-bold text-blue-600">{{ avgLatency.toFixed(1) }}</p>
        </div>

        <!-- 錯誤率 -->
        <div class="bg-white p-6 rounded-lg shadow-md">
          <p class="text-gray-600 text-sm font-medium mb-2">錯誤率</p>
          <p class="text-4xl font-bold" :class="errorRate > 5 ? 'text-red-600' : 'text-green-600'">
            {{ errorRate.toFixed(2) }}%
          </p>
        </div>

        <!-- CPU 平均利用率 -->
        <div class="bg-white p-6 rounded-lg shadow-md">
          <p class="text-gray-600 text-sm font-medium mb-2">CPU 平均利用率</p>
          <p class="text-4xl font-bold" :class="avgCpu > 80 ? 'text-red-600' : 'text-green-600'">
            {{ avgCpu.toFixed(1) }}%
          </p>
        </div>
      </div>

      <!-- 各 Agent 性能對比 -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h3 class="text-2xl font-bold mb-6 text-gray-800">Agent 性能對比</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-sm text-gray-600">
            <thead class="bg-gray-100 border-b-2 border-gray-300">
              <tr>
                <th class="px-4 py-3 text-left font-semibold text-gray-800">Agent ID</th>
                <th class="px-4 py-3 text-left font-semibold text-gray-800">狀態</th>
                <th class="px-4 py-3 text-right font-semibold text-gray-800">吞吐量</th>
                <th class="px-4 py-3 text-right font-semibold text-gray-800">延遲 (ms)</th>
                <th class="px-4 py-3 text-right font-semibold text-gray-800">錯誤</th>
                <th class="px-4 py-3 text-right font-semibold text-gray-800">CPU %</th>
                <th class="px-4 py-3 text-right font-semibold text-gray-800">記憶體 MB</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="agent in agentStore.agents" :key="agent.id" class="border-b hover:bg-gray-50">
                <td class="px-4 py-3 font-mono text-xs">{{ agent.id.substring(0, 8) }}</td>
                <td class="px-4 py-3">
                  <span
                    :class="statusBadgeClass(agent.status)"
                    class="px-3 py-1 rounded-full text-xs font-bold"
                  >
                    {{ statusLabel(agent.status) }}
                  </span>
                </td>
                <td class="px-4 py-3 text-right">{{ (agent.metrics?.throughput || 0).toFixed(2) }}</td>
                <td class="px-4 py-3 text-right">{{ (agent.metrics?.latency || 0).toFixed(1) }}</td>
                <td class="px-4 py-3 text-right text-red-600">{{ agent.metrics?.error_count || 0 }}</td>
                <td class="px-4 py-3 text-right">{{ (agent.metrics?.cpu_usage || 0).toFixed(1) }}</td>
                <td class="px-4 py-3 text-right">{{ (agent.metrics?.memory_usage || 0).toFixed(0) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 日誌 Tab -->
    <div v-if="activeTab === 'logs'" class="space-y-6">
      <AgentLogs :agent="selectedAgent" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAgentStore } from '../stores/agents';
import AgentList from './AgentList.vue';
import AgentStatus from './AgentStatus.vue';
import AgentControl from './AgentControl.vue';
import AgentLogs from './AgentLogs.vue';

const agentStore = useAgentStore();
const activeTab = ref('list');
const selectedAgent = ref(null);

onMounted(async () => {
  await agentStore.fetchAgents();
});

const selectAgent = (agent) => {
  selectedAgent.value = agent;
};

const activeAgents = computed(() => {
  return agentStore.agents.filter(a => a.status === 'running').length;
});

const healthyCount = computed(() => {
  return agentStore.agents.filter(a => a.status === 'running' && a.health === 'healthy').length;
});

const totalThroughput = computed(() => {
  return agentStore.agents.reduce((sum, a) => sum + (a.metrics?.throughput || 0), 0);
});

const avgLatency = computed(() => {
  const agents = agentStore.agents.filter(a => a.metrics);
  if (agents.length === 0) return 0;
  return agents.reduce((sum, a) => sum + (a.metrics?.latency || 0), 0) / agents.length;
});

const errorRate = computed(() => {
  const totalErrors = agentStore.agents.reduce((sum, a) => sum + (a.metrics?.error_count || 0), 0);
  const totalRequests = agentStore.agents.reduce((sum, a) => sum + (a.metrics?.request_count || 1), 0);
  return (totalErrors / totalRequests) * 100 || 0;
});

const avgCpu = computed(() => {
  const agents = agentStore.agents.filter(a => a.metrics);
  if (agents.length === 0) return 0;
  return agents.reduce((sum, a) => sum + (a.metrics?.cpu_usage || 0), 0) / agents.length;
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

const handleAgentAction = async (action) => {
  if (!selectedAgent.value) return;
  await agentStore.controlAgent(selectedAgent.value.id, action);
  // Refresh agent data
  await agentStore.fetchAgents();
};
</script>
