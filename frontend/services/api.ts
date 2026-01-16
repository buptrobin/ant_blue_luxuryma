/**
 * API Service for Marketing Agent Backend
 *
 * Handles communication with the backend API including:
 * - Marketing analysis requests
 * - User data fetching
 * - Metrics prediction
 * - SSE streaming for real-time thinking steps
 */

const API_BASE = process.env.REACT_APP_API_URL || 'http://10.1.6.170:8000';

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
}

export interface ThinkingStepEvent {
  stepId: string;
  title: string;
  description: string;
  status: string;
}

/**
 * Analyze marketing goal with streaming thinking steps
 */
export async function analyzeMarketingGoalStream(
  prompt: string,
  onThinkingStep: (step: ThinkingStep) => void,
  onAnalysisComplete: (result: AnalysisResult) => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    const eventSource = new EventSource(
      `${API_BASE}/api/v1/analysis/stream?${new URLSearchParams({ prompt }).toString()}`
    );

    eventSource.addEventListener('thinking_step', (event) => {
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

    eventSource.addEventListener('analysis_complete', (event) => {
      try {
        const data: AnalysisResult = JSON.parse(event.data);
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
