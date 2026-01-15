import React, { useState } from 'react';
import { Tabs, Layout, Typography } from 'antd';
import { DashboardOutlined, TeamOutlined, ControlOutlined } from '@ant-design/icons';
import InsightCard from './InsightCard';
import PredictionWidget from './PredictionWidget';
import StrategyConstraints from './StrategyConstraints';
import UserList from './UserList';
import { PredictionMetrics } from '../types';
import { AVG_ORDER_VALUE } from '../constants';

const { Content, Header } = Layout;
const { Title, Text } = Typography;

const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<PredictionMetrics>({
    audienceSize: 1200,
    conversionRate: 2.5,
    estimatedRevenue: 5400000 
  });

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
          <InsightCard />
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
          <Text type="secondary">场景：春季手袋上市 • 目标：高潜人群圈选</Text>
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