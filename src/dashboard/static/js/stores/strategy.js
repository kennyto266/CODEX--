import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useStrategyStore = defineStore('strategy', () => {
  const strategies = ref([]);
  const selectedStrategy = ref(null);
  const configurations = ref([]);

  async function fetchStrategies() {
    try {
      const response = await fetch('/api/strategies/list');
      strategies.value = await response.json();
    } catch (err) {
      console.error('獲取策略失敗:', err);
    }
  }

  async function fetchStrategy(strategyId) {
    try {
      const response = await fetch(`/api/strategies/${strategyId}`);
      selectedStrategy.value = await response.json();
    } catch (err) {
      console.error('獲取策略詳情失敗:', err);
    }
  }

  async function saveConfiguration(strategyId, configName, parameters) {
    try {
      const response = await fetch('/api/strategies/configs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy_id: strategyId, config_name: configName, parameters })
      });
      return response.json();
    } catch (err) {
      console.error('保存配置失敗:', err);
    }
  }

  return {
    strategies,
    selectedStrategy,
    configurations,
    fetchStrategies,
    fetchStrategy,
    saveConfiguration
  };
});
