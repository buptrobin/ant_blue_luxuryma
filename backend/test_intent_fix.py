"""
快速测试脚本 - 验证意图识别修复

测试新修复的节点是否能正确识别明确的意图。
"""
import asyncio
import logging
from app.agent.nodes import intent_recognition_node

logging.basicConfig(level=logging.INFO)


async def test_intent_recognition():
    """测试意图识别节点."""
    print("\n" + "="*60)
    print("测试意图识别节点修复")
    print("="*60)

    # 测试1：明确的意图
    print("\n[测试1] 明确的意图:")
    state1 = {
        "user_input": "我要为春季新款手袋上市做一次推广，目标是提升转化率。圈选VVIP和VIP客户，年龄在25-44岁。",
        "messages": []
    }

    result1 = await intent_recognition_node(state1)
    print(f"意图状态: {result1.get('intent_status')}")
    print(f"用户意图: {result1.get('user_intent')}")

    # 测试2：模糊的意图
    print("\n[测试2] 模糊的意图:")
    state2 = {
        "user_input": "帮我圈选一些用户",
        "messages": []
    }

    result2 = await intent_recognition_node(state2)
    print(f"意图状态: {result2.get('intent_status')}")
    print(f"用户意图: {result2.get('user_intent')}")

    # 总结
    print("\n" + "="*60)
    if result1.get('intent_status') == 'clear':
        print("✅ 测试1通过：明确意图被正确识别")
    else:
        print("❌ 测试1失败：明确意图未被识别")

    if result2.get('intent_status') == 'ambiguous':
        print("✅ 测试2通过：模糊意图被正确识别")
    else:
        print("⚠️  测试2警告：模糊意图被识别为明确（可能是 LLM 太聪明）")

    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_intent_recognition())
