"""
OpenRouter MiniMax 測試腳本

測試通過 OpenRouter 使用免費的 MiniMax-M2 模型
"""

import requests
import json
from typing import Dict, Any

class OpenRouterMiniMax:
    """OpenRouter MiniMax 客戶端"""
    
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
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"請求錯誤: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"狀態碼: {e.response.status_code}")
                print(f"回應: {e.response.text}")
            raise
    
    def extract_response(self, response: Dict[str, Any]) -> str:
        """提取回應文本"""
        try:
            return response['choices'][0]['message']['content']
        except (KeyError, IndexError) as e:
            return f"錯誤: 無法提取回應 - {e}"


def test_minimax():
    """測試 MiniMax"""
    
    print("=" * 60)
    print("OpenRouter MiniMax-M2 測試")
    print("=" * 60)
    
    # 從用戶輸入獲取 API Key
    api_key = input("\n請輸入您的 OpenRouter API Key: ").strip()
    
    if not api_key:
        print("\n❌ 錯誤: 需要 API Key")
        print("\n請訪問 https://openrouter.ai 獲取 API Key")
        return
    
    # 創建客戶端
    client = OpenRouterMiniMax(api_key)
    
    # 測試 1: 簡單問候
    print("\n【測試 1】簡單問候...")
    try:
        response = client.chat("你好，請用一句話介紹你自己")
        text = client.extract_response(response)
        print(f"✅ 回應: {text}")
    except Exception as e:
        print(f"❌ 錯誤: {e}")
    
    # 測試 2: 代碼相關問題
    print("\n【測試 2】代碼相關問題...")
    try:
        response = client.chat("請寫一個 Python 函數計算兩個數字的總和")
        text = client.extract_response(response)
        print(f"✅ 回應:\n{text}")
    except Exception as e:
        print(f"❌ 錯誤: {e}")
    
    # 測試 3: 港股分析
    print("\n【測試 3】港股分析...")
    try:
        prompt = """
        請分析港股市場，給出以下股票的基本面分析：
        - 0700.HK (騰訊)
        - 0941.HK (中國移動)
        簡要說明每隻股票的重點。
        """
        response = client.chat(prompt)
        text = client.extract_response(response)
        print(f"✅ 回應:\n{text}")
    except Exception as e:
        print(f"❌ 錯誤: {e}")
    
    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)
    
    # 顯示使用統計
    try:
        response = client.chat("test")  # 觸發一次請求以獲取統計
        print("\n✅ 模型連接成功！")
        print("\n💡 提示: 現在您可以在項目中使用 OpenRouter MiniMax")
        print("   - 模型: minimax/minimax-m2:free")
        print("   - 價格: $0/M tokens (免費)")
        print("   - 上下文: 204,800 tokens")
    except Exception as e:
        print(f"\n⚠️  連接失敗: {e}")


if __name__ == "__main__":
    test_minimax()
