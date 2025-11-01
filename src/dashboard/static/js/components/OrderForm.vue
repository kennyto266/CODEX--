<template>
  <div class="bg-white rounded-lg shadow-md p-6">
    <h3 class="text-2xl font-bold text-gray-800 mb-6">📝 交易下單</h3>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- 左側：下單表單 -->
      <div class="space-y-4">
        <!-- 股票代碼 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">股票代碼 *</label>
          <input
            v-model="form.symbol"
            type="text"
            placeholder="例如：0700.HK"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- 交易方向 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">交易方向 *</label>
          <div class="flex gap-4">
            <label class="flex items-center">
              <input v-model="form.side" type="radio" value="BUY" class="w-4 h-4 text-green-600" />
              <span class="ml-2 text-green-600 font-semibold">🟢 買進</span>
            </label>
            <label class="flex items-center">
              <input v-model="form.side" type="radio" value="SELL" class="w-4 h-4 text-red-600" />
              <span class="ml-2 text-red-600 font-semibold">🔴 賣出</span>
            </label>
          </div>
        </div>

        <!-- 數量 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">數量 *</label>
          <input
            v-model.number="form.qty"
            type="number"
            placeholder="100"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- 價格 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">價格 *</label>
          <input
            v-model.number="form.price"
            type="number"
            step="0.01"
            placeholder="100.00"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- 訂單類型 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">訂單類型</label>
          <select
            v-model="form.order_type"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="LIMIT">限價單</option>
            <option value="MARKET">市價單</option>
            <option value="STOP">止損單</option>
          </select>
        </div>

        <!-- 有效期 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">有效期</label>
          <select
            v-model="form.time_in_force"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="DAY">今日有效</option>
            <option value="GTC">永久有效</option>
            <option value="FOK">全部成交或取消</option>
            <option value="IOC">立即成交或取消</option>
          </select>
        </div>

        <!-- 提交按鈕 -->
        <button
          @click="submitOrder"
          :disabled="isSubmitting || !canSubmit"
          class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-md transition"
        >
          <span v-if="!isSubmitting">🚀 提交訂單</span>
          <span v-else>⏳ 提交中...</span>
        </button>

        <!-- 錯誤提示 -->
        <div v-if="formError" class="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
          ⚠️ {{ formError }}
        </div>
      </div>

      <!-- 右側：訂單預覽 -->
      <div class="bg-gray-50 rounded-lg p-4 space-y-4">
        <h4 class="font-bold text-gray-800">📊 訂單預覽</h4>

        <div class="space-y-2 text-sm">
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-gray-600">股票代碼</span>
            <span class="font-semibold">{{ form.symbol || '-' }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-gray-600">交易方向</span>
            <span :class="form.side === 'BUY' ? 'text-green-600' : 'text-red-600'" class="font-semibold">
              {{ form.side || '-' }}
            </span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-gray-600">數量</span>
            <span class="font-semibold">{{ form.qty || 0 }} 股</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-gray-600">單價</span>
            <span class="font-semibold">¥{{ form.price || 0 }}</span>
          </div>
          <div class="flex justify-between py-3 border-b-2 border-gray-300 text-lg font-bold">
            <span class="text-gray-800">訂單總額</span>
            <span class="text-blue-600">¥{{ orderTotal.toFixed(2) }}</span>
          </div>
          <div class="flex justify-between py-2">
            <span class="text-gray-600">估計費用</span>
            <span class="font-semibold text-orange-600">¥{{ (orderTotal * 0.001).toFixed(2) }}</span>
          </div>
          <div class="flex justify-between py-2 text-lg">
            <span class="text-gray-800">最終金額</span>
            <span class="font-bold text-blue-600">¥{{ (orderTotal + orderTotal * 0.001).toFixed(2) }}</span>
          </div>
        </div>

        <!-- 風險提示 -->
        <div v-if="riskWarning" class="p-3 bg-yellow-50 border border-yellow-200 rounded-md text-yellow-700 text-xs">
          <p class="font-semibold mb-1">⚠️ 風險提示</p>
          <p>{{ riskWarning }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const emit = defineEmits(['submit']);

const isSubmitting = ref(false);
const formError = ref('');

const form = ref({
  symbol: '',
  side: 'BUY',
  qty: 0,
  price: 0,
  order_type: 'LIMIT',
  time_in_force: 'DAY'
});

const orderTotal = computed(() => {
  return (form.value.qty || 0) * (form.value.price || 0);
});

const canSubmit = computed(() => {
  return form.value.symbol && form.value.qty > 0 && form.value.price > 0;
});

const riskWarning = computed(() => {
  if (orderTotal.value > 2000000) {
    return '大額訂單，請確保有足夠資金和流動性';
  }
  if (form.value.qty > 100000) {
    return '超大數量訂單，可能影響市場價格';
  }
  return '';
});

const submitOrder = async () => {
  formError.value = '';

  if (!canSubmit.value) {
    formError.value = '請填寫所有必填字段';
    return;
  }

  isSubmitting.value = true;

  try {
    emit('submit', {
      symbol: form.value.symbol,
      side: form.value.side,
      qty: form.value.qty,
      price: form.value.price,
      order_type: form.value.order_type,
      time_in_force: form.value.time_in_force
    });

    // 重置表單
    form.value = {
      symbol: '',
      side: 'BUY',
      qty: 0,
      price: 0,
      order_type: 'LIMIT',
      time_in_force: 'DAY'
    };
  } catch (error) {
    formError.value = `提交失敗: ${error.message}`;
  } finally {
    isSubmitting.value = false;
  }
};
</script>
