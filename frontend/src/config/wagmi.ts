import { createWeb3Modal } from '@web3modal/wagmi/react'
import { defaultWagmiConfig } from '@web3modal/wagmi/react/config'
import { bsc, bscTestnet } from 'wagmi/chains'
import { reconnect } from '@wagmi/core'

// 获取WalletConnect项目ID
const projectId = import.meta.env.VITE_WALLETCONNECT_PROJECT_ID

if (!projectId) {
  console.warn('⚠️ WalletConnect Project ID未配置！请访问 https://cloud.walletconnect.com 创建项目')
}

// 应用元数据
const metadata = {
  name: 'RWA Referral System',
  description: 'Web3推荐系统 - 区块链积分与推荐奖励平台',
  url: import.meta.env.VITE_APP_URL || 'http://localhost:5173',
  icons: ['https://avatars.githubusercontent.com/u/37784886']
}

// 支持的链
const chains = [bscTestnet, bsc] as const

// 创建Wagmi配置
export const config = defaultWagmiConfig({
  chains,
  projectId: projectId || '',
  metadata,
  enableWalletConnect: true,
  enableInjected: true,
  enableEIP6963: true,
  enableCoinbase: true
})

// 创建Web3Modal实例
createWeb3Modal({
  wagmiConfig: config,
  projectId: projectId || '',
  enableAnalytics: false,
  enableOnramp: false,
  themeMode: 'light',
  themeVariables: {
    '--w3m-accent': '#1890ff'
  }
})

// 自动重连
reconnect(config)

export default config
