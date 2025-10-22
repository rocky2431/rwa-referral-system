/**
 * useUser Hook
 *
 * 职责:统一管理用户信息,处理钱包地址到user_id的映射
 *
 * 设计原则:
 * - SRP: 只负责用户信息管理,不处理业务逻辑
 * - DRY: 所有页面通过这个hook获取用户信息,避免重复查询
 * - KISS: 简单直接的状态管理,无过度设计
 */

import { useState, useEffect, useCallback } from 'react'
import { useWeb3 } from '../contexts/Web3Context'
import { usersApi, UserResponse, UserByWalletResponse } from '../services/api'

interface UseUserReturn {
  // 基础状态
  userId: number | null
  user: UserResponse | null
  isLoading: boolean
  error: string | null

  // 用户状态
  isRegistered: boolean
  isCheckingUser: boolean

  // 方法
  refreshUser: () => Promise<void>
  registerNewUser: (username?: string, avatarUrl?: string) => Promise<UserResponse | null>
}

export const useUser = (): UseUserReturn => {
  const { account } = useWeb3()

  const [userId, setUserId] = useState<number | null>(null)
  const [user, setUser] = useState<UserResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isRegistered, setIsRegistered] = useState(false)
  const [isCheckingUser, setIsCheckingUser] = useState(false)

  /**
   * 检查用户是否已注册
   */
  const checkUser = useCallback(async (walletAddress: string): Promise<UserByWalletResponse | null> => {
    try {
      setIsCheckingUser(true)
      setError(null)

      const response = await usersApi.getUserByWallet(walletAddress)

      if (response.exists && response.user_id) {
        setUserId(response.user_id)
        setIsRegistered(true)
        return response
      } else {
        setUserId(null)
        setIsRegistered(false)
        return response
      }
    } catch (err) {
      console.error('检查用户失败:', err)
      setError(err instanceof Error ? err.message : '检查用户失败')
      return null
    } finally {
      setIsCheckingUser(false)
    }
  }, [])

  /**
   * 获取用户详细信息
   */
  const fetchUserDetail = useCallback(async (uid: number): Promise<void> => {
    try {
      setIsLoading(true)
      setError(null)

      const userDetail = await usersApi.getDetail(uid)
      setUser(userDetail)
    } catch (err) {
      console.error('获取用户详情失败:', err)
      setError(err instanceof Error ? err.message : '获取用户详情失败')
    } finally {
      setIsLoading(false)
    }
  }, [])

  /**
   * 注册新用户
   */
  const registerNewUser = useCallback(async (
    username?: string,
    avatarUrl?: string
  ): Promise<UserResponse | null> => {
    if (!account) {
      setError('请先连接钱包')
      return null
    }

    try {
      setIsLoading(true)
      setError(null)

      const newUser = await usersApi.register({
        wallet_address: account,
        username,
        avatar_url: avatarUrl
      })

      setUserId(newUser.id)
      setUser(newUser)
      setIsRegistered(true)

      console.log('✅ 用户注册成功:', newUser)
      return newUser
    } catch (err) {
      console.error('注册用户失败:', err)
      setError(err instanceof Error ? err.message : '注册用户失败')
      return null
    } finally {
      setIsLoading(false)
    }
  }, [account])

  /**
   * 刷新用户信息
   */
  const refreshUser = useCallback(async (): Promise<void> => {
    if (!account) {
      setUserId(null)
      setUser(null)
      setIsRegistered(false)
      return
    }

    // 先检查用户是否存在
    const userCheck = await checkUser(account)

    if (userCheck && userCheck.exists && userCheck.user_id) {
      // 用户已注册,获取详细信息
      await fetchUserDetail(userCheck.user_id)
    } else {
      // 用户未注册,清空状态
      setUser(null)
    }
  }, [account, checkUser, fetchUserDetail])

  /**
   * 监听钱包地址变化
   */
  useEffect(() => {
    if (account) {
      refreshUser()
    } else {
      // 未连接钱包,重置状态
      setUserId(null)
      setUser(null)
      setIsRegistered(false)
      setError(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [account])  // ✅ 只依赖account,避免循环

  return {
    // 基础状态
    userId,
    user,
    isLoading,
    error,

    // 用户状态
    isRegistered,
    isCheckingUser,

    // 方法
    refreshUser,
    registerNewUser
  }
}
