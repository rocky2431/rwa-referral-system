import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'

/**
 * 推荐码上下文类型
 */
interface ReferralContextType {
  // 推荐码（从URL参数中提取）
  inviteCode: string | null
  // 设置推荐码
  setInviteCode: (code: string | null) => void
  // 清除推荐码
  clearInviteCode: () => void
  // 是否已自动绑定
  hasAutobound: boolean
  // 设置已自动绑定标志
  markAsAutobound: () => void
}

const ReferralContext = createContext<ReferralContextType | undefined>(undefined)

/**
 * 推荐码Provider
 * 负责从URL参数中提取推荐码并提供给子组件
 */
export function ReferralProvider({ children }: { children: ReactNode }) {
  const [inviteCode, setInviteCodeState] = useState<string | null>(null)
  const [hasAutobound, setHasAutobound] = useState(false)

  // 从URL参数中提取推荐码
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const refCode = params.get('ref')

    if (refCode) {
      console.log('检测到推荐码:', refCode)
      setInviteCodeState(refCode)

      // 将推荐码保存到localStorage，以便用户刷新页面后仍能使用
      localStorage.setItem('pending_invite_code', refCode)

      // 清理URL参数（可选）
      const newUrl = window.location.pathname
      window.history.replaceState({}, '', newUrl)
    } else {
      // 尝试从localStorage恢复推荐码
      const savedCode = localStorage.getItem('pending_invite_code')
      if (savedCode) {
        console.log('从localStorage恢复推荐码:', savedCode)
        setInviteCodeState(savedCode)
      }
    }
  }, [])

  const setInviteCode = (code: string | null) => {
    setInviteCodeState(code)
    if (code) {
      localStorage.setItem('pending_invite_code', code)
    } else {
      localStorage.removeItem('pending_invite_code')
    }
  }

  const clearInviteCode = () => {
    setInviteCodeState(null)
    localStorage.removeItem('pending_invite_code')
    setHasAutobound(false)
  }

  const markAsAutobound = () => {
    setHasAutobound(true)
  }

  return (
    <ReferralContext.Provider
      value={{
        inviteCode,
        setInviteCode,
        clearInviteCode,
        hasAutobound,
        markAsAutobound
      }}
    >
      {children}
    </ReferralContext.Provider>
  )
}

/**
 * 使用推荐码Hook
 */
export function useReferralCode() {
  const context = useContext(ReferralContext)
  if (context === undefined) {
    throw new Error('useReferralCode must be used within a ReferralProvider')
  }
  return context
}
