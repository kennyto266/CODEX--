<template>
  <div class="bg-white rounded-lg shadow-md p-6 space-y-6">
    <h3 class="text-2xl font-bold text-gray-800">🔔 風險告警系統</h3>

    <!-- 告警統計 -->
    <div class="grid grid-cols-4 gap-4">
      <div class="bg-red-50 p-4 rounded-lg border border-red-200 text-center">
        <p class="text-xs text-red-700 font-medium">🔴 關鍵</p>
        <p class="text-2xl font-bold text-red-600">{{ alertStats.critical }}</p>
      </div>
      <div class="bg-orange-50 p-4 rounded-lg border border-orange-200 text-center">
        <p class="text-xs text-orange-700 font-medium">🟠 警告</p>
        <p class="text-2xl font-bold text-orange-600">{{ alertStats.warning }}</p>
      </div>
      <div class="bg-yellow-50 p-4 rounded-lg border border-yellow-200 text-center">
        <p class="text-xs text-yellow-700 font-medium">🟡 注意</p>
        <p class="text-2xl font-bold text-yellow-600">{{ alertStats.info }}</p>
      </div>
      <div class="bg-green-50 p-4 rounded-lg border border-green-200 text-center">
        <p class="text-xs text-green-700 font-medium">✅ 已確認</p>
        <p class="text-2xl font-bold text-green-600">{{ alertStats.acknowledged }}</p>
      </div>
    </div>

    <!-- 告警列表 -->
    <div class="space-y-3">
      <h4 class="text-lg font-bold text-gray-800">未確認告警</h4>

      <div v-if="unacknowledgedAlerts.length === 0" class="text-center py-8 text-gray-500">
        <p class="text-lg">✅ 沒有未確認的告警</p>
      </div>

      <div v-for="alert in unacknowledgedAlerts" :key="alert.id" :class="alertBgClass(alert.level)" class="p-4 rounded-lg border-l-4">
        <div class="flex justify-between items-start">
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <span class="font-bold">{{ alertIcon(alert.level) }} {{ alert.level.toUpperCase() }}</span>
              <span class="text-xs text-gray-500">{{ formatTime(alert.timestamp) }}</span>
            </div>
            <p class="mt-2 text-sm font-semibold">{{ alert.message }}</p>
          </div>
          <button
            @click="$emit('acknowledge', alert.id)"
            class="ml-4 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold whitespace-nowrap"
          >
            確認
          </button>
        </div>
      </div>

      <!-- 已確認告警 -->
      <div v-if="acknowledgedAlerts.length > 0" class="mt-6">
        <h4 class="text-lg font-bold text-gray-800 mb-3">已確認告警</h4>
        <div v-for="alert in acknowledgedAlerts" :key="alert.id" class="p-3 rounded-lg bg-gray-50 border border-gray-200 text-sm text-gray-600 line-through">
          <span class="font-semibold">{{ alert.message }}</span>
          <span class="text-xs text-gray-500 ml-2">{{ formatTime(alert.timestamp) }}</span>
        </div>
      </div>
    </div>

    <!-- 告警規則配置 -->
    <div class="border-t border-gray-200 pt-6">
      <h4 class="text-lg font-bold text-gray-800 mb-4">⚙️ 告警規則</h4>

      <div class="space-y-3">
        <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
          <div>
            <p class="font-semibold text-gray-800">投資組合 VaR 超過 95% 限制</p>
            <p class="text-xs text-gray-500">當 VaR > ¥500W 時觸發</p>
          </div>
          <input type="checkbox" checked class="w-5 h-5 text-blue-600" />
        </div>

        <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
          <div>
            <p class="font-semibold text-gray-800">單個頭寸風險過高</p>
            <p class="text-xs text-gray-500">當單頭 VaR > ¥50W 時觸發</p>
          </div>
          <input type="checkbox" checked class="w-5 h-5 text-blue-600" />
        </div>

        <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
          <div>
            <p class="font-semibold text-gray-800">杠桿率超過閾值</p>
            <p class="text-xs text-gray-500">當杠桿 > 2.8x 時觸發</p>
          </div>
          <input type="checkbox" checked class="w-5 h-5 text-blue-600" />
        </div>

        <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
          <div>
            <p class="font-semibold text-gray-800">持倉相關性異常</p>
            <p class="text-xs text-gray-500">當相關性 > 0.8 時觸發</p>
          </div>
          <input type="checkbox" class="w-5 h-5 text-blue-600" />
        </div>
      </div>

      <button class="w-full mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-semibold">
        💾 保存設置
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  alerts: {
    type: Array,
    required: true
  }
});

defineEmits(['acknowledge']);

const alertStats = computed(() => ({
  critical: props.alerts.filter(a => a.level === 'critical').length,
  warning: props.alerts.filter(a => a.level === 'warning').length,
  info: props.alerts.filter(a => a.level === 'info').length,
  acknowledged: props.alerts.filter(a => a.acknowledged).length
}));

const unacknowledgedAlerts = computed(() =>
  props.alerts.filter(a => !a.acknowledged)
);

const acknowledgedAlerts = computed(() =>
  props.alerts.filter(a => a.acknowledged)
);

const alertBgClass = (level) => {
  if (level === 'critical') return 'bg-red-50 border-red-500 text-red-900';
  if (level === 'warning') return 'bg-orange-50 border-orange-500 text-orange-900';
  if (level === 'info') return 'bg-yellow-50 border-yellow-500 text-yellow-900';
  return 'bg-gray-50 border-gray-500 text-gray-900';
};

const alertIcon = (level) => {
  if (level === 'critical') return '🔴';
  if (level === 'warning') return '🟠';
  if (level === 'info') return '🟡';
  return '⚪';
};

const formatTime = (timestamp) => {
  if (!timestamp) return '未知';
  const date = new Date(timestamp);
  const now = new Date();
  const diff = (now - date) / 1000; // 秒

  if (diff < 60) return '剛剛';
  if (diff < 3600) return `${Math.floor(diff / 60)} 分鐘前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小時前`;
  return date.toLocaleString();
};
</script>
