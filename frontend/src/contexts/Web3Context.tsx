import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { BrowserProvider, JsonRpcSigner, Contract } from 'ethers'
import toast from 'react-hot-toast'

// 从部署信息导入合约地址和ABI（稍后需要创建）
const CONTRACT_ADDRESS = import.meta.env.VITE_CONTRACT_ADDRESS || ''

// RWAReferral合约ABI（核心方法）
const REFERRAL_ABI = [
  'function bindReferrer(address referrer) external returns (bool)',
  'function triggerReward(uint256 amount) external payable returns (uint256)',
  'function getUserInfo(address user) external view returns (address referrer, uint256 reward, uint256 referredCount, uint256 lastActiveTimestamp)',
  'function getConfig() external view returns (uint256 decimals, uint256 secondsUntilInactive, uint256 level1Rate, uint256 level2Rate, uint256 referralBonus)',
  'function isActive(address user) external view returns (bool)',
  'function getBatchUserInfo(address[] calldata users) external view returns (tuple(address referrer, uint256 reward, uint256 referredCount, uint256 lastActiveTimestamp)[] memory)',
  'event RegisteredReferrer(address indexed referee, address indexed referrer)',
  'event PaidReferral(address indexed referee, address indexed referrer, uint256 amount, uint256 level)'
]

// Web3状态类型定义
interface Web3State {
  provider: BrowserProvider | null
  signer: JsonRpcSigner | null
  account: string | null
  chainId: number | null
  contract: Contract | null
  isConnected: boolean
  isConnecting: boolean
  connectWallet: () => Promise<void>
  disconnectWallet: () => void
  switchNetwork: (chainId: number) => Promise<void>
}

// 创建Context
const Web3Context = createContext<Web3State | undefined>(undefined)

// BSC网络配置
const BSC_TESTNET_CHAIN_ID = 97
const BSC_MAINNET_CHAIN_ID = 56

const BSC_NETWORKS = {
  testnet: {
    chainId: `0x${BSC_TESTNET_CHAIN_ID.toString(16)}`,
    chainName: 'BSC Testnet',
    nativeCurrency: { name: 'BNB', symbol: 'BNB', decimals: 18 },
    rpcUrls: ['https://data-seed-prebsc-1-s1.binance.org:8545/'],
    blockExplorerUrls: ['https://testnet.bscscan.com/']
  },
  mainnet: {
    chainId: `0x${BSC_MAINNET_CHAIN_ID.toString(16)}`,
    chainName: 'BSC Mainnet',
    nativeCurrency: { name: 'BNB', symbol: 'BNB', decimals: 18 },
    rpcUrls: ['https://bsc-dataseed1.binance.org/'],
    blockExplorerUrls: ['https://bscscan.com/']
  }
}

// Provider组件
export function Web3Provider({ children }: { children: ReactNode }) {
  const [provider, setProvider] = useState<BrowserProvider | null>(null)
  const [signer, setSigner] = useState<JsonRpcSigner | null>(null)
  const [account, setAccount] = useState<string | null>(null)
  const [chainId, setChainId] = useState<number | null>(null)
  const [contract, setContract] = useState<Contract | null>(null)
  const [isConnecting, setIsConnecting] = useState(false)

  // 初始化合约实例
  const initContract = async (_provider: BrowserProvider, signerInstance: JsonRpcSigner) => {
    if (!CONTRACT_ADDRESS) {
      console.warn('Contract address not configured')
      return null
    }

    try {
      const contractInstance = new Contract(CONTRACT_ADDRESS, REFERRAL_ABI, signerInstance)
      return contractInstance
    } catch (error) {
      console.error('Failed to initialize contract:', error)
      return null
    }
  }

  // 连接钱包
  const connectWallet = async () => {
    if (!window.ethereum) {
      toast.error('请安装MetaMask钱包')
      return
    }

    setIsConnecting(true)

    try {
      // 请求账户权限
      const accounts = await window.ethereum.request({
        method: 'eth_requestAccounts'
      })

      // 创建Provider和Signer
      const providerInstance = new BrowserProvider(window.ethereum)
      const signerInstance = await providerInstance.getSigner()
      const network = await providerInstance.getNetwork()

      setProvider(providerInstance)
      setSigner(signerInstance)
      setAccount(accounts[0])
      setChainId(Number(network.chainId))

      // 初始化合约
      const contractInstance = await initContract(providerInstance, signerInstance)
      setContract(contractInstance)

      toast.success('钱包连接成功')
    } catch (error: any) {
      console.error('Failed to connect wallet:', error)
      toast.error(error.message || '钱包连接失败')
    } finally {
      setIsConnecting(false)
    }
  }

  // 断开钱包
  const disconnectWallet = () => {
    setProvider(null)
    setSigner(null)
    setAccount(null)
    setChainId(null)
    setContract(null)
    toast.success('已断开钱包连接')
  }

  // 切换网络
  const switchNetwork = async (targetChainId: number) => {
    if (!window.ethereum) return

    const network = targetChainId === BSC_MAINNET_CHAIN_ID ? BSC_NETWORKS.mainnet : BSC_NETWORKS.testnet

    try {
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: network.chainId }]
      })
    } catch (switchError: any) {
      // 如果网络不存在，尝试添加
      if (switchError.code === 4902) {
        try {
          await window.ethereum.request({
            method: 'wallet_addEthereumChain',
            params: [network]
          })
        } catch (addError) {
          console.error('Failed to add network:', addError)
          toast.error('添加网络失败')
        }
      } else {
        console.error('Failed to switch network:', switchError)
        toast.error('切换网络失败')
      }
    }
  }

  // 监听账户变化
  useEffect(() => {
    if (!window.ethereum) return

    const handleAccountsChanged = (accounts: string[]) => {
      if (accounts.length === 0) {
        disconnectWallet()
      } else {
        setAccount(accounts[0])
        toast('账户已切换', { icon: 'ℹ️' })
      }
    }

    const handleChainChanged = (chainIdHex: string) => {
      const newChainId = parseInt(chainIdHex, 16)
      setChainId(newChainId)
      toast('网络已切换', { icon: 'ℹ️' })
      // 重新加载页面以确保状态同步
      window.location.reload()
    }

    window.ethereum.on('accountsChanged', handleAccountsChanged)
    window.ethereum.on('chainChanged', handleChainChanged)

    return () => {
      window.ethereum?.removeListener('accountsChanged', handleAccountsChanged)
      window.ethereum?.removeListener('chainChanged', handleChainChanged)
    }
  }, [])

  // 自动连接（如果之前已连接）
  useEffect(() => {
    const autoConnect = async () => {
      if (!window.ethereum) return

      try {
        const accounts = await window.ethereum.request({
          method: 'eth_accounts'
        })

        if (accounts.length > 0 && !account) {  // ✅ 只在未连接时自动连接
          // 创建Provider和Signer
          const providerInstance = new BrowserProvider(window.ethereum)
          const signerInstance = await providerInstance.getSigner()
          const network = await providerInstance.getNetwork()

          setProvider(providerInstance)
          setSigner(signerInstance)
          setAccount(accounts[0])
          setChainId(Number(network.chainId))

          // 初始化合约
          const contractInstance = await initContract(providerInstance, signerInstance)
          setContract(contractInstance)
        }
      } catch (error) {
        console.error('Auto connect failed:', error)
      }
    }

    autoConnect()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])  // ✅ 空依赖数组，只在组件挂载时执行一次

  const value: Web3State = {
    provider,
    signer,
    account,
    chainId,
    contract,
    isConnected: !!account,
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

// 扩展Window类型
declare global {
  interface Window {
    ethereum?: any
  }
}
