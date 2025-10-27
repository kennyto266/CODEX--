<template>
  <div class="space-y-6 p-6 bg-gray-50 min-h-screen">
    <!-- 標題 -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-4xl font-bold text-gray-900">📊 回測系統</h1>
        <p class="text-gray-600 mt-2">策略性能評估和參數優化</p>
      </div>
      <div class="text-right">
        <p class="text-sm text-gray-500">已完成回測</p>
        <p class="text-3xl font-bold text-blue-600">{{ backtestStore.completedBacktests.length }}</p>
      </div>
    </div>

    <!-- 標籤頁 -->
    <div class="flex gap-2 border-b border-gray-300">
      <button
        @click="activeTab = 'new'"
        :class="activeTab === 'new' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        ➕ 新建回測
      </button>
      <button
        @click="activeTab = 'results'"
        :class="activeTab === 'results' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        📈 回測結果 ({{ backtestStore.allBacktests.length }})
      </button>
      <button
        @click="activeTab = 'history'"
        :class="activeTab === 'history' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        📜 回測歷史
      </button>
    </div>

    <!-- 新建回測 Tab -->
    <div v-if="activeTab === 'new'" class="space-y-6">
      <BacktestForm />

      <!-- 進行中的回測 -->
      <div v-if="backtestStore.runningBacktests.length > 0">
        <h3 class="text-xl font-bold text-gray-800 mb-4">⚙️ 進行中的回測</h3>
        <div class="space-y-4">
          <div
            v-for="backtest in backtestStore.runningBacktests"
            :key="backtest.backtest_id"
            class="bg-white p-4 rounded-lg shadow-md"
          >
            <div class="flex justify-between items-center mb-3">
              <span class="font-semibold text-gray-800">{{ backtest.config.strategy_id }} - {{ backtest.config.symbol }}</span>
              <span class="text-sm font-bold text-blue-600">{{ backtest.progress }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                :style="{ width: backtest.progress + '%' }"
                class="bg-blue-600 h-2 rounded-full transition-all"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 回測結果 Tab -->
    <div v-if="activeTab === 'results'" class="space-y-6">
      <div v-if="backtestStore.completedBacktests.length > 0" class="space-y-6">
        <!-- 結果列表 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div
            v-for="backtest in backtestStore.completedBacktests"
            :key="backtest.backtest_id"
            @click="selectBacktest(backtest)"
            :class="selectedBacktest?.backtest_id === backtest.backtest_id ? 'ring-2 ring-blue-600' : 'hover:shadow-lg'"
            class="bg-white p-6 rounded-lg shadow-md cursor-pointer transition"
          >
            <div class="flex justify-between items-start mb-3">
              <div>
                <h4 class="text-lg font-bold text-gray-800">{{ backtest.config.strategy_id }}</h4>
                <p class="text-sm text-gray-600">{{ backtest.config.symbol }}</p>
              </div>
              <span class="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full font-bold">
                ✅ 已完成
              </span>
            </div>

            <div class="grid grid-cols-2 gap-3 mb-4 text-sm">
              <div>
                <p class="text-gray-600">總收益率</p>
                <p class="text-2xl font-bold text-green-600">
                  {{ backtest.results?.metrics.total_return_pct.toFixed(1) }}%
                </p>
              </div>
              <div>
                <p class="text-gray-600">Sharpe 比率</p>
                <p class="text-2xl font-bold text-blue-600">
                  {{ backtest.results?.metrics.sharpe_ratio.toFixed(2) }}
                </p>
              </div>
            </div>

            <p class="text-xs text-gray-500">
              🕐 {{ new Date(backtest.created_at).toLocaleString() }}
            </p>
          </div>
        </div>

        <!-- 詳細結果 -->
        <div v-if="selectedBacktest" class="bg-white rounded-lg shadow-md p-6">
          <BacktestResults
            :backtest="selectedBacktest"
            @export="exportResults"
            @compare="compareResults"
          />
        </div>
      </div>

      <!-- 空狀態 -->
      <div v-else class="bg-white rounded-lg shadow-md p-12 text-center text-gray-500">
        <p class="text-lg mb-2">📭 暫無已完成的回測</p>
        <p class="text-sm">請先在「新建回測」標籤頁提交回測任務</p>
      </div>
    </div>

    <!-- 回測歷史 Tab -->
    <div v-if="activeTab === 'history'" class="bg-white rounded-lg shadow-md p-6">
      <h2 class="text-2xl font-bold text-gray-800 mb-6">📜 回測歷史</h2>

      <div class="overflow-x-auto">
        <table class="w-full text-sm text-gray-600">
          <thead class="bg-gray-100 border-b-2 border-gray-300">
            <tr>
              <th class="px-4 py-3 text-left font-semibold text-gray-800">ID</th>
              <th class="px-4 py-3 text-left font-semibold text-gray-800">策略</th>
              <th class="px-4 py-3 text-left font-semibold text-gray-800">股票</th>
              <th class="px-4 py-3 text-left font-semibold text-gray-800">狀態</th>
              <th class="px-4 py-3 text-right font-semibold text-gray-800">收益率</th>
              <th class="px-4 py-3 text-right font-semibold text-gray-800">建立時間</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="backtest in backtestStore.allBacktests"
              :key="backtest.backtest_id"
              class="border-b hover:bg-gray-50"
            >
              <td class="px-4 py-3 font-mono text-xs text-gray-500">{{ backtest.backtest_id.substring(0, 8) }}</td>
              <td class="px-4 py-3">{{ backtest.config.strategy_id }}</td>
              <td class="px-4 py-3 font-bold text-gray-800">{{ backtest.config.symbol }}</td>
              <td class="px-4 py-3">
                <span
                  :class="statusClass(backtest.status)"
                  class="px-3 py-1 rounded-full text-xs font-bold"
                >
                  {{ statusLabel(backtest.status) }}
                </span>
              </td>
              <td class="px-4 py-3 text-right font-semibold" :class="backtest.results?.metrics.total_return_pct > 0 ? 'text-green-600' : 'text-red-600'">
                {{ backtest.results?.metrics.total_return_pct?.toFixed(2) }}%
              </td>
              <td class="px-4 py-3 text-right text-xs">
                {{ new Date(backtest.created_at).toLocaleString() }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="backtestStore.allBacktests.length === 0" class="text-center py-8 text-gray-500">
        沒有回測歷史
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useBacktestStore } from '../stores/backtest';
import BacktestForm from './BacktestForm.vue';
import BacktestResults from './BacktestResults.vue';

const backtestStore = useBacktestStore();
const activeTab = ref('new');
const selectedBacktest = ref(null);

onMounted(() => {
  // 加載歷史回測列表
  backtestStore.fetchBacktestList();
});

const selectBacktest = (backtest) => {
  selectedBacktest.value = backtest;
};

const statusLabel = (status) => {
  if (status === 'pending') return '⏳ 等待';
  if (status === 'running') return '⚙️ 運行中';
  if (status === 'completed') return '✅ 完成';
  if (status === 'failed') return '❌ 失敗';
  return status;
};

const statusClass = (status) => {
  if (status === 'pending') return 'bg-yellow-100 text-yellow-800';
  if (status === 'running') return 'bg-blue-100 text-blue-800';
  if (status === 'completed') return 'bg-green-100 text-green-800';
  if (status === 'failed') return 'bg-red-100 text-red-800';
  return 'bg-gray-100 text-gray-800';
};

const exportResults = () => {
  if (!selectedBacktest.value) return;
  console.log('導出結果:', selectedBacktest.value);
  alert('功能待實現：導出回測結果');
};

const compareResults = () => {
  if (!selectedBacktest.value) return;
  console.log('對比分析:', selectedBacktest.value);
  alert('功能待實現：對比多個回測結果');
};
</script>
