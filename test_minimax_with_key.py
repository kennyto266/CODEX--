"""
使用您的 OpenRouter API Key 測試 MiniMax-M2
"""

import requests
import json
import sys

# 設置 UTF-8 編碼
sys.stdout.reconfigure(encoding='utf-8')

API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

def test_minimax():
    """測試 MiniMax"""
    
    print("=" * 60)
    print("OpenRouter MiniMax-M2 測試")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/penguin8n/hk-quant-system",
        "X-Title": "HK Quant System"
    }
    
    # 測試 1: 簡單問候
    print("\n[測試 1] 簡單問候...")
    try:
        payload = {
            "model": "minimax/minimax-m2:free",
            "messages": [{"role": "user", "content": "你好，請用一句話介紹你自己"}]
        }
        
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            text = result['choices'][0]['message']['content']
            print(f"[OK] 回應: {text}")
        else:
            print(f"[ERROR] 錯誤回應: {response.text}")
    except Exception as e:
        print(f"[ERROR] 錯誤: {e}")
    
    # 測試 2: 代碼生成
    print("\n[測試 2] 代碼生成...")
    try:
        payload = {
            "model": "minimax/minimax-m2:free",
            "messages": [{"role": "user", "content": "請寫一個 Python 函數計算斐波那契數列"}]
        }
        
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            text = result['choices'][0]['message']['content']
            print(f"[OK] 回應:\n{text}")
        else:
            print(f"[ERROR] 錯誤: {response.text}")
    except Exception as e:
        print(f"[ERROR] 錯誤: {e}")
    
    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_minimax()
