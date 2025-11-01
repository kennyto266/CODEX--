"""
驗證 OpenRouter MiniMax API 設置
"""
import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

def test_api():
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "minimax/minimax-m2:free",
        "messages": [{"role": "user", "content": "Hello"}]
    }
    
    response = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {result['choices'][0]['message']['content'][:100]}")
        print("[OK] API 正常工作")
    else:
        print(f"[ERROR] Error: {response.text}")

if __name__ == "__main__":
    test_api()
