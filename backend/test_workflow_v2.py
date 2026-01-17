"""
Test script for the refactored LangGraph workflow.

测试新的多轮对话工作流。
"""
import asyncio
import logging
from app.agent.graph import run_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_scenario_1_clear_intent():
    """测试场景1: 明确的意图，应该直接走完整个流程."""
    print("\n" + "="*60)
    print("测试场景1: 明确的意图")
    print("="*60)

    user_input = "我要为春季新款手袋上市做一次推广，目标是提升转化率。圈选VVIP和VIP客户，年龄在25-44岁，近12个月消费超过10万元。"

    result = await run_agent(user_input)

    print(f"\n意图状态: {result.get('intent_status')}")
    print(f"匹配状态: {result.get('match_status')}")
    print(f"\n最终响应:\n{result.get('final_response', '无')}")

    if result.get('prediction_result'):
        pred = result['prediction_result']
        print(f"\n预测结果:")
        print(f"  - 圈选人数: {pred.get('audience_size')}")
        print(f"  - 预估转化率: {pred.get('conversion_rate'):.2%}")
        print(f"  - 预估收入: ¥{pred.get('estimated_revenue'):,.0f}")
        print(f"  - ROI: {pred.get('roi'):.2f}倍")


async def test_scenario_2_ambiguous_intent():
    """测试场景2: 模糊的意图，应该返回澄清问题."""
    print("\n" + "="*60)
    print("测试场景2: 模糊的意图")
    print("="*60)

    user_input = "帮我圈选一些用户"

    result = await run_agent(user_input)

    print(f"\n意图状态: {result.get('intent_status')}")
    print(f"\n澄清问题:\n{result.get('clarification_question', '无')}")
    print(f"\n最终响应:\n{result.get('final_response', '无')}")


async def test_scenario_3_multi_turn():
    """测试场景3: 多轮对话."""
    print("\n" + "="*60)
    print("测试场景3: 多轮对话")
    print("="*60)

    # 第一轮：模糊意图
    print("\n[第1轮] 用户输入: 我想做一次营销活动")
    conversation_history = []

    result1 = await run_agent("我想做一次营销活动", conversation_history)
    print(f"意图状态: {result1.get('intent_status')}")
    print(f"Agent回复: {result1.get('final_response', result1.get('clarification_question', '无'))}")

    # 更新对话历史
    conversation_history.append({"role": "user", "content": "我想做一次营销活动"})
    conversation_history.append({"role": "assistant", "content": result1.get('final_response', result1.get('clarification_question', ''))})

    # 第二轮：提供更多信息
    print("\n[第2轮] 用户输入: 目标是提升手袋的转化率，圈选VIP客户")
    result2 = await run_agent("目标是提升手袋的转化率，圈选VIP客户", conversation_history)
    print(f"意图状态: {result2.get('intent_status')}")
    print(f"匹配状态: {result2.get('match_status')}")

    if result2.get('prediction_result'):
        pred = result2['prediction_result']
        print(f"\n预测结果:")
        print(f"  - 圈选人数: {pred.get('audience_size')}")
        print(f"  - 预估转化率: {pred.get('conversion_rate'):.2%}")


async def test_scenario_4_feature_matching():
    """测试场景4: 特征匹配测试."""
    print("\n" + "="*60)
    print("测试场景4: 特征匹配")
    print("="*60)

    user_input = "圈选近3个月在海外消费过、且对手袋感兴趣的女性VVIP客户"

    result = await run_agent(user_input)

    print(f"\n意图状态: {result.get('intent_status')}")
    print(f"匹配状态: {result.get('match_status')}")

    if result.get('matched_features'):
        print(f"\n匹配的特征:")
        for feat in result['matched_features']:
            print(f"  - {feat['description']}")

    if result.get('strategy_explanation'):
        print(f"\n策略解释:\n{result['strategy_explanation']}")


async def main():
    """运行所有测试场景."""
    print("\n" + "="*60)
    print("LangGraph 重构工作流测试")
    print("="*60)

    try:
        # 测试场景1: 明确意图
        await test_scenario_1_clear_intent()

        # 测试场景2: 模糊意图
        await test_scenario_2_ambiguous_intent()

        # 测试场景3: 多轮对话
        await test_scenario_3_multi_turn()

        # 测试场景4: 特征匹配
        await test_scenario_4_feature_matching()

        print("\n" + "="*60)
        print("所有测试完成！")
        print("="*60)

    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        print(f"\n❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
