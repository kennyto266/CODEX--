"""
直接測試 OpenRouter 是否能使用 MiniMax API Key
"""

import requests
import sys

# 設置 UTF-8 編碼
sys.stdout.reconfigure(encoding='utf-8')

# 使用您提供的 API Key
API_KEY = "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"

def test_openrouter_minimax():
    """測試 OpenRouter MiniMax"""
    
    print("=" * 60)
    print("OpenRouter MiniMax-M2 測試")
    print("API Key: " + API_KEY[:20] + "...")
    print("=" * 60)
    
    # OpenRouter 端點
    base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/penguin8n/hk-quant-system",
        "X-Title": "HK Quant System Test"
    }
    
    # 測試 1: 嘗試使用免費的 MiniMax-M2
    print("\n[測試 1] 嘗試使用 minimax/minimax-m2:free")
    try:
        payload = {
            "model": "minimax/minimax-m2:free",
            "messages": [{"role": "user", "content": "你好，請問 1+1 等於多少？"}]
        }
        
        response = requests.post(base_url, headers=headers, json=payload, timeout=60)
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            text = result['choices'][0]['message']['content']
            print(f"[OK] 回應: {text[:200]}")
            print("\n[成功] OpenRouter 可以使用這個 API Key！")
            return True
        else:
            print(f"[錯誤] 狀態碼: {response.status_code}")
            print(f"回應: {response.text[:500]}")
            
            # 如果是 401，說明需要 OpenRouter 的 API Key
            if response.status_code == 401:
                print("\n[提示] 這個 API Key 是 MiniMax 的，不是 OpenRouter 的")
                print("您需要到 https://openrouter.ai 註冊並獲取專屬的 OpenRouter API Key")
            
            return False
            
    except Exception as e:
        print(f"[錯誤] 異常: {e}")
        return False
    
    print("\n" + "=" * 60)

def test_minimax_direct():
    """測試直接使用 MiniMax API"""
    
    print("\n" + "=" * 60)
    print("直接測試 MiniMax API")
    print("=" * 60)
    
    # MiniMax 官方 API 端點
    base_url = "https://api.minimax.chat/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        payload = {
            "model": "abab6.5s-chat",
            "messages": [{"role": "user", "content": "你好"}]
        }
        
        response = requests.post(base_url, headers=headers, json=payload, timeout=60)
        print(f"狀態碼: {response.status_code}")
        print(f"回應: {response.text[:300]}")
        
        if response.status_code == 200:
            print("\n[成功] 可以使用 MiniMax 官方 API")
            return True
        else:
            print("\n[失敗] MiniMax API 需要其他配置")
            return False
            
    except Exception as e:
        print(f"[錯誤] 異常: {e}")
        return False

if __name__ == "__main__":
    print("\n首先測試 OpenRouter...")
    success = test_openrouter_minimax()
    
    if not success:
        print("\nOpenRouter 測試失敗，嘗試直接使用 MiniMax API...")
        test_minimax_direct()
    
    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)
