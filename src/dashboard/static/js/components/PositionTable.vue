<template>
  <div class="bg-white rounded-lg shadow-md p-6">
    <h3 class="text-2xl font-bold text-gray-800 mb-6">💼 持倉管理</h3>

    <!-- 持倉統計 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-blue-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600 mb-1">持倉總數</p>
        <p class="text-3xl font-bold text-blue-600">{{ positions.length }}</p>
      </div>
      <div class="bg-green-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600 mb-1">總收益</p>
        <p class="text-3xl font-bold text-green-600">¥{{ totalPnL.toFixed(0) }}</p>
      </div>
      <div class="bg-purple-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600 mb-1">總市值</p>
        <p class="text-3xl font-bold text-purple-600">¥{{ totalValue.toFixed(0) }}</p>
      </div>
      <div class="bg-orange-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600 mb-1">收益率</p>
        <p class="text-3xl font-bold text-orange-600">{{ totalReturn.toFixed(2) }}%</p>
      </div>
    </div>

    <!-- 持倉表格 -->
    <div class="overflow-x-auto">
      <table class="w-full text-sm text-gray-600">
        <thead class="bg-gray-100 border-b-2 border-gray-300">
          <tr>
            <th class="px-4 py-3 text-left font-semibold">股票代碼</th>
            <th class="px-4 py-3 text-right font-semibold">持倉數量</th>
            <th class="px-4 py-3 text-right font-semibold">成本價</th>
            <th class="px-4 py-3 text-right font-semibold">當前價</th>
            <th class="px-4 py-3 text-right font-semibold">市值</th>
            <th class="px-4 py-3 text-right font-semibold">收益</th>
            <th class="px-4 py-3 text-right font-semibold">收益率</th>
            <th class="px-4 py-3 text-left font-semibold">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pos in positions" :key="pos.symbol" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 font-bold text-gray-800">{{ pos.symbol }}</td>
            <td class="px-4 py-3 text-right">{{ pos.qty.toLocaleString() }}</td>
            <td class="px-4 py-3 text-right">¥{{ pos.price.toFixed(2) }}</td>
            <td class="px-4 py-3 text-right font-semibold">¥{{ pos.current_price.toFixed(2) }}</td>
            <td class="px-4 py-3 text-right font-semibold">
              ¥{{ (pos.qty * pos.current_price / 10000).toFixed(1) }}W
            </td>
            <td class="px-4 py-3 text-right font-bold" :class="pos.pnl > 0 ? 'text-green-600' : 'text-red-600'">
              {{ pos.pnl > 0 ? '+' : '' }}¥{{ pos.pnl.toFixed(0) }}
            </td>
            <td class="px-4 py-3 text-right font-bold" :class="positionReturn(pos) > 0 ? 'text-green-600' : 'text-red-600'">
              {{ positionReturn(pos) > 0 ? '+' : '' }}{{ positionReturn(pos).toFixed(2) }}%
            </td>
            <td class="px-4 py-3 space-x-2">
              <button
                @click="showCloseModal(pos)"
                class="text-blue-600 hover:text-blue-800 font-semibold text-xs"
              >
                平倉
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 空狀態 -->
    <div v-if="positions.length === 0" class="text-center py-12 text-gray-500">
      <p class="text-lg">📭 沒有持倉</p>
      <p class="text-sm">開始交易以建立持倉</p>
    </div>

    <!-- 平倉對話框 -->
    <div v-if="closePositionModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h4 class="text-lg font-bold text-gray-800 mb-4">確認平倉</h4>
        <p class="text-gray-600 mb-4">
          確定要平倉 {{ closePositionModal.qty }} 股 {{ closePositionModal.symbol }}？
        </p>
        <div class="mb-4 p-3 bg-gray-50 rounded-lg text-sm">
          <p class="flex justify-between mb-2">
            <span>預期收入</span>
            <span class="font-bold">¥{{ (closePositionModal.qty * closePositionModal.current_price).toFixed(0) }}</span>
          </p>
          <p class="flex justify-between">
            <span>預期虧損</span>
            <span class="font-bold text-red-600">¥{{ (closePositionModal.qty * (closePositionModal.current_price - closePositionModal.price)).toFixed(0) }}</span>
          </p>
        </div>
        <div class="flex gap-3">
          <button
            @click="closePositionModal = null"
            class="flex-1 px-4 py-2 bg-gray-300 hover:bg-gray-400 text-gray-800 rounded-md font-semibold"
          >
            取消
          </button>
          <button
            @click="confirmClosePosition"
            class="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-semibold"
          >
            確認平倉
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

const emit = defineEmits(['close']);

const closePositionModal = ref(null);

const totalValue = computed(() => {
  return props.positions.reduce((sum, pos) => sum + (pos.qty * pos.current_price), 0);
});

const totalPnL = computed(() => {
  return props.positions.reduce((sum, pos) => sum + pos.pnl, 0);
});

const totalReturn = computed(() => {
  const costValue = props.positions.reduce((sum, pos) => sum + (pos.qty * pos.price), 0);
  if (costValue === 0) return 0;
  return (totalPnL.value / costValue) * 100;
});

const positionReturn = (pos) => {
  const costValue = pos.qty * pos.price;
  if (costValue === 0) return 0;
  return ((pos.current_price - pos.price) / pos.price) * 100;
};

const showCloseModal = (pos) => {
  closePositionModal.value = pos;
};

const confirmClosePosition = () => {
  if (closePositionModal.value) {
    emit('close', closePositionModal.value.symbol);
    closePositionModal.value = null;
  }
};
</script>
