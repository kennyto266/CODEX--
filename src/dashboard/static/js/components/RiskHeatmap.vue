<template>
  <div class="bg-white rounded-lg shadow-md p-6 space-y-6">
    <h3 class="text-2xl font-bold text-gray-800">🔥 相關性矩陣熱力圖</h3>

    <!-- 說明 -->
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <p class="text-sm text-blue-900">
        📌 <strong>相關性矩陣:</strong> 顯示各資產間的相關係數。
        深紅色表示高度正相關 (1.0)，深藍色表示高度負相關 (-1.0)，白色表示無相關 (0.0)。
      </p>
    </div>

    <!-- 熱力圖 -->
    <div class="overflow-x-auto">
      <div class="inline-block min-w-full">
        <!-- 列標籤 -->
        <div class="flex">
          <div class="w-24"></div>
          <div v-for="symbol in heatmapData.symbols" :key="symbol" class="w-20 h-12 flex items-center justify-center font-bold text-xs text-gray-800 bg-gray-100">
            {{ symbol }}
          </div>
        </div>

        <!-- 熱力圖行 -->
        <div v-for="(row, rowIdx) in heatmapData.correlations" :key="rowIdx" class="flex">
          <!-- 行標籤 -->
          <div class="w-24 h-12 flex items-center justify-center font-bold text-xs text-gray-800 bg-gray-100">
            {{ heatmapData.symbols[rowIdx] }}
          </div>

          <!-- 熱力圖單元格 -->
          <div v-for="(value, colIdx) in row" :key="colIdx" :style="{ backgroundColor: getHeatmapColor(value) }" class="w-20 h-12 flex items-center justify-center font-bold text-xs text-white border border-gray-200 cursor-pointer hover:opacity-80">
            {{ value.toFixed(2) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 顏色標度 -->
    <div class="mt-6">
      <p class="text-sm font-semibold text-gray-800 mb-2">顏色標度:</p>
      <div class="flex items-center justify-between text-xs">
        <div class="flex items-center gap-2">
          <div class="w-8 h-4 rounded" style="background-color: #1e3a8a;"></div>
          <span>-1.0 (負相關)</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-8 h-4 rounded" style="background-color: #f5f5f5;"></div>
          <span>0.0 (無相關)</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-8 h-4 rounded" style="background-color: #7f1d1d;"></div>
          <span>+1.0 (正相關)</span>
        </div>
      </div>
    </div>

    <!-- 相關性分析 -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
      <!-- 高相關對 -->
      <div class="border border-gray-200 rounded-lg p-4">
        <h4 class="text-lg font-bold text-gray-800 mb-3">🔴 高相關對 (> 0.7)</h4>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between p-2 bg-red-50 rounded">
            <span class="text-gray-700">0700.HK ↔ 0388.HK</span>
            <span class="font-bold text-red-600">0.85</span>
          </div>
          <div class="flex justify-between p-2 bg-red-50 rounded">
            <span class="text-gray-700">0700.HK ↔ 1398.HK</span>
            <span class="font-bold text-red-600">0.78</span>
          </div>
          <div class="flex justify-between p-2 bg-red-50 rounded">
            <span class="text-gray-700">1398.HK ↔ 0939.HK</span>
            <span class="font-bold text-red-600">0.75</span>
          </div>
          <p class="text-xs text-red-700 mt-2">⚠️ 這些資產多樣化不足，需要增加對沖</p>
        </div>
      </div>

      <!-- 負相關對 -->
      <div class="border border-gray-200 rounded-lg p-4">
        <h4 class="text-lg font-bold text-gray-800 mb-3">🟢 負相關對 (< 0)</h4>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between p-2 bg-green-50 rounded">
            <span class="text-gray-700">GOLD ↔ 0700.HK</span>
            <span class="font-bold text-green-600">-0.15</span>
          </div>
          <div class="flex justify-between p-2 bg-green-50 rounded">
            <span class="text-gray-700">GOLD ↔ 0388.HK</span>
            <span class="font-bold text-green-600">-0.12</span>
          </div>
          <div class="flex justify-between p-2 bg-green-50 rounded">
            <span class="text-gray-700">GOLD ↔ 1398.HK</span>
            <span class="font-bold text-green-600">-0.18</span>
          </div>
          <p class="text-xs text-green-700 mt-2">✅ 黃金提供良好的對沖效果</p>
        </div>
      </div>
    </div>

    <!-- 風險啟示 -->
    <div class="border-t border-gray-200 pt-6">
      <h4 class="text-lg font-bold text-gray-800 mb-4">💡 風險啟示</h4>

      <div class="space-y-3">
        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <p class="text-sm font-semibold text-yellow-900">⚠️ 香港股票相關性過高</p>
          <p class="text-xs text-yellow-800 mt-1">0700、0388、1398 的相關係數都超過 0.7，表明這些股票同向波動，多樣化不足。建議增加不同行業或資產類別的持倉。</p>
        </div>

        <div class="bg-green-50 border border-green-200 rounded-lg p-3">
          <p class="text-sm font-semibold text-green-900">✅ 黃金提供有效對沖</p>
          <p class="text-xs text-green-800 mt-1">黃金與股票呈負相關（-0.15 ~ -0.18），在股票下跌時可能上漲，提供了良好的風險對沖。建議保持目前的黃金頭寸。</p>
        </div>

        <div class="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p class="text-sm font-semibold text-blue-900">💭 建議的多樣化策略</p>
          <p class="text-xs text-blue-800 mt-1">
            • 增加美元敞口以應對人民幣貶值風險<br>
            • 考慮減少單個股票的敞口<br>
            • 增加債券或其他低相關資產<br>
            • 定期重新平衡投資組合以保持目標風險水平
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  heatmapData: {
    type: Object,
    required: true
  }
});

const getHeatmapColor = (value) => {
  // 從深藍 (-1) 到白色 (0) 到深紅 (+1)
  if (value < 0) {
    // 負相關：從白色到深藍
    const intensity = Math.abs(value);
    const blue = Math.floor(30 + intensity * 70); // 30 ~ 100
    const red = Math.floor(245 * (1 - intensity));
    const green = Math.floor(245 * (1 - intensity));
    return `rgb(${red}, ${green}, ${blue})`;
  } else if (value > 0) {
    // 正相關：從白色到深紅
    const red = Math.floor(245 - value * 200); // 245 ~ 45
    const green = Math.floor(245 * (1 - value * 0.8));
    const blue = Math.floor(245 * (1 - value * 0.8));
    return `rgb(${red}, ${green}, ${blue})`;
  } else {
    // 零相關
    return 'rgb(245, 245, 245)';
  }
};
</script>
