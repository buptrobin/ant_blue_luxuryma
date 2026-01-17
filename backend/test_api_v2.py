"""
API测试脚本 - 测试新的 V2 endpoint

运行前请确保后端服务器已启动：
cd backend && uvicorn app.main:app --reload
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"


def print_response(title, response_data):
    """格式化打印响应."""
    print("\n" + "="*60)
    print(title)
    print("="*60)
    print(json.dumps(response_data, ensure_ascii=False, indent=2))


def test_v2_clear_intent():
    """测试明确的意图."""
    print("\n" + "="*80)
    print("测试 1: 明确的意图 - 应该返回完整分析")
    print("="*80)

    payload = {
        "prompt": "我要为春季新款手袋上市做一次推广，目标是提升转化率。圈选VVIP和VIP客户，年龄在25-44岁，近12个月消费超过10万元。",
        "session_id": None,
        "stream": False
    }

    response = requests.post(f"{BASE_URL}/analysis/v2", json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功 - Status: {data['status']}")
        print(f"Session ID: {data['session_id']}")
        print(f"\n响应内容:\n{data['response'][:200]}...")

        if data.get('prediction_result'):
            pred = data['prediction_result']
            print(f"\n预测结果:")
            print(f"  - 圈选人数: {pred.get('audience_size')}")
            print(f"  - 预估转化率: {pred.get('conversion_rate'):.2%}")
            print(f"  - 预估收入: ¥{pred.get('estimated_revenue'):,.0f}")
            print(f"  - ROI: {pred.get('roi'):.2f}倍")

        return data['session_id']
    else:
        print(f"❌ 失败 - Status Code: {response.status_code}")
        print(response.text)
        return None


def test_v2_ambiguous_intent():
    """测试模糊的意图."""
    print("\n" + "="*80)
    print("测试 2: 模糊的意图 - 应该返回澄清问题")
    print("="*80)

    payload = {
        "prompt": "帮我圈选一些用户",
        "session_id": None,
        "stream": False
    }

    response = requests.post(f"{BASE_URL}/analysis/v2", json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功 - Status: {data['status']}")
        print(f"\n澄清问题:\n{data['response']}")

        return data['session_id']
    else:
        print(f"❌ 失败 - Status Code: {response.status_code}")
        print(response.text)
        return None


def test_v2_multi_turn():
    """测试多轮对话."""
    print("\n" + "="*80)
    print("测试 3: 多轮对话")
    print("="*80)

    # 第一轮：模糊意图
    print("\n[第1轮] 用户: 我想做一次营销活动")
    payload1 = {
        "prompt": "我想做一次营销活动",
        "session_id": None,
        "stream": False
    }

    response1 = requests.post(f"{BASE_URL}/analysis/v2", json=payload1)

    if response1.status_code == 200:
        data1 = response1.json()
        session_id = data1['session_id']
        print(f"Status: {data1['status']}")
        print(f"Agent: {data1['response'][:150]}...")

        # 第二轮：补充信息
        print("\n[第2轮] 用户: 目标是提升手袋转化率，圈选VIP客户")
        payload2 = {
            "prompt": "目标是提升手袋转化率，圈选VIP客户",
            "session_id": session_id,
            "stream": False
        }

        response2 = requests.post(f"{BASE_URL}/analysis/v2", json=payload2)

        if response2.status_code == 200:
            data2 = response2.json()
            print(f"Status: {data2['status']}")

            if data2.get('prediction_result'):
                pred = data2['prediction_result']
                print(f"\n预测结果:")
                print(f"  - 圈选人数: {pred.get('audience_size')}")
                print(f"  - 预估转化率: {pred.get('conversion_rate'):.2%}")
        else:
            print(f"❌ 第2轮失败 - Status Code: {response2.status_code}")
    else:
        print(f"❌ 第1轮失败 - Status Code: {response1.status_code}")


def test_v2_feature_matching():
    """测试特征匹配."""
    print("\n" + "="*80)
    print("测试 4: 特征匹配 - 复杂条件")
    print("="*80)

    payload = {
        "prompt": "圈选近3个月在海外消费过、对手袋感兴趣、年龄25-44岁的女性VVIP客户",
        "session_id": None,
        "stream": False
    }

    response = requests.post(f"{BASE_URL}/analysis/v2", json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功 - Status: {data['status']}")

        if data.get('matched_features'):
            print(f"\n匹配的特征 ({len(data['matched_features'])}个):")
            for feat in data['matched_features']:
                print(f"  - {feat['description']}")

        if data.get('strategy_explanation'):
            print(f"\n策略解释:\n{data['strategy_explanation'][:200]}...")
    else:
        print(f"❌ 失败 - Status Code: {response.status_code}")
        print(response.text)


def main():
    """运行所有API测试."""
    print("\n" + "="*80)
    print(f"API V2 Endpoint 测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # 测试1: 明确意图
        test_v2_clear_intent()

        # 测试2: 模糊意图
        test_v2_ambiguous_intent()

        # 测试3: 多轮对话
        test_v2_multi_turn()

        # 测试4: 特征匹配
        test_v2_feature_matching()

        print("\n" + "="*80)
        print("✅ 所有测试完成！")
        print("="*80)

    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器！")
        print("请确保后端服务器已启动：")
        print("  cd backend && uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")


if __name__ == "__main__":
    main()
