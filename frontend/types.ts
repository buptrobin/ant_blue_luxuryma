export interface User {
  id: string;
  name: string;
  tier: 'VVIP' | 'VIP' | 'Member';
  score: number;
  recentStore: string;
  lastVisit: string;
  reason: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  timestamp: Date;
  isThinking?: boolean;
}

export enum ThinkingStepStatus {
  Pending = 'pending',
  Active = 'active',
  Completed = 'completed'
}

export interface ThinkingStep {
  id: string;
  title: string;
  description: string;
  status: ThinkingStepStatus;
}

export interface PredictionMetrics {
  audienceSize: number;
  conversionRate: number;
  estimatedRevenue: number;
}

// ========== 圈人方案相关类型 ==========

/**
 * 特征规则定义
 */
export interface FeatureRule {
  key: string;              // 特征键名，如 "R12M_Amount"
  operator: string;         // 操作符，如 ">="、"between"、"in"
  value: string | number | number[];   // 特征值
  description: string;      // 用于展示的描述文案
}

/**
 * 目标特征分类
 */
export interface TargetTrait {
  category: string;         // 特征类别，如 "消费门槛"、"品类兴趣"
  rules: FeatureRule[];     // 该类别下的规则列表
}

/**
 * Agent 产出的结构化圈人方案
 * 前端用于暂存待应用的方案
 */
export interface SegmentationProposal {
  marketing_goal: string;       // 营销目标，如 "春季手袋上市，高潜人群圈选"
  constraints: string[];        // 约束条件列表，如 ["预算<50w", "不打扰高退货用户"]
  target_traits: TargetTrait[]; // 具体的特征条件
  kpi: string;                  // 核心KPI，如 "conversion_rate"
  target_audience: {            // 目标人群描述
    tier?: string[];            // 会员等级，如 ["VVIP", "VIP"]
    age_group?: string;         // 年龄段
    gender?: string;            // 性别
    [key: string]: any;         // 其他人群属性
  };
}

/**
 * 后端 API 返回的预测结果
 * 用于渲染右侧面板
 */
export interface SegmentationResult {
  audience_count: number;           // 目标人群数量
  est_conversion_rate: number;      // 预估转化率（小数，如 0.025）
  est_revenue: number;              // 预估营收
  roi?: number;                     // 投资回报率
  trait_breakdown: SegmentationProposal;  // 回传确认的圈选逻辑
  audience?: User[];                // 圈选的用户列表（可选）
  tier_distribution?: {             // 会员等级分布
    [tier: string]: number;
  };
}