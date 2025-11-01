import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useTradingStore = defineStore('trading', () => {
  const positions = ref([]);
  const orders = ref([]);
  const trades = ref([]);
  const portfolio = ref({ value: 0, cash: 0, returns: 0 });
  const isLoading = ref(false);

  const totalPositionValue = computed(() => {
    return positions.value.reduce((sum, p) => sum + p.position_value, 0);
  });

  const totalUnrealizedPnL = computed(() => {
    return positions.value.reduce((sum, p) => sum + p.unrealized_pnl, 0);
  });

  async function fetchPositions() {
    try {
      const response = await fetch('/api/trading/positions');
      positions.value = await response.json();
    } catch (err) {
      console.error('獲取頭寸失敗:', err);
    }
  }

  async function fetchOrders() {
    try {
      const response = await fetch('/api/trading/orders');
      orders.value = await response.json();
    } catch (err) {
      console.error('獲取訂單失敗:', err);
    }
  }

  async function fetchTrades() {
    try {
      const response = await fetch('/api/trading/trades');
      trades.value = await response.json();
    } catch (err) {
      console.error('獲取成交記錄失敗:', err);
    }
  }

  async function placeOrder(symbol, orderType, quantity, price) {
    try {
      const response = await fetch('/api/trading/order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, order_type: orderType, quantity, price })
      });
      const result = await response.json();
      if (response.ok) {
        await fetchPositions();
        await fetchOrders();
      }
      return result;
    } catch (err) {
      console.error('下單失敗:', err);
      throw err;
    }
  }

  return {
    positions,
    orders,
    trades,
    portfolio,
    isLoading,
    totalPositionValue,
    totalUnrealizedPnL,
    fetchPositions,
    fetchOrders,
    fetchTrades,
    placeOrder
  };
});
