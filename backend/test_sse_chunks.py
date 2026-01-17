"""
SSE 实时性终极诊断工具

这个脚本会：
1. 连接到 SSE 端点
2. 实时显示每个接收到的数据块（不是事件，是 HTTP chunk）
3. 显示接收时间，判断是否实时
"""

import asyncio
import httpx
from datetime import datetime
import sys


async def diagnose_sse():
    url = "http://localhost:8000/api/v1/analysis/stream"
    prompt = "测试实时性"

    print("=" * 80)
    print("SSE 实时性诊断")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Prompt: {prompt}")
    print(f"开始时间: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    print("=" * 80)
    print("\n等待响应...\n")

    start_time = datetime.now()
    last_chunk_time = start_time
    chunk_count = 0

    try:
        timeout = httpx.Timeout(120.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("GET", url, params={"prompt": prompt}) as response:
                print(f"✅ 连接成功 (HTTP {response.status_code})")
                print(f"Headers: {dict(response.headers)}\n")
                print("-" * 80)

                # 使用 aiter_bytes() 而不是 aiter_lines() 来接收原始数据块
                async for chunk in response.aiter_bytes():
                    current_time = datetime.now()
                    elapsed = (current_time - start_time).total_seconds()
                    interval = (current_time - last_chunk_time).total_seconds()

                    chunk_count += 1
                    chunk_size = len(chunk)

                    # 显示接收信息
                    timestamp = current_time.strftime('%H:%M:%S.%f')[:-3]
                    print(f"\n[{timestamp}] (+{interval:.3f}s) Chunk #{chunk_count}")
                    print(f"  大小: {chunk_size} bytes")

                    # 解码并显示内容（前200字符）
                    try:
                        decoded = chunk.decode('utf-8')
                        preview = decoded.replace('\n', '\\n')[:200]
                        print(f"  内容: {preview}")

                        # 统计事件类型
                        if "event:" in decoded:
                            event_types = []
                            for line in decoded.split('\n'):
                                if line.startswith('event:'):
                                    event_types.append(line[6:].strip())
                            if event_types:
                                print(f"  事件: {', '.join(event_types)}")

                    except:
                        print(f"  内容: <binary data>")

                    last_chunk_time = current_time

                    # 限制只测试前 30 个 chunk
                    if chunk_count >= 30:
                        print("\n\n已接收足够数据，停止测试。")
                        break

                    sys.stdout.flush()

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    total_time = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 80)
    print("诊断结果")
    print("=" * 80)
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"Chunk 总数: {chunk_count}")

    if chunk_count > 1:
        print(f"\n判断：")
        print(f"  - 如果各 chunk 之间有明显间隔（几秒），说明是实时的 ✅")
        print(f"  - 如果所有 chunk 几乎同时到达（<0.1秒），说明被缓冲了 ❌")

    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(diagnose_sse())
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
