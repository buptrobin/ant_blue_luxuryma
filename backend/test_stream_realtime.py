"""
测试旧 /analysis/stream 端点的实时性

这个脚本连接到旧的流式端点，实时显示每个事件的到达时间。
如果所有事件几乎同时到达，说明存在缓冲问题。
"""

import asyncio
import httpx
import json
from datetime import datetime
import sys


def print_timestamp(message: str, color_code: str = "0"):
    """打印带时间戳和颜色的消息"""
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    # ANSI 颜色代码: 32=绿, 33=黄, 31=红, 36=青
    print(f"\033[{color_code}m[{timestamp}] {message}\033[0m")


async def test_stream_realtime():
    """测试流式端点的实时性"""
    url = "http://localhost:8000/api/v1/analysis/stream"
    prompt = "我要为春季新款手袋上市做推广,圈选VVIP和VIP客户"

    print("=" * 80)
    print_timestamp("🔍 实时流式输出测试 - /analysis/stream 端点", "1;36")
    print("=" * 80)
    print(f"\n提示词: {prompt}\n")
    print_timestamp("开始连接...", "33")
    print("-" * 80)

    start_time = datetime.now()
    last_event_time = None
    event_count = 0
    node_events = []

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "GET",
                url,
                params={"prompt": prompt}
            ) as response:
                if response.status_code != 200:
                    print_timestamp(f"❌ 错误: HTTP {response.status_code}", "31")
                    return

                print_timestamp("✅ 连接成功，等待事件...\n", "32")

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    current_time = datetime.now()
                    event_count += 1

                    # 计算时间间隔
                    if last_event_time:
                        time_diff = (current_time - last_event_time).total_seconds()
                        interval_str = f"(+{time_diff:.2f}s)"
                    else:
                        time_diff = (current_time - start_time).total_seconds()
                        interval_str = f"(首个事件, +{time_diff:.2f}s)"

                    last_event_time = current_time

                    # 解析事件
                    if line.startswith("event: "):
                        event_type = line[7:].strip()
                        continue

                    if line.startswith("data: "):
                        data_str = line[6:].strip()

                        try:
                            data = json.loads(data_str)

                            # 根据事件类型显示
                            if event_type == "thinking_step":
                                step_id = data.get("stepId", "?")
                                status = data.get("status", "")
                                title = data.get("title", "")

                                if status == "active":
                                    print_timestamp(
                                        f"🚀 步骤{step_id} 开始: {title} {interval_str}",
                                        "32"
                                    )
                                elif status == "pending":
                                    print_timestamp(
                                        f"⏳ 步骤{step_id} 等待: {title}",
                                        "90"  # 灰色
                                    )

                            elif event_type == "thinking_step_update":
                                step_id = data.get("stepId", "?")
                                title = data.get("title", "")
                                print_timestamp(
                                    f"✅ 步骤{step_id} 完成: {title} {interval_str}",
                                    "36"
                                )

                            elif event_type == "node_summary":
                                node = data.get("node", "?")
                                summary = data.get("summary", "")
                                node_events.append({
                                    "node": node,
                                    "time": current_time,
                                    "interval": time_diff if last_event_time != current_time else 0
                                })
                                print_timestamp(
                                    f"📋 节点摘要 [{node}] {interval_str}",
                                    "1;33"
                                )
                                print(f"    {summary[:80]}...")

                            elif event_type == "final_result":
                                print_timestamp(
                                    f"🎉 最终结果到达 {interval_str}",
                                    "1;32"
                                )

                        except json.JSONDecodeError:
                            print_timestamp(f"⚠️  无法解析JSON: {data_str[:50]}...", "33")

    except Exception as e:
        print_timestamp(f"❌ 错误: {e}", "31")
        return

    # 统计分析
    total_time = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 80)
    print_timestamp("📊 时间分析", "1;36")
    print("=" * 80)

    print(f"\n总耗时: {total_time:.2f} 秒")
    print(f"事件总数: {event_count}")

    if node_events:
        print(f"\n节点摘要事件数: {len(node_events)}")
        print("\n节点完成时间间隔：")
        for i, event in enumerate(node_events):
            print(f"  {i+1}. {event['node']:20s} - 间隔: {event['interval']:.2f}秒")

    print("\n" + "=" * 80)

    # 判断是否实时
    if node_events:
        max_interval = max(e['interval'] for e in node_events[1:]) if len(node_events) > 1 else 0
        avg_interval = sum(e['interval'] for e in node_events[1:]) / len(node_events[1:]) if len(node_events) > 1 else 0

        if max_interval > 1.0:
            print_timestamp("✅ 判断：流式输出是实时的", "1;32")
            print(f"   各节点之间有明显的时间间隔（最大间隔 {max_interval:.2f}秒）")
        else:
            print_timestamp("❌ 警告：可能存在缓冲问题", "1;31")
            print(f"   所有事件几乎同时到达（平均间隔 {avg_interval:.3f}秒）")
            print("\n建议：")
            print("   1. 重启 uvicorn 时设置环境变量：")
            print("      Windows: set PYTHONUNBUFFERED=1 && uvicorn app.main:app --reload")
            print("      Linux/Mac: PYTHONUNBUFFERED=1 uvicorn app.main:app --reload")
            print("   2. 如果使用 nginx，确保配置了 proxy_buffering off")

    print("=" * 80)


if __name__ == "__main__":
    print("\n")
    asyncio.run(test_stream_realtime())
    print("\n")
