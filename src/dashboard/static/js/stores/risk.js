import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useRiskStore = defineStore('risk', () => {
  const portfolio = ref(null);
  const alerts = ref([]);
  const positions = ref([]);
  const isLoading = ref(false);

  async function fetchPortfolioRisk() {
    isLoading.value = true;
    try {
      const response = await fetch('/api/risk/portfolio');
      portfolio.value = await response.json();
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchAlerts() {
    try {
      const response = await fetch('/api/risk/alerts');
      alerts.value = await response.json();
    } catch (err) {
      console.error('獲取告警失敗:', err);
    }
  }

  async function fetchPositionRisk() {
    try {
      const response = await fetch('/api/risk/positions');
      positions.value = await response.json();
    } catch (err) {
      console.error('獲取頭寸風險失敗:', err);
    }
  }

  const unacknowledgedAlerts = computed(() =>
    alerts.value.filter(a => !a.acknowledged)
  );

  return {
    portfolio,
    alerts,
    positions,
    isLoading,
    unacknowledgedAlerts,
    fetchPortfolioRisk,
    fetchAlerts,
    fetchPositionRisk
  };
});
