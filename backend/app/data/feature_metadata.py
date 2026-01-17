"""特征元数据库 - 用于人群圈选的特征定义."""
from typing import TypedDict, Literal, Any


class FeatureMetadata(TypedDict):
    """特征元数据定义."""
    name: str  # 特征名称（字段名）
    display_name: str  # 显示名称（中文）
    type: Literal["numeric", "categorical", "boolean", "list"]  # 特征类型
    category: str  # 特征分类（用于组织）
    description: str  # 特征描述
    examples: list[str]  # 自然语言示例
    valid_operators: list[str]  # 支持的操作符
    value_range: Any  # 值域范围（可选）


# =====================================================
# 特征元数据库 - 按业务分类组织
# =====================================================

FEATURE_METADATA: dict[str, FeatureMetadata] = {
    # ========== 人口属性 ==========
    "gender": {
        "name": "gender",
        "display_name": "性别",
        "type": "categorical",
        "category": "人口属性",
        "description": "客户性别",
        "examples": ["女性客户", "男性用户", "性别为女"],
        "valid_operators": ["==", "in"],
        "value_range": ["M", "F"],
    },
    "age_group": {
        "name": "age_group",
        "display_name": "年龄段",
        "type": "categorical",
        "category": "人口属性",
        "description": "客户年龄段",
        "examples": ["25-34岁客户", "35-44岁的用户", "年龄在45-54岁"],
        "valid_operators": ["==", "in"],
        "value_range": ["25-34", "35-44", "45-54", "55+"],
    },
    "city_tier": {
        "name": "city_tier",
        "display_name": "城市等级",
        "type": "categorical",
        "category": "人口属性",
        "description": "客户所在城市等级",
        "examples": ["一线城市客户", "新一线城市", "二线城市用户"],
        "valid_operators": ["==", "in"],
        "value_range": ["T1", "T2", "T3"],
    },
    "occupation": {
        "name": "occupation",
        "display_name": "职业",
        "type": "categorical",
        "category": "人口属性",
        "description": "客户职业类型",
        "examples": ["企业高管", "企业家客户", "专业人士"],
        "valid_operators": ["==", "in"],
        "value_range": ["企业高管", "企业家", "专业人士", "自由职业", "继承人/家族企业"],
    },

    # ========== 会员等级 ==========
    "tier": {
        "name": "tier",
        "display_name": "会员等级",
        "type": "categorical",
        "category": "会员等级",
        "description": "客户会员等级",
        "examples": ["VVIP客户", "VIP会员", "白金会员", "普通会员"],
        "valid_operators": ["==", "in"],
        "value_range": ["VVIP", "VIP", "Member"],
    },

    # ========== 消费力指标 ==========
    "r12m_spending": {
        "name": "r12m_spending",
        "display_name": "近12个月消费额",
        "type": "numeric",
        "category": "消费力指标",
        "description": "客户近12个月累计消费金额（人民币）",
        "examples": ["消费额大于10万", "年度消费超过50万", "近一年消费10-30万"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 10000000},
    },
    "avg_order_value": {
        "name": "avg_order_value",
        "display_name": "平均客单价",
        "type": "numeric",
        "category": "消费力指标",
        "description": "客户平均每笔订单金额（人民币）",
        "examples": ["客单价大于5万", "平均单笔消费超过2万"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 1000000},
    },
    "purchase_frequency": {
        "name": "purchase_frequency",
        "display_name": "年购买频次",
        "type": "numeric",
        "category": "消费力指标",
        "description": "客户近12个月购买次数",
        "examples": ["购买频次大于10次", "年度购买超过5次"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 100},
    },
    "last_purchase_days": {
        "name": "last_purchase_days",
        "display_name": "距上次购买天数",
        "type": "numeric",
        "category": "消费力指标",
        "description": "距离最近一次购买的天数",
        "examples": ["最近30天内购买过", "距上次购买不超过7天", "最近一周有购买"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 3650},
    },
    "has_overseas_purchase": {
        "name": "has_overseas_purchase",
        "display_name": "有海外消费记录",
        "type": "boolean",
        "category": "消费力指标",
        "description": "最近3个月是否有海外消费记录",
        "examples": ["有海外消费记录", "最近在国外购买过", "海外购物用户"],
        "valid_operators": ["=="],
        "value_range": [True, False],
    },
    "overseas_spending_12m": {
        "name": "overseas_spending_12m",
        "display_name": "近12个月海外消费额",
        "type": "numeric",
        "category": "消费力指标",
        "description": "客户近12个月海外消费金额（人民币）",
        "examples": ["海外消费超过10万", "国外购买金额大于50万"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 10000000},
    },

    # ========== 品牌忠诚度 ==========
    "brand_loyalty_score": {
        "name": "brand_loyalty_score",
        "display_name": "品牌忠诚度分数",
        "type": "numeric",
        "category": "品牌忠诚度",
        "description": "客户品牌忠诚度评分（0-100分）",
        "examples": ["忠诚度大于80分", "品牌忠诚度高", "忠诚度评分超过90"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 100},
    },
    "style_preference": {
        "name": "style_preference",
        "display_name": "款式偏好",
        "type": "categorical",
        "category": "品牌忠诚度",
        "description": "客户喜欢的款式风格",
        "examples": ["经典款式爱好者", "时尚风格客户", "偏好前卫设计"],
        "valid_operators": ["==", "in"],
        "value_range": ["经典", "时尚", "前卫", "度假休闲", "商务正式"],
    },

    # ========== 品类兴趣 ==========
    "category_browsing_handbag": {
        "name": "category_browsing.手袋",
        "display_name": "手袋浏览次数",
        "type": "numeric",
        "category": "品类兴趣",
        "description": "客户浏览手袋品类的次数（近30天）",
        "examples": ["浏览手袋超过10次", "手袋品类浏览大于5次"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 1000},
    },
    "category_browsing_jewelry": {
        "name": "category_browsing.高级珠宝",
        "display_name": "珠宝浏览次数",
        "type": "numeric",
        "category": "品类兴趣",
        "description": "客户浏览高级珠宝品类的次数（近30天）",
        "examples": ["浏览珠宝超过5次", "珠宝品类感兴趣"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 1000},
    },
    "cart_items_pending": {
        "name": "cart_items_pending",
        "display_name": "加购未支付商品",
        "type": "list",
        "category": "品类兴趣",
        "description": "客户加入购物车但未支付的商品品类",
        "examples": ["加购了手袋未下单", "购物车有商品待支付", "加购未购买"],
        "valid_operators": ["contains", "not_empty", "empty"],
        "value_range": None,
    },

    # ========== 品牌活跃度 ==========
    "store_visits_90d": {
        "name": "store_visits_90d",
        "display_name": "近90天门店到访次数",
        "type": "numeric",
        "category": "品牌活跃度",
        "description": "客户近90天到访线下门店的次数",
        "examples": ["门店到访超过3次", "近3个月到店5次以上"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 100},
    },
    "online_active_days_30d": {
        "name": "online_active_days_30d",
        "display_name": "近30天线上活跃天数",
        "type": "numeric",
        "category": "品牌活跃度",
        "description": "客户近30天线上活跃的天数",
        "examples": ["线上活跃超过15天", "近1个月活跃天数大于20"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 30},
    },
    "email_open_rate": {
        "name": "email_open_rate",
        "display_name": "邮件打开率",
        "type": "numeric",
        "category": "品牌活跃度",
        "description": "客户邮件打开率（0-1）",
        "examples": ["邮件打开率大于50%", "打开率超过0.7"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 1},
    },
    "email_click_rate": {
        "name": "email_click_rate",
        "display_name": "邮件点击率",
        "type": "numeric",
        "category": "品牌活跃度",
        "description": "客户邮件点击率（0-1）",
        "examples": ["邮件点击率大于30%", "点击率超过0.5"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 1},
    },
    "event_participation": {
        "name": "event_participation",
        "display_name": "活动参与次数",
        "type": "numeric",
        "category": "品牌活跃度",
        "description": "客户参与品牌活动的次数",
        "examples": ["参与活动超过3次", "活动参与次数大于5"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 100},
    },

    # ========== 会员权益使用 ==========
    "vip_lounge_visits": {
        "name": "vip_lounge_visits",
        "display_name": "VIP休息室使用次数",
        "type": "numeric",
        "category": "会员权益使用",
        "description": "客户使用VIP休息室的次数（近12个月）",
        "examples": ["使用过VIP休息室", "休息室使用超过5次"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 100},
    },
    "personal_shopper_usage": {
        "name": "personal_shopper_usage",
        "display_name": "私人顾问服务使用次数",
        "type": "numeric",
        "category": "会员权益使用",
        "description": "客户使用私人顾问服务的次数（近12个月）",
        "examples": ["使用过私人顾问", "私人顾问服务超过3次"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 100},
    },

    # ========== 数字行为 ==========
    "app_daily_active": {
        "name": "app_daily_active",
        "display_name": "APP日活天数",
        "type": "numeric",
        "category": "数字行为",
        "description": "客户APP日活天数（近30天）",
        "examples": ["APP活跃超过15天", "近1个月APP使用超过20天"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 30},
    },
    "wechat_interaction": {
        "name": "wechat_interaction",
        "display_name": "微信互动次数",
        "type": "numeric",
        "category": "数字行为",
        "description": "客户微信互动次数（近30天）",
        "examples": ["微信互动超过20次", "微信互动频繁"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 1000},
    },
    "live_stream_participation": {
        "name": "live_stream_participation",
        "display_name": "直播参与次数",
        "type": "numeric",
        "category": "数字行为",
        "description": "客户参与直播的次数（近90天）",
        "examples": ["参与过直播", "直播参与超过3次"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 100},
    },

    # ========== 营销响应 ==========
    "last_email_click_days": {
        "name": "last_email_click_days",
        "display_name": "距上次邮件点击天数",
        "type": "numeric",
        "category": "营销响应",
        "description": "距离最近一次邮件点击的天数",
        "examples": ["最近7天内点击过邮件", "距上次邮件点击不超过30天"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 3650},
    },
    "referral_count": {
        "name": "referral_count",
        "display_name": "推荐好友数量",
        "type": "numeric",
        "category": "营销响应",
        "description": "客户推荐好友的数量",
        "examples": ["推荐过好友", "推荐数量大于2"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 100},
    },
    "social_engagement": {
        "name": "social_engagement",
        "display_name": "社交媒体互动次数",
        "type": "numeric",
        "category": "营销响应",
        "description": "客户社交媒体互动次数",
        "examples": ["社交媒体互动超过20次", "社交活跃度高"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 1000},
    },

    # ========== 生命周期 ==========
    "member_since_days": {
        "name": "member_since_days",
        "display_name": "会员天数",
        "type": "numeric",
        "category": "生命周期",
        "description": "客户成为会员的天数",
        "examples": ["会员超过1年", "新会员（少于6个月）", "老客户（超过3年）"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 10000},
    },
    "first_purchase_days": {
        "name": "first_purchase_days",
        "display_name": "距首次购买天数",
        "type": "numeric",
        "category": "生命周期",
        "description": "距离首次购买的天数",
        "examples": ["首购超过1年", "新客户（首购少于3个月）"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 10000},
    },

    # ========== 风控与排除 ==========
    "complaints_open": {
        "name": "complaints_open",
        "display_name": "未结案投诉数",
        "type": "numeric",
        "category": "风控与排除",
        "description": "客户未结案的投诉数量",
        "examples": ["无投诉", "有未解决投诉", "排除有投诉的用户"],
        "valid_operators": [">", ">=", "<", "<=", "=="],
        "value_range": {"min": 0, "max": 100},
    },
    "return_rate": {
        "name": "return_rate",
        "display_name": "退货率",
        "type": "numeric",
        "category": "风控与排除",
        "description": "客户退货率（0-1）",
        "examples": ["退货率低于10%", "退货率小于0.15", "排除高退货率用户"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 1},
    },

    # ========== 营销疲劳度 ==========
    "last_campaign_days": {
        "name": "last_campaign_days",
        "display_name": "距上次营销触达天数",
        "type": "numeric",
        "category": "营销疲劳度",
        "description": "距离最近一次营销触达的天数",
        "examples": ["最近7天未触达", "距上次营销超过14天", "排除近期触达用户"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 3650},
    },
    "campaign_exposure_30d": {
        "name": "campaign_exposure_30d",
        "display_name": "近30天营销触达次数",
        "type": "numeric",
        "category": "营销疲劳度",
        "description": "客户近30天被营销触达的次数",
        "examples": ["营销触达少于5次", "触达次数小于3", "排除高频触达用户"],
        "valid_operators": [">", ">=", "<", "<=", "==", "between"],
        "value_range": {"min": 0, "max": 100},
    },
}


def get_feature_by_name(name: str) -> FeatureMetadata | None:
    """根据特征名称获取特征元数据."""
    return FEATURE_METADATA.get(name)


def get_features_by_category(category: str) -> dict[str, FeatureMetadata]:
    """根据分类获取特征列表."""
    return {
        name: meta
        for name, meta in FEATURE_METADATA.items()
        if meta["category"] == category
    }


def search_features_by_keywords(keywords: list[str]) -> dict[str, FeatureMetadata]:
    """根据关键词搜索特征（用于自然语言匹配）."""
    results = {}
    for name, meta in FEATURE_METADATA.items():
        # 搜索显示名称、描述和示例
        search_text = f"{meta['display_name']} {meta['description']} {' '.join(meta['examples'])}".lower()
        if any(keyword.lower() in search_text for keyword in keywords):
            results[name] = meta
    return results


# 特征分类列表（用于组织和展示）
FEATURE_CATEGORIES = [
    "人口属性",
    "会员等级",
    "消费力指标",
    "品牌忠诚度",
    "品类兴趣",
    "品牌活跃度",
    "会员权益使用",
    "数字行为",
    "营销响应",
    "生命周期",
    "风控与排除",
    "营销疲劳度",
]
