# HKEX Crawlee 爬蟲 - 快速開始指南

## 快速開始 (5 分鐘)

### 1️⃣ 運行爬蟲
```bash
npm start
```

爬蟲會:
- 訪問 HKEX 日報表頁面
- 提取所有表格數據
- 保存數據到 `data/` 文件夾

### 2️⃣ 查看結果

**查看最新的 JSON 數據**:
```bash
ls -lt data/*.json | head -1
```

**查看數據結構**:
```bash
cat data/hkex_daily_report_*.json | jq '.marketData | length'
```

**查看頁面截圖**:
```bash
open data/hkex_screenshot_*.png
```

### 3️⃣ 輸出文件說明

| 文件類型 | 名稱格式 | 用途 |
|---------|---------|------|
| JSON | `hkex_daily_report_TIMESTAMP.json` | 結構化表格數據 |
| HTML | `hkex_daily_report_TIMESTAMP.html` | 完整頁面快照 |
| PNG | `hkex_screenshot_TIMESTAMP.png` | 頁面視覺驗證 |

## 数据格式说明

### JSON 結構
```json
{
  "tables": [],          // 非市場數據的表格
  "marketData": [        // 包含數字的表格（市場數據）
    {
      "tableIndex": 3,
      "rowCount": 19,
      "columnCount": 93,
      "rows": [
        ["日期", "數據1", "數據2", ...],
        ["2025-10-20", "100", "200", ...]
      ]
    }
  ],
  "pageText": "完整頁面文本..."
}
```

## 自定義爬蟲

### 修改目標 URL
編輯 `src/main.ts`:
```typescript
const startUrls = ['https://your-target-url.com'];
```

### 修改提取邏輯
編輯 `src/routes.ts` 中的 `page.evaluate()`:
```typescript
const tableData = await page.evaluate(() => {
  // 自定義 DOM 選擇和提取邏輯
  return customData;
});
```

### 添加頁面互動
```typescript
// 點擊按鈕
await page.locator('button.load-data').click();

// 填充輸入框
await page.fill('input[name=search]', '搜索詞');

// 等待元素出現
await page.waitForSelector('.data-table');
```

## 常見問題

### ❓ 如何提取特定的表格？
在 `src/routes.ts` 中修改選擇器:
```typescript
// 只提取第一個表格
const table = document.querySelector('table:first-of-type');

// 或者按 ID
const table = document.getElementById('market-data');
```

### ❓ 如何保存到數據庫？
添加到 `src/routes.ts` 的數據保存部分:
```typescript
import { saveToDatabase } from './db';

await saveToDatabase(tableData);
```

### ❓ 如何定時運行爬蟲？
使用 `node-cron`:
```typescript
import cron from 'node-cron';

// 每天早上 9 點運行
cron.schedule('0 9 * * *', async () => {
  await crawler.run(startUrls);
});
```

### ❓ 如何處理分頁？
```typescript
// 循環遍歷分頁
for (let page = 1; page <= 10; page++) {
  const url = `https://example.com?page=${page}`;
  await crawler.run([url]);
}
```

## 性能優化

### 增加並行度
編輯 `src/main.ts`:
```typescript
const crawler = new PlaywrightCrawler({
  maxRequestsPerCrawl: 100,    // 增加並行請求
  maxCrawlDepth: 2,             // 增加爬蟲深度
  // ...
});
```

### 添加代理
```typescript
import { ProxyConfiguration } from 'crawlee';

const proxyConfiguration = new ProxyConfiguration({
  proxyUrls: ['http://proxy1.com:8080', 'http://proxy2.com:8080']
});

const crawler = new PlaywrightCrawler({
  proxyConfiguration,
  // ...
});
```

### 使用請求隊列重用
```typescript
const crawler = new PlaywrightCrawler({
  reuseRequestQueue: true,  // 重用請求隊列
  // ...
});
```

## 調試技巧

### 查看日誌
```bash
# 查看詳細日誌
npm start -- --loglevel debug
```

### 保存調試截圖
```typescript
// 在 routes.ts 中添加
await page.screenshot({ path: 'debug.png' });
```

### 檢查 HTML 結構
```typescript
const html = await page.content();
console.log(html);  // 打印完整 HTML
```

### 使用瀏覽器調試
```typescript
// 添加到 src/main.ts
const crawler = new PlaywrightCrawler({
  headless: false,  // 顯示瀏覽器窗口
  // ...
});
```

## 安裝和依賴

### 安裝依賴
```bash
npm install
```

### 更新 Crawlee
```bash
npm update crawlee
```

### 檢查版本
```bash
npm list crawlee
```

## 目錄結構

```
my-crawler/
├── src/
│   ├── main.ts           # 爬蟲主文件
│   └── routes.ts         # 路由和數據提取
├── data/                 # 輸出數據
│   ├── *.json            # JSON 數據
│   ├── *.html            # HTML 快照
│   └── *.png             # 截圖
├── package.json          # 項目配置
├── tsconfig.json         # TypeScript 配置
└── README.md            # 項目文檔
```

## 有用的命令

```bash
# 開發模式運行 (自動重新加載)
npm run start:dev

# 構建生產版本
npm run build

# 運行生產版本
npm run start:prod

# 清理緩存
npm run clean

# 查看所有命令
npm run
```

## 外部資源

- [Crawlee 文檔](https://crawlee.dev/)
- [Playwright 文檔](https://playwright.dev/)
- [TypeScript 文檔](https://www.typescriptlang.org/)
- [Node.js 文檔](https://nodejs.org/)

## 需要幫助？

1. 查看 `../HKEX_CRAWLER_SUMMARY.md` 了解完整文檔
2. 查看 GitHub Issues
3. 查看 Crawlee 官方文檔

---
**最後更新**: 2025-10-20
**爬蟲框架**: Crawlee (Playwright)
**Node 版本**: 14+
**開發者**: Claude Code
