import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#334155', // Slate 700 - Primary Brand Color
          colorSuccess: '#10b981',
          colorWarning: '#D4AF37', // Luxury Gold
          colorError: '#ef4444',
          colorBgBase: '#ffffff',
          fontFamily: '"Inter", sans-serif',
          borderRadius: 8,
          wireframe: false,
        },
        components: {
          Button: {
            colorPrimary: '#334155',
            algorithm: true,
            fontWeight: 500,
          },
          Card: {
            boxShadowTertiary: '0 4px 30px rgba(15, 23, 42, 0.04)',
          },
          Steps: {
            colorPrimary: '#D4AF37', // Steps use Gold
          },
          Slider: {
            colorPrimary: '#D4AF37', // Sliders use Gold
            handleColor: '#D4AF37',
            trackBg: '#D4AF37',
            trackHoverBg: '#b5952f',
          },
          Switch: {
            colorPrimary: '#D4AF37',
          },
          Tabs: {
            colorPrimary: '#D4AF37',
            inkBarColor: '#D4AF37',
            itemHoverColor: '#334155',
            itemSelectedColor: '#334155',
          },
          Input: {
             activeBorderColor: '#334155',
             hoverBorderColor: '#334155',
          }
        }
      }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>
);