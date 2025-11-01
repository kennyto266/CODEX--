# 香港物業數據源指南

## 📊 政府開放數據源

### 1. 香港政府開放數據門戶
**URL**: https://data.gov.hk/tc/
**API**: 可用 CKAN API

### 2. 差餉物業估價署 (RVD)
**URL**: https://www.rvd.gov.hk/
**數據集**:
- 私人住宅 - 各類別平均售價 [季度] (1982-1998)
- 私人住宅 - 各類別平均售價 [季度] (1999-2025)
- 私人住宅 - 各類別平均租金 [季度] (1982-1998)
- 私人住宅 - 各類別平均租金 [季度] (1999-2025)

### 3. 土地註冊處
**URL**: https://www.landreg.gov.hk/
**數據集**:
- 樓宇買賣合約
- 樓宇註冊統計
- 物業市場統計

## 🔗 數據下載示例

### RVD 物業價格數據 (CSV)
```python
# 私人住宅平均售價 (1982-1998)
url_1982_1998 = "https://www.rvd.gov.hk/doc/en/statistics/his_3_3_2009.xls"

# 私人住宅平均售價 (1999-2025)
url_1999_2025 = "https://www.rvd.gov.hk/doc/en/statistics/his_3_3.xlsx"

# 私人住宅平均租金 (1982-1998)
rent_url_1982_1998 = "https://www.rvd.gov.hk/doc/en/statistics/his_3_4_2009.xls"

# 私人住宅平均租金 (1999-2025)
rent_url_1999_2025 = "https://www.rvd.gov.hk/doc/en/statistics/his_3_4.xlsx"
```

### 政府數據門戶 API
```python
# 搜索物業相關數據集
api_url = "https://data.gov.hk/tc/api/3/action/package_search?q=property"
response = requests.get(api_url)
datasets = response.json()

# 獲取數據集
for dataset in datasets['result']['results']:
    print(f"數據集: {dataset['title']}")
    print(f"URL: {dataset['resources'][0]['url']}")
```

## 🛠️ 實際數據源配置

基於政府開放數據，我們需要：

1. **直接下載 Excel/CSV 文件**
   - 使用 pandas 讀取
   - 自動解析和清洗

2. **使用 CKAN API**
   - 搜索和獲取數據集
   - 自動化數據獲取

3. **定期更新機制**
   - 檢查數據更新
   - 自動下載新版本

## ✅ 推薦方案

1. **主要數據源**: RVD 官方網站 (已連接成功)
2. **備份數據源**: 政府開放數據門戶
3. **輔助數據源**: 土地註冊處統計資料

## 📋 下一步行動

1. 更新適配器以使用真實的政府數據 URL
2. 實現 Excel/CSV 文件下載和解析
3. 添加數據更新檢查機制
4. 測試數據獲取流程
