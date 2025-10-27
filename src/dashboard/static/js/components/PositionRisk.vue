<template>
  <div class="space-y-6">
    <div class="bg-white rounded-lg shadow-md p-6">
      <h3 class="text-2xl font-bold text-gray-800 mb-6">💼 頭寸風險分析</h3>

      <!-- 篩選工具 -->
      <div class="mb-6 flex gap-4">
        <input
          v-model="searchSymbol"
          type="text"
          placeholder="搜索股票代碼..."
          class="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          v-model="sortBy"
          class="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="symbol">按代碼</option>
          <option value="risk">按風險</option>
          <option value="qty">按數量</option>
        </select>
      </div>

      <!-- 頭寸表格 -->
      <div class="overflow-x-auto">
        <table class="w-full text-sm text-gray-600">
          <thead class="bg-gray-100 border-b-2 border-gray-300">
            <tr>
              <th class="px-4 py-3 text-left font-semibold">代碼</th>
              <th class="px-4 py-3 text-right font-semibold">數量</th>
              <th class="px-4 py-3 text-right font-semibold">價格</th>
              <th class="px-4 py-3 text-right font-semibold">頭寸值</th>
              <th class="px-4 py-3 text-right font-semibold">VaR 1D</th>
              <th class="px-4 py-3 text-center font-semibold">相關性</th>
              <th class="px-4 py-3 text-center font-semibold">風險級別</th>
              <th class="px-4 py-3 text-left font-semibold">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="pos in filteredPositions" :key="pos.symbol" class="border-b hover:bg-gray-50">
              <td class="px-4 py-3 font-bold text-gray-800">{{ pos.symbol }}</td>
              <td class="px-4 py-3 text-right">{{ pos.qty.toLocaleString() }}</td>
              <td class="px-4 py-3 text-right">¥{{ pos.price.toFixed(2) }}</td>
              <td class="px-4 py-3 text-right font-semibold">
                ¥{{ (pos.qty * pos.price / 10000).toFixed(1) }}W
              </td>
              <td class="px-4 py-3 text-right font-bold text-red-600">
                ¥{{ (pos.var_1d / 10000).toFixed(1) }}W
              </td>
              <td class="px-4 py-3 text-center">
                <span :class="correlationColor(pos.correlation)" class="font-bold">
                  {{ pos.correlation > 0 ? '+' : '' }}{{ pos.correlation.toFixed(2) }}
                </span>
              </td>
              <td class="px-4 py-3 text-center">
                <span :class="riskBadgeClass(pos.var_1d)" class="px-2 py-1 rounded-full text-xs font-bold">
                  {{ riskLevel(pos.var_1d) }}
                </span>
              </td>
              <td class="px-4 py-3">
                <button class="text-blue-600 hover:text-blue-800 font-semibold text-xs">詳情 →</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 風險警告 -->
      <div v-if="hasHighRiskPositions" class="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
        <p class="text-red-800 font-semibold mb-2">⚠️ 高風險頭寸預警</p>
        <ul class="text-sm text-red-700 space-y-1">
          <li v-for="pos in highRiskPositions" :key="pos.symbol">
            • {{ pos.symbol }}: VaR ¥{{ (pos.var_1d / 10000).toFixed(1) }}W，需要監控
          </li>
        </ul>
      </div>
    </div>

    <!-- 頭寸詳細分析 -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- 頭寸集中度 -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h4 class="text-lg font-bold text-gray-800 mb-4">📊 頭寸集中度</h4>

        <div class="space-y-3">
          <div v-for="pos in positions.slice(0, 3)" :key="pos.symbol">
            <div class="flex justify-between mb-1">
              <span class="text-gray-600">{{ pos.symbol }}</span>
              <span class="font-semibold">{{ positionPercentage(pos) }}%</span>
            </div>
            <div class="w-full bg-gray-300 rounded-full h-2">
              <div
                :style="{ width: positionPercentage(pos) + '%' }"
                :class="positionColor(pos.symbol)"
                class="h-2 rounded-full"
              ></div>
            </div>
          </div>
        </div>

        <p class="text-xs text-gray-500 mt-4">
          首 3 大頭寸佔投資組合的 {{ top3Percentage.toFixed(1) }}%
        </p>
      </div>

      <!-- 對沖分析 -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h4 class="text-lg font-bold text-gray-800 mb-4">🛡️ 對沖策略</h4>

        <div class="space-y-3 text-sm">
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-gray-600">總敞口</span>
            <span class="font-bold">¥3,200W</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-gray-600">對沖持倉</span>
            <span class="font-bold text-green-600">¥350W (黃金)</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-gray-600">淨敞口</span>
            <span class="font-bold">¥2,850W</span>
          </div>
          <div class="flex justify-between py-2">
            <span class="text-gray-600">對沖比率</span>
            <span class="font-bold text-yellow-600">10.9%</span>
          </div>
          <button class="w-full mt-3 px-3 py-2 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded text-xs font-semibold">
            建議對沖 →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  positions: {
    type: Array,
    required: true
  }
});

const searchSymbol = ref('');
const sortBy = ref('symbol');

const filteredPositions = computed(() => {
  let filtered = props.positions.filter(pos =>
    pos.symbol.toLowerCase().includes(searchSymbol.value.toLowerCase())
  );

  if (sortBy.value === 'risk') {
    filtered.sort((a, b) => b.var_1d - a.var_1d);
  } else if (sortBy.value === 'qty') {
    filtered.sort((a, b) => b.qty - a.qty);
  }

  return filtered;
});

const highRiskPositions = computed(() => {
  return props.positions.filter(pos => pos.var_1d > 40000);
});

const hasHighRiskPositions = computed(() => {
  return highRiskPositions.value.length > 0;
});

const totalPositionValue = computed(() => {
  return props.positions.reduce((sum, pos) => sum + (pos.qty * pos.price), 0);
});

const top3Percentage = computed(() => {
  const top3Value = props.positions
    .slice(0, 3)
    .reduce((sum, pos) => sum + (pos.qty * pos.price), 0);
  return (top3Value / totalPositionValue.value) * 100;
});

const positionPercentage = (pos) => {
  return ((pos.qty * pos.price / totalPositionValue.value) * 100).toFixed(1);
};

const positionColor = (symbol) => {
  const colors = {
    '0700.HK': 'bg-blue-600',
    '0388.HK': 'bg-purple-600',
    '1398.HK': 'bg-green-600'
  };
  return colors[symbol] || 'bg-gray-600';
};

const correlationColor = (corr) => {
  if (corr > 0.7) return 'text-red-600';
  if (corr < 0) return 'text-green-600';
  return 'text-gray-600';
};

const riskLevel = (var1d) => {
  if (var1d > 50000) return '🔴 高';
  if (var1d > 30000) return '🟡 中';
  return '🟢 低';
};

const riskBadgeClass = (var1d) => {
  if (var1d > 50000) return 'bg-red-100 text-red-800';
  if (var1d > 30000) return 'bg-yellow-100 text-yellow-800';
  return 'bg-green-100 text-green-800';
};
</script>
