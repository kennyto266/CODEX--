<template>
  <div class="bg-white rounded-lg shadow-md p-6">
    <h2 class="text-2xl font-bold mb-6 text-gray-800">回測配置</h2>

    <!-- 基本信息 -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <!-- 策略選擇 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          策略 <span class="text-red-500">*</span>
        </label>
        <select
          v-model="form.strategy_id"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">-- 選擇策略 --</option>
          <option value="moving_average_crossover">移動平均線交叉</option>
          <option value="rsi_oscillator">RSI 震蕩策略</option>
          <option value="bollinger_bands">布林帶策略</option>
          <option value="macd_strategy">MACD 指標策略</option>
          <option value="kdj_strategy">KDJ 隨機指標</option>
        </select>
      </div>

      <!-- 股票代碼 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          股票代碼 <span class="text-red-500">*</span>
        </label>
        <input
          v-model="form.symbol"
          type="text"
          placeholder="e.g., 0700.HK"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <!-- 開始日期 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          開始日期 <span class="text-red-500">*</span>
        </label>
        <input
          v-model="form.start_date"
          type="date"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <!-- 結束日期 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          結束日期 <span class="text-red-500">*</span>
        </label>
        <input
          v-model="form.end_date"
          type="date"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <!-- 初始資本 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          初始資本
        </label>
        <input
          v-model.number="form.initial_capital"
          type="number"
          placeholder="100000"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <!-- 回測名稱 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          回測名稱（可選）
        </label>
        <input
          v-model="form.run_name"
          type="text"
          placeholder="e.g., 2024-10-26 Test"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
    </div>

    <!-- 策略參數 -->
    <div v-if="form.strategy_id" class="mb-6 p-4 bg-gray-50 rounded-md">
      <h3 class="text-lg font-semibold text-gray-800 mb-4">策略參數</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- 移動平均線參數 -->
        <template v-if="form.strategy_id === 'moving_average_crossover'">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">快速周期</label>
            <input
              v-model.number="form.parameters.fast_period"
              type="number"
              :value="20"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">慢速周期</label>
            <input
              v-model.number="form.parameters.slow_period"
              type="number"
              :value="50"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">信號周期</label>
            <input
              v-model.number="form.parameters.signal_period"
              type="number"
              :value="9"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
        </template>

        <!-- RSI 參數 -->
        <template v-if="form.strategy_id === 'rsi_oscillator'">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">RSI 周期</label>
            <input
              v-model.number="form.parameters.rsi_period"
              type="number"
              :value="14"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">超賣水平</label>
            <input
              v-model.number="form.parameters.oversold_level"
              type="number"
              :value="30"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">超買水平</label>
            <input
              v-model.number="form.parameters.overbought_level"
              type="number"
              :value="70"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
        </template>

        <!-- KDJ 參數 -->
        <template v-if="form.strategy_id === 'kdj_strategy'">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">K 周期</label>
            <input
              v-model.number="form.parameters.k_period"
              type="number"
              :value="9"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">D 周期</label>
            <input
              v-model.number="form.parameters.d_period"
              type="number"
              :value="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">超買水平</label>
            <input
              v-model.number="form.parameters.overbought"
              type="number"
              :value="80"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
        </template>
      </div>
    </div>

    <!-- 提交按鈕 -->
    <div class="flex gap-4">
      <button
        @click="submitBacktest"
        :disabled="isSubmitting"
        class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-2 px-6 rounded-md transition"
      >
        <span v-if="!isSubmitting">🚀 開始回測</span>
        <span v-else>⏳ 提交中...</span>
      </button>

      <button
        @click="resetForm"
        class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-6 rounded-md transition"
      >
        🔄 重置
      </button>
    </div>

    <!-- 錯誤消息 -->
    <div
      v-if="formError"
      class="mt-4 p-4 bg-red-50 border border-red-200 rounded-md text-red-700"
    >
      ⚠️ {{ formError }}
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useBacktestStore } from '../stores/backtest';

const backtestStore = useBacktestStore();
const isSubmitting = ref(false);
const formError = ref(null);

const form = reactive({
  strategy_id: '',
  symbol: '',
  start_date: '2023-01-01',
  end_date: '2023-12-31',
  initial_capital: 100000,
  run_name: '',
  parameters: {
    fast_period: 20,
    slow_period: 50,
    signal_period: 9,
    rsi_period: 14,
    oversold_level: 30,
    overbought_level: 70,
    k_period: 9,
    d_period: 3,
    overbought: 80
  }
});

const submitBacktest = async () => {
  formError.value = null;

  // 驗證表單
  if (!form.strategy_id || !form.symbol || !form.start_date || !form.end_date) {
    formError.value = '請填寫所有必填字段';
    return;
  }

  isSubmitting.value = true;

  try {
    await backtestStore.submitBacktest({
      strategy_id: form.strategy_id,
      symbol: form.symbol,
      start_date: form.start_date,
      end_date: form.end_date,
      initial_capital: form.initial_capital,
      parameters: form.parameters
    });

    // 成功後重置表單
    resetForm();
  } catch (error) {
    formError.value = `提交失敗: ${error.message}`;
  } finally {
    isSubmitting.value = false;
  }
};

const resetForm = () => {
  form.strategy_id = '';
  form.symbol = '';
  form.start_date = '2023-01-01';
  form.end_date = '2023-12-31';
  form.initial_capital = 100000;
  form.run_name = '';
  formError.value = null;
};
</script>
