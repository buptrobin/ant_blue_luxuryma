"""
直接测试 SSE 端点的实时性 - 精简版
"""
import asyncio
import httpx
from datetime import datetime


async def test_sse_realtime():
    url = "http://localhost:8000/api/v1/analysis/stream"
    prompt = "测试"

    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%H:%M:%S')}")
    print(f"测试 URL: {url}?prompt={prompt}")
    print("=" * 80)

    start_time = datetime.now()
    last_time = start_time
    event_count = 0

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("GET", url, params={"prompt": prompt}) as response:
                print(f"\n✅ 连接成功 (HTTP {response.status_code})\n")

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    current_time = datetime.now()
                    elapsed = (current_time - start_time).total_seconds()
                    interval = (current_time - last_time).total_seconds()

                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                        print(f"\n[{elapsed:6.2f}s] (+{interval:.2f}s) Event: {event_type}")
                        event_count += 1
                        last_time = current_time

                    elif line.startswith("data:"):
                        data = line[5:].strip()
                        if len(data) > 100:
                            print(f"          Data: {data[:100]}...")
                        else:
                            print(f"          Data: {data}")

                    # 如果收到超过 20 个事件就停止
                    if event_count > 20:
                        print("\n\n已收到足够事件，停止测试。")
                        break

    except Exception as e:
        print(f"\n❌ 错误: {e}")

    total_time = (datetime.now() - start_time).total_seconds()
    print("\n" + "=" * 80)
    print(f"总耗时: {total_time:.2f}s")
    print(f"事件总数: {event_count}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_sse_realtime())
