import React, { useState, useEffect, useRef } from 'react';
import { flushSync } from 'react-dom';
import {
  UserOutlined,
  RobotOutlined,
  SendOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { Input, Button, Avatar, Card, Space, Typography, Alert } from 'antd';
import { ChatMessage, ThinkingStep, ThinkingStepStatus } from '../types';
import ThinkingProcess from './ThinkingProcess';
import { INITIAL_PROMPT } from '../constants';
import { analyzeMarketingGoalStream, healthCheck, resetSession, createSession } from '../services/api';

const { TextArea } = Input;
const { Text, Title } = Typography;

interface ChatInterfaceProps {
  onAnalyzeStart: () => void;
  onAnalyzeComplete: (analysisData: any) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onAnalyzeStart, onAnalyzeComplete }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState(INITIAL_PROMPT);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isThinkingExpanded, setIsThinkingExpanded] = useState(true);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isApiReady, setIsApiReady] = useState(true);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, thinkingSteps]);

  // Check API availability on component mount
  useEffect(() => {
    const checkApi = async () => {
      const ready = await healthCheck();
      setIsApiReady(ready);
      if (!ready) {
        setApiError('后端API不可用，请启动后端服务（python main.py）');
      } else {
        // Create a new session when component mounts
        try {
          const sessionResponse = await createSession();
          setSessionId(sessionResponse.session_id);
          console.log('Created new session:', sessionResponse.session_id);
        } catch (error) {
          console.error('Failed to create session:', error);
        }
      }
    };

    checkApi();
  }, []);

  const handleSend = async () => {
    if (!inputValue.trim() || isProcessing) return;

    if (!isApiReady) {
      setApiError('后端API不可用，请启动后端服务');
      return;
    }

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: inputValue,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsProcessing(true);
    setApiError(null);
    onAnalyzeStart();

    // Reset thinking steps
    setThinkingSteps([]);

    try {
      // Call backend API with streaming
      await analyzeMarketingGoalStream(
        userMsg.text,
        // onThinkingStep callback
        (step: ThinkingStep) => {
          setThinkingSteps(prev => {
            // Update or add step
            const existingIndex = prev.findIndex(s => s.id === step.id);
            if (existingIndex >= 0) {
              const updated = [...prev];
              updated[existingIndex] = step;
              return updated;
            } else {
              return [...prev, step];
            }
          });
        },
        // onAnalysisComplete callback
        (result) => {
          const agentMsg: ChatMessage = {
            id: (Date.now() + 1).toString(),
            sender: 'agent',
            text: result.response,
            timestamp: new Date(),
            isThinking: true
          };
          setMessages(prev => [...prev, agentMsg]);
          setIsProcessing(false);
          setThinkingSteps(result.thinkingSteps);

          // Pass analysis data to parent component
          onAnalyzeComplete({
            audience: result.audience,
            metrics: result.metrics,
            thinking_steps: result.thinkingSteps
          });
        },
        // onError callback
        (errorMsg) => {
          setApiError(errorMsg);
          setIsProcessing(false);
          const errorMsg2: ChatMessage = {
            id: (Date.now() + 1).toString(),
            sender: 'agent',
            text: `分析失败：${errorMsg}`,
            timestamp: new Date(),
            isThinking: false
          };
          setMessages(prev => [...prev, errorMsg2]);
        },
        // 🔥 onNodeComplete callback (新增)
        (node: string, timestamp: string) => {
          console.log(`✅ 节点 ${node} 完成于 ${timestamp}`);
        },
        // 🔥 onNodeSummary callback (新增) - 显示节点摘要
        (node: string, summary: string) => {
          console.log(`📝 节点 ${node} 摘要:`, summary);

          // 🔥 使用 flushSync 强制立即更新 UI（绕过 React 批处理）
          flushSync(() => {
            // 立即添加一条消息显示节点摘要
            const summaryMsg: ChatMessage = {
              id: `${Date.now()}-${node}`,
              sender: 'agent',
              text: summary,
              timestamp: new Date(),
              isThinking: false
            };
            setMessages(prev => [...prev, summaryMsg]);
          });
        },
        // Pass session ID for multi-turn conversation
        sessionId
      );
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      setApiError(`分析失败：${errorMessage}`);
      setIsProcessing(false);
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'agent',
        text: `出现错误：${errorMessage}`,
        timestamp: new Date(),
        isThinking: false
      };
      setMessages(prev => [...prev, errorMsg]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = async () => {
    try {
      // Reset session on backend
      const sessionResponse = await resetSession(sessionId);

      // Update session ID
      setSessionId(sessionResponse.session_id);

      // Clear messages and thinking steps
      setMessages([]);
      setThinkingSteps([]);

      // Clear input
      setInputValue('');

      console.log('Session cleared, new session:', sessionResponse.session_id);
    } catch (error) {
      console.error('Failed to clear session:', error);
      setApiError(`清空失败：${error instanceof Error ? error.message : String(error)}`);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white border-r border-gray-100">
      {/* Header */}
      <div className="p-5 border-b border-gray-100 flex items-center gap-3">
        <Avatar
          size={40}
          icon={<RobotOutlined style={{ color: '#D4AF37' }} />}
          style={{ backgroundColor: '#334155' }}
        />
        <div>
          <Title level={5} style={{ margin: 0, fontFamily: 'Playfair Display, serif' }}>LuxuryMA 智能助手</Title>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {isApiReady ? 'Intelligent Marketing Engine' : '等待后端连接...'}
          </Text>
        </div>
      </div>

      {/* API Error Alert */}
      {apiError && (
        <div className="p-3 border-b border-gray-100">
          <Alert
            message={apiError}
            type="error"
            showIcon
            icon={<ExclamationCircleOutlined />}
            closable
            onClose={() => setApiError(null)}
            style={{ margin: 0 }}
          />
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.sender === 'agent' && (
              <Avatar
                size={32}
                icon={<RobotOutlined />}
                style={{ backgroundColor: '#334155' }}
              />
            )}

            <div className={msg.sender === 'user' ? 'flex justify-end' : 'flex justify-start'} style={{ maxWidth: '80%' }}>
              <Card
                className="shadow-sm"
                style={{
                  backgroundColor: msg.sender === 'user' ? '#334155' : '#F5F5F5',
                  borderColor: msg.sender === 'user' ? '#D4AF37' : '#E0E0E0'
                }}
              >
                <Text style={{
                  color: msg.sender === 'user' ? '#FFFFFF' : '#000000'
                }}>
                  {msg.text}
                </Text>
              </Card>
            </div>

            {msg.sender === 'user' && (
              <Avatar
                size={32}
                icon={<UserOutlined />}
                style={{ backgroundColor: '#D4AF37' }}
              />
            )}
          </div>
        ))}

        {/* Thinking Process */}
        {(isProcessing || thinkingSteps.length > 0) && (
          <div className="mt-6">
            <ThinkingProcess
              steps={thinkingSteps}
              isExpanded={isThinkingExpanded}
              onToggle={() => setIsThinkingExpanded(!isThinkingExpanded)}
            />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-5 border-t border-gray-100 space-y-3">
        <div className="flex justify-between">
          <Button
            size="small"
            onClick={handleClear}
            disabled={isProcessing}
          >
            清空
          </Button>
          <Button
            size="small"
            onClick={() => setInputValue(INITIAL_PROMPT)}
            disabled={isProcessing}
          >
            应用
          </Button>
        </div>

        <TextArea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="请输入您的营销目标，按 Enter 发送（Shift+Enter 换行）..."
          rows={3}
          style={{
            borderColor: '#D4AF37',
            fontFamily: 'Playfair Display, serif'
          }}
          disabled={isProcessing || !isApiReady}
        />

        <Button
          type="primary"
          block
          onClick={handleSend}
          loading={isProcessing}
          disabled={!inputValue.trim() || isProcessing || !isApiReady}
          icon={isProcessing ? <LoadingOutlined /> : <SendOutlined />}
          style={{
            backgroundColor: isProcessing ? '#999' : '#334155',
            borderColor: '#D4AF37',
            color: '#FFFFFF',
            fontWeight: 600,
            height: 44
          }}
        >
          {isProcessing ? '分析中...' : '开始分析'}
        </Button>

        {!isApiReady && (
          <Text type="danger" style={{ fontSize: 12 }}>
            ⚠️ 后端服务未连接。请运行：cd backend && python main.py
          </Text>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;
