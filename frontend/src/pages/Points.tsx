import React, { useState, useEffect } from 'react'
import { Space, Alert, Spin, Button } from 'antd'
import { ReloadOutlined, WalletOutlined, UserAddOutlined } from '@ant-design/icons'
import { useWeb3 } from '@/contexts/Web3Context'
import { useUser } from '@/hooks/useUser'
import { pointsApi, UserPointsResponse } from '@/services/api'
import { PointsCard } from '@/components/points/PointsCard'
import { PointsHistory } from '@/components/points/PointsHistory'
import { RegisterModal } from '@/components/user/RegisterModal'

const Points: React.FC = () => {
  const { isConnected } = useWeb3()
  const { userId, isRegistered, isLoading: isUserLoading, error: userError, refreshUser } = useUser()
  const [points, setPoints] = useState<UserPointsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [registerModalVisible, setRegisterModalVisible] = useState(false)

  // 加载积分数据
  const loadPoints = async () => {
    if (!userId) return

    setLoading(true)
    setError(null)

    try {
      const data = await pointsApi.getUserPoints(userId)
      setPoints(data)
    } catch (err: any) {
      console.error('加载积分数据失败:', err)
      setError(err.message || '加载积分数据失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isConnected && userId) {
      loadPoints()
    }
  }, [isConnected, userId])

  // 未连接钱包提示
  if (!isConnected) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="请先连接钱包"
          description="查看积分信息需要先连接您的Web3钱包"
          type="warning"
          showIcon
          icon={<WalletOutlined />}
          action={
            <Button size="small" onClick={() => window.location.href = '/'}>
              前往首页
            </Button>
          }
        />
      </div>
    )
  }

  // 用户加载中
  if (isUserLoading) {
    return (
      <div style={{ padding: '100px', textAlign: 'center' }}>
        <Spin size="large" tip="加载用户信息中..." />
      </div>
    )
  }

  // 用户错误
  if (userError) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="用户信息加载失败"
          description={userError}
          type="error"
          showIcon
        />
      </div>
    )
  }

  // 用户未注册
  if (!isRegistered || !userId) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="用户未注册"
          description="请先注册账户后再查看积分信息"
          type="warning"
          showIcon
          action={
            <Button
              type="primary"
              icon={<UserAddOutlined />}
              onClick={() => setRegisterModalVisible(true)}
            >
              立即注册
            </Button>
          }
        />

        {/* 注册弹窗 */}
        <RegisterModal
          visible={registerModalVisible}
          onClose={() => setRegisterModalVisible(false)}
          onSuccess={() => {
            setRegisterModalVisible(false)
            refreshUser()
          }}
        />
      </div>
    )
  }

  // 加载中
  if (loading && !points) {
    return (
      <div style={{ padding: '100px', textAlign: 'center' }}>
        <Spin size="large" tip="加载积分数据中..." />
      </div>
    )
  }

  // 错误状态
  if (error && !points) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="加载失败"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" icon={<ReloadOutlined />} onClick={loadPoints}>
              重试
            </Button>
          }
        />
      </div>
    )
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 页面标题和刷新按钮 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ margin: 0 }}>
            <WalletOutlined style={{ marginRight: 8 }} />
            我的积分
          </h1>
          <Button icon={<ReloadOutlined />} onClick={loadPoints} loading={loading}>
            刷新数据
          </Button>
        </div>

        {/* 积分概览卡片 */}
        {points && <PointsCard points={points} loading={loading} />}

        {/* 积分流水记录 */}
        {userId && <PointsHistory userId={userId} />}
      </Space>
    </div>
  )
}

export default Points
