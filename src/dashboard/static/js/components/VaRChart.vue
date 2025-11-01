<template>
  <div class="bg-white rounded-lg shadow-md p-6 space-y-6">
    <h3 class="text-2xl font-bold text-gray-800">📈 風險值 (VaR) 分析</h3>

    <!-- VaR 概念說明 -->
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <p class="text-sm text-blue-900">
        📌 <strong>Value at Risk (VaR):</strong> 在給定置信度和時間horizon下，投資組合可能遭受的最大損失。
        <br>
        • <strong>VaR 95%:</strong> 95% 概率下，1 天最多虧損的額度
        <br>
        • <strong>VaR 99%:</strong> 99% 概率下，1 天最多虧損的額度
      </p>
    </div>

    <!-- VaR 趨勢 -->
    <div class="border border-gray-200 rounded-lg p-4">
      <h4 class="text-lg font-bold text-gray-800 mb-4">📊 VaR 趨勢圖</h4>
      <div class="bg-gray-50 p-4 rounded-lg h-64 flex items-center justify-center text-gray-500">
        <div class="text-center">
          <p class="text-lg font-bold">📈 圖表展示</p>
          <p class="text-sm">(需要集成 Chart.js/ECharts)</p>
          <p class="text-xs text-gray-400 mt-2">6 天 VaR 95% 和 VaR 99% 趨勢</p>
        </div>
      </div>

      <!-- 數據表格 -->
      <div class="mt-4">
        <h5 class="font-semibold text-gray-800 mb-3">數據詳情</h5>
        <div class="overflow-x-auto">
          <table class="w-full text-sm text-gray-600">
            <thead class="bg-gray-100 border-b border-gray-300">
              <tr>
                <th class="px-4 py-2 text-left">日期</th>
                <th class="px-4 py-2 text-right">VaR 95%</th>
                <th class="px-4 py-2 text-right">VaR 99%</th>
                <th class="px-4 py-2 text-right">變化幅度</th>
                <th class="px-4 py-2 text-left">狀態</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(date, idx) in varData.dates" :key="date" class="border-b hover:bg-gray-50">
                <td class="px-4 py-2">{{ date }}</td>
                <td class="px-4 py-2 text-right font-semibold">
                  ¥{{ (varData.daily_var_95[idx] / 10000).toFixed(0) }}W
                </td>
                <td class="px-4 py-2 text-right font-semibold">
                  ¥{{ (varData.daily_var_99[idx] / 10000).toFixed(0) }}W
                </td>
                <td class="px-4 py-2 text-right" :class="varChangeColor(idx)">
                  {{ varChange(idx) > 0 ? '+' : '' }}{{ varChange(idx).toFixed(1) }}%
                </td>
                <td class="px-4 py-2">
                  <span :class="varTrendBadge(idx)" class="px-2 py-1 rounded-full text-xs font-bold">
                    {{ varTrend(idx) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- VaR 成分分解 -->
    <div class="border border-gray-200 rounded-lg p-4">
      <h4 class="text-lg font-bold text-gray-800 mb-4">🔍 VaR 成分分析</h4>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- VaR by Asset Class -->
        <div class="space-y-3">
          <h5 class="font-semibold text-gray-800 mb-2">按資產類別</h5>
          <div class="space-y-2 text-sm">
            <div>
              <div class="flex justify-between mb-1">
                <span class="text-gray-600">香港股票</span>
                <span class="font-bold">¥280W (62%)</span>
              </div>
              <div class="w-full bg-gray-300 rounded-full h-2">
                <div class="w-3/5 bg-blue-600 h-2 rounded-full"></div>
              </div>
            </div>
            <div>
              <div class="flex justify-between mb-1">
                <span class="text-gray-600">黃金現貨</span>
                <span class="font-bold">¥100W (22%)</span>
              </div>
              <div class="w-full bg-gray-300 rounded-full h-2">
                <div class="w-1/4 bg-yellow-600 h-2 rounded-full"></div>
              </div>
            </div>
            <div>
              <div class="flex justify-between mb-1">
                <span class="text-gray-600">現金/其他</span>
                <span class="font-bold">¥70W (16%)</span>
              </div>
              <div class="w-full bg-gray-300 rounded-full h-2">
                <div class="w-1/6 bg-green-600 h-2 rounded-full"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- VaR by Risk Factor -->
        <div class="space-y-3">
          <h5 class="font-semibold text-gray-800 mb-2">按風險因子</h5>
          <div class="space-y-2 text-sm">
            <div>
              <div class="flex justify-between mb-1">
                <span class="text-gray-600">市場風險 (Delta)</span>
                <span class="font-bold">¥350W (78%)</span>
              </div>
              <div class="w-full bg-gray-300 rounded-full h-2">
                <div class="w-4/5 bg-red-600 h-2 rounded-full"></div>
              </div>
            </div>
            <div>
              <div class="flex justify-between mb-1">
                <span class="text-gray-600">波動率風險 (Vega)</span>
                <span class="font-bold">¥80W (18%)</span>
              </div>
              <div class="w-full bg-gray-300 rounded-full h-2">
                <div class="w-1/5 bg-orange-600 h-2 rounded-full"></div>
              </div>
            </div>
            <div>
              <div class="flex justify-between mb-1">
                <span class="text-gray-600">其他</span>
                <span class="font-bold">¥20W (4%)</span>
              </div>
              <div class="w-full bg-gray-300 rounded-full h-2">
                <div class="w-1/25 bg-gray-600 h-2 rounded-full"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- VaR 壓力測試 -->
    <div class="border border-gray-200 rounded-lg p-4">
      <h4 class="text-lg font-bold text-gray-800 mb-4">🔬 壓力測試</h4>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <!-- 場景 1 -->
        <div class="bg-red-50 p-3 rounded-lg border border-red-200">
          <h5 class="font-bold text-red-900 mb-2">股市跌 10%</h5>
          <p class="text-red-800 text-lg font-bold">-¥520W</p>
          <p class="text-red-700 text-xs mt-1">預期損失</p>
          <div class="mt-2 pt-2 border-t border-red-300">
            <p class="text-xs text-red-700">觸發止損: 是</p>
          </div>
        </div>

        <!-- 場景 2 -->
        <div class="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
          <h5 class="font-bold text-yellow-900 mb-2">波動率 +50%</h5>
          <p class="text-yellow-800 text-lg font-bold">-¥120W</p>
          <p class="text-yellow-700 text-xs mt-1">預期損失</p>
          <div class="mt-2 pt-2 border-t border-yellow-300">
            <p class="text-xs text-yellow-700">觸發止損: 否</p>
          </div>
        </div>

        <!-- 場景 3 -->
        <div class="bg-orange-50 p-3 rounded-lg border border-orange-200">
          <h5 class="font-bold text-orange-900 mb-2">利率 +200bps</h5>
          <p class="text-orange-800 text-lg font-bold">-¥280W</p>
          <p class="text-orange-700 text-xs mt-1">預期損失</p>
          <div class="mt-2 pt-2 border-t border-orange-300">
            <p class="text-xs text-orange-700">觸發止損: 是</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  varData: {
    type: Object,
    required: true
  }
});

const varChange = (idx) => {
  if (idx === 0) return 0;
  const prev = props.varData.daily_var_95[idx - 1];
  const curr = props.varData.daily_var_95[idx];
  return ((curr - prev) / prev) * 100;
};

const varChangeColor = (idx) => {
  const change = varChange(idx);
  if (change > 2) return 'text-red-600 font-bold';
  if (change < -2) return 'text-green-600 font-bold';
  return 'text-gray-600';
};

const varTrend = (idx) => {
  const change = varChange(idx);
  if (change > 2) return '↑ 上升';
  if (change < -2) return '↓ 下降';
  return '→ 平穩';
};

const varTrendBadge = (idx) => {
  const change = varChange(idx);
  if (change > 2) return 'bg-red-100 text-red-800';
  if (change < -2) return 'bg-green-100 text-green-800';
  return 'bg-gray-100 text-gray-800';
};
</script>
