import { createContext, useContext, ReactNode, useEffect } from 'react'
import { useAccount, useDisconnect, useChainId, useSwitchChain } from 'wagmi'
import { useWeb3Modal } from '@web3modal/wagmi/react'
import toast from 'react-hot-toast'

// Web3状态类型定义
interface Web3State {
  account: string | undefined
  chainId: number | undefined
  isConnected: boolean
  isConnecting: boolean
  connectWallet: () => Promise<void>
  disconnectWallet: () => void
  switchNetwork: (chainId: number) => Promise<void>
}

// 创建Context
const Web3Context = createContext<Web3State | undefined>(undefined)

// Provider组件
export function Web3Provider({ children }: { children: ReactNode }) {
  const { address, isConnecting, isConnected } = useAccount()
  const chainId = useChainId()
  const { disconnect } = useDisconnect()
  const { switchChain } = useSwitchChain()
  const { open } = useWeb3Modal()

  // 连接钱包 - 打开Web3Modal
  const connectWallet = async () => {
    try {
      await open()
    } catch (error: any) {
      console.error('Failed to connect wallet:', error)
      toast.error(error.message || '钱包连接失败')
    }
  }

  // 断开钱包
  const disconnectWallet = () => {
    disconnect()
    toast.success('已断开钱包连接')
  }

  // 切换网络
  const switchNetwork = async (targetChainId: number) => {
    try {
      await switchChain({ chainId: targetChainId })
      toast.success('网络切换成功')
    } catch (error: any) {
      console.error('Failed to switch network:', error)
      toast.error('网络切换失败')
    }
  }

  // 监听连接状态变化
  useEffect(() => {
    if (isConnected && address) {
      toast.success(`钱包已连接: ${address.slice(0, 6)}...${address.slice(-4)}`)
    }
  }, [isConnected, address])

  const value: Web3State = {
    account: address,
    chainId,
    isConnected,
    isConnecting,
    connectWallet,
    disconnectWallet,
    switchNetwork
  }

  return <Web3Context.Provider value={value}>{children}</Web3Context.Provider>
}

// 自定义Hook
export function useWeb3() {
  const context = useContext(Web3Context)
  if (context === undefined) {
    throw new Error('useWeb3 must be used within Web3Provider')
  }
  return context
}
