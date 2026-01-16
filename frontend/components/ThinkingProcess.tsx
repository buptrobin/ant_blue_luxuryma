import React from 'react';
import { Steps, Collapse, theme } from 'antd';
import {
  CheckCircleOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  BulbOutlined
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ThinkingStep, ThinkingStepStatus } from '../types';
import './ThinkingProcess.css';

const { Panel } = Collapse;

interface ThinkingProcessProps {
  steps: ThinkingStep[];
  isExpanded: boolean;
  onToggle: () => void;
}

const ThinkingProcess: React.FC<ThinkingProcessProps> = ({ steps, isExpanded, onToggle }) => {
  const { token } = theme.useToken();

  const getStepStatus = (status: ThinkingStepStatus) => {
    switch (status) {
      case ThinkingStepStatus.Completed: return 'finish';
      case ThinkingStepStatus.Active: return 'process';
      default: return 'wait';
    }
  };

  const getIcon = (status: ThinkingStepStatus) => {
    switch (status) {
      case ThinkingStepStatus.Completed: return <CheckCircleOutlined />;
      case ThinkingStepStatus.Active: return <LoadingOutlined />;
      default: return <ClockCircleOutlined />;
    }
  };

  return (
    <div className="mt-2">
      <Collapse 
        activeKey={isExpanded ? ['1'] : []} 
        onChange={onToggle}
        bordered={false}
        ghost
        expandIconPosition="end"
        style={{ background: '#F8FAFC', borderRadius: 8, border: '1px solid #E2E8F0' }}
      >
        <Panel 
          header={
            <div className="flex items-center gap-2 text-slate-700">
              <BulbOutlined style={{ color: token.colorWarning }} />
              <span className="font-medium font-serif">智能思考链路</span>
            </div>
          } 
          key="1"
        >
          <Steps
            direction="vertical"
            size="small"
            items={steps.map(step => ({
              title: step.title,
              description: step.status !== ThinkingStepStatus.Pending ? (
                <div className="thinking-step-description">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      // 自定义渲染组件
                      strong: ({children}) => <><br className="data-split" /><strong className="text-blue-600 font-semibold">{children}</strong></>,
                      p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
                      ul: ({children}) => <ul className="list-disc ml-5 mb-2 space-y-1">{children}</ul>,
                      ol: ({children}) => <ol className="list-decimal ml-5 mb-2 space-y-1">{children}</ol>,
                      li: ({children}) => <li className="text-gray-700">{children}</li>,
                      code: ({children}) => <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">{children}</code>,
                      h3: ({children}) => <h3 className="text-base font-bold mt-3 mb-2 text-gray-800">{children}</h3>,
                      h4: ({children}) => <h4 className="text-sm font-semibold mt-2 mb-1 text-gray-700">{children}</h4>,
                    }}
                  >
                    {step.description}
                  </ReactMarkdown>
                </div>
              ) : null,
              status: getStepStatus(step.status),
              icon: getIcon(step.status)
            }))}
          />
        </Panel>
      </Collapse>
    </div>
  );
};

export default ThinkingProcess;