import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { Toaster } from 'react-hot-toast'
import { Web3Provider } from '@/contexts/Web3Context'
import { ReferralProvider } from '@/contexts/ReferralContext'
import App from './App'
import './index.css'

// Ant Design主题配置 - 复古未来主义风格
const themeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#ff6b35', // 主色调：橙红色
    colorSuccess: '#4ecdc4', // 成功色：青绿色
    colorWarning: '#ffe66d', // 警告色：金黄色
    colorError: '#ff006e', // 错误色：粉红色
    colorInfo: '#00d9ff', // 信息色：天蓝色
    borderRadius: 8,
    fontSize: 14,
    fontFamily: '"SF Pro Display", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
  },
  components: {
    Button: {
      controlHeight: 40,
      fontWeight: 600
    },
    Input: {
      controlHeight: 40
    },
    Card: {
      borderRadiusLG: 16
    }
  }
}

// Toast配置
const toastOptions = {
  duration: 3000,
  position: 'top-center' as const,
  style: {
    background: '#1f1f1f',
    color: '#fff',
    padding: '16px',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: 500
  },
  success: {
    iconTheme: {
      primary: '#4ecdc4',
      secondary: '#fff'
    }
  },
  error: {
    iconTheme: {
      primary: '#ff006e',
      secondary: '#fff'
    }
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ConfigProvider theme={themeConfig} locale={zhCN}>
        <Web3Provider>
          <ReferralProvider>
            <App />
            <Toaster toastOptions={toastOptions} />
          </ReferralProvider>
        </Web3Provider>
      </ConfigProvider>
    </BrowserRouter>
  </React.StrictMode>
)
