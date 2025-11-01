import requests
import time

print("Testing CODEX Dashboard...")
print("=" * 50)

# Test 1: Health check
print("\n1. Testing health endpoint...")
response = requests.get("http://localhost:8001/api/health")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Test 2: Main page
print("\n2. Testing main page...")
response = requests.get("http://localhost:8001/")
print(f"Status: {response.status_code}")
print(f"Content length: {len(response.text)} chars")

# Check for key elements
content = response.text
checks = {
    "Vue CDN": "vue@3.3.4" in content,
    "Vue Router CDN": "vue-router@4.2.5" in content,
    "Pinia CDN": "pinia@2.1.6" in content,
    "main.js": "/static/js/main.js" in content,
    "#app div": 'id="app"' in content,
    "#router-view": 'id="router-view"' in content,
    "nav links": 'href="#/"' in content
}

print("\n3. Checking HTML elements:")
for name, status in checks.items():
    print(f"  {'[OK]' if status else '[FAIL]'} {name}")

# Test 3: Static files
print("\n4. Testing static files...")
response = requests.get("http://localhost:8001/static/js/main.js")
print(f"main.js status: {response.status_code}")
print(f"main.js length: {len(response.text)} chars")
print(f"Contains Vue: {'Vue' in response.text}")
print(f"Contains Router: {'Router' in response.text}")
print(f"Contains createApp: {'createApp' in response.text}")

print("\n" + "=" * 50)
print("Test complete!")
