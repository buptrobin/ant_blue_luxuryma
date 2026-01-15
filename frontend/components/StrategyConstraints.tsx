import React, { useState, useMemo } from 'react';
import { 
  Card, 
  Switch, 
  Slider, 
  Select, 
  Segmented, 
  Progress, 
  Button, 
  Row, 
  Col, 
  Typography, 
  Divider,
  Tag
} from 'antd';
import { 
  SafetyCertificateOutlined, 
  StopOutlined, 
  TagOutlined, 
  ThunderboltOutlined, 
  RocketOutlined, 
  ShopOutlined, 
  RiseOutlined
} from '@ant-design/icons';
import { motion } from 'framer-motion';

const { Title, Text } = Typography;
const { Option } = Select;

const StrategyConstraints: React.FC = () => {
  // State
  const [returnFilter, setReturnFilter] = useState(true);
  const [returnRateLevel, setReturnRateLevel] = useState(1);
  const [scalperBlock, setScalperBlock] = useState(true);
  const [pricePref, setPricePref] = useState<string>('mix');
  const [allowEntry, setAllowEntry] = useState(false);
  const [onlineAction, setOnlineAction] = useState('miniprog');
  const [dormantActive, setDormantActive] = useState(false);

  // Metrics Calculation
  const metrics = useMemo(() => {
    const baseAudience = 12500;
    
    let riskDrop = 0;
    if (returnFilter) riskDrop += 600 + (returnRateLevel * 150);
    if (scalperBlock) riskDrop += 45;

    let brandDrop = 0;
    if (pricePref === 'full') brandDrop += 3500;
    else if (pricePref === 'mix') brandDrop += 1200;
    if (!allowEntry) brandDrop += 800;

    const dormantCount = 1800;
    const activeDormant = dormantActive ? dormantCount * 0.4 : 0;

    const afterRisk = baseAudience - riskDrop;
    const afterBrand = afterRisk - brandDrop;
    const finalCount = Math.floor(afterBrand + activeDormant);

    const baseROI = 8.5;
    const roiBoost = (pricePref === 'full' ? 3.5 : 0) + (returnFilter ? 1.2 : 0) + (scalperBlock ? 0.5 : 0);
    const finalROI = (baseROI + roiBoost).toFixed(1);
    
    const visitRate = (3.5 + (onlineAction === 'invite' ? 1.2 : 0) + (pricePref === 'full' ? 0.8 : 0)).toFixed(1);

    return {
      base: baseAudience,
      afterRisk,
      afterBrand,
      final: finalCount,
      riskDropPercent: Math.round((riskDrop / baseAudience) * 100),
      brandDropPercent: Math.round((brandDrop / afterRisk) * 100),
      roi: finalROI,
      visitRate
    };
  }, [returnFilter, returnRateLevel, scalperBlock, pricePref, allowEntry, dormantActive, onlineAction]);

  return (
    <div className="flex flex-col gap-6 relative pb-24">
      {/* Funnel Section */}
      <Card bordered={false} className="shadow-sm">
        <Title level={5} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <TagOutlined style={{ color: '#D4AF37' }} /> 人群漏斗
        </Title>
        <div className="flex flex-col items-center gap-1 mt-4 w-full">
            <div className="w-full bg-gray-100 rounded p-2 flex justify-between text-xs text-gray-500">
                <span>原始人群</span> <span>{metrics.base.toLocaleString()}</span>
            </div>
            
            <div className="w-full flex justify-center">
                 <motion.div 
                    animate={{ width: `${(metrics.afterRisk / metrics.base) * 100}%` }}
                    className="bg-blue-50 border border-blue-100 text-blue-900 h-10 rounded p-2 flex justify-between items-center text-xs whitespace-nowrap overflow-hidden"
                    style={{ minWidth: '30%' }}
                 >
                    <span><SafetyCertificateOutlined /> 风控后</span>
                    <span>{metrics.afterRisk.toLocaleString()}</span>
                 </motion.div>
            </div>

            <div className="w-full flex justify-center">
                 <motion.div 
                    animate={{ width: `${(metrics.afterBrand / metrics.base) * 100}%` }}
                    className="bg-yellow-50 border border-yellow-100 text-yellow-900 h-10 rounded p-2 flex justify-between items-center text-xs whitespace-nowrap overflow-hidden"
                    style={{ minWidth: '25%' }}
                 >
                    <span><TagOutlined /> 调性筛选</span>
                    <span>{metrics.afterBrand.toLocaleString()}</span>
                 </motion.div>
            </div>

            <div className="w-full flex justify-center mt-2">
                 <motion.div 
                    animate={{ width: `${(metrics.final / metrics.base) * 100}%` }}
                    className="bg-gradient-to-r from-amber-100 to-amber-300 border border-amber-300 h-14 rounded-lg px-4 flex justify-between items-center text-slate-800 shadow-md"
                    style={{ minWidth: '20%' }}
                 >
                    <div className="flex flex-col">
                        <span className="text-[10px] uppercase font-bold text-amber-800">Target</span>
                        <span className="font-serif font-bold">最终触达</span>
                    </div>
                    <span className="text-xl font-bold font-mono">{metrics.final.toLocaleString()}</span>
                 </motion.div>
            </div>
        </div>
      </Card>

      {/* Constraints Config */}
      <Row gutter={[24, 24]}>
        <Col span={24}>
            <Card title={<><SafetyCertificateOutlined /> 品质与风控盾</>} size="small" bordered={false} className="shadow-sm">
                <div className="space-y-6">
                    <div className="flex justify-between items-start">
                        <div>
                            <Text strong>高退货率过滤</Text>
                            <div className="text-xs text-gray-400">剔除过去12个月退货率过高的用户</div>
                            {returnFilter && (
                                <div className="mt-4 w-64">
                                     <Slider 
                                        min={0} max={2} step={1} 
                                        value={returnRateLevel}
                                        onChange={setReturnRateLevel}
                                        marks={{0: '宽松', 1: '适中', 2: '严苛'}}
                                     />
                                </div>
                            )}
                        </div>
                        <Switch checked={returnFilter} onChange={setReturnFilter} />
                    </div>
                    <Divider style={{ margin: '12px 0' }} dashed />
                    <div className="flex justify-between items-center">
                        <div>
                            <Text strong><StopOutlined /> 黄牛拦截</Text>
                            <div className="text-xs text-gray-400">拦截疑似代购及同款多件购买</div>
                        </div>
                        <Switch checked={scalperBlock} onChange={setScalperBlock} />
                    </div>
                </div>
            </Card>
        </Col>

        <Col span={24}>
            <Card title={<><TagOutlined /> 消费偏好筛选</>} size="small" bordered={false} className="shadow-sm">
                 <div className="mb-4">
                    <Text strong className="block mb-2">正价/折扣偏好</Text>
                    <Segmented 
                        block
                        value={pricePref}
                        onChange={(val) => setPricePref(val.toString())}
                        options={[
                            { label: '仅限正价', value: 'full' },
                            { label: '混合偏好', value: 'mix' },
                            { label: '包含奥莱', value: 'outlet' },
                        ]}
                    />
                 </div>
                 <div className="flex justify-between items-center bg-gray-50 p-3 rounded">
                     <div>
                        <Text>允许入门品类用户</Text>
                        <div className="text-xs text-gray-400">包含仅购买过美妆/小皮具的用户</div>
                     </div>
                     <Switch size="small" checked={allowEntry} onChange={setAllowEntry} />
                 </div>
            </Card>
        </Col>

        <Col span={24}>
            <Card title={<><ThunderboltOutlined /> 渠道分配</>} size="small" bordered={false} className="shadow-sm">
                 <div className="mb-4">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>Offline</span><span>Online</span><span>Dormant</span>
                    </div>
                    <Progress percent={40} success={{ percent: 35 }} strokeColor="#334155" trailColor="#e2e8f0" showInfo={false} />
                 </div>
                 <div className="space-y-4">
                    <div>
                        <Text strong className="text-xs text-gray-400 block mb-1">纯线上客群处理</Text>
                        <Select value={onlineAction} onChange={setOnlineAction} style={{ width: '100%' }}>
                            <Option value="miniprog">转为小程序链接</Option>
                            <Option value="invite">发送到店邀请</Option>
                            <Option value="exclude">剔除</Option>
                        </Select>
                    </div>
                    <div className="flex justify-between items-center">
                         <Text>沉睡客群激活 (近6月无互动)</Text>
                         <Switch checked={dormantActive} onChange={setDormantActive} />
                    </div>
                 </div>
            </Card>
        </Col>
      </Row>

      {/* Sticky Footer */}
      <div className="sticky bottom-0 z-20 -mx-6 -mb-6">
         <div className="bg-white/95 backdrop-blur border-t border-gray-200 px-6 py-4 flex items-center justify-between shadow-[0_-4px_20px_rgba(0,0,0,0.05)]">
            <div className="flex gap-6">
                <div>
                    <div className="text-[10px] text-gray-500 uppercase">Total Reach</div>
                    <div className="text-xl font-serif font-bold">{metrics.final.toLocaleString()}</div>
                </div>
                <Divider type="vertical" className="h-8" />
                <div className="flex gap-4">
                    <div>
                        <div className="flex items-center gap-1 text-xs text-gray-500"><RiseOutlined /> ROI</div>
                        <div className="font-bold">{metrics.roi}</div>
                    </div>
                    <div>
                        <div className="flex items-center gap-1 text-xs text-gray-500"><ShopOutlined /> Visit</div>
                        <div className="font-bold">{metrics.visitRate}%</div>
                    </div>
                </div>
            </div>
            <Button type="primary" size="large" icon={<RocketOutlined />}>
                应用策略
            </Button>
         </div>
      </div>
    </div>
  );
};

export default StrategyConstraints;