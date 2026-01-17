"""
测试流式V2 endpoint - 验证逐步推理输出

运行前请确保后端服务器已启动：
cd backend && uvicorn app.main:app --reload

这个测试脚本会连接到流式endpoint并实时打印：
1. 节点开始执行的通知
2. LLM的逐步推理过程
3. 节点完成的结果
4. 最终工作流完成的状态
"""
import httpx
import asyncio
import json
from datetime import datetime


BASE_URL = "http://localhost:8000/api/v1"


async def test_streaming_v2_clear_intent():
    """测试明确意图的流式处理."""
    print("\n" + "=" * 80)
    print("测试1: 明确意图 - 流式输出")
    print("=" * 80)

    prompt = "我要为春季新款手袋上市做一次推广，目标是提升转化率。圈选VVIP和VIP客户，年龄在25-44岁。"

    print(f"\n用户输入: {prompt}")
    print("\n开始流式处理...\n")
    print("-" * 80)

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream(
                "GET",
                f"{BASE_URL}/analysis/v2/stream",
                params={"prompt": prompt}
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix

                        if not data_str.strip():
                            continue

                        try:
                            event = json.loads(data_str)
                            event_type = event.get("type")

                            if event_type == "node_start":
                                node = event.get("node")
                                title = event.get("title", node)
                                print(f"\n🚀 【节点开始】 {title} ({node})")
                                print("-" * 80)

                            elif event_type == "reasoning":
                                # 实时打印LLM推理过程
                                reasoning_chunk = event.get("data", "")
                                print(reasoning_chunk, end="", flush=True)

                            elif event_type == "node_complete":
                                node = event.get("node")
                                data = event.get("data", {})

                                print(f"\n\n✅ 【节点完成】 {node}")

                                # 显示自然语言输出 (新增)
                                if "display_text" in data:
                                    print(f"\n{data['display_text']}")
                                    print("-" * 80)
                                    continue

                                # 原有的详细输出（作为备选）
                                if "user_intent" in data:
                                    print(f"  - 意图状态: {data.get('intent_status')}")
                                    print(f"  - 业务目标: {data['user_intent'].get('business_goal')}")
                                    if "summary" in data:
                                        print(f"  - 意图摘要: {data['summary']}")

                                if "matched_features" in data:
                                    features = data['matched_features']
                                    print(f"  - 匹配特征数: {len(features)}")
                                    if "summary" in data:
                                        print(f"  - 特征摘要: {data['summary']}")
                                    for feat in features[:3]:
                                        print(f"    · {feat.get('description')}")

                                if "strategy_summary" in data:
                                    print(f"  - 策略摘要: {data['strategy_summary']}")

                                if "executive_summary" in data:
                                    print(f"  - 执行摘要: {data['executive_summary']}")

                                if "prediction_result" in data:
                                    pred = data['prediction_result']
                                    print(f"  - 圈选人数: {pred.get('audience_size')}")
                                    print(f"  - 预估转化率: {pred.get('conversion_rate', 0):.2%}")
                                    print(f"  - 预估收入: ¥{pred.get('estimated_revenue', 0):,.0f}")

                                print("-" * 80)

                            elif event_type == "workflow_complete":
                                status = event.get("status")
                                session_id = event.get("session_id")

                                print(f"\n🎉 【工作流完成】")
                                print(f"  - 状态: {status}")
                                print(f"  - Session ID: {session_id}")

                                data = event.get("data", {})
                                if data.get("prediction_result"):
                                    pred = data["prediction_result"]
                                    print(f"\n最终预测结果:")
                                    print(f"  - 圈选人数: {pred.get('audience_size')}")
                                    print(f"  - 预估转化率: {pred.get('conversion_rate', 0):.2%}")
                                    print(f"  - 预估收入: ¥{pred.get('estimated_revenue', 0):,.0f}")
                                    print(f"  - ROI: {pred.get('roi', 0):.2f}倍")

                            elif event_type == "error":
                                error_msg = event.get("data")
                                print(f"\n❌ 【错误】 {error_msg}")

                        except json.JSONDecodeError:
                            print(f"[Warning] Failed to parse: {data_str[:100]}")

            print("\n" + "=" * 80)
            print("✅ 流式处理完成")
            print("=" * 80)

        except httpx.HTTPError as e:
            print(f"\n❌ HTTP Error: {e}")
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def test_streaming_v2_ambiguous_intent():
    """测试模糊意图的流式处理."""
    print("\n" + "=" * 80)
    print("测试2: 模糊意图 - 流式输出（应返回澄清问题）")
    print("=" * 80)

    prompt = "帮我圈选一些用户"

    print(f"\n用户输入: {prompt}")
    print("\n开始流式处理...\n")
    print("-" * 80)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            async with client.stream(
                "GET",
                f"{BASE_URL}/analysis/v2/stream",
                params={"prompt": prompt}
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]

                        if not data_str.strip():
                            continue

                        try:
                            event = json.loads(data_str)
                            event_type = event.get("type")

                            if event_type == "node_start":
                                node = event.get("node")
                                title = event.get("title", node)
                                print(f"\n🚀 【节点开始】 {title}")

                            elif event_type == "reasoning":
                                reasoning_chunk = event.get("data", "")
                                print(reasoning_chunk, end="", flush=True)

                            elif event_type == "node_complete":
                                node = event.get("node")
                                print(f"\n\n✅ 【节点完成】 {node}")

                                data = event.get("data", {})
                                if "clarification_question" in data:
                                    print(f"\n澄清问题:\n{data['clarification_question']}")

                            elif event_type == "workflow_complete":
                                status = event.get("status")
                                print(f"\n🎉 【工作流完成】 状态: {status}")

                                data = event.get("data", {})
                                response_text = data.get("response", "")
                                print(f"\n最终响应:\n{response_text}")

                        except json.JSONDecodeError:
                            pass

            print("\n" + "=" * 80)
            print("✅ 流式处理完成")
            print("=" * 80)

        except Exception as e:
            print(f"\n❌ Error: {e}")


async def main():
    """运行所有测试."""
    print("\n" + "=" * 80)
    print(f"V2 流式 Endpoint 测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    try:
        # 测试1: 明确意图
        await test_streaming_v2_clear_intent()

        # 等待2秒
        await asyncio.sleep(2)

        # 测试2: 模糊意图
        await test_streaming_v2_ambiguous_intent()

        print("\n" + "=" * 80)
        print("✅ 所有测试完成！")
        print("=" * 80)

    except httpx.ConnectError:
        print("\n❌ 无法连接到服务器！")
        print("请确保后端服务器已启动：")
        print("  cd backend && uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
