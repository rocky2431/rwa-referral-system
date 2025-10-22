import React, { useState, useEffect } from 'react'
import { Space, Alert, Spin, Button, Empty } from 'antd'
import {
  TeamOutlined,
  WalletOutlined,
  PlusOutlined,
  ReloadOutlined,
  UserAddOutlined
} from '@ant-design/icons'
import { useWeb3 } from '@/contexts/Web3Context'
import { useUser } from '@/hooks/useUser'
import { teamsApi, TeamResponse } from '@/services/api'
import { TeamCard } from '@/components/teams/TeamCard'
import { TeamMemberList } from '@/components/teams/TeamMemberList'
import { TeamTaskList } from '@/components/teams/TeamTaskList'
import { JoinTeamModal } from '@/components/teams/JoinTeamModal'
import { CreateTeamModal } from '@/components/teams/CreateTeamModal'
import { RegisterModal } from '@/components/user/RegisterModal'

const Teams: React.FC = () => {
  const { isConnected } = useWeb3()
  const { userId, isRegistered, isLoading: isUserLoading, refreshUser } = useUser()
  const [loading, setLoading] = useState(false)
  const [myTeam, setMyTeam] = useState<TeamResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [joinModalVisible, setJoinModalVisible] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [registerModalVisible, setRegisterModalVisible] = useState(false)

  // 加载用户的战队信息
  const loadMyTeam = async () => {
    if (!userId) return

    setLoading(true)
    setError(null)

    try {
      // 调用getUserTeam API获取用户所在的战队
      const team = await teamsApi.getUserTeam(userId)
      setMyTeam(team)
    } catch (err: any) {
      console.error('加载战队信息失败:', err)
      setError(err.message || '加载战队信息失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isConnected && userId) {
      loadMyTeam()
    }
  }, [isConnected, userId])

  // 未连接钱包提示
  if (!isConnected) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="请先连接钱包"
          description="查看战队信息需要先连接您的Web3钱包"
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
          description="请先注册账户后再查看战队信息"
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
  if (loading && !myTeam) {
    return (
      <div style={{ padding: '100px', textAlign: 'center' }}>
        <Spin size="large" tip="加载战队信息中..." />
      </div>
    )
  }

  // 错误状态
  if (error && !myTeam) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="加载失败"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" icon={<ReloadOutlined />} onClick={loadMyTeam}>
              重试
            </Button>
          }
        />
      </div>
    )
  }

  // 用户未加入任何战队
  if (!myTeam) {
    return (
      <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
        <Empty
          image="https://gw.alipayobjects.com/zos/antfincdn/ZHrcdLPrvN/empty.svg"
          imageStyle={{ height: 200 }}
          description={
            <Space direction="vertical" size={16}>
              <h2>你还没有加入任何战队</h2>
              <p style={{ color: '#666' }}>
                加入战队可以与队友一起完成任务、获得奖励，并在排行榜上竞争！
              </p>
            </Space>
          }
        >
          <Space size={16}>
            <Button
              type="primary"
              size="large"
              icon={<TeamOutlined />}
              onClick={() => setJoinModalVisible(true)}
            >
              浏览战队
            </Button>
            <Button
              size="large"
              icon={<PlusOutlined />}
              onClick={() => setCreateModalVisible(true)}
            >
              创建战队
            </Button>
          </Space>
        </Empty>

        {/* 加入战队弹窗 */}
        <JoinTeamModal
          visible={joinModalVisible}
          userId={userId}
          onClose={() => setJoinModalVisible(false)}
          onSuccess={loadMyTeam}
        />

        {/* 创建战队弹窗 */}
        <CreateTeamModal
          visible={createModalVisible}
          captainId={userId}
          onClose={() => setCreateModalVisible(false)}
          onSuccess={loadMyTeam}
        />
      </div>
    )
  }

  // 用户已加入战队 - 显示战队详情
  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 页面标题和操作按钮 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ margin: 0 }}>
            <TeamOutlined style={{ marginRight: 8 }} />
            我的战队
          </h1>
          <Space>
            <Button icon={<ReloadOutlined />} onClick={loadMyTeam} loading={loading}>
              刷新数据
            </Button>
            <Button
              danger
              onClick={async () => {
                if (window.confirm('确定要离开战队吗？')) {
                  try {
                    await teamsApi.leave(myTeam.id, userId)
                    setMyTeam(null)
                  } catch (error) {
                    console.error('离开战队失败:', error)
                  }
                }
              }}
            >
              离开战队
            </Button>
          </Space>
        </div>

        {/* 战队信息卡片 */}
        <TeamCard team={myTeam} loading={loading} />

        {/* 战队成员列表 */}
        <TeamMemberList teamId={myTeam.id} />

        {/* 战队任务列表 */}
        <TeamTaskList teamId={myTeam.id} />
      </Space>
    </div>
  )
}

export default Teams
