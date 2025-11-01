<template>
  <div class="bg-white rounded-lg shadow-md p-6 space-y-6">
    <h3 class="text-2xl font-bold text-gray-800">📜 成交記錄</h3>

    <!-- 篩選和搜索 -->
    <div class="flex gap-4">
      <input
        v-model="searchSymbol"
        type="text"
        placeholder="搜索股票代碼..."
        class="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <select
        v-model="filterSide"
        class="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">全部交易</option>
        <option value="BUY">買進</option>
        <option value="SELL">賣出</option>
      </select>
    </div>

    <!-- 成交統計 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-blue-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600">總成交筆數</p>
        <p class="text-2xl font-bold text-blue-600">{{ trades.length }}</p>
      </div>
      <div class="bg-green-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600">買進成交</p>
        <p class="text-2xl font-bold text-green-600">{{ buyTrades.length }}</p>
      </div>
      <div class="bg-red-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600">賣出成交</p>
        <p class="text-2xl font-bold text-red-600">{{ sellTrades.length }}</p>
      </div>
      <div class="bg-purple-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600">總費用</p>
        <p class="text-2xl font-bold text-purple-600">¥{{ totalFee.toFixed(0) }}</p>
      </div>
    </div>

    <!-- 成交表格 -->
    <div class="overflow-x-auto">
      <table class="w-full text-sm text-gray-600">
        <thead class="bg-gray-100 border-b-2 border-gray-300">
          <tr>
            <th class="px-4 py-3 text-left font-semibold">交易 ID</th>
            <th class="px-4 py-3 text-left font-semibold">股票代碼</th>
            <th class="px-4 py-3 text-left font-semibold">方向</th>
            <th class="px-4 py-3 text-right font-semibold">數量</th>
            <th class="px-4 py-3 text-right font-semibold">成交價</th>
            <th class="px-4 py-3 text-right font-semibold">總額</th>
            <th class="px-4 py-3 text-right font-semibold">費用</th>
            <th class="px-4 py-3 text-left font-semibold">成交時間</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="trade in filteredTrades" :key="trade.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 font-mono text-xs">{{ trade.id.substring(0, 8) }}</td>
            <td class="px-4 py-3 font-bold text-gray-800">{{ trade.symbol }}</td>
            <td class="px-4 py-3">
              <span :class="trade.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'" class="px-2 py-1 rounded text-xs font-bold">
                {{ trade.side }}
              </span>
            </td>
            <td class="px-4 py-3 text-right">{{ trade.qty.toLocaleString() }}</td>
            <td class="px-4 py-3 text-right font-semibold">¥{{ trade.price.toFixed(2) }}</td>
            <td class="px-4 py-3 text-right font-semibold">
              ¥{{ (trade.qty * trade.price).toFixed(0) }}
            </td>
            <td class="px-4 py-3 text-right text-orange-600">¥{{ trade.fee.toFixed(2) }}</td>
            <td class="px-4 py-3 text-xs">{{ formatTime(trade.timestamp) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 空狀態 -->
    <div v-if="filteredTrades.length === 0" class="text-center py-12 text-gray-500">
      <p class="text-lg">📭 沒有成交記錄</p>
      <p class="text-sm">開始交易後會顯示成交記錄</p>
    </div>

    <!-- 分頁 -->
    <div v-if="trades.length > 10" class="flex justify-between items-center mt-4">
      <p class="text-sm text-gray-600">顯示 {{ trades.length }} 條記錄</p>
      <div class="flex gap-2">
        <button class="px-3 py-1 bg-gray-300 hover:bg-gray-400 rounded text-sm">← 上一頁</button>
        <button class="px-3 py-1 bg-gray-300 hover:bg-gray-400 rounded text-sm">下一頁 →</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  trades: {
    type: Array,
    required: true
  }
});

const searchSymbol = ref('');
const filterSide = ref('');

const filteredTrades = computed(() => {
  return props.trades.filter(trade => {
    const matchesSymbol = !searchSymbol.value ||
      trade.symbol.toLowerCase().includes(searchSymbol.value.toLowerCase());
    const matchesSide = !filterSide.value || trade.side === filterSide.value;
    return matchesSymbol && matchesSide;
  });
});

const buyTrades = computed(() => {
  return props.trades.filter(t => t.side === 'BUY');
});

const sellTrades = computed(() => {
  return props.trades.filter(t => t.side === 'SELL');
});

const totalFee = computed(() => {
  return props.trades.reduce((sum, t) => sum + (t.fee || 0), 0);
});

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleString();
};
</script>
