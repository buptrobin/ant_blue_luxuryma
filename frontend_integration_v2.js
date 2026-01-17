// V2 流式 Endpoint 前端集成完整示例
// Endpoint: GET /api/v1/analysis/v2/stream

/**
 * 事件类型说明：
 *
 * 1. node_start - 节点开始执行
 *    { type: "node_start", node: "intent_recognition", title: "意图识别" }
 *
 * 2. reasoning - LLM 推理过程（逐字流式）
 *    { type: "reasoning", node: "intent_recognition", data: "我首先分析..." }
 *
 * 3. node_complete - 节点完成（包含自然语言摘要）
 *    {
 *      type: "node_complete",
 *      node: "intent_recognition",
 *      data: {
 *        summary: "您希望提升整体购买转化率...",
 *        display_text: "✓ 意图识别完成\n\n您希望...",
 *        user_intent: {...},  // 结构化数据
 *        ...
 *      }
 *    }
 *
 * 4. workflow_complete - 工作流完成
 *    {
 *      type: "workflow_complete",
 *      status: "success",
 *      session_id: "abc123",
 *      data: { ... }
 *    }
 *
 * 5. error - 错误
 *    { type: "error", data: "错误信息" }
 */

// ========================================
// 方案1：使用原生 EventSource（最简单）
// ========================================

function analyzeWithEventSource(prompt) {
  const url = `/api/v1/analysis/v2/stream?prompt=${encodeURIComponent(prompt)}`;
  const eventSource = new EventSource(url);

  // 监听所有事件（SSE 使用 'message' 事件）
  eventSource.addEventListener('message', (e) => {
    const event = JSON.parse(e.data);

    switch (event.type) {
      case 'node_start':
        handleNodeStart(event.node, event.title);
        break;

      case 'reasoning':
        handleReasoning(event.node, event.data);
        break;

      case 'node_complete':
        handleNodeComplete(event.node, event.data);
        break;

      case 'workflow_complete':
        handleWorkflowComplete(event.status, event.data);
        eventSource.close();
        break;

      case 'error':
        handleError(event.data);
        eventSource.close();
        break;
    }
  });

  eventSource.onerror = (error) => {
    console.error('SSE 连接错误:', error);
    eventSource.close();
  };

  return eventSource;
}

// 处理函数示例
function handleNodeStart(node, title) {
  console.log(`[节点开始] ${title}`);

  // 更新 UI - 显示节点正在执行
  const nodeElement = document.getElementById(`node-${node}`);
  if (nodeElement) {
    nodeElement.classList.add('running');
    nodeElement.querySelector('.status').textContent = '执行中...';
  }
}

function handleReasoning(node, reasoningText) {
  // 可选：实时显示 LLM 推理过程（打字机效果）
  const reasoningElement = document.getElementById(`reasoning-${node}`);
  if (reasoningElement) {
    reasoningElement.textContent += reasoningText;
  }
}

function handleNodeComplete(node, data) {
  console.log(`[节点完成] ${node}`, data);

  // ⭐ 核心：显示格式化的自然语言输出
  const displayText = data.display_text;
  if (displayText) {
    showNodeResult(node, displayText);
  }

  // 或者分别处理各个字段
  switch (node) {
    case 'intent_recognition':
      if (data.summary) {
        showIntentSummary(data.summary);
      }
      break;

    case 'feature_matching':
      if (data.summary && data.matched_features) {
        showFeatureSummary(data.summary, data.matched_features);
      }
      break;

    case 'strategy_generation':
      if (data.strategy_summary && data.strategy_detail) {
        showStrategy(data.strategy_summary, data.strategy_detail);
      }
      break;

    case 'final_analysis':
      if (data.executive_summary && data.full_report) {
        showFinalReport(data.executive_summary, data.full_report);
      }
      break;
  }

  // 更新节点状态
  const nodeElement = document.getElementById(`node-${node}`);
  if (nodeElement) {
    nodeElement.classList.remove('running');
    nodeElement.classList.add('completed');
    nodeElement.querySelector('.status').textContent = '✓ 完成';
  }
}

function handleWorkflowComplete(status, data) {
  console.log(`[工作流完成] ${status}`, data);

  if (status === 'success') {
    // 显示最终结果
    showSuccessResult(data);
  } else if (status === 'clarification_needed') {
    // 需要澄清
    showClarificationPrompt(data.response);
  } else if (status === 'modification_needed') {
    // 需要修正
    showModificationPrompt(data.response);
  }
}

function handleError(errorMessage) {
  console.error('错误:', errorMessage);
  alert(`分析失败: ${errorMessage}`);
}

// UI 更新函数
function showNodeResult(node, displayText) {
  const resultElement = document.getElementById(`result-${node}`);
  if (resultElement) {
    // 支持 markdown 格式（如果需要）
    resultElement.innerHTML = formatMarkdown(displayText);
    resultElement.classList.add('show');
  }
}

function formatMarkdown(text) {
  // 简单的 markdown 转换（或使用 marked.js 等库）
  return text
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}


// ========================================
// 方案2：使用 fetch + ReadableStream（更灵活）
// ========================================

async function analyzeWithFetch(prompt) {
  const url = `/api/v1/analysis/v2/stream?prompt=${encodeURIComponent(prompt)}`;

  try {
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        console.log('流式响应完成');
        break;
      }

      // 解码数据块
      buffer += decoder.decode(value, { stream: true });

      // 处理完整的 SSE 事件
      const lines = buffer.split('\n');
      buffer = lines.pop(); // 保留不完整的行

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const eventData = line.slice(6);

          if (eventData.trim()) {
            try {
              const event = JSON.parse(eventData);
              handleEvent(event);
            } catch (e) {
              console.warn('JSON 解析失败:', eventData);
            }
          }
        }
      }
    }

  } catch (error) {
    console.error('请求失败:', error);
    handleError(error.message);
  }
}

function handleEvent(event) {
  switch (event.type) {
    case 'node_start':
      handleNodeStart(event.node, event.title);
      break;
    case 'reasoning':
      handleReasoning(event.node, event.data);
      break;
    case 'node_complete':
      handleNodeComplete(event.node, event.data);
      break;
    case 'workflow_complete':
      handleWorkflowComplete(event.status, event.data);
      break;
    case 'error':
      handleError(event.data);
      break;
  }
}


// ========================================
// 方案3：React 组件示例
// ========================================

import { useState, useEffect, useRef } from 'react';

function StreamingAnalysis({ prompt }) {
  const [nodes, setNodes] = useState({});
  const [reasoning, setReasoning] = useState({});
  const [finalResult, setFinalResult] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, running, success, error
  const eventSourceRef = useRef(null);

  useEffect(() => {
    if (!prompt) return;

    setStatus('running');
    const url = `/api/v1/analysis/v2/stream?prompt=${encodeURIComponent(prompt)}`;
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.addEventListener('message', (e) => {
      const event = JSON.parse(e.data);

      switch (event.type) {
        case 'node_start':
          setNodes(prev => ({
            ...prev,
            [event.node]: {
              status: 'running',
              title: event.title
            }
          }));
          break;

        case 'reasoning':
          setReasoning(prev => ({
            ...prev,
            [event.node]: (prev[event.node] || '') + event.data
          }));
          break;

        case 'node_complete':
          setNodes(prev => ({
            ...prev,
            [event.node]: {
              ...prev[event.node],
              status: 'completed',
              data: event.data,
              displayText: event.data.display_text
            }
          }));
          break;

        case 'workflow_complete':
          setFinalResult(event.data);
          setStatus('success');
          eventSource.close();
          break;

        case 'error':
          setStatus('error');
          console.error('Error:', event.data);
          eventSource.close();
          break;
      }
    });

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error);
      setStatus('error');
      eventSource.close();
    };

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [prompt]);

  return (
    <div className="streaming-analysis">
      {/* 节点状态显示 */}
      {Object.entries(nodes).map(([nodeId, node]) => (
        <div key={nodeId} className={`node node-${node.status}`}>
          <h3>{node.title}</h3>

          {/* 推理过程（可折叠） */}
          {reasoning[nodeId] && (
            <details>
              <summary>查看推理过程</summary>
              <pre className="reasoning">{reasoning[nodeId]}</pre>
            </details>
          )}

          {/* 节点结果 - 自然语言输出 */}
          {node.displayText && (
            <div className="node-result">
              {node.displayText.split('\n').map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>
          )}
        </div>
      ))}

      {/* 最终结果 */}
      {finalResult && (
        <div className="final-result">
          <h2>分析完成</h2>
          {finalResult.prediction_result && (
            <div className="metrics">
              <p>圈选人数: {finalResult.prediction_result.audience_size}</p>
              <p>预估转化率: {(finalResult.prediction_result.conversion_rate * 100).toFixed(2)}%</p>
              <p>预估收入: ¥{finalResult.prediction_result.estimated_revenue.toLocaleString()}</p>
              <p>ROI: {finalResult.prediction_result.roi.toFixed(2)}倍</p>
            </div>
          )}
        </div>
      )}

      {/* 状态指示器 */}
      {status === 'running' && <div className="spinner">分析中...</div>}
      {status === 'error' && <div className="error">分析失败，请重试</div>}
    </div>
  );
}

export default StreamingAnalysis;


// ========================================
// 方案4：Vue 组件示例
// ========================================

/*
<template>
  <div class="streaming-analysis">
    <!-- 节点列表 -->
    <div
      v-for="(node, nodeId) in nodes"
      :key="nodeId"
      :class="['node', `node-${node.status}`]"
    >
      <h3>{{ node.title }}</h3>

      <!-- 推理过程 -->
      <details v-if="reasoning[nodeId]">
        <summary>查看推理过程</summary>
        <pre class="reasoning">{{ reasoning[nodeId] }}</pre>
      </details>

      <!-- 节点结果 -->
      <div v-if="node.displayText" class="node-result" v-html="formatText(node.displayText)"></div>
    </div>

    <!-- 最终结果 -->
    <div v-if="finalResult" class="final-result">
      <h2>分析完成</h2>
      <div v-if="finalResult.prediction_result" class="metrics">
        <p>圈选人数: {{ finalResult.prediction_result.audience_size }}</p>
        <p>预估转化率: {{ (finalResult.prediction_result.conversion_rate * 100).toFixed(2) }}%</p>
        <p>预估收入: ¥{{ finalResult.prediction_result.estimated_revenue.toLocaleString() }}</p>
        <p>ROI: {{ finalResult.prediction_result.roi.toFixed(2) }}倍</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StreamingAnalysis',
  props: {
    prompt: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      nodes: {},
      reasoning: {},
      finalResult: null,
      eventSource: null
    };
  },
  mounted() {
    this.startAnalysis();
  },
  beforeUnmount() {
    if (this.eventSource) {
      this.eventSource.close();
    }
  },
  methods: {
    startAnalysis() {
      const url = `/api/v1/analysis/v2/stream?prompt=${encodeURIComponent(this.prompt)}`;
      this.eventSource = new EventSource(url);

      this.eventSource.addEventListener('message', (e) => {
        const event = JSON.parse(e.data);

        switch (event.type) {
          case 'node_start':
            this.$set(this.nodes, event.node, {
              status: 'running',
              title: event.title
            });
            break;

          case 'reasoning':
            const current = this.reasoning[event.node] || '';
            this.$set(this.reasoning, event.node, current + event.data);
            break;

          case 'node_complete':
            this.$set(this.nodes, event.node, {
              ...this.nodes[event.node],
              status: 'completed',
              data: event.data,
              displayText: event.data.display_text
            });
            break;

          case 'workflow_complete':
            this.finalResult = event.data;
            this.eventSource.close();
            break;

          case 'error':
            console.error('Error:', event.data);
            this.eventSource.close();
            break;
        }
      });

      this.eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        this.eventSource.close();
      };
    },

    formatText(text) {
      return text.replace(/\n/g, '<br>');
    }
  }
};
</script>

<style scoped>
.node {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.node-running {
  border-color: #4CAF50;
  background-color: #f1f8f4;
}

.node-completed {
  border-color: #2196F3;
  background-color: #e3f2fd;
}

.reasoning {
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}

.node-result {
  margin-top: 10px;
  white-space: pre-wrap;
}
</style>
*/


// ========================================
// 完整的 HTML + 原生 JS 示例
// ========================================

/*
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>V2 流式分析 Demo</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      max-width: 900px;
      margin: 40px auto;
      padding: 20px;
    }

    .input-section {
      margin-bottom: 30px;
    }

    textarea {
      width: 100%;
      height: 80px;
      padding: 10px;
      font-size: 14px;
      border: 1px solid #ddd;
      border-radius: 4px;
    }

    button {
      padding: 10px 20px;
      font-size: 14px;
      background-color: #4CAF50;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }

    button:hover {
      background-color: #45a049;
    }

    .node {
      margin-bottom: 20px;
      padding: 15px;
      border: 1px solid #ddd;
      border-radius: 8px;
      transition: all 0.3s;
    }

    .node.running {
      border-color: #4CAF50;
      background-color: #f1f8f4;
    }

    .node.completed {
      border-color: #2196F3;
      background-color: #e3f2fd;
    }

    .node-title {
      font-weight: bold;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .status-indicator {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background-color: #ccc;
    }

    .running .status-indicator {
      background-color: #4CAF50;
      animation: pulse 1.5s infinite;
    }

    .completed .status-indicator {
      background-color: #2196F3;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

    .node-result {
      margin-top: 10px;
      white-space: pre-wrap;
      line-height: 1.6;
    }

    .reasoning {
      background-color: #f5f5f5;
      padding: 10px;
      border-radius: 4px;
      font-size: 12px;
      max-height: 200px;
      overflow-y: auto;
      margin-top: 10px;
    }

    details {
      margin-top: 10px;
      cursor: pointer;
    }

    summary {
      color: #666;
      font-size: 13px;
    }

    .final-result {
      margin-top: 30px;
      padding: 20px;
      background-color: #e8f5e9;
      border-radius: 8px;
    }
  </style>
</head>
<body>
  <h1>V2 流式分析 Demo</h1>

  <div class="input-section">
    <textarea id="promptInput" placeholder="输入您的需求，例如：我要为春季新款手袋上市做推广，圈选VVIP和VIP客户">我要为春季新款手袋上市做推广，圈选VVIP和VIP客户</textarea>
    <br><br>
    <button onclick="startAnalysis()">开始分析</button>
  </div>

  <div id="results"></div>

  <script>
    let eventSource = null;
    const nodes = {};

    function startAnalysis() {
      const prompt = document.getElementById('promptInput').value;
      if (!prompt.trim()) {
        alert('请输入分析需求');
        return;
      }

      // 清空之前的结果
      document.getElementById('results').innerHTML = '';
      Object.keys(nodes).forEach(key => delete nodes[key]);

      // 关闭之前的连接
      if (eventSource) {
        eventSource.close();
      }

      // 创建 SSE 连接
      const url = `/api/v1/analysis/v2/stream?prompt=${encodeURIComponent(prompt)}`;
      eventSource = new EventSource(url);

      eventSource.addEventListener('message', (e) => {
        const event = JSON.parse(e.data);

        switch (event.type) {
          case 'node_start':
            createNodeElement(event.node, event.title);
            updateNodeStatus(event.node, 'running');
            break;

          case 'reasoning':
            appendReasoning(event.node, event.data);
            break;

          case 'node_complete':
            updateNodeStatus(event.node, 'completed');
            if (event.data.display_text) {
              showNodeResult(event.node, event.data.display_text);
            }
            break;

          case 'workflow_complete':
            showFinalResult(event.data);
            eventSource.close();
            break;

          case 'error':
            alert('错误: ' + event.data);
            eventSource.close();
            break;
        }
      });

      eventSource.onerror = () => {
        console.error('SSE 连接错误');
        eventSource.close();
      };
    }

    function createNodeElement(nodeId, title) {
      const nodeDiv = document.createElement('div');
      nodeDiv.id = `node-${nodeId}`;
      nodeDiv.className = 'node';
      nodeDiv.innerHTML = `
        <div class="node-title">
          <span class="status-indicator"></span>
          <span>${title}</span>
        </div>
        <div class="node-result" id="result-${nodeId}"></div>
        <details id="reasoning-container-${nodeId}" style="display:none;">
          <summary>查看推理过程</summary>
          <pre class="reasoning" id="reasoning-${nodeId}"></pre>
        </details>
      `;
      document.getElementById('results').appendChild(nodeDiv);
      nodes[nodeId] = { element: nodeDiv };
    }

    function updateNodeStatus(nodeId, status) {
      const nodeElement = document.getElementById(`node-${nodeId}`);
      if (nodeElement) {
        nodeElement.className = `node ${status}`;
      }
    }

    function appendReasoning(nodeId, text) {
      const reasoningElement = document.getElementById(`reasoning-${nodeId}`);
      const containerElement = document.getElementById(`reasoning-container-${nodeId}`);

      if (reasoningElement && containerElement) {
        reasoningElement.textContent += text;
        containerElement.style.display = 'block';
      }
    }

    function showNodeResult(nodeId, displayText) {
      const resultElement = document.getElementById(`result-${nodeId}`);
      if (resultElement) {
        resultElement.textContent = displayText;
      }
    }

    function showFinalResult(data) {
      const finalDiv = document.createElement('div');
      finalDiv.className = 'final-result';

      let html = '<h2>✓ 分析完成</h2>';

      if (data.prediction_result) {
        const pr = data.prediction_result;
        html += `
          <p><strong>圈选人数:</strong> ${pr.audience_size} 人</p>
          <p><strong>预估转化率:</strong> ${(pr.conversion_rate * 100).toFixed(2)}%</p>
          <p><strong>预估收入:</strong> ¥${pr.estimated_revenue.toLocaleString()}</p>
          <p><strong>ROI:</strong> ${pr.roi.toFixed(2)} 倍</p>
        `;
      }

      finalDiv.innerHTML = html;
      document.getElementById('results').appendChild(finalDiv);
    }
  </script>
</body>
</html>
*/
