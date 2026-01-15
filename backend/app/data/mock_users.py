"""Mock user data for testing and development."""
from typing import TypedDict


class User(TypedDict):
    """User data structure."""
    id: str
    name: str
    tier: str  # 'VVIP', 'VIP', 'Member'
    score: int
    recentStore: str
    lastVisit: str
    reason: str


MOCK_USERS: list[User] = [
    {
        "id": "1",
        "name": "王女士",
        "tier": "VVIP",
        "score": 98,
        "recentStore": "上海恒隆广场店",
        "lastVisit": "3天前",
        "reason": "上月到访上海恒隆店3次 + 点击新品邮件"
    },
    {
        "id": "2",
        "name": "陈小姐",
        "tier": "VIP",
        "score": 95,
        "recentStore": "北京SKP",
        "lastVisit": "1周前",
        "reason": "过去90天购买过2件配饰 + 浏览手袋页面超过10次"
    },
    {
        "id": "3",
        "name": "李先生",
        "tier": "VVIP",
        "score": 92,
        "recentStore": "成都IFS",
        "lastVisit": "2周前",
        "reason": "年度消费总额 Top 5% + 情人节礼品搜索记录"
    },
    {
        "id": "4",
        "name": "张女士",
        "tier": "Member",
        "score": 88,
        "recentStore": "深圳湾万象城",
        "lastVisit": "5天前",
        "reason": "近期升级为金卡会员 + 收藏了春季新款"
    },
    {
        "id": "5",
        "name": "刘小姐",
        "tier": "VIP",
        "score": 85,
        "recentStore": "杭州大厦",
        "lastVisit": "1个月前",
        "reason": "高频浏览度假系列 + 曾购买过同品牌小皮具"
    },
    {
        "id": "6",
        "name": "赵先生",
        "tier": "VVIP",
        "score": 93,
        "recentStore": "北京商务会所",
        "lastVisit": "4天前",
        "reason": "春节期间购买礼品套装 + 经常参加VIP活动"
    },
    {
        "id": "7",
        "name": "苏女士",
        "tier": "VIP",
        "score": 89,
        "recentStore": "南京德基广场",
        "lastVisit": "6天前",
        "reason": "近期加购购物袋且多次浏览春季新品"
    },
    {
        "id": "8",
        "name": "郭小姐",
        "tier": "Member",
        "score": 82,
        "recentStore": "成都SKP",
        "lastVisit": "1周前",
        "reason": "浏览皮具类目超过8次 + 关注春季上新"
    },
    {
        "id": "9",
        "name": "吴先生",
        "tier": "VVIP",
        "score": 96,
        "recentStore": "上海静安嘉里中心",
        "lastVisit": "2天前",
        "reason": "年度消费额Top 2% + 频繁参加线下品鉴会"
    },
    {
        "id": "10",
        "name": "周女士",
        "tier": "VIP",
        "score": 91,
        "recentStore": "深圳书城",
        "lastVisit": "3周前",
        "reason": "点击营销邮件达10次 + 浏览手袋页面记录"
    },
    {
        "id": "11",
        "name": "许小姐",
        "tier": "Member",
        "score": 87,
        "recentStore": "杭州大楼",
        "lastVisit": "10天前",
        "reason": "去年新增会员 + 已购买过1件配饰"
    },
    {
        "id": "12",
        "name": "何先生",
        "tier": "VVIP",
        "score": 94,
        "recentStore": "重庆IFS",
        "lastVisit": "5天前",
        "reason": "月均消费额Top 10% + 关注所有新品发布"
    },
    {
        "id": "13",
        "name": "范女士",
        "tier": "VIP",
        "score": 84,
        "recentStore": "北京燕莎购物中心",
        "lastVisit": "2周前",
        "reason": "浏览春季新品页面达5次 + 加购历史记录"
    },
    {
        "id": "14",
        "name": "丁小姐",
        "tier": "Member",
        "score": 80,
        "recentStore": "广州太古汇",
        "lastVisit": "15天前",
        "reason": "新注册会员 + 有浏览手袋商品的行为"
    },
    {
        "id": "15",
        "name": "曹先生",
        "tier": "VIP",
        "score": 90,
        "recentStore": "南京德基",
        "lastVisit": "1周前",
        "reason": "过去半年购买3件及以上 + 参加品牌活动2次"
    },
]

# Constants for business logic
AVG_ORDER_VALUE = 18000  # 客单价，单位：CNY
MIN_TIER_RANK = {"Member": 1, "VIP": 2, "VVIP": 3}

def get_mock_users() -> list[User]:
    """Get all mock users."""
    return MOCK_USERS.copy()
