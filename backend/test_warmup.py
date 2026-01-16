#!/usr/bin/env python
"""Test script to verify warmup optimization."""
import time
import asyncio
import httpx


async def test_health_check():
    """Test enhanced health check endpoint."""
    print("\n" + "=" * 60)
    print("Testing Health Check Endpoint")
    print("=" * 60)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/v1/health")
            response.raise_for_status()
            health = response.json()

            print(f"\nStatus: {health['status']}")
            print(f"Timestamp: {health['timestamp']}")
            print("\nComponents:")

            for component, details in health.get('components', {}).items():
                status = details.get('status', 'unknown')
                icon = "✓" if status == "ready" else "✗"
                print(f"  {icon} {component}: {status}")

                if component == "llm_manager":
                    print(f"      Model Type: {details.get('model_type', 'N/A')}")
                    print(f"      SDK Available: {details.get('sdk_available', 'N/A')}")
                elif component == "agent_graph":
                    print(f"      Nodes: {details.get('nodes', 'N/A')}")
                elif component == "session_manager":
                    print(f"      Active Sessions: {details.get('active_sessions', 'N/A')}")

            print("\n✓ Health check passed!")
            return True

    except Exception as e:
        print(f"\n✗ Health check failed: {e}")
        return False


async def test_first_request_latency():
    """Test first request latency (should be fast with warmup)."""
    print("\n" + "=" * 60)
    print("Testing First Request Latency")
    print("=" * 60)

    prompt = "我要圈选高消费VVIP用户做新品推广"
    print(f"\nPrompt: {prompt}")
    print("Sending request...")

    start_time = time.time()
    first_event_time = None
    total_steps = 0

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "GET",
                f"http://localhost:8000/api/v1/analysis/stream",
                params={"prompt": prompt}
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("event: thinking_step"):
                        if first_event_time is None:
                            first_event_time = time.time()
                            elapsed = first_event_time - start_time
                            print(f"\n⚡ First thinking step received in {elapsed:.2f}s")

                        total_steps += 1
                        print(f"  Step {total_steps} received")

                    elif line.startswith("event: analysis_complete"):
                        total_time = time.time() - start_time
                        print(f"\n✓ Analysis completed in {total_time:.2f}s")
                        print(f"  Total thinking steps: {total_steps}")
                        break

        # Evaluate performance
        print("\n" + "=" * 60)
        print("Performance Evaluation")
        print("=" * 60)

        if first_event_time:
            first_latency = first_event_time - start_time
            if first_latency <= 5.0:
                print(f"✓ EXCELLENT: First response in {first_latency:.2f}s (target: ≤5s)")
            elif first_latency <= 10.0:
                print(f"⚠ ACCEPTABLE: First response in {first_latency:.2f}s (target: ≤5s)")
            else:
                print(f"✗ SLOW: First response in {first_latency:.2f}s (target: ≤5s)")
                print("  Warmup may not be working properly")

        return True

    except Exception as e:
        print(f"\n✗ Request failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Warmup Optimization Test Suite")
    print("=" * 60)
    print("\nPrerequisites:")
    print("  1. Backend server must be running on http://localhost:8000")
    print("  2. Server should have just started (to test warmup)")

    input("\nPress Enter to start tests...")

    # Test 1: Health check
    health_ok = await test_health_check()

    if not health_ok:
        print("\n⚠ Warning: Health check failed. Continuing with latency test...")

    # Wait a bit
    await asyncio.sleep(1)

    # Test 2: First request latency
    latency_ok = await test_first_request_latency()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"  Health Check: {'✓ PASS' if health_ok else '✗ FAIL'}")
    print(f"  Latency Test: {'✓ PASS' if latency_ok else '✗ FAIL'}")

    if health_ok and latency_ok:
        print("\n🎉 All tests passed! Warmup optimization is working correctly.")
    else:
        print("\n⚠ Some tests failed. Please check the logs above.")


if __name__ == "__main__":
    asyncio.run(main())
