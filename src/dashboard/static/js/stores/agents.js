/**
 * Pinia Store: Agents Module
 * 管理 AI Agent 系統狀態
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useAgentsStore = defineStore('agents', () => {
  const agents = ref({});
  const logs = ref({});
  const isLoading = ref(false);
  const error = ref(null);

  const allAgents = computed(() => Object.values(agents.value));
  const activeAgents = computed(() =>
    Object.values(agents.value).filter(a => a.status === 'running')
  );

  async function fetchAgents() {
    isLoading.value = true;
    try {
      const response = await fetch('/api/agents/list');
      const data = await response.json();
      data.forEach(agent => {
        agents.value[agent.agent_id] = agent;
      });
    } catch (err) {
      error.value = err.message;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchAgentLogs(agentId) {
    try {
      const response = await fetch(`/api/agents/${agentId}/logs?limit=50`);
      const data = await response.json();
      logs.value[agentId] = data;
    } catch (err) {
      console.error('獲取日誌失敗:', err);
    }
  }

  async function controlAgent(agentId, action) {
    try {
      const response = await fetch(`/api/agents/${agentId}/${action}`, {
        method: 'POST'
      });
      return response.json();
    } catch (err) {
      error.value = err.message;
      throw err;
    }
  }

  return {
    agents,
    logs,
    isLoading,
    error,
    allAgents,
    activeAgents,
    fetchAgents,
    fetchAgentLogs,
    controlAgent
  };
});
