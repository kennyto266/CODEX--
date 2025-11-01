<template>
  <div class="space-y-6 p-6 bg-gray-50 min-h-screen">
    <!-- 標題 -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-4xl font-bold text-gray-900">💱 交易系統</h1>
        <p class="text-gray-600 mt-2">實時交易執行和頭寸管理</p>
      </div>
      <div class="text-right">
        <p class="text-sm text-gray-500">賬戶淨值</p>
        <p class="text-3xl font-bold text-green-600">¥{{ (accountValue / 1000000).toFixed(2) }}M</p>
      </div>
    </div>

    <!-- 標籤頁 -->
    <div class="flex gap-2 border-b border-gray-300">
      <button
        @click="activeTab = 'trade'"
        :class="activeTab === 'trade' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        📝 下單
      </button>
      <button
        @click="activeTab = 'positions'"
        :class="activeTab === 'positions' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        💼 頭寸 ({{ positions.length }})
      </button>
      <button
        @click="activeTab = 'orders'"
        :class="activeTab === 'orders' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        📊 訂單 ({{ orders.length }})
      </button>
      <button
        @click="activeTab = 'history'"
        :class="activeTab === 'history' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        📜 成交記錄
      </button>
      <button
        @click="activeTab = 'ticker'"
        :class="activeTab === 'ticker' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-600'"
        class="px-6 py-3 transition hover:text-blue-600"
      >
        📈 實時行情
      </button>
    </div>

    <!-- 下單 Tab -->
    <div v-if="activeTab === 'trade'" class="space-y-6">
      <OrderForm @submit="submitOrder" />
    </div>

    <!-- 頭寸 Tab -->
    <div v-if="activeTab === 'positions'" class="space-y-6">
      <PositionTable :positions="positions" @close="closePosition" />
    </div>

    <!-- 訂單 Tab -->
    <div v-if="activeTab === 'orders'" class="space-y-6">
      <div class="bg-white rounded-lg shadow-md p-6">
        <h3 class="text-2xl font-bold text-gray-800 mb-6">📊 活躍訂單</h3>

        <!-- 訂單統計 -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div class="bg-blue-50 p-3 rounded-lg text-center">
            <p class="text-sm text-gray-600">待執行</p>
            <p class="text-2xl font-bold text-blue-600">{{ pendingOrders.length }}</p>
          </div>
          <div class="bg-green-50 p-3 rounded-lg text-center">
            <p class="text-sm text-gray-600">部分成交</p>
            <p class="text-2xl font-bold text-green-600">{{ partialOrders.length }}</p>
          </div>
          <div class="bg-red-50 p-3 rounded-lg text-center">
            <p class="text-sm text-gray-600">已取消</p>
            <p class="text-2xl font-bold text-red-600">{{ canceledOrders.length }}</p>
          </div>
          <div class="bg-purple-50 p-3 rounded-lg text-center">
            <p class="text-sm text-gray-600">已成交</p>
            <p class="text-2xl font-bold text-purple-600">{{ filledOrders.length }}</p>
          </div>
        </div>

        <!-- 訂單表格 -->
        <div class="overflow-x-auto">
          <table class="w-full text-sm text-gray-600">
            <thead class="bg-gray-100 border-b-2 border-gray-300">
              <tr>
                <th class="px-4 py-3 text-left">訂單 ID</th>
                <th class="px-4 py-3 text-left">股票</th>
                <th class="px-4 py-3 text-left">方向</th>
                <th class="px-4 py-3 text-right">數量</th>
                <th class="px-4 py-3 text-right">價格</th>
                <th class="px-4 py-3 text-right">成交量</th>
                <th class="px-4 py-3 text-left">狀態</th>
                <th class="px-4 py-3 text-left">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in orders" :key="order.id" class="border-b hover:bg-gray-50">
                <td class="px-4 py-3 font-mono text-xs">{{ order.id.substring(0, 8) }}</td>
                <td class="px-4 py-3 font-bold">{{ order.symbol }}</td>
                <td class="px-4 py-3">
                  <span :class="order.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'" class="px-2 py-1 rounded text-xs font-bold">
                    {{ order.side }}
                  </span>
                </td>
                <td class="px-4 py-3 text-right">{{ order.qty }}</td>
                <td class="px-4 py-3 text-right">¥{{ order.price.toFixed(2) }}</td>
                <td class="px-4 py-3 text-right">{{ order.filled_qty }}/{{ order.qty }}</td>
                <td class="px-4 py-3">
                  <span :class="orderStatusClass(order.status)" class="px-2 py-1 rounded text-xs font-bold">
                    {{ orderStatusLabel(order.status) }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <button v-if="order.status === 'pending' || order.status === 'partial'" @click="cancelOrder(order.id)" class="text-red-600 hover:text-red-800 font-semibold text-xs">
                    取消
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 成交記錄 Tab -->
    <div v-if="activeTab === 'history'" class="space-y-6">
      <TradeHistory :trades="trades" />
    </div>

    <!-- 實時行情 Tab -->
    <div v-if="activeTab === 'ticker'" class="space-y-6">
      <RealTimeTicker :tickers="tickers" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useTradingStore } from '../stores/trading';
import OrderForm from './OrderForm.vue';
import PositionTable from './PositionTable.vue';
import TradeHistory from './TradeHistory.vue';
import RealTimeTicker from './RealTimeTicker.vue';

const tradingStore = useTradingStore();
const activeTab = ref('trade');

// 模擬數據
const accountValue = ref(5000000);
const positions = ref([
  { symbol: '0700.HK', qty: 1000, price: 325.50, current_price: 328.75, pnl: 3250 },
  { symbol: '0388.HK', qty: 500, price: 45.20, current_price: 46.80, pnl: 800 },
  { symbol: '1398.HK', qty: 2000, price: 6.85, current_price: 7.10, pnl: 500 }
]);

const orders = ref([
  { id: 'ORD001', symbol: '0700.HK', side: 'BUY', qty: 500, price: 325.00, filled_qty: 500, status: 'filled', timestamp: new Date(Date.now() - 3600000) },
  { id: 'ORD002', symbol: '0939.HK', side: 'BUY', qty: 1000, price: 12.50, filled_qty: 600, status: 'partial', timestamp: new Date(Date.now() - 1800000) },
  { id: 'ORD003', symbol: '3988.HK', side: 'SELL', qty: 800, price: 5.20, filled_qty: 0, status: 'pending', timestamp: new Date() }
]);

const trades = ref([
  { id: 'TRD001', symbol: '0700.HK', side: 'BUY', qty: 500, price: 325.10, timestamp: new Date(Date.now() - 3600000), fee: 162.55 },
  { id: 'TRD002', symbol: '0388.HK', side: 'BUY', qty: 500, price: 45.20, timestamp: new Date(Date.now() - 1800000), fee: 11.30 }
]);

const tickers = ref([
  { symbol: '0700.HK', price: 328.75, change: 2.15, change_pct: 0.66, bid: 328.50, ask: 328.75 },
  { symbol: '0388.HK', price: 46.80, change: 1.20, change_pct: 2.63, bid: 46.70, ask: 46.90 },
  { symbol: '1398.HK', price: 7.10, change: 0.25, change_pct: 3.65, bid: 7.08, ask: 7.12 },
  { symbol: '0939.HK', price: 12.70, change: -0.05, change_pct: -0.39, bid: 12.65, ask: 12.75 },
  { symbol: '3988.HK', price: 5.15, change: 0.10, change_pct: 1.98, bid: 5.12, ask: 5.18 }
]);

const pendingOrders = computed(() => orders.value.filter(o => o.status === 'pending'));
const partialOrders = computed(() => orders.value.filter(o => o.status === 'partial'));
const canceledOrders = computed(() => orders.value.filter(o => o.status === 'canceled'));
const filledOrders = computed(() => orders.value.filter(o => o.status === 'filled'));

onMounted(() => {
  // 加載交易數據
});

const submitOrder = (orderData) => {
  const newOrder = {
    id: `ORD${Math.floor(Math.random() * 10000).toString().padStart(4, '0')}`,
    ...orderData,
    filled_qty: 0,
    status: 'pending',
    timestamp: new Date()
  };
  orders.value.unshift(newOrder);
};

const cancelOrder = (orderId) => {
  const order = orders.value.find(o => o.id === orderId);
  if (order) {
    order.status = 'canceled';
  }
};

const closePosition = (symbol) => {
  const posIdx = positions.value.findIndex(p => p.symbol === symbol);
  if (posIdx >= 0) {
    positions.value.splice(posIdx, 1);
  }
};

const orderStatusLabel = (status) => {
  if (status === 'pending') return '⏳ 待執行';
  if (status === 'partial') return '⚙️ 部分成交';
  if (status === 'filled') return '✅ 已成交';
  if (status === 'canceled') return '❌ 已取消';
  return status;
};

const orderStatusClass = (status) => {
  if (status === 'pending') return 'bg-yellow-100 text-yellow-800';
  if (status === 'partial') return 'bg-blue-100 text-blue-800';
  if (status === 'filled') return 'bg-green-100 text-green-800';
  if (status === 'canceled') return 'bg-red-100 text-red-800';
  return 'bg-gray-100 text-gray-800';
};
</script>
