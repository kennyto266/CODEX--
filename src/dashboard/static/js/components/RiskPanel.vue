<template>
  <div class="space-y-6 p-6 bg-gray-50 min-h-screen">
    <!-- 標題 -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-4xl font-bold text-gray-900">⚠️ 風險儀表板</h1>
        <p class="text-gray-600 mt-2">實時風險監控與管理</p>
      </div>
      <div class="text-right">
        <p class="text-sm text-gray-500">風險評級</p>
        <p class="text-3xl font-bold" :class="riskLevelColor">{{ riskLevel }}</p>
      </div>
    </div>

    <!-- 標籤頁 -->
    <div class="flex gap-2 border-b border-gray-300">
      <button
        @click="activeTab = 'overview'"
        :class="activeTab === 'overview' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        📊 風險概覽
      </button>
      <button
        @click="activeTab = 'var'"
        :class="activeTab === 'var' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        📈 風險值 (VaR)
      </button>
      <button
        @click="activeTab = 'positions'"
        :class="activeTab === 'positions' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        💼 頭寸風險
      </button>
      <button
        @click="activeTab = 'alerts'"
        :class="activeTab === 'alerts' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        🔔 風險告警 ({{ alertCount }})
      </button>
      <button
        @click="activeTab = 'heatmap'"
        :class="activeTab === 'heatmap' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        🔥 風險熱力圖
      </button>
    </div>

    <!-- 風險概覽 Tab -->
    <div v-if="activeTab === 'overview'" class="space-y-6">
      <PortfolioRisk :riskData="riskData" />
    </div>

    <!-- VaR Tab -->
    <div v-if="activeTab === 'var'" class="space-y-6">
      <VaRChart :varData="varData" />
    </div>

    <!-- 頭寸風險 Tab -->
    <div v-if="activeTab === 'positions'" class="space-y-6">
      <PositionRisk :positions="positions" />
    </div>

    <!-- 風險告警 Tab -->
    <div v-if="activeTab === 'alerts'" class="space-y-6">
      <AlertManager :alerts="alerts" @acknowledge="acknowledgeAlert" />
    </div>

    <!-- 風險熱力圖 Tab -->
    <div v-if="activeTab === 'heatmap'" class="space-y-6">
      <RiskHeatmap :heatmapData="heatmapData" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRiskStore } from '../stores/risk';
import PortfolioRisk from './PortfolioRisk.vue';
import VaRChart from './VaRChart.vue';
import PositionRisk from './PositionRisk.vue';
import AlertManager from './AlertManager.vue';
import RiskHeatmap from './RiskHeatmap.vue';

const riskStore = useRiskStore();
const activeTab = ref('overview');

// 模擬風險數據
const riskData = ref({
  portfolio_value: 5000000,
  total_var_95: 450000,
  total_var_99: 650000,
  max_drawdown_pct: 12.5,
  current_leverage: 2.3,
  max_leverage: 3.0,
  positions_at_risk: 5,
  correlation_avg: 0.45
});

const varData = ref({
  daily_var_95: [350000, 365000, 380000, 420000, 440000, 450000],
  daily_var_99: [500000, 515000, 540000, 620000, 630000, 650000],
  dates: ['2025-10-20', '2025-10-21', '2025-10-22', '2025-10-23', '2025-10-24', '2025-10-25']
});

const positions = ref([
  { symbol: '0700.HK', qty: 1000, price: 325.50, var_1d: 45000, correlation: 0.85, delta: 0.92 },
  { symbol: '0388.HK', qty: 500, price: 45.20, var_1d: 35000, correlation: 0.72, delta: 0.88 },
  { symbol: '1398.HK', qty: 2000, price: 6.85, var_1d: 55000, correlation: 0.68, delta: 0.95 },
  { symbol: '0939.HK', qty: 800, price: 12.50, var_1d: 28000, correlation: 0.61, delta: 0.90 },
  { symbol: 'GOLD', qty: 100, price: 2050.00, var_1d: 35000, correlation: -0.15, delta: 1.0 }
]);

const alerts = ref([
  { id: 1, level: 'critical', message: '投資組合 VaR 超過 95% 限制', timestamp: new Date(), acknowledged: false },
  { id: 2, level: 'warning', message: '持倉相關性高於閾值', timestamp: new Date(Date.now() - 300000), acknowledged: false },
  { id: 3, level: 'info', message: '杠桿率達到 80% 上限', timestamp: new Date(Date.now() - 600000), acknowledged: true }
]);

const heatmapData = ref({
  symbols: ['0700.HK', '0388.HK', '1398.HK', '0939.HK', 'GOLD', 'USD'],
  correlations: [
    [1.0, 0.85, 0.78, 0.72, -0.15, 0.42],
    [0.85, 1.0, 0.68, 0.65, -0.12, 0.38],
    [0.78, 0.68, 1.0, 0.75, -0.18, 0.35],
    [0.72, 0.65, 0.75, 1.0, -0.20, 0.40],
    [-0.15, -0.12, -0.18, -0.20, 1.0, -0.08],
    [0.42, 0.38, 0.35, 0.40, -0.08, 1.0]
  ]
});

const riskLevel = computed(() => {
  if (riskData.value.total_var_95 / riskData.value.portfolio_value > 0.15) return '🔴 高';
  if (riskData.value.total_var_95 / riskData.value.portfolio_value > 0.08) return '🟡 中';
  return '🟢 低';
});

const riskLevelColor = computed(() => {
  if (riskLevel.value.includes('🔴')) return 'text-red-600';
  if (riskLevel.value.includes('🟡')) return 'text-yellow-600';
  return 'text-green-600';
});

const alertCount = computed(() => {
  return alerts.value.filter(a => !a.acknowledged).length;
});

onMounted(async () => {
  // 可以在這裡加載數據
});

const acknowledgeAlert = (alertId) => {
  const alert = alerts.value.find(a => a.id === alertId);
  if (alert) {
    alert.acknowledged = true;
  }
};
</script>
