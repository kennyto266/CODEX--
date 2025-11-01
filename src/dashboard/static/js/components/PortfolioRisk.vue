<template>
  <div class="space-y-6">
    <!-- 核心風險指標 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- 投資組合總值 -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <p class="text-gray-600 text-sm font-medium mb-2">投資組合總值</p>
        <p class="text-3xl font-bold text-blue-600">
          ¥{{ (riskData.portfolio_value / 1000000).toFixed(1) }}M
        </p>
      </div>

      <!-- VaR 95% -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <p class="text-gray-600 text-sm font-medium mb-2">VaR 95%</p>
        <p class="text-3xl font-bold text-orange-600">
          ¥{{ (riskData.total_var_95 / 10000).toFixed(0) }}W
        </p>
        <p class="text-xs text-gray-500 mt-2">
          {{ ((riskData.total_var_95 / riskData.portfolio_value) * 100).toFixed(2) }}% 比例
        </p>
      </div>

      <!-- VaR 99% -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <p class="text-gray-600 text-sm font-medium mb-2">VaR 99%</p>
        <p class="text-3xl font-bold text-red-600">
          ¥{{ (riskData.total_var_99 / 10000).toFixed(0) }}W
        </p>
        <p class="text-xs text-gray-500 mt-2">
          {{ ((riskData.total_var_99 / riskData.portfolio_value) * 100).toFixed(2) }}% 比例
        </p>
      </div>

      <!-- 最大回撤 -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <p class="text-gray-600 text-sm font-medium mb-2">最大回撤</p>
        <p class="text-3xl font-bold text-red-600">{{ riskData.max_drawdown_pct.toFixed(1) }}%</p>
        <p class="text-xs text-gray-500 mt-2">當前水位</p>
      </div>
    </div>

    <!-- 杠桿率和風險指標 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- 杠桿率 -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h4 class="text-lg font-bold text-gray-800 mb-4">📊 杠桿率</h4>
        <div class="space-y-3">
          <div>
            <div class="flex justify-between mb-2">
              <span class="text-sm text-gray-600">目前杠桿</span>
              <span class="font-bold" :class="leverageColor(riskData.current_leverage)">
                {{ riskData.current_leverage.toFixed(2) }}x
              </span>
            </div>
            <div class="w-full bg-gray-300 rounded-full h-3">
              <div
                :style="{ width: (riskData.current_leverage / riskData.max_leverage) * 100 + '%' }"
                :class="leverageBarColor(riskData.current_leverage)"
                class="h-3 rounded-full"
              ></div>
            </div>
          </div>
          <div class="text-xs text-gray-500">
            最大允許: {{ riskData.max_leverage.toFixed(2) }}x
          </div>
        </div>
      </div>

      <!-- 相關性分析 -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h4 class="text-lg font-bold text-gray-800 mb-4">🔗 相關性分析</h4>
        <div class="space-y-3">
          <div class="flex justify-between text-sm">
            <span class="text-gray-600">平均相關性</span>
            <span class="font-bold text-gray-800">{{ riskData.correlation_avg.toFixed(3) }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-gray-600">風險狀態</span>
            <span :class="correlationStatus(riskData.correlation_avg)" class="font-bold">
              {{ correlationLabel(riskData.correlation_avg) }}
            </span>
          </div>
          <div class="text-xs text-gray-500 mt-2">
            {{
              riskData.correlation_avg > 0.7
                ? '持倉高度相關，多樣化不足'
                : riskData.correlation_avg < 0.3
                  ? '持倉相關性低，分散度良好'
                  : '持倉適度相關，風險均衡'
            }}
          </div>
        </div>
      </div>

      <!-- 風險頭寸統計 -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h4 class="text-lg font-bold text-gray-800 mb-4">⚠️ 風險頭寸</h4>
        <div class="space-y-3">
          <div class="flex justify-between text-sm">
            <span class="text-gray-600">高風險頭寸</span>
            <span class="font-bold text-red-600">{{ riskData.positions_at_risk }}</span>
          </div>
          <div class="text-xs text-gray-500 mt-2">
            需要監控的頭寸數
          </div>
          <button class="w-full mt-3 px-3 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded text-xs font-semibold">
            查看詳情 →
          </button>
        </div>
      </div>
    </div>

    <!-- 風險詳細表格 -->
    <div class="bg-white rounded-lg shadow-md p-6">
      <h4 class="text-xl font-bold mb-4 text-gray-800">📋 風險因子詳細</h4>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- 市場風險 -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h5 class="font-bold text-gray-800 mb-3">📈 市場風險</h5>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between py-2 border-b border-gray-100">
              <span class="text-gray-600">股票敞口</span>
              <span class="font-semibold">3,200,000</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-100">
              <span class="text-gray-600">Beta 系數</span>
              <span class="font-semibold">1.25</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-100">
              <span class="text-gray-600">波動率</span>
              <span class="font-semibold">18.5%</span>
            </div>
            <div class="flex justify-between py-2">
              <span class="text-gray-600">敞口方向</span>
              <span class="font-semibold text-green-600">做多</span>
            </div>
          </div>
        </div>

        <!-- 流動性風險 -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h5 class="font-bold text-gray-800 mb-3">💧 流動性風險</h5>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between py-2 border-b border-gray-100">
              <span class="text-gray-600">流動資金</span>
              <span class="font-semibold">500,000</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-100">
              <span class="text-gray-600">流動性比率</span>
              <span class="font-semibold">16.7%</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-100">
              <span class="text-gray-600">平均換手</span>
              <span class="font-semibold">2.3 天</span>
            </div>
            <div class="flex justify-between py-2">
              <span class="text-gray-600">風險級別</span>
              <span class="font-semibold text-yellow-600">⚠️ 中</span>
            </div>
          </div>
        </div>

        <!-- 信用風險 -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h5 class="font-bold text-gray-800 mb-3">💳 信用風險</h5>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between py-2 border-b border-gray-100">
              <span class="text-gray-600">融資額度</span>
              <span class="font-semibold">1,000,000</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-100">
              <span class="text-gray-600">已用額度</span>
              <span class="font-semibold">700,000</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-100">
              <span class="text-gray-600">可用額度</span>
              <span class="font-semibold text-green-600">300,000</span>
            </div>
            <div class="flex justify-between py-2">
              <span class="text-gray-600">利息成本</span>
              <span class="font-semibold">3.5% p.a.</span>
            </div>
          </div>
        </div>

        <!-- 操作風險 -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h5 class="font-bold text-gray-800 mb-3">⚙️ 操作風險</h5>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between py-2 border-b border-gray-100">
              <span class="text-gray-600">系統可用性</span>
              <span class="font-semibold text-green-600">99.9%</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-100">
              <span class="text-gray-600">數據同步延遲</span>
              <span class="font-semibold">120ms</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-100">
              <span class="text-gray-600">最後故障時間</span>
              <span class="font-semibold">7 天前</span>
            </div>
            <div class="flex justify-between py-2">
              <span class="text-gray-600">風險評級</span>
              <span class="font-semibold text-green-600">✅ 低</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  riskData: {
    type: Object,
    required: true
  }
});

const leverageColor = (leverage) => {
  if (leverage > 2.5) return 'text-red-600';
  if (leverage > 2.0) return 'text-yellow-600';
  return 'text-green-600';
};

const leverageBarColor = (leverage) => {
  if (leverage > 2.5) return 'bg-red-600';
  if (leverage > 2.0) return 'bg-yellow-600';
  return 'bg-green-600';
};

const correlationLabel = (corr) => {
  if (corr > 0.7) return '高相關性 ⚠️';
  if (corr < 0.3) return '低相關性 ✅';
  return '適度相關 ⚖️';
};

const correlationStatus = (corr) => {
  if (corr > 0.7) return 'text-red-600';
  if (corr < 0.3) return 'text-green-600';
  return 'text-yellow-600';
};
</script>
