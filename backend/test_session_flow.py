"""Test script for session-aware multi-turn conversation flow."""
import requests
import json
import time
import sys
import io

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000/api/v1"


def test_session_flow():
    """Test the complete session flow with multi-turn conversation."""

    print("=" * 80)
    print("Testing LuxuryMA Session & Multi-Turn Conversation Flow")
    print("=" * 80)

    # Step 1: Create a new session
    print("\n[Step 1] Creating a new session...")
    response = requests.post(f"{BASE_URL}/session/create")
    session_data = response.json()
    session_id = session_data["session_id"]
    print(f"[OK] Session created: {session_id}")
    print(f"  Message: {session_data['message']}")

    # Step 2: First analysis - Fresh request
    print("\n[Step 2] First analysis - Fresh marketing request...")
    analysis_request_1 = {
        "prompt": "我要为春季新款手袋上市做一次推广，目标是提升转化率，请帮我圈选高潜人群。",
        "session_id": session_id
    }

    response = requests.post(
        f"{BASE_URL}/analysis",
        json=analysis_request_1
    )

    if response.status_code == 200:
        result_1 = response.json()
        print(f"[OK] First analysis completed")
        print(f"  Session ID: {result_1['session_id']}")
        print(f"  Audience size: {result_1['metrics']['audienceSize']}")
        print(f"  Conversion rate: {result_1['metrics']['conversionRate']:.2%}")
        print(f"  Estimated revenue: ¥{result_1['metrics']['estimatedRevenue']:,.0f}")
        print(f"  Response: {result_1['response'][:100]}...")
        print(f"  Thinking steps: {len(result_1['thinkingSteps'])} steps")
    else:
        print(f"[ERROR] Analysis failed: {response.status_code}")
        print(response.text)
        return

    time.sleep(2)

    # Step 3: Second analysis - Modification request
    print("\n[Step 3] Second analysis - Modifying intent (只要VVIP)...")
    analysis_request_2 = {
        "prompt": "只要VVIP客户，去掉VIP",
        "session_id": session_id
    }

    response = requests.post(
        f"{BASE_URL}/analysis",
        json=analysis_request_2
    )

    if response.status_code == 200:
        result_2 = response.json()
        print(f"[OK] Second analysis completed (modification)")
        print(f"  Session ID: {result_2['session_id']}")
        print(f"  Audience size: {result_2['metrics']['audienceSize']}")
        print(f"  Conversion rate: {result_2['metrics']['conversionRate']:.2%}")
        print(f"  Estimated revenue: ¥{result_2['metrics']['estimatedRevenue']:,.0f}")
        print(f"  Response: {result_2['response'][:100]}...")

        # Show top 3 users
        print(f"\n  Top 3 selected users:")
        for i, user in enumerate(result_2['audience'][:3], 1):
            print(f"    {i}. {user['name']} ({user['tier']}) - Score: {user['score']}")
    else:
        print(f"[ERROR] Second analysis failed: {response.status_code}")
        print(response.text)
        return

    time.sleep(2)

    # Step 4: Get session info
    print("\n[Step 4] Retrieving session information...")
    response = requests.get(f"{BASE_URL}/session/{session_id}")

    if response.status_code == 200:
        session_info = response.json()
        print(f"[OK] Session info retrieved")
        print(f"  Total turns: {len(session_info['turns'])}")
        print(f"  Created at: {session_info['created_at']}")
        print(f"  Updated at: {session_info['updated_at']}")
    else:
        print(f"[ERROR] Failed to get session info: {response.status_code}")

    # Step 5: Apply campaign
    print("\n[Step 5] Applying marketing campaign...")
    apply_request = {
        "session_id": session_id
    }

    response = requests.post(
        f"{BASE_URL}/campaign/apply",
        json=apply_request
    )

    if response.status_code == 200:
        apply_result = response.json()
        print(f"[OK] Campaign applied successfully")
        print(f"  Status: {apply_result['status']}")
        print(f"  Message: {apply_result['message']}")
        print(f"  Campaign ID: {apply_result['mock_payload']['campaign_id']}")
        print(f"  Target audience: {apply_result['campaign_summary']['target_audience_size']} users")
        print(f"  Target tiers: {', '.join(apply_result['campaign_summary']['target_tiers'])}")
        print(f"  Estimated revenue: ¥{apply_result['campaign_summary']['estimated_revenue']:,.0f}")
        print(f"  Estimated ROI: {apply_result['campaign_summary']['estimated_roi']:.2f}")
    else:
        print(f"[ERROR] Campaign application failed: {response.status_code}")
        print(response.text)
        return

    # Step 6: Reset session
    print("\n[Step 6] Resetting session...")
    response = requests.post(f"{BASE_URL}/session/reset?session_id={session_id}")

    if response.status_code == 200:
        reset_result = response.json()
        new_session_id = reset_result["session_id"]
        print(f"[OK] Session reset")
        print(f"  Old session: {session_id}")
        print(f"  New session: {new_session_id}")
        print(f"  Message: {reset_result['message']}")
    else:
        print(f"[ERROR] Session reset failed: {response.status_code}")

    # Step 7: Health check
    print("\n[Step 7] Health check...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        health = response.json()
        print(f"[OK] API is healthy")
        print(f"  Status: {health['status']}")
        print(f"  Timestamp: {health['timestamp']}")

    print("\n" + "=" * 80)
    print("[OK] All tests completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_session_flow()
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
