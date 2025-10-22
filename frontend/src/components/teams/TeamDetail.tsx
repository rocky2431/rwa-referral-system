import React, { useState, useEffect } from 'react'
import {
  Space,
  Card,
  Button,
  Tabs,
  Statistic,
  Row,
  Col,
  Alert,
  Modal,
  message,
  Spin,
  Descriptions,
  Tag
} from 'antd'
import {
  TeamOutlined,
  UserAddOutlined,
  LogoutOutlined,
  SettingOutlined,
  TrophyOutlined,
  GiftOutlined,
  RiseOutlined,
  LineChartOutlined,
  InfoCircleOutlined
} from '@ant-design/icons'
import type { TeamDetailResponse, TeamStatistics, TeamMemberRole } from '@/services/api'
import { teamsApi, TeamMemberStatus } from '@/services/api'
import { TeamCard } from './TeamCard'
import { TeamMemberList } from './TeamMemberList'
import { TeamTaskList } from './TeamTaskList'

/**
 * TeamDetail 组件属性
 */
interface TeamDetailProps {
  /** 战队ID */
  teamId: number
  /** 当前用户ID */
  userId?: number
  /** 当前用户在该战队的角色（如果已加入） */
  userRole?: TeamMemberRole
  /** 当前用户在该战队的状态（如果已加入） */
  userStatus?: TeamMemberStatus
  /** 关闭回调 */
  onClose?: () => void
  /** 刷新回调 */
  onRefresh?: () => void
}

/**
 * 战队详情组件
 *
 * 完整展示战队的所有信息，包括：
 * - 战队基本信息卡片
 * - 战队统计数据
 * - 成员列表
 * - 任务列表
 * - 操作按钮（加入/退出/管理）
 *
 * 根据用户角色显示不同功能：
 * - 访客：可查看公开战队信息，可申请加入
 * - 成员：可查看完整信息，可退出战队
 * - 管理员：可管理成员
 * - 队长：可修改设置、分配奖励
 *
 * 设计原则：
 * - SRP：专注于战队详情展示和基本操作
 * - DRY：复用 TeamCard、TeamMemberList、TeamTaskList 组件
 * - KISS：清晰的信息层级和简洁的操作流程
 */
export const TeamDetail: React.FC<TeamDetailProps> = ({
  teamId,
  userId,
  userRole,
  userStatus,
  onClose,
  onRefresh
}) => {
  // ==================== 状态管理 ====================

  /** 战队详情数据 */
  const [teamDetail, setTeamDetail] = useState<TeamDetailResponse | null>(null)

  /** 战队统计数据 */
  const [statistics, setStatistics] = useState<TeamStatistics | null>(null)

  /** 加载中 */
  const [loading, setLoading] = useState(false)

  /** 操作中（加入/退出/分配） */
  const [processing, setProcessing] = useState(false)

  /** 当前激活的标签页 */
  const [activeTab, setActiveTab] = useState('info')

  // ==================== 权限判断 ====================

  /** 是否是队长 */
  const isCaptain = userId === teamDetail?.captain_id

  /** 是否是管理员或队长 */
  const isAdmin = isCaptain || (userRole && ['captain', 'admin'].includes(userRole))

  /** 是否是战队成员 */
  const isMember = userStatus === TeamMemberStatus.ACTIVE

  /** 是否可以加入（未加入 + 战队公开 + 未达人数上限） */
  const canJoin =
    !isMember &&
    teamDetail?.is_public &&
    (teamDetail?.member_count || 0) < (teamDetail?.max_members || Infinity)

  // ==================== 业务逻辑 ====================

  /**
   * 加载战队详情
   */
  const loadTeamDetail = async () => {
    setLoading(true)
    try {
      const detail = await teamsApi.getDetail(teamId)
      setTeamDetail(detail)
    } catch (error: any) {
      console.error('加载战队详情失败:', error)
      message.error(error.message || '加载战队详情失败')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 加载战队统计
   */
  const loadStatistics = async () => {
    try {
      const stats = await teamsApi.getStatistics(teamId)
      setStatistics(stats)
    } catch (error) {
      console.error('加载战队统计失败:', error)
    }
  }

  /**
   * 加入战队
   */
  const handleJoinTeam = async () => {
    if (!userId) {
      message.warning('请先登录')
      return
    }

    Modal.confirm({
      title: '加入战队',
      content: `确定要加入 "${teamDetail?.name}" 战队吗？${
        teamDetail?.require_approval ? '需要等待队长审批。' : ''
      }`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        setProcessing(true)
        try {
          await teamsApi.join(teamId, userId)
          message.success(
            teamDetail?.require_approval
              ? '申请已提交，请等待队长审批'
              : '加入战队成功！'
          )
          await loadTeamDetail()
          onRefresh?.()
        } catch (error: any) {
          console.error('加入战队失败:', error)
          message.error(error.message || '加入战队失败')
        } finally {
          setProcessing(false)
        }
      }
    })
  }

  /**
   * 退出战队
   */
  const handleLeaveTeam = async () => {
    if (!userId) return

    Modal.confirm({
      title: '退出战队',
      content: `确定要退出 "${teamDetail?.name}" 战队吗？退出后需要重新申请才能加入。`,
      okText: '确定退出',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        setProcessing(true)
        try {
          await teamsApi.leave(teamId, userId)
          message.success('已退出战队')
          onRefresh?.()
          onClose?.()
        } catch (error: any) {
          console.error('退出战队失败:', error)
          message.error(error.message || '退出战队失败')
        } finally {
          setProcessing(false)
        }
      }
    })
  }

  /**
   * 分配奖励池（仅队长）
   */
  const handleDistributeRewards = async () => {
    if (!userId || !isCaptain) return

    Modal.confirm({
      title: '分配奖励池',
      content: `确定要将战队奖励池（${teamDetail?.reward_pool} 积分）分配给所有成员吗？将根据贡献值按比例分配。`,
      okText: '确定分配',
      cancelText: '取消',
      onOk: async () => {
        setProcessing(true)
        try {
          await teamsApi.distributeRewards(teamId, userId)
          message.success('奖励分配成功！')
          await loadTeamDetail()
          await loadStatistics()
          onRefresh?.()
        } catch (error: any) {
          console.error('分配奖励失败:', error)
          message.error(error.message || '分配奖励失败')
        } finally {
          setProcessing(false)
        }
      }
    })
  }

  // ==================== 生命周期 ====================

  useEffect(() => {
    loadTeamDetail()
    loadStatistics()
  }, [teamId])

  // ==================== 渲染 ====================

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0' }}>
        <Spin size="large" tip="加载战队信息中..." />
      </div>
    )
  }

  if (!teamDetail) {
    return (
      <Alert
        message="战队未找到"
        description="无法加载战队详情，请返回战队列表重试"
        type="error"
        showIcon
        action={
          onClose && (
            <Button size="small" onClick={onClose}>
              返回
            </Button>
          )
        }
      />
    )
  }

  // 标签页配置
  const tabItems = [
    {
      key: 'info',
      label: (
        <span>
          <InfoCircleOutlined />
          基本信息
        </span>
      ),
      children: (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 战队信息卡片 */}
          <TeamCard team={teamDetail} loading={loading} />

          {/* 战队统计 */}
          {statistics && (
            <Card title="战队统计">
              <Row gutter={[16, 16]}>
                <Col xs={12} sm={8} md={6}>
                  <Statistic
                    title="总成员"
                    value={statistics.total_members}
                    prefix={<TeamOutlined />}
                  />
                </Col>
                <Col xs={12} sm={8} md={6}>
                  <Statistic
                    title="活跃成员"
                    value={statistics.active_members}
                    prefix={<TeamOutlined />}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
                <Col xs={12} sm={8} md={6}>
                  <Statistic
                    title="总任务"
                    value={statistics.total_tasks}
                    prefix={<LineChartOutlined />}
                  />
                </Col>
                <Col xs={12} sm={8} md={6}>
                  <Statistic
                    title="已完成"
                    value={statistics.completed_tasks}
                    prefix={<TrophyOutlined />}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
                <Col xs={12} sm={8} md={6}>
                  <Statistic
                    title="奖励池"
                    value={statistics.reward_pool}
                    prefix={<GiftOutlined />}
                    valueStyle={{ color: '#eb2f96' }}
                  />
                </Col>
                <Col xs={12} sm={8} md={6}>
                  <Statistic
                    title="人均贡献"
                    value={Math.round(statistics.average_contribution)}
                    prefix={<RiseOutlined />}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Col>
              </Row>
            </Card>
          )}

          {/* 战队详细信息 */}
          <Card title="详细信息">
            <Descriptions bordered column={{ xs: 1, sm: 2 }}>
              <Descriptions.Item label="战队ID">#{teamDetail.id}</Descriptions.Item>
              <Descriptions.Item label="队长ID">#{teamDetail.captain_id}</Descriptions.Item>
              {teamDetail.captain_name && (
                <Descriptions.Item label="队长名称">{teamDetail.captain_name}</Descriptions.Item>
              )}
              {teamDetail.captain_wallet && (
                <Descriptions.Item label="队长钱包">
                  <code style={{ fontSize: 12 }}>
                    {teamDetail.captain_wallet.slice(0, 6)}...{teamDetail.captain_wallet.slice(-4)}
                  </code>
                </Descriptions.Item>
              )}
              <Descriptions.Item label="成员人数">
                {teamDetail.member_count} / {teamDetail.max_members}
              </Descriptions.Item>
              <Descriptions.Item label="战队类型">
                {teamDetail.is_public ? (
                  <Tag color="green">公开</Tag>
                ) : (
                  <Tag color="orange">私密</Tag>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="加入方式">
                {teamDetail.require_approval ? (
                  <Tag color="blue">需审批</Tag>
                ) : (
                  <Tag color="green">自由加入</Tag>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间" span={teamDetail.captain_wallet ? 1 : 2}>
                {new Date(teamDetail.created_at).toLocaleString()}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Space>
      )
    },
    {
      key: 'members',
      label: (
        <span>
          <TeamOutlined />
          成员列表
        </span>
      ),
      children: <TeamMemberList teamId={teamId} />
    },
    {
      key: 'tasks',
      label: (
        <span>
          <TrophyOutlined />
          战队任务
        </span>
      ),
      children: <TeamTaskList teamId={teamId} />
    }
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* 操作按钮区域 */}
      <Card>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space>
            {canJoin && userId && (
              <Button
                type="primary"
                icon={<UserAddOutlined />}
                onClick={handleJoinTeam}
                loading={processing}
                size="large"
              >
                {teamDetail.require_approval ? '申请加入' : '立即加入'}
              </Button>
            )}
            {isMember && (
              <Button
                danger
                icon={<LogoutOutlined />}
                onClick={handleLeaveTeam}
                loading={processing}
              >
                退出战队
              </Button>
            )}
            {isCaptain && (
              <>
                <Button icon={<SettingOutlined />} onClick={() => message.info('设置功能开发中')}>
                  战队设置
                </Button>
                <Button
                  type="primary"
                  icon={<GiftOutlined />}
                  onClick={handleDistributeRewards}
                  loading={processing}
                  disabled={!teamDetail.reward_pool || teamDetail.reward_pool === 0}
                >
                  分配奖励池 ({teamDetail.reward_pool})
                </Button>
              </>
            )}
          </Space>
          {onClose && (
            <Button onClick={onClose} size="large">
              返回
            </Button>
          )}
        </Space>
      </Card>

      {/* 提示信息 */}
      {!isMember && !teamDetail.is_public && (
        <Alert
          message="私密战队"
          description="这是一个私密战队，只有受邀成员可以加入"
          type="info"
          showIcon
        />
      )}
      {isMember && userStatus === TeamMemberStatus.PENDING && (
        <Alert
          message="待审批"
          description="您的加入申请正在等待队长审批"
          type="warning"
          showIcon
        />
      )}

      {/* 标签页 */}
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
    </Space>
  )
}

export default TeamDetail
