import { useState, useCallback, useEffect } from 'react'
import { useWeb3 } from '@/contexts/Web3Context'
import { parseEther } from 'ethers'
import toast from 'react-hot-toast'
import { referralApi } from '@/services/api'

// 用户信息类型
export interface UserInfo {
  referrer: string
  reward: bigint
  referredCount: number
  lastActiveTimestamp: number
  isActive: boolean
}

// 推荐系统配置
export interface ReferralConfig {
  decimals: number
  secondsUntilInactive: number
  level1Rate: number
  level2Rate: number
  referralBonus: number
}

/**
 * 推荐系统Hook
 * 封装所有与推荐合约交互的功能
 */
export function useReferral() {
  const { contract, account, isConnected } = useWeb3()
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null)
  const [config, setConfig] = useState<ReferralConfig | null>(null)
  const [loading, setLoading] = useState(false)

  /**
   * 获取推荐系统配置
   */
  const fetchConfig = useCallback(async () => {
    try {
      // 优先使用API获取配置（更可靠）
      const apiConfig = await referralApi.getConfig()
      const configData: ReferralConfig = {
        decimals: apiConfig.decimals,
        secondsUntilInactive: apiConfig.seconds_until_inactive,
        level1Rate: apiConfig.level_1_bonus_rate,
        level2Rate: apiConfig.level_2_bonus_rate,
        referralBonus: apiConfig.level_1_bonus_rate + apiConfig.level_2_bonus_rate
      }
      setConfig(configData)
      return configData
    } catch (error) {
      // API失败时，尝试智能合约（降级方案）
      if (!contract) {
        console.error('Failed to fetch config from API and no contract available')
        return null
      }

      try {
        const result = await contract.getConfig()
        const configData: ReferralConfig = {
          decimals: Number(result[0]),
          secondsUntilInactive: Number(result[1]),
          level1Rate: Number(result[2]),
          level2Rate: Number(result[3]),
          referralBonus: Number(result[4])
        }
        setConfig(configData)
        return configData
      } catch (contractError) {
        console.error('Failed to fetch config from contract:', contractError)
        return null
      }
    }
  }, [contract])

  /**
   * 获取用户推荐信息
   */
  const fetchUserInfo = useCallback(async (address?: string) => {
    const targetAddress = address || account
    if (!targetAddress) return

    setLoading(true)
    try {
      // 优先使用API获取用户信息（更可靠）
      const apiUserInfo = await referralApi.getUserInfo(targetAddress)

      const info: UserInfo = {
        referrer: apiUserInfo.referrer,
        reward: BigInt(apiUserInfo.reward),
        referredCount: apiUserInfo.referred_count,
        lastActiveTimestamp: apiUserInfo.last_active_timestamp,
        isActive: apiUserInfo.is_active
      }

      if (!address || address === account) {
        setUserInfo(info)
      }

      return info
    } catch (error) {
      // API失败时，尝试智能合约（降级方案）
      if (!contract) {
        console.error('Failed to fetch user info from API and no contract available')
        return null
      }

      try {
        const result = await contract.getUserInfo(targetAddress)
        const isActive = await contract.isActive(targetAddress)

        const info: UserInfo = {
          referrer: result[0],
          reward: result[1],
          referredCount: Number(result[2]),
          lastActiveTimestamp: Number(result[3]),
          isActive
        }

        if (!address || address === account) {
          setUserInfo(info)
        }

        return info
      } catch (contractError) {
        console.error('Failed to fetch user info from contract:', contractError)
        return null
      }
    } finally {
      setLoading(false)
    }
  }, [contract, account])

  /**
   * 绑定推荐人（使用后端API）
   */
  const bindReferrer = useCallback(async (referrerAddress: string) => {
    if (!account) {
      toast.error('请先连接钱包')
      return false
    }

    setLoading(true)
    try {
      // 调用后端API绑定推荐关系
      const result = await referralApi.bindReferrer(account, referrerAddress)

      if (result.success) {
        toast.success(result.message || '绑定成功！')

        // 刷新用户信息
        await fetchUserInfo()

        return true
      } else {
        toast.error(result.message || '绑定失败')
        return false
      }
    } catch (error: any) {
      console.error('Failed to bind referrer:', error)

      // 解析错误消息
      let errorMessage = '绑定失败'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }

      toast.error(errorMessage)
      return false
    } finally {
      setLoading(false)
    }
  }, [account, fetchUserInfo])

  /**
   * 通过邀请码绑定推荐人（使用后端API）
   */
  const bindReferrerByCode = useCallback(async (inviteCode: string) => {
    if (!account) {
      toast.error('请先连接钱包')
      return false
    }

    setLoading(true)
    try {
      // 调用后端API通过邀请码绑定推荐关系
      const result = await referralApi.bindReferrerByCode(account, inviteCode)

      if (result.success) {
        toast.success(result.message || '绑定成功！')

        // 刷新用户信息
        await fetchUserInfo()

        return true
      } else {
        toast.error(result.message || '绑定失败')
        return false
      }
    } catch (error: any) {
      console.error('Failed to bind referrer by code:', error)

      // 解析错误消息
      let errorMessage = '绑定失败'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }

      toast.error(errorMessage)
      return false
    } finally {
      setLoading(false)
    }
  }, [account, fetchUserInfo])

  /**
   * 触发推荐奖励
   * @param amount 购买金额（ETH/BNB）
   */
  const triggerReward = useCallback(async (amount: string) => {
    if (!contract || !account) {
      toast.error('请先连接钱包')
      return null
    }

    setLoading(true)
    try {
      // 转换金额为Wei
      const amountWei = parseEther(amount)

      // 发送交易并附带相应的BNB
      const tx = await contract.triggerReward(amountWei, {
        value: amountWei
      })

      toast.loading('奖励分发中...', { id: 'reward-tx' })
      await tx.wait()

      toast.success('奖励分发成功！', { id: 'reward-tx' })

      // 刷新用户信息
      await fetchUserInfo()

      return true
    } catch (error: any) {
      console.error('Failed to trigger reward:', error)

      let errorMessage = '奖励分发失败'
      if (error.message?.includes('user rejected')) {
        errorMessage = '用户取消交易'
      } else if (error.message?.includes('insufficient funds')) {
        errorMessage = '余额不足'
      }

      toast.error(errorMessage, { id: 'reward-tx' })
      return null
    } finally {
      setLoading(false)
    }
  }, [contract, account, fetchUserInfo])

  /**
   * 批量获取用户信息
   */
  const getBatchUserInfo = useCallback(async (addresses: string[]) => {
    if (!contract) return null

    try {
      const results = await contract.getBatchUserInfo(addresses)

      return results.map((result: any, index: number) => ({
        address: addresses[index],
        referrer: result[0],
        reward: result[1],
        referredCount: Number(result[2]),
        lastActiveTimestamp: Number(result[3])
      }))
    } catch (error) {
      console.error('Failed to fetch batch user info:', error)
      return null
    }
  }, [contract])

  /**
   * 格式化奖励金额
   */
  const formatReward = useCallback((reward: bigint): string => {
    // 将Wei转换为ETH/BNB，保留4位小数
    const bnbAmount = Number(reward) / 1e18
    return bnbAmount.toFixed(4)
  }, [])

  /**
   * 计算用户活跃天数
   */
  const calculateActiveDays = useCallback((lastActiveTimestamp: number): number => {
    if (lastActiveTimestamp === 0) return 0

    const now = Math.floor(Date.now() / 1000)
    const daysPassed = Math.floor((now - lastActiveTimestamp) / 86400)

    return daysPassed
  }, [])

  /**
   * 检查推荐地址有效性
   */
  const validateReferrerAddress = useCallback((address: string): { valid: boolean; error?: string } => {
    // 检查地址格式
    if (!/^0x[a-fA-F0-9]{40}$/.test(address)) {
      return { valid: false, error: '无效的地址格式' }
    }

    // 检查是否是零地址
    if (address === '0x0000000000000000000000000000000000000000') {
      return { valid: false, error: '不能使用零地址' }
    }

    // 检查是否是自己的地址
    if (account && address.toLowerCase() === account.toLowerCase()) {
      return { valid: false, error: '不能推荐自己' }
    }

    return { valid: true }
  }, [account])

  // 自动加载配置和用户信息
  useEffect(() => {
    // 总是尝试加载配置（优先使用API）
    fetchConfig()
  }, [fetchConfig])

  useEffect(() => {
    // 钱包连接后加载用户信息（优先使用API）
    if (isConnected && account) {
      fetchUserInfo()
    }
  }, [isConnected, account, fetchUserInfo])

  return {
    // 状态
    userInfo,
    config,
    loading,

    // 方法
    fetchUserInfo,
    fetchConfig,
    bindReferrer,
    bindReferrerByCode,
    triggerReward,
    getBatchUserInfo,

    // 工具方法
    formatReward,
    calculateActiveDays,
    validateReferrerAddress
  }
}
