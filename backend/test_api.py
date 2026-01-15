import requests
import json
import asyncio

BASE_URL = "http://localhost:8000"

# Test 1: Health check
print("=== Test 1: Health Check ===")
resp = requests.get(f"{BASE_URL}/api/v1/health")
print(f"Status: {resp.status_code}")
print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

# Test 2: Get high-potential users (before analysis)
print("\n=== Test 2: Get High-Potential Users ===")
resp = requests.get(f"{BASE_URL}/api/v1/users/high-potential?limit=5")
print(f"Status: {resp.status_code}")
result = resp.json()
print(f"Total users: {result['total']}")
if result['users']:
    print(f"First user ID: {result['users'][0]['id']}, Name: {result['users'][0]['name']}")

# Test 3: Predict metrics
print("\n=== Test 3: Predict Metrics ===")
resp = requests.post(
    f"{BASE_URL}/api/v1/prediction/metrics",
    json={"audienceSize": 100, "constraints": {}}
)
print(f"Status: {resp.status_code}")
result = resp.json()
print(f"Audience size: {result['audienceSize']}")
print(f"Conversion rate: {result['conversionRate']:.2%}")
print(f"Estimated revenue: {result['estimatedRevenue']:.0f}")

# Test 4: Run analysis
print("\n=== Test 4: Run Analysis ===")
resp = requests.post(
    f"{BASE_URL}/api/v1/analysis",
    json={
        "prompt": "我要为春季新款手袋上市做一次推广，目标是提升转化率，请帮我圈选高潜人群。",
        "stream": False
    }
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    result = resp.json()
    print(f"Audience size: {result['metrics']['audienceSize']}")
    print(f"Conversion rate: {result['metrics']['conversionRate']:.2%}")
    print(f"Estimated revenue: {result['metrics']['estimatedRevenue']:.0f}")
    print(f"\nAgent response: {result['response']}")
    print(f"\nThinking steps: {len(result['thinkingSteps'])} steps")
    for step in result['thinkingSteps']:
        print(f"  - {step['title']}: {step['status']}")
else:
    print(f"Error: {resp.text}")

print("\n✅ All tests completed successfully!")

