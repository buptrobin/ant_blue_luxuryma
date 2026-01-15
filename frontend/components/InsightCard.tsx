import React from 'react';
import { Card, Row, Col, Typography, Tag } from 'antd';
import { 
  BulbOutlined, 
  WalletOutlined, 
  AimOutlined, 
  LineChartOutlined, 
  StopOutlined 
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

const InsightCard: React.FC = () => {
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
            智能引擎基于 <Text strong>[RFM模型]</Text> 与 <Text strong>[实时行为序列]</Text>，为您精准定位了 <Text strong style={{ color: '#D4AF37' }}>1,200</Text> 位高潜用户。
          </Text>
        </div>
      </div>

      <Row gutter={[16, 16]}>
        {/* Logic Block 1 */}
        <Col xs={24} md={12}>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-100 h-full hover:border-yellow-500/30 transition-colors">
            <SpaceTitle icon={<WalletOutlined />} title="消费力门槛" />
            <ul className="list-disc pl-4 mt-2 text-xs text-gray-500 space-y-1">
              <li>特征: 年消费额 (R12M) & 会员等级</li>
              <li>逻辑: R12M &gt; ¥100,000 <Tag color="gold" className="ml-1 mr-0 text-[10px] leading-tight py-0">OR</Tag> 等级 ∈ {'{VVIP, VIP}'}</li>
            </ul>
          </div>
        </Col>

        {/* Logic Block 2 */}
        <Col xs={24} md={12}>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-100 h-full hover:border-yellow-500/30 transition-colors">
            <SpaceTitle icon={<AimOutlined />} title="品类兴趣" />
            <ul className="list-disc pl-4 mt-2 text-xs text-gray-500 space-y-1">
              <li>特征: 品类浏览频次 & 加购行为</li>
              <li>逻辑: 近30天浏览“手袋” &gt; 5次 <Tag color="gold" className="ml-1 mr-0 text-[10px] leading-tight py-0">AND</Tag> 加购未支付</li>
            </ul>
          </div>
        </Col>

        {/* Logic Block 3 */}
        <Col xs={24} md={12}>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-100 h-full hover:border-yellow-500/30 transition-colors">
            <SpaceTitle icon={<LineChartOutlined />} title="品牌活跃度" />
            <ul className="list-disc pl-4 mt-2 text-xs text-gray-500 space-y-1">
               <li>特征: 渠道触点 & 营销响应</li>
               <li>逻辑: 近3个月到访门店 <Tag color="gold" className="ml-1 mr-0 text-[10px] leading-tight py-0">OR</Tag> 邮件点击率 &gt; 0</li>
            </ul>
          </div>
        </Col>

        {/* Logic Block 4 */}
        <Col xs={24} md={12}>
          <div className="bg-white p-4 rounded-lg border border-red-100 h-full hover:border-red-200 transition-colors">
            <SpaceTitle icon={<StopOutlined style={{ color: '#ff4d4f' }} />} title="排除规则" color="#ff4d4f" />
            <ul className="list-disc pl-4 mt-2 text-xs text-gray-500 space-y-1">
              <li>疲劳度: 过去7天内已购买过手袋</li>
              <li>风控: 近30天有未结案投诉记录</li>
            </ul>
          </div>
        </Col>
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