<template>
  <div v-if="backtest" class="space-y-6">
    <!-- 回測進度 -->
    <div class="bg-white rounded-lg shadow-md p-6">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-2xl font-bold text-gray-800">回測 #{{ backtest.backtest_id }}</h2>
        <span
          :class="statusBadge"
          class="px-4 py-2 rounded-full text-sm font-bold"
        >
          {{ statusLabel }}
        </span>
      </div>

      <!-- 進度條 -->
      <div class="mb-4">
        <div class="flex justify-between mb-2">
          <span class="text-sm text-gray-600">進度</span>
          <span class="text-sm font-semibold text-gray-800">{{ backtest.progress }}%</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2">
          <div
            :style="{ width: backtest.progress + '%' }"
            class="bg-blue-600 h-2 rounded-full transition-all duration-300"
          ></div>
        </div>
      </div>

      <!-- 基本信息 -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
        <div>
          <p class="font-semibold text-gray-800">策略</p>
          <p>{{ backtest.config.strategy_id }}</p>
        </div>
        <div>
          <p class="font-semibold text-gray-800">股票</p>
          <p>{{ backtest.config.symbol }}</p>
        </div>
        <div>
          <p class="font-semibold text-gray-800">周期</p>
          <p>{{ backtest.config.start_date }} ~ {{ backtest.config.end_date }}</p>
        </div>
        <div>
          <p class="font-semibold text-gray-800">初始資本</p>
          <p>{{ formatCurrency(backtest.config.initial_capital) }}</p>
        </div>
      </div>
    </div>

    <!-- 性能指標 -->
    <div v-if="backtest.results" class="bg-white rounded-lg shadow-md p-6">
      <h3 class="text-2xl font-bold mb-6 text-gray-800">性能指標</h3>

      <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <!-- 總收益率 -->
        <div class="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
          <p class="text-gray-700 text-sm font-medium mb-1">總收益率</p>
          <p class="text-3xl font-bold text-green-600">
            {{ backtest.results.metrics.total_return_pct.toFixed(2) }}%
          </p>
        </div>

        <!-- 年化收益率 -->
        <div class="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
          <p class="text-gray-700 text-sm font-medium mb-1">年化收益率</p>
          <p class="text-3xl font-bold text-blue-600">
            {{ backtest.results.metrics.annual_return_pct.toFixed(2) }}%
          </p>
        </div>

        <!-- Sharpe 比率 -->
        <div class="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
          <p class="text-gray-700 text-sm font-medium mb-1">Sharpe 比率</p>
          <p class="text-3xl font-bold text-purple-600">
            {{ backtest.results.metrics.sharpe_ratio.toFixed(2) }}
          </p>
        </div>

        <!-- 最大回撤 -->
        <div class="bg-gradient-to-br from-red-50 to-red-100 p-4 rounded-lg border border-red-200">
          <p class="text-gray-700 text-sm font-medium mb-1">最大回撤</p>
          <p class="text-3xl font-bold text-red-600">
            {{ backtest.results.metrics.max_drawdown.toFixed(2) }}%
          </p>
        </div>

        <!-- 波動率 -->
        <div class="bg-gradient-to-br from-yellow-50 to-yellow-100 p-4 rounded-lg border border-yellow-200">
          <p class="text-gray-700 text-sm font-medium mb-1">波動率</p>
          <p class="text-3xl font-bold text-yellow-600">
            {{ (backtest.results.metrics.volatility * 100).toFixed(2) }}%
          </p>
        </div>

        <!-- Sortino 比率 -->
        <div class="bg-gradient-to-br from-indigo-50 to-indigo-100 p-4 rounded-lg border border-indigo-200">
          <p class="text-gray-700 text-sm font-medium mb-1">Sortino 比率</p>
          <p class="text-3xl font-bold text-indigo-600">
            {{ backtest.results.metrics.sortino_ratio.toFixed(2) }}
          </p>
        </div>

        <!-- 勝率 -->
        <div class="bg-gradient-to-br from-cyan-50 to-cyan-100 p-4 rounded-lg border border-cyan-200">
          <p class="text-gray-700 text-sm font-medium mb-1">勝率</p>
          <p class="text-3xl font-bold text-cyan-600">
            {{ (backtest.results.metrics.win_rate * 100).toFixed(1) }}%
          </p>
        </div>

        <!-- 交易次數 -->
        <div class="bg-gradient-to-br from-pink-50 to-pink-100 p-4 rounded-lg border border-pink-200">
          <p class="text-gray-700 text-sm font-medium mb-1">交易次數</p>
          <p class="text-3xl font-bold text-pink-600">
            {{ backtest.results.metrics.total_trades }}
          </p>
        </div>
      </div>
    </div>

    <!-- 權益曲線圖 (簡化版) -->
    <div v-if="backtest.results && backtest.results.equity_curve" class="bg-white rounded-lg shadow-md p-6">
      <h3 class="text-xl font-bold mb-4 text-gray-800">權益曲線</h3>
      <div class="bg-gray-50 p-4 rounded-lg h-64 flex items-center justify-center text-gray-500">
        📈 圖表展示 (需要集成 Chart.js/Plotly)
        <br />
        <span class="text-sm">數據點: {{ backtest.results.equity_curve.length }}</span>
      </div>
    </div>

    <!-- 成交記錄 -->
    <div v-if="backtest.results && backtest.results.trade_list" class="bg-white rounded-lg shadow-md p-6">
      <h3 class="text-xl font-bold mb-4 text-gray-800">成交記錄</h3>

      <div class="overflow-x-auto">
        <table class="w-full text-sm text-gray-600">
          <thead class="bg-gray-100 border-b-2 border-gray-300">
            <tr>
              <th class="px-4 py-3 text-left font-semibold text-gray-800">日期</th>
              <th class="px-4 py-3 text-left font-semibold text-gray-800">信號</th>
              <th class="px-4 py-3 text-right font-semibold text-gray-800">價格</th>
              <th class="px-4 py-3 text-right font-semibold text-gray-800">數量</th>
              <th class="px-4 py-3 text-right font-semibold text-gray-800">損益</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(trade, idx) in backtest.results.trade_list" :key="idx" class="border-b hover:bg-gray-50">
              <td class="px-4 py-3">{{ trade.date }}</td>
              <td class="px-4 py-3">
                <span
                  :class="trade.signal === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                  class="px-3 py-1 rounded-full text-xs font-bold"
                >
                  {{ trade.signal }}
                </span>
              </td>
              <td class="px-4 py-3 text-right">{{ trade.price.toFixed(2) }}</td>
              <td class="px-4 py-3 text-right">{{ trade.quantity }}</td>
              <td class="px-4 py-3 text-right font-semibold" :class="trade.profit > 0 ? 'text-green-600' : 'text-red-600'">
                {{ trade.profit > 0 ? '+' : '' }}{{ trade.profit.toFixed(2) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="backtest.results.trade_list.length === 0" class="text-center py-8 text-gray-500">
        沒有成交記錄
      </div>
    </div>

    <!-- 操作按鈕 -->
    <div class="flex gap-4">
      <button
        @click="$emit('export')"
        class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded-md transition"
      >
        📥 導出結果
      </button>
      <button
        @click="$emit('compare')"
        class="bg-orange-600 hover:bg-orange-700 text-white font-bold py-2 px-6 rounded-md transition"
      >
        📊 對比分析
      </button>
    </div>
  </div>

  <!-- 空狀態 -->
  <div v-else class="bg-white rounded-lg shadow-md p-12 text-center text-gray-500">
    <p class="text-lg mb-2">📭 暫無回測結果</p>
    <p class="text-sm">請先提交一個回測任務</p>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  backtest: Object
});

const emit = defineEmits(['export', 'compare']);

const statusLabel = computed(() => {
  if (!props.backtest) return '';
  const status = props.backtest.status;
  if (status === 'pending') return '⏳ 等待中';
  if (status === 'running') return '⚙️ 運行中';
  if (status === 'completed') return '✅ 已完成';
  if (status === 'failed') return '❌ 失敗';
  return status;
});

const statusBadge = computed(() => {
  if (!props.backtest) return '';
  const status = props.backtest.status;
  if (status === 'pending') return 'bg-yellow-100 text-yellow-800';
  if (status === 'running') return 'bg-blue-100 text-blue-800';
  if (status === 'completed') return 'bg-green-100 text-green-800';
  if (status === 'failed') return 'bg-red-100 text-red-800';
  return 'bg-gray-100 text-gray-800';
});

const formatCurrency = (value) => {
  return '¥' + value.toLocaleString('zh-CN', { maximumFractionDigits: 0 });
};
</script>
