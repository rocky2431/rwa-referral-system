import React, { useState } from 'react'
import { Space, Alert, Button, Spin } from 'antd'
import {
  CheckCircleOutlined,
  WalletOutlined,
  UserAddOutlined
} from '@ant-design/icons'
import { useWeb3 } from '@/contexts/Web3Context'
import { useUser } from '@/hooks/useUser'
import { TaskProgress } from '@/components/tasks/TaskProgress'
import { TaskList } from '@/components/tasks/TaskList'
import { RegisterModal } from '@/components/user/RegisterModal'

const Tasks: React.FC = () => {
  const { isConnected } = useWeb3()
  const { userId, isRegistered, isLoading: isUserLoading, refreshUser } = useUser()
  const [refreshKey, setRefreshKey] = useState(0)
  const [registerModalVisible, setRegisterModalVisible] = useState(false)

  // 刷新数据
  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1)
  }

  // 未连接钱包提示
  if (!isConnected) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="请先连接钱包"
          description="查看任务列表需要先连接您的Web3钱包"
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

  // 用户未注册
  if (!isRegistered || !userId) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="用户未注册"
          description="请先注册账户后再查看任务"
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

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 页面标题 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ margin: 0 }}>
            <CheckCircleOutlined style={{ marginRight: 8 }} />
            我的任务
          </h1>
        </div>

        {/* 任务统计 */}
        <TaskProgress key={`progress-${refreshKey}`} userId={userId} />

        {/* 任务列表 */}
        <TaskList key={`list-${refreshKey}`} userId={userId!} onRefresh={handleRefresh} />
      </Space>
    </div>
  )
}

export default Tasks
