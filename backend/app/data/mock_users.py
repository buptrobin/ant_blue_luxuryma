"""Mock user data with rich feature tags for luxury marketing scenarios."""
from typing import TypedDict, Optional, Any
from datetime import datetime, timedelta
import random


# Type alias for backward compatibility
User = dict[str, Any]


class UserFeatures(TypedDict):
    """Extended user features for marketing segmentation."""
    # 基础信息
    id: str
    name: str
    tier: str  # 'VVIP', 'VIP', 'Member'
    score: int
    recentStore: str
    lastVisit: str
    reason: str

    # 人口属性
    gender: str  # 'M' (男) / 'F' (女)
    age_group: str  # '25-34', '35-44', '45-54', '55+'
    city_tier: str  # 'T1' (一线) / 'T2' (新一线) / 'T3' (二线)
    occupation: str  # '企业高管', '企业家', '专业人士', '自由职业', '继承人/家族企业'

    # 消费力指标
    r12m_spending: int  # 近12个月消费额（CNY）
    avg_order_value: int  # 平均客单价（CNY）
    purchase_frequency: int  # 年购买频次
    last_purchase_days: int  # 距上次购买天数
    has_overseas_purchase: bool  # 最近3个月有海外消费记录
    overseas_spending_12m: int  # 近12个月海外消费额（CNY）

    # 品牌忠诚度
    preferred_brands: list  # 偏好品牌列表 ['Hermès', 'Chanel', 'Louis Vuitton', ...]
    brand_loyalty_score: int  # 品牌忠诚度分数 (0-100)
    style_preference: str  # 款式偏好: '经典', '时尚', '前卫', '度假休闲', '商务正式'

    # 品类兴趣标签
    category_browsing: dict  # 品类浏览次数 {"手袋": 8, "配饰": 5, ...}
    cart_items_pending: list  # 加购未支付品类
    favorites: list  # 收藏品类
    category_purchases: dict  # 历史购买品类统计

    # 品牌活跃度
    store_visits_90d: int  # 近90天门店到访次数
    online_active_days_30d: int  # 近30天线上活跃天数
    email_open_rate: float  # 邮件打开率 0-1
    email_click_rate: float  # 邮件点击率 0-1
    event_participation: int  # 活动参与次数

    # 会员权益使用
    vip_lounge_visits: int  # VIP休息室使用次数（近12个月）
    personal_shopper_usage: int  # 私人顾问服务使用次数（近12个月）
    exclusive_event_invites: int  # 独家活动邀请次数（近12个月）
    birthday_gift_redeemed: bool  # 生日礼物是否领取

    # 数字行为
    app_daily_active: int  # APP日活天数（近30天）
    wechat_interaction: int  # 微信互动次数（近30天）
    live_stream_participation: int  # 直播参与次数（近90天）
    mini_program_usage: int  # 小程序使用天数（近30天）

    # 营销响应
    last_email_click_days: int  # 距上次邮件点击天数
    referral_count: int  # 推荐好友数量
    social_engagement: int  # 社交媒体互动次数
    customer_service_contact_30d: int  # 近30天客服咨询次数

    # 生命周期
    member_since_days: int  # 会员天数
    first_purchase_days: int  # 距首次购买天数

    # 风控与排除
    complaints_open: int  # 未结案投诉数
    return_rate: float  # 退货率 0-1
    payment_failures_30d: int  # 近30天支付失败次数

    # 营销疲劳度
    last_campaign_days: int  # 距上次营销触达天数
    campaign_exposure_30d: int  # 近30天营销触达次数


# 扩展的mock用户数据库，包含完整特征标签
MOCK_USERS_WITH_FEATURES: list[UserFeatures] = [
    # VVIP Tier - Ultra High Net Worth Individuals
    {
        "id": "1",
        "name": "王女士",
        "tier": "VVIP",
        "score": 98,
        "recentStore": "上海恒隆广场店",
        "lastVisit": "3天前",
        "reason": "上月到访上海恒隆店3次 + 点击新品邮件 + 年度消费180万",

        # 人口属性
        "gender": "F",
        "age_group": "35-44",
        "city_tier": "T1",
        "occupation": "企业家",

        # 消费力指标
        "r12m_spending": 1800000,
        "avg_order_value": 85000,
        "purchase_frequency": 21,
        "last_purchase_days": 8,
        "has_overseas_purchase": True,
        "overseas_spending_12m": 520000,

        # 品牌忠诚度
        "preferred_brands": ["Hermès", "Chanel", "Dior", "Cartier"],
        "brand_loyalty_score": 95,
        "style_preference": "经典",

        # 品类兴趣
        "category_browsing": {"手袋": 12, "高级珠宝": 8, "成衣": 15, "配饰": 6},
        "cart_items_pending": ["限量款手袋", "珍珠项链"],
        "favorites": ["手袋", "高级珠宝", "丝巾"],
        "category_purchases": {"手袋": 8, "高级珠宝": 3, "成衣": 6, "配饰": 4},

        # 品牌活跃度
        "store_visits_90d": 9,
        "online_active_days_30d": 18,
        "email_open_rate": 0.85,
        "email_click_rate": 0.62,
        "event_participation": 5,

        # 会员权益使用
        "vip_lounge_visits": 12,
        "personal_shopper_usage": 8,
        "exclusive_event_invites": 15,
        "birthday_gift_redeemed": True,

        # 数字行为
        "app_daily_active": 22,
        "wechat_interaction": 35,
        "live_stream_participation": 4,
        "mini_program_usage": 18,

        # 营销响应
        "last_email_click_days": 2,
        "referral_count": 3,
        "social_engagement": 28,
        "customer_service_contact_30d": 2,

        # 生命周期
        "member_since_days": 1850,
        "first_purchase_days": 1820,

        # 风控
        "complaints_open": 0,
        "return_rate": 0.05,
        "payment_failures_30d": 0,

        # 疲劳度
        "last_campaign_days": 3,
        "campaign_exposure_30d": 8,
    },
    {
        "id": "2",
        "name": "陈小姐",
        "tier": "VIP",
        "score": 95,
        "recentStore": "北京SKP",
        "lastVisit": "1周前",
        "reason": "过去90天购买过2件配饰 + 浏览手袋页面超过10次 + 邮件打开率高",

        # 人口属性
        "gender": "F",
        "age_group": "25-34",
        "city_tier": "T1",
        "occupation": "专业人士",

        # 消费力指标
        "r12m_spending": 280000,
        "avg_order_value": 28000,
        "purchase_frequency": 10,
        "last_purchase_days": 15,
        "has_overseas_purchase": True,
        "overseas_spending_12m": 95000,

        # 品牌忠诚度
        "preferred_brands": ["Chanel", "Dior", "Gucci", "Prada"],
        "brand_loyalty_score": 82,
        "style_preference": "时尚",

        # 品类兴趣
        "category_browsing": {"手袋": 18, "配饰": 12, "鞋履": 7, "成衣": 5},
        "cart_items_pending": ["春季新款手袋"],
        "favorites": ["手袋", "配饰", "太阳镜"],
        "category_purchases": {"手袋": 3, "配饰": 5, "鞋履": 2},

        # 品牌活跃度
        "store_visits_90d": 4,
        "online_active_days_30d": 22,
        "email_open_rate": 0.78,
        "email_click_rate": 0.45,
        "event_participation": 3,

        # 会员权益使用
        "vip_lounge_visits": 6,
        "personal_shopper_usage": 4,
        "exclusive_event_invites": 8,
        "birthday_gift_redeemed": True,

        # 数字行为
        "app_daily_active": 25,
        "wechat_interaction": 42,
        "live_stream_participation": 6,
        "mini_program_usage": 22,

        # 营销响应
        "last_email_click_days": 5,
        "referral_count": 1,
        "social_engagement": 15,
        "customer_service_contact_30d": 1,

        # 生命周期
        "member_since_days": 920,
        "first_purchase_days": 900,

        # 风控
        "complaints_open": 0,
        "return_rate": 0.10,
        "payment_failures_30d": 0,

        # 疲劳度
        "last_campaign_days": 7,
        "campaign_exposure_30d": 6,
    },
    {
        "id": "3",
        "name": "李先生",
        "tier": "VVIP",
        "score": 92,
        "recentStore": "成都IFS",
        "lastVisit": "2周前",
        "reason": "年度消费总额 Top 5% + 情人节礼品搜索记录 + VIP品鉴会参与者",

        # 人口属性
        "gender": "M",
        "age_group": "45-54",
        "city_tier": "T2",
        "occupation": "企业高管",

        # 消费力指标
        "r12m_spending": 1200000,
        "avg_order_value": 95000,
        "purchase_frequency": 13,
        "last_purchase_days": 22,
        "has_overseas_purchase": True,
        "overseas_spending_12m": 380000,

        # 品牌忠诚度
        "preferred_brands": ["Hermès", "Bottega Veneta", "Montblanc", "Cartier"],
        "brand_loyalty_score": 88,
        "style_preference": "商务正式",

        # 品类兴趣
        "category_browsing": {"手袋": 5, "配饰": 8, "男士皮具": 15, "高级珠宝": 6},
        "cart_items_pending": [],
        "favorites": ["男士皮具", "高级珠宝", "手表"],
        "category_purchases": {"手袋": 2, "男士皮具": 7, "高级珠宝": 2, "配饰": 2},

        # 品牌活跃度
        "store_visits_90d": 3,
        "online_active_days_30d": 12,
        "email_open_rate": 0.65,
        "email_click_rate": 0.38,
        "event_participation": 4,

        # 会员权益使用
        "vip_lounge_visits": 8,
        "personal_shopper_usage": 6,
        "exclusive_event_invites": 12,
        "birthday_gift_redeemed": True,

        # 数字行为
        "app_daily_active": 10,
        "wechat_interaction": 18,
        "live_stream_participation": 1,
        "mini_program_usage": 8,

        # 营销响应
        "last_email_click_days": 10,
        "referral_count": 2,
        "social_engagement": 8,
        "customer_service_contact_30d": 0,

        # 生命周期
        "member_since_days": 1650,
        "first_purchase_days": 1600,

        # 风控
        "complaints_open": 0,
        "return_rate": 0.08,
        "payment_failures_30d": 0,

        # 疲劳度
        "last_campaign_days": 14,
        "campaign_exposure_30d": 4,
    },
    {
        "id": "4",
        "name": "张女士",
        "tier": "Member",
        "score": 88,
        "recentStore": "深圳湾万象城",
        "lastVisit": "5天前",
        "reason": "近期升级为金卡会员 + 收藏了春季新款 + 首次购买满意度高",

        # 人口属性
        "gender": "F",
        "age_group": "25-34",
        "city_tier": "T1",
        "occupation": "专业人士",

        # 消费力指标
        "r12m_spending": 95000,
        "avg_order_value": 19000,
        "purchase_frequency": 5,
        "last_purchase_days": 18,
        "has_overseas_purchase": False,
        "overseas_spending_12m": 0,

        # 品牌忠诚度
        "preferred_brands": ["Coach", "Michael Kors", "Gucci"],
        "brand_loyalty_score": 68,
        "style_preference": "时尚",

        # 品类兴趣
        "category_browsing": {"手袋": 9, "配饰": 6, "成衣": 8, "鞋履": 4},
        "cart_items_pending": ["春季手袋", "丝巾"],
        "favorites": ["手袋", "丝巾", "太阳镜"],
        "category_purchases": {"手袋": 2, "配饰": 2, "成衣": 1},

        # 品牌活跃度
        "store_visits_90d": 2,
        "online_active_days_30d": 16,
        "email_open_rate": 0.72,
        "email_click_rate": 0.51,
        "event_participation": 1,

        # 会员权益使用
        "vip_lounge_visits": 1,
        "personal_shopper_usage": 1,
        "exclusive_event_invites": 2,
        "birthday_gift_redeemed": False,

        # 数字行为
        "app_daily_active": 18,
        "wechat_interaction": 28,
        "live_stream_participation": 3,
        "mini_program_usage": 15,

        # 营销响应
        "last_email_click_days": 6,
        "referral_count": 0,
        "social_engagement": 12,
        "customer_service_contact_30d": 3,

        # 生命周期
        "member_since_days": 180,
        "first_purchase_days": 165,

        # 风控
        "complaints_open": 0,
        "return_rate": 0.0,
        "payment_failures_30d": 0,

        # 疲劳度
        "last_campaign_days": 5,
        "campaign_exposure_30d": 5,
    },
    {
        "id": "5",
        "name": "刘小姐",
        "tier": "VIP",
        "score": 85,
        "recentStore": "杭州大厦",
        "lastVisit": "1个月前",
        "reason": "高频浏览度假系列 + 曾购买过同品牌小皮具 + 春季新品收藏",

        # 人口属性
        "gender": "F",
        "age_group": "35-44",
        "city_tier": "T2",
        "occupation": "自由职业",

        # 消费力指标
        "r12m_spending": 220000,
        "avg_order_value": 22000,
        "purchase_frequency": 10,
        "last_purchase_days": 45,
        "has_overseas_purchase": True,
        "overseas_spending_12m": 150000,

        # 品牌忠诚度
        "preferred_brands": ["Louis Vuitton", "Fendi", "Celine"],
        "brand_loyalty_score": 75,
        "style_preference": "度假休闲",

        # 品类兴趣
        "category_browsing": {"手袋": 7, "度假系列": 14, "配饰": 5, "成衣": 9},
        "cart_items_pending": [],
        "favorites": ["度假系列", "手袋", "泳装"],
        "category_purchases": {"手袋": 2, "度假系列": 3, "配饰": 3, "成衣": 2},

        # 品牌活跃度
        "store_visits_90d": 1,
        "online_active_days_30d": 8,
        "email_open_rate": 0.55,
        "email_click_rate": 0.28,
        "event_participation": 2,

        # 会员权益使用
        "vip_lounge_visits": 3,
        "personal_shopper_usage": 2,
        "exclusive_event_invites": 5,
        "birthday_gift_redeemed": False,

        # 数字行为
        "app_daily_active": 8,
        "wechat_interaction": 15,
        "live_stream_participation": 2,
        "mini_program_usage": 6,

        # 营销响应
        "last_email_click_days": 35,
        "referral_count": 1,
        "social_engagement": 6,
        "customer_service_contact_30d": 0,

        # 生命周期
        "member_since_days": 850,
        "first_purchase_days": 820,

        # 风控
        "complaints_open": 0,
        "return_rate": 0.15,
        "payment_failures_30d": 1,

        # 疲劳度
        "last_campaign_days": 30,
        "campaign_exposure_30d": 3,
    },
    {
        "id": "6",
        "name": "赵先生",
        "tier": "VVIP",
        "score": 93,
        "recentStore": "北京商务会所",
        "lastVisit": "4天前",
        "reason": "春节期间购买礼品套装 + 经常参加VIP活动 + 私人顾问服务用户",

        # 人口属性
        "gender": "M",
        "age_group": "45-54",
        "city_tier": "T1",
        "occupation": "企业家",

        # 消费力指标
        "r12m_spending": 1500000,
        "avg_order_value": 120000,
        "purchase_frequency": 13,
        "last_purchase_days": 6,
        "has_overseas_purchase": True,
        "overseas_spending_12m": 680000,

        # 品牌忠诚度
        "preferred_brands": ["Hermès", "Loro Piana", "Brioni", "Patek Philippe"],
        "brand_loyalty_score": 92,
        "style_preference": "经典",

        # 品类兴趣
        "category_browsing": {"手袋": 6, "高级珠宝": 10, "男士皮具": 8, "配饰": 7},
        "cart_items_pending": ["定制手袋"],
        "favorites": ["高级珠宝", "男士皮具", "手表"],
        "category_purchases": {"手袋": 3, "高级珠宝": 4, "男士皮具": 4, "配饰": 2},

        # 品牌活跃度
        "store_visits_90d": 8,
        "online_active_days_30d": 10,
        "email_open_rate": 0.82,
        "email_click_rate": 0.58,
        "event_participation": 6,

        # 会员权益使用
        "vip_lounge_visits": 15,
        "personal_shopper_usage": 12,
        "exclusive_event_invites": 18,
        "birthday_gift_redeemed": True,

        # 数字行为
        "app_daily_active": 12,
        "wechat_interaction": 22,
        "live_stream_participation": 2,
        "mini_program_usage": 10,

        # 营销响应
        "last_email_click_days": 4,
        "referral_count": 5,
        "social_engagement": 18,
        "customer_service_contact_30d": 1,

        # 生命周期
        "member_since_days": 2100,
        "first_purchase_days": 2080,

        # 风控
        "complaints_open": 0,
        "return_rate": 0.03,
        "payment_failures_30d": 0,

        # 疲劳度
        "last_campaign_days": 4,
        "campaign_exposure_30d": 7,
    },
    {
        "id": "7",
        "name": "苏女士",
        "tier": "VIP",
        "score": 89,
        "recentStore": "南京德基广场",
        "lastVisit": "6天前",
        "reason": "近期加购购物袋且多次浏览春季新品 + 社交媒体互动活跃",

        # 人口属性
        "gender": "F",
        "age_group": "35-44",
        "city_tier": "T2",
        "occupation": "企业高管",

        # 消费力指标
        "r12m_spending": 310000,
        "avg_order_value": 31000,
        "purchase_frequency": 10,
        "last_purchase_days": 25,
        "has_overseas_purchase": True,
        "overseas_spending_12m": 120000,

        # 品牌忠诚度
        "preferred_brands": ["Chanel", "Dior", "Valentino", "Givenchy"],
        "brand_loyalty_score": 80,
        "style_preference": "时尚",

        # 品类兴趣
        "category_browsing": {"手袋": 15, "成衣": 12, "配饰": 8, "鞋履": 6},
        "cart_items_pending": ["春季托特包", "丝巾"],
        "favorites": ["手袋", "成衣", "配饰"],
        "category_purchases": {"手袋": 4, "成衣": 3, "配饰": 2, "鞋履": 1},

        # 品牌活跃度
        "store_visits_90d": 3,
        "online_active_days_30d": 20,
        "email_open_rate": 0.75,
        "email_click_rate": 0.48,
        "event_participation": 2,

        # 会员权益使用
        "vip_lounge_visits": 5,
        "personal_shopper_usage": 3,
        "exclusive_event_invites": 6,
        "birthday_gift_redeemed": True,

        # 数字行为
        "app_daily_active": 24,
        "wechat_interaction": 48,
        "live_stream_participation": 5,
        "mini_program_usage": 20,

        # 营销响应
        "last_email_click_days": 8,
        "referral_count": 2,
        "social_engagement": 32,
        "customer_service_contact_30d": 2,

        # 生命周期
        "member_since_days": 680,
        "first_purchase_days": 650,

        # 风控
        "complaints_open": 0,
        "return_rate": 0.12,
        "payment_failures_30d": 0,

        # 疲劳度
        "last_campaign_days": 6,
        "campaign_exposure_30d": 6,
    },
    {
        "id": "8",
        "name": "郭小姐",
        "tier": "Member",
        "score": 82,
        "recentStore": "成都SKP",
        "lastVisit": "1周前",
        "reason": "浏览皮具类目超过8次 + 关注春季上新 + 新会员引导计划参与",

        # 人口属性
        "gender": "F",
        "age_group": "25-34",
        "city_tier": "T2",
        "occupation": "专业人士",

        # 消费力指标
        "r12m_spending": 65000,
        "avg_order_value": 16000,
        "purchase_frequency": 4,
        "last_purchase_days": 35,
        "has_overseas_purchase": False,
        "overseas_spending_12m": 0,

        # 品牌忠诚度
        "preferred_brands": ["Kate Spade", "Tory Burch", "Coach"],
        "brand_loyalty_score": 62,
        "style_preference": "时尚",

        # 品类兴趣
        "category_browsing": {"手袋": 11, "配饰": 7, "小皮具": 9, "鞋履": 3},
        "cart_items_pending": ["小号手袋"],
        "favorites": ["手袋", "小皮具", "钱包"],
        "category_purchases": {"手袋": 1, "配饰": 2, "小皮具": 1},

        # 品牌活跃度
        "store_visits_90d": 2,
        "online_active_days_30d": 14,
        "email_open_rate": 0.68,
        "email_click_rate": 0.42,
        "event_participation": 1,

        # 会员权益使用
        "vip_lounge_visits": 0,
        "personal_shopper_usage": 0,
        "exclusive_event_invites": 1,
        "birthday_gift_redeemed": False,

        # 数字行为
        "app_daily_active": 16,
        "wechat_interaction": 25,
        "live_stream_participation": 2,
        "mini_program_usage": 12,

        # 营销响应
        "last_email_click_days": 12,
        "referral_count": 0,
        "social_engagement": 9,
        "customer_service_contact_30d": 2,

        # 生命周期
        "member_since_days": 220,
        "first_purchase_days": 200,

        # 风控
        "complaints_open": 0,
        "return_rate": 0.0,
        "payment_failures_30d": 0,

        # 疲劳度
        "last_campaign_days": 7,
        "campaign_exposure_30d": 5,
    },
    {
        "id": "9",
        "name": "吴先生",
        "tier": "VVIP",
        "score": 96,
        "recentStore": "上海静安嘉里中心",
        "lastVisit": "2天前",
        "reason": "年度消费额Top 2% + 频繁参加线下品鉴会 + 限量款首购客户",

        # 人口属性
        "gender": "M",
        "age_group": "55+",
        "city_tier": "T1",
        "occupation": "继承人/家族企业",

        # 消费力指标
        "r12m_spending": 2200000,
        "avg_order_value": 180000,
        "purchase_frequency": 12,
        "last_purchase_days": 5,
        "has_overseas_purchase": True,
        "overseas_spending_12m": 1200000,

        # 品牌忠诚度
        "preferred_brands": ["Hermès", "Louis Vuitton", "Cartier", "Van Cleef & Arpels"],
        "brand_loyalty_score": 98,
        "style_preference": "经典",

        # 品类兴趣
        "category_browsing": {"手袋": 8, "高级珠宝": 15, "成衣": 10, "男士皮具": 12},
        "cart_items_pending": ["限量版手袋"],
        "favorites": ["高级珠宝", "限量系列", "男士皮具"],
        "category_purchases": {"手袋": 3, "高级珠宝": 5, "成衣": 2, "男士皮具": 2},

        # 品牌活跃度
        "store_visits_90d": 10,
        "online_active_days_30d": 15,
        "email_open_rate": 0.88,
        "email_click_rate": 0.65,
        "event_participation": 8,

        # 会员权益使用
        "vip_lounge_visits": 18,
        "personal_shopper_usage": 15,
        "exclusive_event_invites": 20,
        "birthday_gift_redeemed": True,

        # 数字行为
        "app_daily_active": 14,
        "wechat_interaction": 28,
        "live_stream_participation": 3,
        "mini_program_usage": 12,

        # 营销响应
        "last_email_click_days": 1,
        "referral_count": 4,
        "social_engagement": 22,
        "customer_service_contact_30d": 1,

        # 生命周期
        "member_since_days": 2300,
        "first_purchase_days": 2280,

        # 风控
        "complaints_open": 0,
        "return_rate": 0.02,
        "payment_failures_30d": 0,

        # 疲劳度
        "last_campaign_days": 2,
        "campaign_exposure_30d": 9,
    },
    {
        "id": "10",
        "name": "周女士",
        "tier": "VIP",
        "score": 91,
        "recentStore": "深圳书城",
        "lastVisit": "3周前",
        "reason": "点击营销邮件达10次 + 浏览手袋页面记录 + 参加线上直播2次",

        # 人口属性
        "gender": "F",
        "age_group": "35-44",
        "city_tier": "T1",
        "occupation": "企业高管",

        # 消费力指标
        "r12m_spending": 260000,
        "avg_order_value": 26000,
        "purchase_frequency": 10,
        "last_purchase_days": 28,
        "has_overseas_purchase": False,
        "overseas_spending_12m": 0,

        # 品牌忠诚度
        "preferred_brands": ["Gucci", "Prada", "Miu Miu", "Balenciaga"],
        "brand_loyalty_score": 78,
        "style_preference": "前卫",

        # 品类兴趣
        "category_browsing": {"手袋": 13, "配饰": 9, "成衣": 7, "鞋履": 5},
        "cart_items_pending": [],
        "favorites": ["手袋", "配饰", "鞋履"],
        "category_purchases": {"手袋": 4, "配饰": 3, "成衣": 2, "鞋履": 1},

        # 品牌活跃度
        "store_visits_90d": 1,
        "online_active_days_30d": 18,
        "email_open_rate": 0.80,
        "email_click_rate": 0.55,
        "event_participation": 3,

        # 会员权益使用
        "vip_lounge_visits": 4,
        "personal_shopper_usage": 2,
        "exclusive_event_invites": 6,
        "birthday_gift_redeemed": True,

        # 数字行为
        "app_daily_active": 20,
        "wechat_interaction": 38,
        "live_stream_participation": 7,
        "mini_program_usage": 18,

        # 营销响应
        "last_email_click_days": 9,
        "referral_count": 1,
        "social_engagement": 16,
        "customer_service_contact_30d": 1,

        # 生命周期
        "member_since_days": 780,
        "first_purchase_days": 750,

        # 风控
        "complaints_open": 0,
        "return_rate": 0.11,
        "payment_failures_30d": 0,

        # 疲劳度
        "last_campaign_days": 9,
        "campaign_exposure_30d": 7,
    },
]

# 为了向后兼容，保留原有的简化版本
MOCK_USERS = [
    {
        "id": user["id"],
        "name": user["name"],
        "tier": user["tier"],
        "score": user["score"],
        "recentStore": user["recentStore"],
        "lastVisit": user["lastVisit"],
        "reason": user["reason"],
    }
    for user in MOCK_USERS_WITH_FEATURES[:10]  # 只取前10个用户
]

# 常量定义
AVG_ORDER_VALUE = 18000  # 平均客单价（CNY）
TIER_AVG_ORDER_VALUE = {
    "VVIP": 45000,
    "VIP": 22000,
    "Member": 12000
}
MIN_TIER_RANK = {"Member": 1, "VIP": 2, "VVIP": 3}

# 特征标签定义
FEATURE_TAGS = {
    # 消费力标签
    "high_value": "高价值客户 (R12M > ¥500k)",
    "medium_value": "中等价值客户 (R12M ¥100k-500k)",
    "growth_potential": "增长潜力客户 (R12M ¥50k-100k)",

    # 品类兴趣标签
    "handbag_lover": "手袋爱好者 (浏览手袋>10次)",
    "jewelry_interested": "珠宝兴趣 (浏览珠宝>5次)",
    "cart_ready": "加购待转化 (有加购未支付)",

    # 活跃度标签
    "highly_active": "高度活跃 (30天活跃>15天)",
    "store_regular": "门店常客 (90天到店>5次)",
    "email_responsive": "邮件响应者 (点击率>50%)",

    # 营销响应标签
    "event_participant": "活动参与者 (参与>3次)",
    "referral_contributor": "推荐贡献者 (推荐>1人)",
    "social_active": "社交活跃 (互动>20次)",

    # 风控标签
    "low_risk": "低风险 (无投诉/退货率<10%)",
    "medium_risk": "中风险 (退货率10-20%)",
    "high_risk": "高风险 (有投诉或退货率>20%)",
}

# 筛选规则示例
FILTER_RULES = {
    "消费力门槛": {
        "特征": ["r12m_spending", "tier"],
        "逻辑": "r12m_spending > 100000 OR tier IN ['VVIP', 'VIP']",
        "描述": "年消费额超10万或VIP及以上会员"
    },
    "品类兴趣_手袋": {
        "特征": ["category_browsing['手袋']", "cart_items_pending"],
        "逻辑": "category_browsing['手袋'] > 5 AND '手袋' IN cart_items_pending",
        "描述": "近30天浏览手袋>5次且有加购未支付"
    },
    "品牌活跃度": {
        "特征": ["store_visits_90d", "email_click_rate"],
        "逻辑": "store_visits_90d > 0 OR email_click_rate > 0",
        "描述": "近3个月到访门店或有邮件点击"
    },
    "排除_疲劳度": {
        "特征": ["last_purchase_days", "category_purchases['手袋']"],
        "逻辑": "NOT (last_purchase_days < 7 AND category_purchases['手袋'] > 0)",
        "描述": "排除过去7天购买过手袋的用户"
    },
    "排除_风控": {
        "特征": ["complaints_open"],
        "逻辑": "complaints_open == 0",
        "描述": "排除有未结案投诉的用户"
    }
}


def get_mock_users() -> list[dict]:
    """获取简化版mock用户（向后兼容）."""
    return MOCK_USERS.copy()


def get_users_with_features() -> list[UserFeatures]:
    """获取完整特征标签的用户数据."""
    return MOCK_USERS_WITH_FEATURES.copy()


def get_users_by_tier(tier: str) -> list[UserFeatures]:
    """按会员等级筛选用户."""
    return [u for u in MOCK_USERS_WITH_FEATURES if u["tier"] == tier]


def get_high_value_users(min_r12m: int = 500000) -> list[UserFeatures]:
    """按年消费额筛选高价值用户."""
    return [u for u in MOCK_USERS_WITH_FEATURES if u["r12m_spending"] >= min_r12m]


def filter_by_category_interest(category: str, min_views: int = 5) -> list[UserFeatures]:
    """按品类兴趣筛选用户."""
    return [
        u for u in MOCK_USERS_WITH_FEATURES
        if u["category_browsing"].get(category, 0) >= min_views
    ]


def filter_active_users(min_active_days: int = 15) -> list[UserFeatures]:
    """筛选活跃用户."""
    return [
        u for u in MOCK_USERS_WITH_FEATURES
        if u["online_active_days_30d"] >= min_active_days
    ]


def filter_cart_ready_users(category: str = None) -> list[UserFeatures]:
    """筛选有加购未支付的用户."""
    if category:
        return [
            u for u in MOCK_USERS_WITH_FEATURES
            if any(category in item for item in u["cart_items_pending"])
        ]
    return [u for u in MOCK_USERS_WITH_FEATURES if len(u["cart_items_pending"]) > 0]


def exclude_fatigued_users(days: int = 7, category: str = None) -> list[UserFeatures]:
    """排除营销疲劳用户."""
    filtered = []
    for u in MOCK_USERS_WITH_FEATURES:
        # 检查最近是否购买过
        if u["last_purchase_days"] < days:
            if category and u["category_purchases"].get(category, 0) > 0:
                continue  # 排除
        filtered.append(u)
    return filtered


def exclude_risk_users() -> list[UserFeatures]:
    """排除风险用户（有投诉或退货率高）."""
    return [
        u for u in MOCK_USERS_WITH_FEATURES
        if u["complaints_open"] == 0 and u["return_rate"] < 0.20
    ]
