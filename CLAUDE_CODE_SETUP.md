# Claude Code 使用 OpenRouter MiniMax 指南

## 🎯 快速開始

您的 OpenRouter MiniMax API Key 已經驗證可用：
```
API Key: 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
狀態: ✅ 正常工作
模型: minimax/minimax-m2:free (免費)
```

## ⚠️ 重要說明

**Claude Code 目前不支持在配置文件中直接使用 OpenRouter 或其他第三方 API。**

但是，您可以在 **Python 代碼** 中使用 OpenRouter MiniMax！

## 📝 解決方案

### 方案 1: 在 Python 項目中集成 OpenRouter MiniMax

#### 步驟 1: 創建 OpenRouter 客戶端

```python
# openrouter_client.py
import requests
from typing import Dict, Any
import os

class OpenRouterClient:
    """OpenRouter API 客戶端"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def chat(self, message: str, model: str = "minimax/minimax-m2:free") -> Dict[str, Any]:
        """發送聊天請求"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/penguin8n/hk-quant-system",
            "X-Title": "HK Quant System"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": message}]
        }
        
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    
    def get_response_text(self, response: Dict[str, Any]) -> str:
        """提取回應文本"""
        return response['choices'][0]['message']['content']

# 使用示例
if __name__ == "__main__":
    # 您的 API Key
    api_key = "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"
    
    # 創建客戶端
    client = OpenRouterClient(api_key)
    
    # 發送請求
    result = client.chat("你好，請介紹你自己")
    print(client.get_response_text(result))
```

#### 步驟 2: 在 Claude Code 中使用

1. **在 Python 文件中導入**
```python
from openrouter_client import OpenRouterClient

# 初始化
api_key = "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"
client = OpenRouterClient(api_key)

# 使用
response = client.chat("請幫我分析港股 0700.HK")
print(client.get_response_text(response))
```

2. **在 Claude Code 聊天中調用**
```
我有一個 Python 文件 openrouter_client.py，請幫我用它來分析港股數據
```

### 方案 2: 在港股量化系統中集成

#### 在您的項目中創建 OpenRouter 提供者

```python
# src/agents/llm_providers/openrouter_provider.py
import requests
from typing import Dict, Any

class OpenRouterProvider:
    """OpenRouter LLM 提供者"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    async def generate(
        self, 
        prompt: str, 
        model: str = "minimax/minimax-m2:free",
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """生成回應"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/penguin8n/hk-quant-system",
            "X-Title": "HK Quant System"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    
    def extract_text(self, response: Dict[str, Any]) -> str:
        """從回應中提取文本"""
        return response['choices'][0]['message']['content']

# 使用
if __name__ == "__main__":
    provider = OpenRouterProvider("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")
    result = await provider.generate("分析港股市場")
    print(provider.extract_text(result))
```

## 🚀 快速測試

使用測試腳本驗證：

```bash
python test_api_setup.py
```

## 📋 配置說明

### Claude Code 配置 (目前無法直接配置第三方 API)

```json
{
  "model": "haiku",
  "enabledPlugins": {
    "full-stack-orchestration@claude-code-workflows": true,
    "quantitative-trading@claude-code-workflows": true
  },
  "alwaysThinkingEnabled": true
}
```

**重要**: Claude Code 的配置文件不支持添加第三方 API 的環境變量。您需要在 Python 代碼中直接使用 API Key。

## 💡 推薦工作流程

1. **在 Claude Code 中編寫代碼**（使用 Claude 的編碼能力）
2. **在 Python 代碼中使用 OpenRouter MiniMax**
3. **兩者結合使用**：
   - Claude Code 幫助編寫代碼
   - OpenRouter MiniMax 在代碼中執行 AI 分析

## 📝 示例：在 Claude Code 中使用

### 步驟 1: 創建客戶端文件

在 Claude Code 中，您可以說：
```
請幫我創建一個 OpenRouter MiniMax 客戶端，
API Key 是: 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
模型使用: minimax/minimax-m2:free
```

### 步驟 2: 使用客戶端

在 Claude Code 中：
```
請使用剛才創建的 OpenRouter 客戶端來分析港股 0700.HK
```

## 🎯 總結

- ✅ **API Key 驗證成功** - 可以正常使用
- ✅ **模型可用** - minimax/minimax-m2:free (免費)
- ✅ **集成方式** - 在 Python 代碼中直接使用
- ⚠️ **Claude Code 限制** - 不支持在配置中添加第三方 API

**建議**: 在 Claude Code 中編寫使用 OpenRouter MiniMax 的 Python 代碼，然後在項目中執行。

## 📚 參考文檔

- OpenRouter 文檔: https://openrouter.ai/docs
- MiniMax-M2: https://openrouter.ai/minimax/minimax-m2:free/api
- 測試文件: `test_api_setup.py`

---

**更新日期**: 2025-10-26  
**狀態**: API Key 驗證成功，可在 Python 代碼中使用
