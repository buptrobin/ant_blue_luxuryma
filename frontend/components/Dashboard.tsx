import React, { useState, useEffect } from 'react';
import { Tabs, Layout, Typography } from 'antd';
import { DashboardOutlined, TeamOutlined, ControlOutlined } from '@ant-design/icons';
import InsightCard from './InsightCard';
import PredictionWidget from './PredictionWidget';
import StrategyConstraints from './StrategyConstraints';
import UserList from './UserList';
import { PredictionMetrics, SegmentationProposal, SegmentationResult } from '../types';
import { AVG_ORDER_VALUE } from '../constants';

const { Content, Header } = Layout;
const { Title, Text } = Typography;

interface DashboardProps {
  pendingProposal: SegmentationProposal | null;
  segmentationResult: SegmentationResult | null;
  onApplyProposal: (result: SegmentationResult) => void;
}

const Dashboard: React.FC<DashboardProps> = ({
  pendingProposal,
  segmentationResult,
  onApplyProposal
}) => {
  // 使用真实数据或默认值
  const [metrics, setMetrics] = useState<PredictionMetrics>(() => {
    if (segmentationResult) {
      return {
        audienceSize: segmentationResult.audience_count,
        conversionRate: segmentationResult.est_conversion_rate * 100, // 转换为百分比
        estimatedRevenue: segmentationResult.est_revenue
      };
    }
    return {
      audienceSize: 0,
      conversionRate: 0,
      estimatedRevenue: 0
    };
  });

  // 当segmentationResult更新时，更新metrics
  useEffect(() => {
    if (segmentationResult) {
      setMetrics({
        audienceSize: segmentationResult.audience_count,
        conversionRate: segmentationResult.est_conversion_rate * 100,
        estimatedRevenue: segmentationResult.est_revenue
      });
    }
  }, [segmentationResult]);

  const handleAudienceSizeChange = (size: number) => {
    const baseRate = 4.0;
    const rateDrop = ((size - 1000) / 4000) * 2.5; 
    const newRate = Math.max(0.5, Number((baseRate - rateDrop).toFixed(2)));
    const newRevenue = Math.floor(size * (newRate / 100) * AVG_ORDER_VALUE);

    setMetrics({
      audienceSize: size,
      conversionRate: newRate,
      estimatedRevenue: newRevenue
    });
  };

  const items = [
    {
      key: 'overview',
      label: (
        <span className="flex items-center gap-2">
          <DashboardOutlined />
          人群总览
        </span>
      ),
      children: (
        <div className="space-y-6">
          <InsightCard
            targetTraits={segmentationResult?.trait_breakdown?.target_traits || []}
            constraints={segmentationResult?.trait_breakdown?.constraints || []}
          />
          <PredictionWidget metrics={metrics} onAudienceSizeChange={handleAudienceSizeChange} />
        </div>
      ),
    },
    {
      key: 'users',
      label: (
        <span className="flex items-center gap-2">
          <TeamOutlined />
          用户列表
        </span>
      ),
      children: <UserList />,
    },
    {
      key: 'strategy',
      label: (
        <span className="flex items-center gap-2">
          <ControlOutlined />
          策略配置
        </span>
      ),
      children: <StrategyConstraints />,
    },
  ];

  return (
    <Layout className="h-full bg-[#F1F5F9]">
      <Header className="bg-[#F1F5F9] px-6 lg:px-8 py-4 h-auto border-b border-transparent flex flex-col justify-end">
        <div className="max-w-5xl w-full mx-auto">
          <Title level={2} style={{ marginBottom: 4, fontFamily: 'Playfair Display, serif', color: '#0F172A' }}>
            营销活动工作台
          </Title>
          <Text type="secondary">
            {segmentationResult?.trait_breakdown?.marketing_goal || '等待Agent分析...'}
          </Text>
        </div>
      </Header>
      <Content className="overflow-y-auto px-6 lg:px-8 pb-8 custom-scrollbar">
        <div className="max-w-5xl w-full mx-auto">
          <Tabs 
            defaultActiveKey="overview" 
            items={items} 
            className="custom-tabs"
            animated
            size="large"
            tabBarStyle={{ borderBottom: '1px solid #e2e8f0', marginBottom: 24 }}
          />
        </div>
      </Content>
    </Layout>
  );
};

export default Dashboard;