import React, { useEffect, useState } from 'react';
import { Layout, Button } from 'antd';
import { MenuUnfoldOutlined, MenuFoldOutlined } from '@ant-design/icons';
import ChatInterface from './components/ChatInterface';
import Dashboard from './components/Dashboard';
import { motion, AnimatePresence } from 'framer-motion';

const { Sider, Content } = Layout;

const App: React.FC = () => {
  const [isDashboardVisible, setIsDashboardVisible] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(420);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      if (!isDragging || collapsed) return;
      let newWidth = event.clientX;
      const minWidth = 280;
      const maxWidth = Math.min(600, window.innerWidth - 480);
      if (newWidth < minWidth) newWidth = minWidth;
      if (newWidth > maxWidth) newWidth = maxWidth;
      setSidebarWidth(newWidth);
    };

    const handleMouseUp = () => {
      if (!isDragging) return;
      setIsDragging(false);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, collapsed]);

  const handleDragStart = (event: React.MouseEvent<HTMLDivElement>) => {
    if (window.innerWidth < 992 || collapsed) return;
    event.preventDefault();
    setIsDragging(true);
  };

  return (
    <Layout style={{ minHeight: '100vh', overflow: 'hidden' }}>
      <Sider
        width={sidebarWidth}
        collapsedWidth={0}
        trigger={null}
        collapsed={collapsed}
        theme="light"
        className="border-r border-gray-200 z-20 shadow-lg lg:shadow-none"
        style={{ position: 'fixed', left: 0, top: 0, bottom: 0, height: '100vh', zIndex: 50 }}
        breakpoint="lg"
        onBreakpoint={(broken) => {
            if (broken) setCollapsed(true);
        }}
      >
        <ChatInterface
          onAnalyzeStart={() => {
            if (window.innerWidth < 992) setCollapsed(true);
          }}
          onAnalyzeComplete={() => {
            setIsDashboardVisible(true);
          }}
        />
        {/* Mobile Toggle inside Sider for closing */}
        <Button
            type="text"
            icon={<MenuFoldOutlined />}
            onClick={() => setCollapsed(true)}
            className="lg:hidden absolute top-4 right-4"
        />
        <div
          style={{
            position: 'absolute',
            top: 0,
            right: -4,
            width: 8,
            height: '100%',
            cursor: 'col-resize',
            zIndex: 60,
          }}
          onMouseDown={handleDragStart}
        />
      </Sider>

      {/* Main Layout */}
      <Layout style={{ marginLeft: collapsed ? 0 : sidebarWidth, transition: 'margin-left 0.2s' }}>
        <Content className="relative h-screen bg-[#F1F5F9]">
            {/* Mobile Toggle for opening */}
            <Button
                icon={<MenuUnfoldOutlined />}
                onClick={() => setCollapsed(false)}
                className={`fixed top-4 left-4 z-40 lg:hidden ${!collapsed ? 'hidden' : ''}`}
                size="large"
                shape="circle"
                type="primary"
            />

            <AnimatePresence mode="wait">
            {isDashboardVisible ? (
                <motion.div
                key="dashboard"
                className="h-full w-full"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                >
                <Dashboard />
                </motion.div>
            ) : (
                <motion.div
                key="empty"
                className="h-full w-full flex items-center justify-center bg-[#F1F5F9]"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                >
                <div className="text-center p-8 max-w-md">
                    <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center mx-auto mb-6 shadow-sm border border-yellow-500/20">
                    <div className="w-16 h-16 border-2 border-yellow-500 rounded-full opacity-20 animate-ping"></div>
                    </div>
                    <h1 className="text-3xl font-serif text-slate-800 mb-4">LuxuryMA</h1>
                    <p className="text-slate-500 leading-relaxed">
                    欢迎使用智能营销助手。<br/>
                    请在左侧对话框输入需求以开始人群圈选。
                    </p>
                </div>
                </motion.div>
            )}
            </AnimatePresence>
        </Content>
      </Layout>
    </Layout>
  );
};

export default App;
