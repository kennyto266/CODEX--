<template>
  <div class="space-y-6">
    <!-- 日誌篩選和操作 -->
    <div class="bg-white rounded-lg shadow-md p-6">
      <h3 class="text-2xl font-bold mb-4 text-gray-800">📜 Agent 日誌</h3>

      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        <!-- 日誌級別篩選 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">日誌級別</label>
          <select
            v-model="filterLevel"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部</option>
            <option value="DEBUG">🔵 DEBUG</option>
            <option value="INFO">🟢 INFO</option>
            <option value="WARNING">🟡 WARNING</option>
            <option value="ERROR">🔴 ERROR</option>
          </select>
        </div>

        <!-- 搜索關鍵詞 -->
        <div class="md:col-span-2">
          <label class="block text-sm font-medium text-gray-700 mb-2">搜索</label>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索日誌內容..."
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- 刷新按鈕 -->
        <div class="flex items-end">
          <button
            @click="refreshLogs"
            :disabled="isLoading"
            class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded-md transition"
          >
            <span v-if="!isLoading">🔄 刷新</span>
            <span v-else>⏳ 刷新中...</span>
          </button>
        </div>
      </div>

      <!-- 日誌統計 -->
      <div class="grid grid-cols-4 gap-2 mb-4">
        <div class="bg-blue-50 p-3 rounded text-center">
          <p class="text-xs text-gray-600">DEBUG</p>
          <p class="text-lg font-bold text-blue-600">{{ logStats.DEBUG }}</p>
        </div>
        <div class="bg-green-50 p-3 rounded text-center">
          <p class="text-xs text-gray-600">INFO</p>
          <p class="text-lg font-bold text-green-600">{{ logStats.INFO }}</p>
        </div>
        <div class="bg-yellow-50 p-3 rounded text-center">
          <p class="text-xs text-gray-600">WARNING</p>
          <p class="text-lg font-bold text-yellow-600">{{ logStats.WARNING }}</p>
        </div>
        <div class="bg-red-50 p-3 rounded text-center">
          <p class="text-xs text-gray-600">ERROR</p>
          <p class="text-lg font-bold text-red-600">{{ logStats.ERROR }}</p>
        </div>
      </div>
    </div>

    <!-- 日誌列表 -->
    <div class="bg-white rounded-lg shadow-md p-6">
      <div class="space-y-2 max-h-96 overflow-y-auto">
        <div
          v-for="(log, idx) in filteredLogs"
          :key="idx"
          :class="logRowClass(log.level)"
          class="p-3 rounded border-l-4 font-mono text-xs"
        >
          <div class="flex justify-between items-start">
            <div class="flex-1">
              <span class="font-bold">{{ log.level }}</span>
              <span class="text-gray-600 ml-2">{{ log.timestamp }}</span>
              <p class="text-gray-700 mt-1">{{ log.message }}</p>
            </div>
            <span v-if="log.code" class="bg-gray-200 px-2 py-1 rounded text-xs font-semibold">
              {{ log.code }}
            </span>
          </div>
        </div>

        <!-- 無日誌提示 -->
        <div v-if="filteredLogs.length === 0" class="text-center py-8 text-gray-500">
          <p class="text-lg">📭 沒有日誌</p>
        </div>
      </div>

      <!-- 分頁 -->
      <div v-if="totalLogs > logsPerPage" class="mt-4 flex justify-between items-center">
        <p class="text-sm text-gray-600">
          顯示 {{ currentPage * logsPerPage + 1 }} - {{ Math.min((currentPage + 1) * logsPerPage, totalLogs) }}
          / 共 {{ totalLogs }} 條
        </p>
        <div class="flex gap-2">
          <button
            @click="previousPage"
            :disabled="currentPage === 0"
            class="px-3 py-1 bg-gray-300 hover:bg-gray-400 disabled:bg-gray-200 rounded text-sm"
          >
            ← 上一頁
          </button>
          <button
            @click="nextPage"
            :disabled="(currentPage + 1) * logsPerPage >= totalLogs"
            class="px-3 py-1 bg-gray-300 hover:bg-gray-400 disabled:bg-gray-200 rounded text-sm"
          >
            下一頁 →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';

const props = defineProps({
  agent: Object
});

const isLoading = ref(false);
const filterLevel = ref('');
const searchQuery = ref('');
const currentPage = ref(0);
const logsPerPage = 50;

// 模擬日誌數據
const allLogs = ref([]);

// 在實際應用中，這些日誌來自 API
const mockLogs = () => {
  const levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR'];
  const messages = [
    '初始化 Agent 完成',
    '開始處理任務 #123',
    '任務 #123 完成，耗時 245ms',
    '檢測到高 CPU 使用率: 85%',
    '無法連接到數據源',
    '自動重試連接...',
    '連接恢復成功',
    '收到新的策略更新',
    '應用策略更新',
    '執行回測任務',
    '回測完成，收益率 15.2%',
    '發送報告...'
  ];

  const logs = [];
  for (let i = 0; i < 200; i++) {
    logs.push({
      level: levels[Math.floor(Math.random() * levels.length)],
      timestamp: new Date(Date.now() - Math.random() * 3600000).toLocaleTimeString(),
      message: messages[Math.floor(Math.random() * messages.length)] + ` [${i}]`,
      code: Math.random() > 0.7 ? `CODE_${Math.floor(Math.random() * 9000) + 1000}` : null
    });
  }
  return logs.reverse();
};

onMounted(() => {
  allLogs.value = mockLogs();
});

const filteredLogs = computed(() => {
  let filtered = allLogs.value;

  // 按級別篩選
  if (filterLevel.value) {
    filtered = filtered.filter(log => log.level === filterLevel.value);
  }

  // 按搜索詞篩選
  if (searchQuery.value) {
    filtered = filtered.filter(log =>
      log.message.toLowerCase().includes(searchQuery.value.toLowerCase())
    );
  }

  return filtered;
});

const totalLogs = computed(() => filteredLogs.value.length);

const paginatedLogs = computed(() => {
  const start = currentPage.value * logsPerPage;
  const end = start + logsPerPage;
  return filteredLogs.value.slice(start, end);
});

const logStats = computed(() => {
  return {
    DEBUG: allLogs.value.filter(l => l.level === 'DEBUG').length,
    INFO: allLogs.value.filter(l => l.level === 'INFO').length,
    WARNING: allLogs.value.filter(l => l.level === 'WARNING').length,
    ERROR: allLogs.value.filter(l => l.level === 'ERROR').length
  };
});

const logRowClass = (level) => {
  if (level === 'DEBUG') return 'bg-blue-50 border-blue-500 text-blue-900';
  if (level === 'INFO') return 'bg-green-50 border-green-500 text-green-900';
  if (level === 'WARNING') return 'bg-yellow-50 border-yellow-500 text-yellow-900';
  if (level === 'ERROR') return 'bg-red-50 border-red-500 text-red-900';
  return 'bg-gray-50 border-gray-500 text-gray-900';
};

const refreshLogs = async () => {
  isLoading.value = true;
  try {
    // 在實際應用中，這裡會調用 API 獲取最新日誌
    // const response = await fetch(`/api/agents/${props.agent.id}/logs`);
    // allLogs.value = await response.json();

    // 模擬刷新
    await new Promise(r => setTimeout(r, 500));
    allLogs.value = mockLogs();
    currentPage.value = 0;
  } finally {
    isLoading.value = false;
  }
};

const previousPage = () => {
  if (currentPage.value > 0) {
    currentPage.value--;
  }
};

const nextPage = () => {
  if ((currentPage.value + 1) * logsPerPage < totalLogs.value) {
    currentPage.value++;
  }
};

// 當 agent 變更時重新加載日誌
watch(() => props.agent?.id, () => {
  allLogs.value = mockLogs();
  currentPage.value = 0;
}, { immediate: true });

// 重新計算分頁日誌
const displayLogs = paginatedLogs;
</script>
