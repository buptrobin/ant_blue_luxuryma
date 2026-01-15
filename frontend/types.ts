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