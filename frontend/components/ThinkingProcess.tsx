import React from 'react';
import { Steps, Collapse, theme } from 'antd';
import { 
  CheckCircleOutlined, 
  LoadingOutlined, 
  ClockCircleOutlined, 
  BulbOutlined 
} from '@ant-design/icons';
import { ThinkingStep, ThinkingStepStatus } from '../types';

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
                <div className="text-xs text-gray-500 mt-1 mb-2 whitespace-pre-line font-mono bg-white p-2 rounded border border-gray-100">
                  {step.description}
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