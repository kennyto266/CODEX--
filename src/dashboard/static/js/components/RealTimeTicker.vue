<template>
  <div class="bg-white rounded-lg shadow-md p-6 space-y-6">
    <h3 class="text-2xl font-bold text-gray-800">📈 實時行情</h3>

    <!-- 行情網格 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="ticker in tickers"
        :key="ticker.symbol"
        class="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition"
      >
        <!-- 股票代碼和方向 -->
        <div class="flex justify-between items-start mb-3">
          <h4 class="text-lg font-bold text-gray-800">{{ ticker.symbol }}</h4>
          <span :class="ticker.change > 0 ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100'" class="px-2 py-1 rounded text-xs font-bold">
            {{ ticker.change > 0 ? '↑' : '↓' }} {{ Math.abs(ticker.change_pct).toFixed(2) }}%
          </span>
        </div>

        <!-- 當前價格 -->
        <div class="mb-4">
          <p class="text-4xl font-bold" :class="ticker.change > 0 ? 'text-green-600' : 'text-red-600'">
            ¥{{ ticker.price.toFixed(2) }}
          </p>
          <p class="text-sm text-gray-500 mt-1">
            <span :class="ticker.change > 0 ? 'text-green-600' : 'text-red-600'">
              {{ ticker.change > 0 ? '+' : '' }}¥{{ ticker.change.toFixed(2) }}
            </span>
          </p>
        </div>

        <!-- 買賣價 -->
        <div class="grid grid-cols-2 gap-2 mb-4 text-sm">
          <div class="bg-red-50 p-2 rounded">
            <p class="text-gray-600 text-xs">買價</p>
            <p class="font-bold text-red-600">¥{{ ticker.bid.toFixed(2) }}</p>
          </div>
          <div class="bg-green-50 p-2 rounded">
            <p class="text-gray-600 text-xs">賣價</p>
            <p class="font-bold text-green-600">¥{{ ticker.ask.toFixed(2) }}</p>
          </div>
        </div>

        <!-- 技術指標 -->
        <div class="border-t border-gray-200 pt-3 text-xs space-y-1">
          <div class="flex justify-between">
            <span class="text-gray-600">價差</span>
            <span class="font-semibold">¥{{ (ticker.ask - ticker.bid).toFixed(2) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">漲幅度</span>
            <span :class="ticker.change_pct > 0 ? 'text-green-600' : 'text-red-600'" class="font-semibold">
              {{ ticker.change_pct > 0 ? '+' : '' }}{{ ticker.change_pct.toFixed(2) }}%
            </span>
          </div>
        </div>

        <!-- 快速操作 -->
        <div class="mt-4 flex gap-2">
          <button @click="quickBuy(ticker)" class="flex-1 px-2 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-xs font-bold">
            買入
          </button>
          <button @click="quickSell(ticker)" class="flex-1 px-2 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs font-bold">
            賣出
          </button>
        </div>
      </div>
    </div>

    <!-- 排序和篩選選項 -->
    <div class="flex justify-between items-center pt-6 border-t border-gray-200">
      <p class="text-sm text-gray-600">共 {{ tickers.length }} 個股票</p>
      <div class="flex gap-2">
        <button @click="sortBy('change')" class="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-xs font-semibold">
          按漲跌排序
        </button>
        <button @click="sortBy('price')" class="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-xs font-semibold">
          按價格排序
        </button>
      </div>
    </div>

    <!-- 行情說明 -->
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-900">
      <p class="font-semibold mb-2">💡 實時行情提示</p>
      <ul class="list-disc list-inside space-y-1 text-xs">
        <li>行情數據每秒更新一次</li>
        <li>買價(Bid): 市場願意購買的價格</li>
        <li>賣價(Ask): 市場願意出售的價格</li>
        <li>快速操作按鈕將打開下單窗口</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  tickers: {
    type: Array,
    required: true
  }
});

const sortedTickers = ref([...props.tickers]);

const quickBuy = (ticker) => {
  // 觸發下單表單
  window.dispatchEvent(new CustomEvent('quick-order', {
    detail: {
      symbol: ticker.symbol,
      side: 'BUY',
      price: ticker.ask
    }
  }));
};

const quickSell = (ticker) => {
  // 觸發下單表單
  window.dispatchEvent(new CustomEvent('quick-order', {
    detail: {
      symbol: ticker.symbol,
      side: 'SELL',
      price: ticker.bid
    }
  }));
};

const sortBy = (field) => {
  if (field === 'change') {
    sortedTickers.value.sort((a, b) => b.change_pct - a.change_pct);
  } else if (field === 'price') {
    sortedTickers.value.sort((a, b) => b.price - a.price);
  }
};
</script>
