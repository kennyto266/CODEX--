/**
 * Pinia Store: Agents Module (Enhanced)
 * 管理 AI Agent 系統狀態
 * Phase 7: Enhanced Architecture
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { apiClient, APIError } from '../utils/api.js';
import { apiCache } from '../utils/cache.js';
import { errorHandler } from '../utils/errorHandler.js';
import { AGENT_STATUS, AGENT_TYPES } from '../utils/constants.js';

export const useAgentsStore = defineStore('agents', () => {
  // State
  const agents = ref({});
  const logs = ref({});
  const isLoading = ref(false);
  const error = ref(null);
  const lastFetch = ref(null);
  const selectedAgentId = ref(null);
  const filterStatus = ref(null);

  // Getters
  const allAgents = computed(() => Object.values(agents.value));

  const activeAgents = computed(() =>
    Object.values(agents.value).filter(a => a.status === AGENT_STATUS.RUNNING)
  );

  const filteredAgents = computed(() => {
    if (!filterStatus.value) return allAgents.value;
    return allAgents.value.filter(a => a.status === filterStatus.value);
  });

  const selectedAgent = computed(() => {
    if (!selectedAgentId.value) return null;
    return agents.value[selectedAgentId.value] || null;
  });

  const agentStats = computed(() => {
    const stats = {
      total: allAgents.value.length,
      running: 0,
      stopped: 0,
      error: 0,
      pending: 0
    };

    allAgents.value.forEach(agent => {
      stats[agent.status] = (stats[agent.status] || 0) + 1;
    });

    return stats;
  });

  // Actions
  async function fetchAgents(useCache = true) {
    if (isLoading.value) return;

    isLoading.value = true;
    error.value = null;

    try {
      const cacheKey = useCache ? 'agents-list' : null;

      if (useCache) {
        // Try cache first
        const cachedData = apiCache.cache.get(cacheKey);
        if (cachedData) {
          _updateAgentsFromData(cachedData);
          lastFetch.value = Date.now();
          return;
        }
      }

      // Fetch from API
      const response = await apiClient.get('/api/agents/list');
      const data = Array.isArray(response.data) ? response.data : [];

      _updateAgentsFromData(data);
      lastFetch.value = Date.now();

      // Cache the result
      if (useCache) {
        apiCache.cache.set(cacheKey, data, 60000); // 1 minute cache
      }

      console.log('✅ Agents data fetched successfully');
    } catch (err) {
      const errorMsg = err.message || 'Failed to fetch agents';
      error.value = errorMsg;
      errorHandler.handle(err, { context: 'fetchAgents' });
      console.error('❌ Failed to fetch agents:', err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  function _updateAgentsFromData(data) {
    const agentsMap = {};
    data.forEach(agent => {
      agentsMap[agent.agent_id] = {
        ...agent,
        type: agent.type || AGENT_TYPES.COORDINATOR,
        status: agent.status || AGENT_STATUS.STOPPED,
        health: agent.health || 'unknown',
        lastUpdate: agent.lastUpdate || new Date().toISOString()
      };
    });
    agents.value = agentsMap;
  }

  async function fetchAgentLogs(agentId, limit = 100) {
    if (!agentId) return;

    try {
      const response = await apiClient.get(`/api/agents/${agentId}/logs`, {
        params: { limit }
      });

      logs.value[agentId] = {
        data: response.data || [],
        lastFetch: Date.now()
      };

      return response.data;
    } catch (err) {
      errorHandler.handle(err, { context: 'fetchAgentLogs', agentId });
      throw err;
    }
  }

  async function controlAgent(agentId, action) {
    if (!agentId || !action) {
      throw new Error('Agent ID and action are required');
    }

    try {
      const response = await apiClient.post(`/api/agents/${agentId}/${action}`);

      // Update agent status immediately
      if (agents.value[agentId]) {
        agents.value[agentId] = {
          ...agents.value[agentId],
          status: action === 'start' ? AGENT_STATUS.RUNNING : AGENT_STATUS.STOPPED,
          lastUpdate: new Date().toISOString()
        };
      }

      // Invalidate cache
      apiCache.delete('agents-list');

      return response.data;
    } catch (err) {
      const errorMsg = err.message || `Failed to ${action} agent`;
      error.value = errorMsg;
      errorHandler.handle(err, { context: 'controlAgent', agentId, action });
      throw err;
    }
  }

  function selectAgent(agentId) {
    selectedAgentId.value = agentId;
  }

  function setFilterStatus(status) {
    filterStatus.value = status;
  }

  function clearFilter() {
    filterStatus.value = null;
  }

  function clearError() {
    error.value = null;
  }

  // Refresh with debounce
  let refreshTimeout;
  function refreshAgents(debounceMs = 1000) {
    clearTimeout(refreshTimeout);
    refreshTimeout = setTimeout(() => {
      apiCache.delete('agents-list');
      fetchAgents(false);
    }, debounceMs);
  }

  return {
    // State
    agents,
    logs,
    isLoading,
    error,
    lastFetch,
    selectedAgentId,
    filterStatus,

    // Getters
    allAgents,
    activeAgents,
    filteredAgents,
    selectedAgent,
    agentStats,

    // Actions
    fetchAgents,
    fetchAgentLogs,
    controlAgent,
    selectAgent,
    setFilterStatus,
    clearFilter,
    clearError,
    refreshAgents
  };
});
