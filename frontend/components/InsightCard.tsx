import React from 'react';
import { Card, Row, Col, Typography, Tag } from 'antd';
import {
  BulbOutlined,
  WalletOutlined,
  AimOutlined,
  LineChartOutlined,
  StopOutlined,
  StarOutlined
} from '@ant-design/icons';
import { TargetTrait } from '../types';

const { Title, Text, Paragraph } = Typography;

interface InsightCardProps {
  targetTraits?: TargetTrait[];
  constraints?: string[];
}

const InsightCard: React.FC<InsightCardProps> = ({ targetTraits = [], constraints = [] }) => {
  // 根据category选择图标
  const getCategoryIcon = (category: string) => {
    const lowerCategory = category.toLowerCase();
    if (lowerCategory.includes('消费') || lowerCategory.includes('门槛')) {
      return <WalletOutlined />;
    }
    if (lowerCategory.includes('品类') || lowerCategory.includes('兴趣')) {
      return <AimOutlined />;
    }
    if (lowerCategory.includes('活跃') || lowerCategory.includes('行为')) {
      return <LineChartOutlined />;
    }
    return <StarOutlined />;
  };

  // 如果没有数据，显示占位符
  if (targetTraits.length === 0 && constraints.length === 0) {
    return (
      <Card
        bordered={false}
        className="shadow-sm border border-gold-100 overflow-hidden relative"
        bodyStyle={{ padding: 24 }}
      >
        <div className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-yellow-500/10 rounded-full blur-2xl pointer-events-none"></div>

        <div className="flex items-start gap-4 mb-6 relative z-10">
          <div className="p-2 bg-yellow-500/10 rounded-full shrink-0">
            <BulbOutlined style={{ fontSize: 20, color: '#D4AF37' }} />
          </div>
          <div>
            <Title level={4} style={{ marginTop: 0, marginBottom: 8, fontFamily: 'Playfair Display' }}>
              人群圈选逻辑详解
            </Title>
            <Text type="secondary">
              等待Agent分析并点击"应用"按钮查看圈选逻辑
            </Text>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card
      bordered={false}
      className="shadow-sm border border-gold-100 overflow-hidden relative"
      bodyStyle={{ padding: 24 }}
    >
       <div className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-yellow-500/10 rounded-full blur-2xl pointer-events-none"></div>

      <div className="flex items-start gap-4 mb-6 relative z-10">
        <div className="p-2 bg-yellow-500/10 rounded-full shrink-0">
          <BulbOutlined style={{ fontSize: 20, color: '#D4AF37' }} />
        </div>
        <div>
          <Title level={4} style={{ marginTop: 0, marginBottom: 8, fontFamily: 'Playfair Display' }}>
            人群圈选逻辑详解
          </Title>
          <Text type="secondary">
            智能引擎基于特征匹配为您精准定位高潜用户
          </Text>
        </div>
      </div>

      <Row gutter={[16, 16]}>
        {/* 渲染特征规则 */}
        {targetTraits.map((trait, index) => (
          <Col xs={24} md={12} key={index}>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100 h-full hover:border-yellow-500/30 transition-colors">
              <SpaceTitle icon={getCategoryIcon(trait.category)} title={trait.category} />
              <ul className="list-disc pl-4 mt-2 text-xs text-gray-500 space-y-1">
                {trait.rules.map((rule, rIndex) => (
                  <li key={rIndex}>{rule.description}</li>
                ))}
              </ul>
            </div>
          </Col>
        ))}

        {/* 渲染约束条件 */}
        {constraints.length > 0 && (
          <Col xs={24} md={12}>
            <div className="bg-white p-4 rounded-lg border border-red-100 h-full hover:border-red-200 transition-colors">
              <SpaceTitle icon={<StopOutlined style={{ color: '#ff4d4f' }} />} title="约束条件" color="#ff4d4f" />
              <ul className="list-disc pl-4 mt-2 text-xs text-gray-500 space-y-1">
                {constraints.map((constraint, index) => (
                  <li key={index}>{constraint}</li>
                ))}
              </ul>
            </div>
          </Col>
        )}
      </Row>
    </Card>
  );
};

const SpaceTitle = ({ icon, title, color }: { icon: React.ReactNode, title: string, color?: string }) => (
  <div className="flex items-center gap-2 text-sm font-bold" style={{ color: color || '#1e293b' }}>
    {icon}
    <span>{title}</span>
  </div>
);

export default InsightCard;