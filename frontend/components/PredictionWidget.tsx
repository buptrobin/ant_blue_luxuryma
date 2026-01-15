import React from 'react';
import { Card, Row, Col, Statistic, Slider, Typography } from 'antd';
import { ArrowUpOutlined } from '@ant-design/icons';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { PredictionMetrics } from '../types';

const { Title, Text } = Typography;

interface PredictionWidgetProps {
  metrics: PredictionMetrics;
  onAudienceSizeChange: (size: number) => void;
}

const PredictionWidget: React.FC<PredictionWidgetProps> = ({ metrics, onAudienceSizeChange }) => {
  // Generate curve data
  const data = Array.from({ length: 9 }, (_, i) => {
    const size = 1000 + i * 500;
    const rate = 4.0 - ((size - 1000) / 4000) * 2.5;
    return {
      size,
      rate: Number(rate.toFixed(2)),
    };
  });

  return (
    <Card 
      title={<span className="font-serif">效果预估与调整</span>} 
      bordered={false} 
      className="shadow-sm"
    >
      <Row gutter={24} style={{ marginBottom: 32 }}>
        <Col span={8}>
          <Card size="small" className="bg-yellow-50 border-yellow-100">
            <Statistic 
              title="Target Audience" 
              value={metrics.audienceSize} 
              groupSeparator=","
              valueStyle={{ color: '#0F172A', fontFamily: 'Playfair Display' }}
              suffix={<span className="text-xs text-green-600 ml-1">人</span>}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small" bordered={false} className="bg-gray-50">
            <Statistic 
              title="Est. Conversion" 
              value={metrics.conversionRate} 
              precision={1}
              suffix="%"
              valueStyle={{ fontFamily: 'Playfair Display' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small" bordered={false} className="bg-gray-50">
            <Statistic 
              title="Est. Revenue" 
              value={metrics.estimatedRevenue} 
              prefix="¥"
              formatter={(value) => {
                const val = Number(value);
                if (val >= 1000000) return `${(val / 1000000).toFixed(1)}M`;
                return `${(val / 1000).toFixed(0)}k`;
              }}
              valueStyle={{ fontFamily: 'Playfair Display' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={32}>
        <Col span={24} md={10}>
          <div className="mb-4">
            <div className="flex justify-between mb-2">
              <Text strong>圈选范围 (Reach)</Text>
              <Text style={{ color: '#D4AF37' }} strong>{metrics.audienceSize}</Text>
            </div>
            <Slider 
              min={1000} 
              max={5000} 
              step={100} 
              value={metrics.audienceSize} 
              onChange={onAudienceSizeChange}
              tooltip={{ formatter: (value) => `${value} 人` }}
            />
            <div className="flex justify-between text-xs text-gray-400">
              <span>精准 (1k)</span>
              <span>广泛 (5k)</span>
            </div>
          </div>
          <Text type="secondary" className="text-xs">
            拖动滑块调整受众规模。扩大规模通常会导致转化率边际递减，请寻找最佳平衡点。
          </Text>
        </Col>
        
        <Col span={24} md={14}>
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                <XAxis 
                  dataKey="size" 
                  tick={{ fontSize: 10, fill: '#888' }} 
                  axisLine={false} 
                  tickLine={false}
                />
                <YAxis 
                  domain={[1, 4.5]} 
                  tick={{ fontSize: 10, fill: '#888' }} 
                  axisLine={false} 
                  tickLine={false}
                  unit="%"
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#FFF', border: '1px solid #eee', borderRadius: '4px', boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }}
                  itemStyle={{ color: '#2C2C2C', fontSize: '12px' }}
                  formatter={(value: number) => [`${value}%`, '预估转化率']}
                  labelFormatter={(label) => `人群规模: ${label}`}
                />
                <Line 
                  type="monotone" 
                  dataKey="rate" 
                  stroke="#D4AF37" 
                  strokeWidth={2} 
                  dot={{ r: 3, fill: '#D4AF37' }} 
                  activeDot={{ r: 5 }} 
                />
                <ReferenceLine x={metrics.audienceSize} stroke="#334155" strokeDasharray="3 3" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Col>
      </Row>
    </Card>
  );
};

export default PredictionWidget;