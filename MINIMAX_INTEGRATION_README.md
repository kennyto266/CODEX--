# MiniMax API 集成說明

## ⚠️ 重要說明

**Claude Code 目前不支援直接使用 MiniMax API**

根據技術文檔和實際測試，Claude Code 只支援通過官方 Claude API 使用模型，無法直接配置第三方 API（如 MiniMax）。

## 問題根源

```
API Error: Cannot read properties of undefined (reading 'map')
```

這個錯誤表明 Claude Code 無法讀取 MiniMax API 配置，因為：
1. Claude Code 的內部架構不支持自定義 API 端點
2. `env` 配置項在 Claude Code 中不被識別
3. MiniMax 說明文檔針對的是其他 AI 助手工具，不是 Claude Code

## 替代方案

### 方案 1: 使用 MiniMax API 開發自己的客戶端

如果您想使用 MiniMax-M2 模型，可以創建一個獨立的 Python 客戶端：

```python
import requests
import json

class MiniMaxClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.minimax.io/anthropic"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def chat(self, message):
        """發送聊天請求"""
        payload = {
            "model": "MiniMax-M2",
            "messages": [{"role": "user", "content": message}]
        }
        
        response = requests.post(
            f"{self.base_url}/v1/messages",
            headers=self.headers,
            json=payload,
            timeout=300
        )
        
        return response.json()

# 使用範例
client = MiniMaxClient("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")
result = client.chat("你好，請幫我分析港股市場")
print(result)
```

### 方案 2: 在項目中集成 MiniMax 作為 LLM 提供者

可以在您的港股量化交易系統中添加 MiniMax 作為可選的 LLM 提供者：

```python
# src/agents/llm_providers/minimax_provider.py
import requests
from typing import Dict, Any, Optional

class MiniMaxProvider:
    """MiniMax LLM 提供者"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.minimax.io/anthropic"
    
    async def generate(
        self, 
        prompt: str, 
        model: str = "MiniMax-M2",
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """生成回應"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(
            f"{self.base_url}/v1/messages",
            headers=headers,
            json=payload,
            timeout=300
        )
        
        response.raise_for_status()
        return response.json()
```

然後在 `src/agents/hk_prompt_engine.py` 中添加支持：

```python
from src.agents.llm_providers.minimax_provider import MiniMaxProvider

# 在 HKPromptEngine 中添加
if self.llm_config.provider == LLMProvider.MINIMAX:
    self.client = MiniMaxProvider(self.llm_config.api_key)
```

### 方案 3: 使用 OpenAI 兼容的其他工具

如果您想使用 MiniMax-M2 的能力，考慮使用支持 OpenAI 兼容 API 的工具：

- **Cursor** - 支持自定義 API 配置
- **Codeium** - 支持多種 LLM 提供商
- **Continue.dev** - 開源的 VS Code 擴展，支持自定義 API

## 配置示例（其他工具）

如果您使用其他工具（非 Claude Code），配置如下：

### Cursor 配置

```json
// cursor/.cursor/settings.json
{
  "anthropic.apiKey": "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",
  "anthropic.baseURL": "https://api.minimax.io/anthropic",
  "anthropic.model": "MiniMax-M2"
}
```

### Continue.dev 配置

```json
// continue/config.json
{
  "models": [
    {
      "title": "MiniMax-M2",
      "provider": "openai",
      "model": "MiniMax-M2",
      "apiKey": "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",
      "apiBase": "https://api.minimax.io/anthropic"
    }
  ]
}
```

## 建議

基於您當前的項目需求（港股量化交易系統），建議：

1. **繼續使用 Claude Code** - 它已經有很好的代碼分析和理解能力
2. **保持現有配置** - 使用默認的 Claude 模型
3. **在系統內部集成 MiniMax** - 如果需要，可以在您的交易系統中添加 MiniMax 作為 AI 分析提供者

## 當前配置

您的 Claude Code 當前配置：

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

這個配置已經非常適合您的項目，包括：
- ✅ 量化交易工作流
- ✅ 全棧編排能力
- ✅ 強化思考模式

可以直接使用，無需額外配置！

## 總結

- ❌ Claude Code 不支持 MiniMax API
- ✅ 可以在您的項目中集成 MiniMax
- ✅ 可以使用其他支持 MiniMax 的工具
- ✅ Claude Code 的現有功能已經足夠強大

---

**更新日期**: 2025-10-26  
**狀態**: 配置已恢復到正常狀態
