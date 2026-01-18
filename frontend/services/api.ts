/**
 * API Service for Marketing Agent Backend
 *
 * Handles communication with the backend API including:
 * - Marketing analysis requests
 * - User data fetching
 * - Metrics prediction
 * - SSE streaming for real-time thinking steps
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface User {
  id: string;
  name: string;
  tier: string;
  score: number;
  recentStore: string;
  lastVisit: string;
  reason: string;
  matchScore?: number;
}

export interface ThinkingStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'active' | 'completed';
}

export interface PredictionMetrics {
  audienceSize: number;
  conversionRate: number;
  estimatedRevenue: number;
  roi?: number;
  reachRate?: number;
  qualityScore?: number;
}

export interface AnalysisResult {
  audience: User[];
  metrics: PredictionMetrics;
  response: string;
  thinkingSteps: ThinkingStep[];
  timestamp: string;
  segmentationProposal?: any;  // 新增：结构化方案
}

export interface ThinkingStepEvent {
  stepId: string;
  title: string;
  description: string;
  status: string;
}

export interface SessionResponse {
  session_id: string;
  message: string;
  created_at: string;
}

/**
 * Analyze marketing goal with streaming thinking steps
 */
export async function analyzeMarketingGoalStream(
  prompt: string,
  onThinkingStep: (step: ThinkingStep) => void,
  onAnalysisComplete: (result: AnalysisResult) => void,
  onError: (error: string) => void,
  onNodeComplete?: (node: string, timestamp: string) => void,
  onNodeSummary?: (node: string, summary: string) => void,
  sessionId?: string | null
): Promise<void> {
  try {
    const params: Record<string, string> = { prompt };
    if (sessionId) {
      params.session_id = sessionId;
    }

    const eventSource = new EventSource(
      `${API_BASE}/api/v1/analysis/stream?${new URLSearchParams(params).toString()}`
    );

    // 🔥 添加实时日志，确认事件是否到达
    eventSource.onopen = () => {
      console.log(`[${new Date().toLocaleTimeString()}] ✅ SSE 连接已建立`);
    };

    eventSource.addEventListener('thinking_step', (event) => {
      const timestamp = new Date().toLocaleTimeString();
      console.log(`[${timestamp}] 📋 thinking_step 事件`, event.data.substring(0, 80));
      try {
        const data: ThinkingStepEvent = JSON.parse(event.data);
        onThinkingStep({
          id: data.stepId,
          title: data.title,
          description: data.description,
          status: data.status as 'pending' | 'active' | 'completed',
        });
      } catch (e) {
        console.error('Error parsing thinking step:', e);
      }
    });

    // Listen to thinking_step_update events for real-time node completion updates
    eventSource.addEventListener('thinking_step_update', (event) => {
      const timestamp = new Date().toLocaleTimeString();
      console.log(`[${timestamp}] ✅ thinking_step_update 事件`, event.data.substring(0, 80));
      try {
        const data: ThinkingStepEvent = JSON.parse(event.data);
        onThinkingStep({
          id: data.stepId,
          title: data.title,
          description: data.description,
          status: data.status as 'pending' | 'active' | 'completed',
        });
      } catch (e) {
        console.error('Error parsing thinking step update:', e);
      }
    });

    // 🔥 新增：监听节点完成事件
    eventSource.addEventListener('node_complete', (event) => {
      const timestamp = new Date().toLocaleTimeString();
      console.log(`[${timestamp}] 🎉 node_complete 事件`, event.data);
      try {
        const data = JSON.parse(event.data);
        if (onNodeComplete) {
          onNodeComplete(data.node, data.timestamp);
        }
      } catch (e) {
        console.error('Error parsing node complete:', e);
      }
    });

    // 🔥 新增：监听节点摘要事件
    eventSource.addEventListener('node_summary', (event) => {
      const timestamp = new Date().toLocaleTimeString();
      console.log(`[${timestamp}] 📝 node_summary 事件`, event.data.substring(0, 80));
      try {
        const data = JSON.parse(event.data);
        if (onNodeSummary) {
          onNodeSummary(data.node, data.summary);
        }
      } catch (e) {
        console.error('Error parsing node summary:', e);
      }
    });

    eventSource.addEventListener('analysis_complete', (event) => {
      const timestamp = new Date().toLocaleTimeString();
      console.log(`[${timestamp}] 🏁 analysis_complete 事件`);
      try {
        const data: AnalysisResult = JSON.parse(event.data);
        console.log('Analysis complete data:', data);
        console.log('Has segmentationProposal?', !!data.segmentationProposal);
        if (data.segmentationProposal) {
          console.log('SegmentationProposal content:', data.segmentationProposal);
        }
        eventSource.close();
        onAnalysisComplete(data);
      } catch (e) {
        console.error('Error parsing analysis result:', e);
        onError('Failed to parse analysis result');
        eventSource.close();
      }
    });

    eventSource.addEventListener('error', (event) => {
      console.error('SSE Error:', event);
      eventSource.close();
      onError('Connection error while streaming analysis');
    });
  } catch (error) {
    console.error('Error starting analysis stream:', error);
    onError(`Failed to start analysis: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Analyze marketing goal without streaming
 */
export async function analyzeMarketingGoal(prompt: string): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE}/api/v1/analysis`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt,
      stream: false,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get high-potential users
 */
export async function getHighPotentialUsers(limit: number = 50): Promise<User[]> {
  const response = await fetch(
    `${API_BASE}/api/v1/users/high-potential?limit=${limit}`
  );

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.users || [];
}

/**
 * Predict metrics for given audience size
 */
export async function predictMetrics(
  audienceSize: number,
  constraints?: Record<string, unknown>
): Promise<PredictionMetrics> {
  const response = await fetch(`${API_BASE}/api/v1/prediction/metrics`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      audienceSize,
      constraints: constraints || {},
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Health check
 */
export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/api/v1/health`);
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Reset/clear a session and create a new one
 */
export async function resetSession(sessionId?: string | null): Promise<SessionResponse> {
  const params = new URLSearchParams();
  if (sessionId) {
    params.append('session_id', sessionId);
  }

  const response = await fetch(`${API_BASE}/api/v1/session/reset?${params.toString()}`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Create a new session explicitly
 */
export async function createSession(): Promise<SessionResponse> {
  const response = await fetch(`${API_BASE}/api/v1/session/create`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Calculate segmentation result based on proposal
 */
export async function calculateSegmentation(proposal: any): Promise<any> {
  const response = await fetch(`${API_BASE}/api/v1/segmentation/calculate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(proposal),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}
