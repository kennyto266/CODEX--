/**
 * Pinia Store: Backtest Module
 *
 * 管理回測系統的狀態：配置、進度、結果等
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useBacktestStore = defineStore('backtest', () => {
  // ==================== State ====================

  const backtests = ref({});
  const currentBacktestId = ref(null);
  const configurations = ref([]);
  const isLoading = ref(false);
  const error = ref(null);

  // ==================== Getters ====================

  const currentBacktest = computed(() => {
    return backtests.value[currentBacktestId.value] || null;
  });

  const allBacktests = computed(() => {
    return Object.values(backtests.value);
  });

  const completedBacktests = computed(() => {
    return Object.values(backtests.value).filter(bt => bt.status === 'completed');
  });

  const runningBacktests = computed(() => {
    return Object.values(backtests.value).filter(bt => bt.status === 'running');
  });

  // ==================== Actions ====================

  /**
   * 提交新回測
   */
  async function submitBacktest(config) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch('/api/backtest/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      const backtestId = data.backtest_id;
      currentBacktestId.value = backtestId;

      // 初始化回測記錄
      backtests.value[backtestId] = {
        backtest_id: backtestId,
        config,
        status: 'pending',
        progress: 0,
        created_at: new Date(),
        started_at: null,
        completed_at: null,
        results: null
      };

      // 開始輪詢狀態
      pollBacktestStatus(backtestId);

      return backtestId;
    } catch (err) {
      error.value = err.message;
      console.error('提交回測失敗:', err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * 輪詢回測狀態
   */
  async function pollBacktestStatus(backtestId, interval = 2000) {
    const maxAttempts = 300; // 10 分鐘
    let attempts = 0;

    const pollInterval = setInterval(async () => {
      attempts++;

      try {
        const response = await fetch(`/api/backtest/status/${backtestId}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        backtests.value[backtestId] = {
          ...backtests.value[backtestId],
          status: data.status,
          progress: data.progress,
          error_message: data.error_message
        };

        // 如果完成，獲取結果
        if (data.status === 'completed') {
          await fetchBacktestResults(backtestId);
          clearInterval(pollInterval);
        }
      } catch (err) {
        console.error('輪詢回測狀態失敗:', err);
        if (attempts >= maxAttempts) {
          clearInterval(pollInterval);
        }
      }
    }, interval);
  }

  /**
   * 獲取回測結果
   */
  async function fetchBacktestResults(backtestId) {
    try {
      const response = await fetch(`/api/backtest/results/${backtestId}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      backtests.value[backtestId].results = data;
      backtests.value[backtestId].completed_at = new Date();
    } catch (err) {
      console.error('獲取回測結果失敗:', err);
      throw err;
    }
  }

  /**
   * 獲取回測列表
   */
  async function fetchBacktestList(limit = 20) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch(`/api/backtest/list?limit=${limit}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();

      // 合併到現有回測列表
      data.forEach(bt => {
        backtests.value[bt.backtest_id] = {
          ...backtests.value[bt.backtest_id],
          ...bt
        };
      });

      return data;
    } catch (err) {
      error.value = err.message;
      console.error('獲取回測列表失敗:', err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * 保存配置
   */
  function saveConfiguration(config) {
    configurations.value.push({
      id: Date.now(),
      name: config.name,
      strategy_id: config.strategy_id,
      parameters: config.parameters,
      created_at: new Date(),
      saved: true
    });
  }

  /**
   * 清除所有回測
   */
  function clearBacktests() {
    backtests.value = {};
    currentBacktestId.value = null;
  }

  return {
    // State
    backtests,
    currentBacktestId,
    configurations,
    isLoading,
    error,

    // Getters
    currentBacktest,
    allBacktests,
    completedBacktests,
    runningBacktests,

    // Actions
    submitBacktest,
    fetchBacktestResults,
    fetchBacktestList,
    saveConfiguration,
    clearBacktests,
    pollBacktestStatus
  };
});
