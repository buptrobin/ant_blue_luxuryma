import React from 'react';
import { List, Avatar, Tag, Collapse, Typography, Card, Button } from 'antd';
import { UserOutlined, EnvironmentOutlined, QuestionCircleOutlined, RightOutlined } from '@ant-design/icons';
import { MOCK_USERS } from '../constants';
import { User } from '../types';

const { Text } = Typography;
const { Panel } = Collapse;

const UserList: React.FC = () => {
  return (
    <Card 
      bordered={false} 
      className="shadow-sm h-full flex flex-col"
      bodyStyle={{ padding: 0, height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      <div className="p-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center shrink-0">
        <div>
          <Text strong className="font-serif">高潜用户名单</Text>
          <div className="text-xs text-gray-500">Top 50 High Potential Leads</div>
        </div>
        <Tag>Total: 1,200</Tag>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-2 custom-scrollbar">
        <List
          itemLayout="horizontal"
          dataSource={MOCK_USERS}
          renderItem={(user: User) => (
            <List.Item className="hover:bg-gray-50 transition-colors rounded-lg px-2 border-b-0 mb-2">
               <Collapse 
                 ghost 
                 expandIcon={({ isActive }) => <RightOutlined rotate={isActive ? 90 : 0} />}
                 expandIconPosition="end"
                 style={{ width: '100%' }}
               >
                 <Panel
                   key={user.id}
                   header={
                     <div className="flex items-center gap-3 w-full pr-4">
                        <Avatar 
                          size="large" 
                          icon={<UserOutlined />} 
                          style={{ 
                              backgroundColor: user.tier === 'VVIP' ? '#334155' : '#F1F5F9',
                              color: user.tier === 'VVIP' ? '#D4AF37' : '#94A3B8'
                          }} 
                        />
                        <div className="flex-1 min-w-0">
                           <div className="flex items-center gap-2">
                             <Text strong>{user.name}</Text>
                             <Tag color={user.tier === 'VVIP' ? 'gold' : user.tier === 'VIP' ? 'orange' : 'default'} style={{ margin: 0, fontSize: 10 }}>
                               {user.tier}
                             </Tag>
                           </div>
                           <div className="flex items-center gap-2 text-xs text-gray-400 mt-1">
                              <EnvironmentOutlined /> {user.recentStore}
                              <span className="w-1 h-1 bg-gray-300 rounded-full"></span>
                              {user.lastVisit}
                           </div>
                        </div>
                        <div className="text-right hidden sm:block mr-4">
                           <div className="font-mono text-lg font-bold text-slate-700">{user.score}</div>
                           <div className="text-[10px] text-gray-400">Score</div>
                        </div>
                     </div>
                   }
                 >
                    <div className="bg-gray-50 p-3 rounded-lg flex gap-2 ml-10">
                       <QuestionCircleOutlined className="mt-1 text-yellow-600" />
                       <div>
                          <Text strong className="text-xs block">入选归因:</Text>
                          <Text type="secondary" className="text-xs">{user.reason}</Text>
                       </div>
                    </div>
                 </Panel>
               </Collapse>
            </List.Item>
          )}
        />
        <div className="text-center py-4">
           <Button type="text" size="small" className="text-xs text-gray-400">加载更多</Button>
        </div>
      </div>
    </Card>
  );
};

export default UserList;