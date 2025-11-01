# OpenRouter MiniMax 集成指南

## 📌 重要發現

根據 [OpenRouter 文檔](https://openrouter.ai/minimax/minimax-m2:free/api)，**MiniMax-M2 可以通過 OpenRouter 免費使用！**

### MiniMax-M2 模型信息

- **模型 ID**: `minimax/minimax-m2:free`
- **價格**: $0/M 輸入 tokens, $0/M 輸出 tokens (完全免費！)
- **上下文長度**: 204,800 tokens
- **特點**: 
  - 支持代碼生成和多文件編輯
  - 強化的代理工作流
  - 低成本、高效率

## OpenRouter API 配置

### 步驟 1: 獲取 OpenRouter API Key

1. 訪問 [OpenRouter](https://openrouter.ai/)
2. 註冊賬號並創建 API Key
3. 記錄您的 API Key

### 步驟 2: 在您的項目中集成

由於 Claude Code 不支持自定義 API，我們可以在您的港股量化交易系統中集成 MiniMax。

```python
# src/agents/llm_providers/openrouter_provider.py
import requests
from typing import Dict, Any, Optional
import os

class OpenRouterProvider:
    """OpenRouter LLM 提供者（支持 MiniMax）"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
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
            "HTTP-Referer": "https://github.com/yourrepo",  # 可選
            "X-Title": "HK Quant System"  # 可選
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=300
        )
        
        response.raise_for_status()
        return response.json()
    
    def extract_text(self, response: Dict[str, Any]) -> str:
        """從回應中提取文本"""
        try:
            return response['choices'][0]['message']['content']
        except (KeyError, IndexError):
            return "Error: Unable to extract response"
```

### 步驟 3: 在配置中添加 MiniMax

```python
# config/hk_prompt_agents_config.json
{
  "hk_prompt_agents": {
    "llm_providers": {
      "openrouter": {
        "name": "OpenRouter",
        "models": [
          "minimax/minimax-m2:free",
          "google/gemini-flash-1.5"
        ],
        "api_key": "YOUR_OPENROUTER_API_KEY",
        "max_tokens": 4000,
        "temperature": 0.1,
        "timeout": 30
      }
    }
  }
}
```

### 步驟 4: 在 HKPromptEngine 中添加支持

```python
# src/agents/hk_prompt_engine.py
from src.agents.llm_providers.openrouter_provider import OpenRouterProvider

class LLMProvider(str, Enum):
    OPENAI = "openai"
    CLAUDE = "claude"
    GROK = "grok"
    MINIMAX = "minimax"
    OPENROUTER = "openrouter"  # 新增

# 在 HKPromptEngine 中添加
def _init_llm_client(self):
    """初始化LLM客户端"""
    try:
        if self.llm_config.provider == LLMProvider.OPENAI:
            # ... existing code ...
        elif self.llm_config.provider == LLMProvider.MINIMAX or \
             self.llm_config.provider == LLMProvider.OPENROUTER:
            self.client = OpenRouterProvider(self.llm_config.api_key)
        else:
            self.client = None
    except Exception as e:
        self.logger.error(f"LLM客户端初始化失败: {e}")
        self.client = None
```

## 使用示例

### 基本使用

```python
import asyncio
from src.agents.hk_prompt_engine import HKPromptEngine, LLMConfig, LLMProvider

async def test_minimax():
    # 配置 MiniMax
    llm_config = LLMConfig(
        provider=LLMProvider.OPENROUTER,
        api_key="YOUR_OPENROUTER_API_KEY",
        model="minimax/minimax-m2:free",
        max_tokens=2000,
        temperature=0.1
    )
    
    # 創建引擎
    engine = HKPromptEngine(llm_config)
    
    # 使用 MiniMax 分析
    result = await engine.execute_prompt(
        agent_type=AgentType.FUNDAMENTAL_ANALYST,
        input_data={"stock_code": "0700.HK"}
    )
    
    print(result.explanation)

asyncio.run(test_minimax())
```

### 在交易系統中使用

```python
# 在 src/agents/coordinator.py 中添加 MiniMax 選項
class Coordinator:
    def __init__(self):
        self.llm_engines = {
            "claude": HKPromptEngine(LLMConfig(...)),
            "minimax": HKPromptEngine(LLMConfig(
                provider=LLMProvider.OPENROUTER,
                api_key=os.getenv("OPENROUTER_API_KEY"),
                model="minimax/minimax-m2:free"
            ))
        }
    
    async def analyze_with_minimax(self, data):
        """使用 MiniMax 進行分析"""
        engine = self.llm_engines["minimax"]
        result = await engine.execute_prompt(...)
        return result
```

## 優勢

### ✅ 免費使用
- MiniMax-M2 完全免費
- 不需要付費訂閱

### ✅ 高質量代碼生成
- 針對代碼生成優化
- 支持多文件編輯
- 強化的代理工作流

### ✅ OpenAI 兼容
- 標準 OpenAI API 格式
- 易於集成
- 豐富的 SDK 支持

### ✅ 高上下文窗口
- 204,800 tokens 上下文
- 適合處理大型代碼庫

## 環境變量配置

創建 `.env` 文件：

```env
# OpenRouter Configuration
OPENROUTER_API_KEY=your_api_key_here

# 可選配置
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_DEFAULT_MODEL=minimax/minimax-m2:free
```

## 測試連接

```python
# test_openrouter.py
import asyncio
from src.agents.llm_providers.openrouter_provider import OpenRouterProvider

async def test():
    client = OpenRouterProvider("YOUR_API_KEY")
    result = await client.generate("你好，請介紹一下你自己")
    print(client.extract_text(result))

asyncio.run(test())
```

## 推薦配置

對於港股量化交易系統，建議使用：

```python
llm_config = LLMConfig(
    provider=LLMProvider.OPENROUTER,
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="minimax/minimax-m2:free",  # 免費且高質量
    max_tokens=2000,
    temperature=0.1,  # 低溫度保證一致性
    timeout=60
)
```

## 注意事項

1. **API Key 安全**: 不要將 API Key 提交到版本控制
2. **速率限制**: OpenRouter 有速率限制，注意控制請求頻率
3. **免費配額**: MiniMax-M2 免費版本可能有配額限制
4. **錯誤處理**: 添加適當的錯誤處理和重試機制

## 總結

通過 OpenRouter 使用 MiniMax-M2 是一個很好的選擇：
- ✅ 完全免費
- ✅ 高質量代碼生成
- ✅ OpenAI 兼容格式
- ✅ 易於集成

**參考文檔**: https://openrouter.ai/minimax/minimax-m2:free/api

---

**更新日期**: 2025-10-26  
**狀態**: OpenRouter 集成方案
