"""Test detailed thinking steps output."""
import requests
import json
import sys
import io

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000/api/v1"


def print_thinking_step(step, step_num):
    """Print a thinking step with nice formatting."""
    print(f"\n{'='*80}")
    print(f"思考步骤 {step_num}: {step['title']}")
    print(f"状态: {step['status']}")
    print(f"{'='*80}")
    print(step['description'])
    print(f"{'='*80}\n")


def test_detailed_analysis():
    """Test analysis with detailed thinking steps."""

    print("\n" + "="*80)
    print("测试详细的思考过程输出")
    print("="*80)

    # Create session
    print("\n[1] 创建会话...")
    response = requests.post(f"{BASE_URL}/session/create")
    session_data = response.json()
    session_id = session_data["session_id"]
    print(f"会话ID: {session_id}")

    # First analysis
    print("\n[2] 执行第一次分析...")
    print("输入: '我要为春季新款手袋上市做一次推广，目标是提升转化率，请帮我圈选高潜人群'")

    analysis_request = {
        "prompt": "我要为春季新款手袋上市做一次推广，目标是提升转化率，请帮我圈选高潜人群",
        "session_id": session_id
    }

    response = requests.post(
        f"{BASE_URL}/analysis",
        json=analysis_request
    )

    if response.status_code == 200:
        result = response.json()

        print(f"\n{'#'*80}")
        print("分析结果概览")
        print(f"{'#'*80}")
        print(f"圈选人数: {result['metrics']['audienceSize']}")
        print(f"转化率: {result['metrics']['conversionRate']:.2%}")
        print(f"预估收入: ¥{result['metrics']['estimatedRevenue']:,.0f}")
        print(f"ROI: {result['metrics']['roi']:.2f}倍")

        # Print all thinking steps
        print(f"\n{'#'*80}")
        print("详细思考过程")
        print(f"{'#'*80}")

        for i, step in enumerate(result['thinkingSteps'], 1):
            print_thinking_step(step, i)

        # Print final response
        print(f"\n{'#'*80}")
        print("最终回复")
        print(f"{'#'*80}")
        print(result['response'])
        print(f"{'#'*80}\n")

    else:
        print(f"分析失败: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    try:
        test_detailed_analysis()
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
