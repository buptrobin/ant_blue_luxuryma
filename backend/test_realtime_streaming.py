"""
测试流式输出是否实时 - 验证每个节点完成立即输出

这个脚本会：
1. 连接到流式 endpoint
2. 记录每个事件接收的时间戳
3. 验证事件是实时接收的（不是批量接收）
"""
import httpx
import asyncio
import json
from datetime import datetime


BASE_URL = "http://localhost:8000/api/v1"


async def test_realtime_streaming():
    """测试流式输出是否实时."""
    print("\n" + "=" * 80)
    print("实时流式输出测试")
    print("=" * 80)

    prompt = "我要为春季新款手袋上市做推广，圈选VVIP和VIP客户"

    print(f"\n用户输入: {prompt}")
    print(f"\n开始时间: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    print("\n" + "-" * 80)

    event_times = []
    last_event_time = None

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream(
                "GET",
                f"{BASE_URL}/analysis/v2/stream",
                params={"prompt": prompt}
            ) as response:
                response.raise_for_status()

                event_count = 0

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        current_time = datetime.now()
                        data_str = line[6:]

                        if not data_str.strip():
                            continue

                        try:
                            event = json.loads(data_str)
                            event_type = event.get("type")
                            event_count += 1

                            # 记录时间间隔
                            if last_event_time:
                                time_diff = (current_time - last_event_time).total_seconds()
                                interval_str = f"(+{time_diff:.2f}s)"
                            else:
                                interval_str = "(首个事件)"

                            timestamp = current_time.strftime('%H:%M:%S.%f')[:-3]

                            # 显示事件和时间戳
                            if event_type == "node_start":
                                node = event.get("node")
                                title = event.get("title", node)
                                print(f"\n[{timestamp}] {interval_str} 🚀 节点开始: {title}")
                                event_times.append({
                                    "time": current_time,
                                    "type": "node_start",
                                    "node": node
                                })

                            elif event_type == "reasoning":
                                # 不显示详细推理内容，只记录接收到推理事件
                                if event_count % 10 == 0:  # 每10个推理chunk显示一次
                                    print(f"[{timestamp}] 💭 推理中... (已接收 {event_count} 个事件)")

                            elif event_type == "node_complete":
                                node = event.get("node")
                                print(f"[{timestamp}] {interval_str} ✅ 节点完成: {node}")

                                # 显示是否有 display_text
                                data = event.get("data", {})
                                if "display_text" in data:
                                    display_preview = data["display_text"][:80].replace("\n", " ")
                                    print(f"    └─ 输出: {display_preview}...")

                                event_times.append({
                                    "time": current_time,
                                    "type": "node_complete",
                                    "node": node
                                })

                            elif event_type == "workflow_complete":
                                status = event.get("status")
                                print(f"\n[{timestamp}] {interval_str} 🎉 工作流完成: {status}")
                                event_times.append({
                                    "time": current_time,
                                    "type": "workflow_complete",
                                    "status": status
                                })

                            last_event_time = current_time

                        except json.JSONDecodeError:
                            pass

            # 分析结果
            print("\n" + "=" * 80)
            print("时间分析")
            print("=" * 80)

            if len(event_times) > 1:
                total_time = (event_times[-1]["time"] - event_times[0]["time"]).total_seconds()
                print(f"\n总耗时: {total_time:.2f}秒")
                print(f"事件总数: {event_count}")

                # 分析每个节点的间隔
                print("\n节点完成时间间隔：")
                node_complete_events = [e for e in event_times if e["type"] == "node_complete"]

                for i, event in enumerate(node_complete_events):
                    if i > 0:
                        interval = (event["time"] - node_complete_events[i-1]["time"]).total_seconds()
                        print(f"  {node_complete_events[i-1]['node']} → {event['node']}: {interval:.2f}秒")

                # 判断是否实时
                print("\n" + "=" * 80)
                if total_time > 5 and len(node_complete_events) > 2:
                    # 检查是否有明显的间隔
                    intervals = []
                    for i in range(1, len(node_complete_events)):
                        interval = (node_complete_events[i]["time"] - node_complete_events[i-1]["time"]).total_seconds()
                        intervals.append(interval)

                    if max(intervals) > 1:  # 如果有超过1秒的间隔
                        print("✅ 判断：流式输出是实时的")
                        print(f"   各节点之间有明显的时间间隔（最大间隔 {max(intervals):.2f}秒）")
                    else:
                        print("⚠️  判断：可能存在缓冲问题")
                        print("   所有事件几乎同时到达，间隔都很短")
                else:
                    print("⚠️  判断：无法确定（数据不足）")

                print("=" * 80)

        except httpx.HTTPError as e:
            print(f"\n❌ HTTP Error: {e}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """运行测试."""
    print("\n" + "=" * 80)
    print(f"实时流式输出测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    try:
        await test_realtime_streaming()

    except httpx.ConnectError:
        print("\n❌ 无法连接到服务器！")
        print("请确保后端服务器已启动：")
        print("  cd backend && uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
