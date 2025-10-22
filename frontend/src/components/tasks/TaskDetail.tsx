import React, { useState, useEffect } from 'react'
import {
  Card,
  Descriptions,
  Progress,
  Tag,
  Button,
  Space,
  Statistic,
  Row,
  Col,
  Timeline,
  Alert,
  message,
  Spin
} from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  GiftOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  FireOutlined,
  CalendarOutlined,
  ThunderboltOutlined,
  InfoCircleOutlined
} from '@ant-design/icons'
import type { UserTaskDetailResponse } from '@/services/api'
import { TaskType, UserTaskStatus, tasksApi } from '@/services/api'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

/**
 * TaskDetail 组件属性
 */
interface TaskDetailProps {
  /** 用户任务ID（UserTask表的ID） */
  userTaskId: number
  /** 用户ID */
  userId: number
  /** 关闭回调 */
  onClose?: () => void
  /** 刷新回调（奖励领取后） */
  onRefresh?: () => void
}

/**
 * 任务详情组件
 *
 * 显示单个任务的详细信息，包括：
 * - 任务基本信息（标题、描述、类型、状态）
 * - 进度详情（当前值/目标值、百分比）
 * - 奖励详情（基础积分、奖励积分、经验值）
 * - 时间信息（开始时间、过期时间、完成时间）
 * - 操作按钮（领取奖励）
 *
 * 设计原则：
 * - SRP：只负责任务详情展示和奖励领取操作
 * - DRY：复用 api.ts 的类型定义和 API 方法
 * - KISS：清晰的信息层级和简洁的操作流程
 */
export const TaskDetail: React.FC<TaskDetailProps> = ({
  userTaskId,
  userId,
  onClose,
  onRefresh
}) => {
  // ==================== 状态管理 ====================

  /** 任务详情数据 */
  const [taskDetail, setTaskDetail] = useState<UserTaskDetailResponse | null>(null)

  /** 加载中 */
  const [loading, setLoading] = useState(false)

  /** 领取奖励中 */
  const [claiming, setClaiming] = useState(false)

  // ==================== 配置常量 ====================

  /** 任务类型配置 */
  const TASK_TYPE_CONFIG: Record<TaskType, { label: string; icon: React.ReactNode; color: string }> = {
    [TaskType.DAILY]: { label: '每日任务', icon: <CalendarOutlined />, color: 'blue' },
    [TaskType.WEEKLY]: { label: '每周任务', icon: <CalendarOutlined />, color: 'cyan' },
    [TaskType.ONCE]: { label: '一次性任务', icon: <CheckCircleOutlined />, color: 'green' },
    [TaskType.SPECIAL]: { label: '特殊任务', icon: <FireOutlined />, color: 'volcano' }
  }

  /** 任务状态配置 */
  const STATUS_CONFIG: Record<UserTaskStatus, { label: string; color: string; icon: React.ReactNode }> = {
    [UserTaskStatus.IN_PROGRESS]: {
      label: '进行中',
      color: 'processing',
      icon: <ClockCircleOutlined />
    },
    [UserTaskStatus.COMPLETED]: {
      label: '已完成',
      color: 'success',
      icon: <CheckCircleOutlined />
    },
    [UserTaskStatus.CLAIMED]: {
      label: '已领取',
      color: 'default',
      icon: <TrophyOutlined />
    },
    [UserTaskStatus.EXPIRED]: {
      label: '已过期',
      color: 'error',
      icon: <CloseCircleOutlined />
    },
    [UserTaskStatus.FAILED]: {
      label: '失败',
      color: 'error',
      icon: <CloseCircleOutlined />
    }
  }

  // ==================== 业务逻辑 ====================

  /**
   * 加载任务详情
   */
  const loadTaskDetail = async () => {
    setLoading(true)
    try {
      const detail = await tasksApi.getUserTask(userTaskId, userId)
      setTaskDetail(detail)
    } catch (error: any) {
      console.error('加载任务详情失败:', error)
      message.error(error.message || '加载任务详情失败')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 领取任务奖励
   */
  const handleClaimReward = async () => {
    if (!taskDetail) return

    setClaiming(true)
    try {
      await tasksApi.claimReward(userTaskId, userId)
      message.success('🎉 奖励领取成功！')

      // 刷新任务详情
      await loadTaskDetail()

      // 通知外部刷新
      onRefresh?.()
    } catch (error: any) {
      console.error('领取奖励失败:', error)
      message.error(error.message || '领取奖励失败，请稍后重试')
    } finally {
      setClaiming(false)
    }
  }

  /**
   * 判断任务是否即将过期
   */
  const isExpiringSoon = (): boolean => {
    if (!taskDetail?.expires_at) return false
    const diffHours = dayjs(taskDetail.expires_at).diff(dayjs(), 'hours')
    return diffHours > 0 && diffHours <= 24
  }

  /**
   * 计算剩余时间
   */
  const getRemainingTime = (): string => {
    if (!taskDetail?.expires_at) return '无限制'
    const now = dayjs()
    const expireTime = dayjs(taskDetail.expires_at)
    if (expireTime.isBefore(now)) return '已过期'
    return expireTime.fromNow()
  }

  // ==================== 生命周期 ====================

  useEffect(() => {
    loadTaskDetail()
  }, [userTaskId, userId])

  // ==================== 渲染 ====================

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0' }}>
        <Spin size="large" tip="加载任务详情中..." />
      </div>
    )
  }

  if (!taskDetail) {
    return (
      <Alert
        message="任务未找到"
        description="无法加载任务详情，请返回任务列表重试"
        type="error"
        showIcon
        action={
          <Button size="small" onClick={onClose}>
            返回
          </Button>
        }
      />
    )
  }

  const taskTypeConfig = taskDetail.task_type
    ? TASK_TYPE_CONFIG[taskDetail.task_type]
    : TASK_TYPE_CONFIG[TaskType.ONCE]
  const statusConfig = STATUS_CONFIG[taskDetail.status]
  const totalReward = taskDetail.reward_points + taskDetail.bonus_points

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* 任务头部信息 */}
      <Card
        title={
          <Space>
            <InfoCircleOutlined />
            <span>任务详情</span>
          </Space>
        }
        extra={
          <Space>
            {taskDetail.task_type && (
              <Tag icon={taskTypeConfig.icon} color={taskTypeConfig.color}>
                {taskTypeConfig.label}
              </Tag>
            )}
            <Tag icon={statusConfig.icon} color={statusConfig.color}>
              {statusConfig.label}
            </Tag>
            {isExpiringSoon() && (
              <Tag color="warning" icon={<ClockCircleOutlined />}>
                即将过期
              </Tag>
            )}
          </Space>
        }
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 任务标题和描述 */}
          <div>
            <h2 style={{ margin: 0, marginBottom: 12 }}>
              {taskDetail.task_title || `任务 #${taskDetail.task_id}`}
            </h2>
            {taskDetail.task_description && (
              <p style={{ margin: 0, color: '#666', fontSize: 15, lineHeight: 1.6 }}>
                {taskDetail.task_description}
              </p>
            )}
          </div>

          {/* 任务进度 */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
              <span style={{ fontSize: 15, fontWeight: 600 }}>任务进度</span>
              <span style={{ fontSize: 16, fontWeight: 'bold', color: '#1890ff' }}>
                {taskDetail.current_value} / {taskDetail.target_value}
              </span>
            </div>
            <Progress
              percent={Math.round(taskDetail.progress_percentage)}
              status={taskDetail.is_completed ? 'success' : 'active'}
              strokeColor={
                taskDetail.is_completed
                  ? '#52c41a'
                  : {
                      '0%': '#108ee9',
                      '100%': '#87d068'
                    }
              }
              strokeWidth={12}
            />
          </div>

          {/* 奖励统计 */}
          <Row gutter={16}>
            <Col xs={24} sm={8}>
              <Statistic
                title="基础积分"
                value={taskDetail.reward_points}
                prefix={<GiftOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            {taskDetail.bonus_points > 0 && (
              <Col xs={24} sm={8}>
                <Statistic
                  title="奖励积分"
                  value={taskDetail.bonus_points}
                  prefix={<ThunderboltOutlined />}
                  valueStyle={{ color: '#faad14' }}
                />
              </Col>
            )}
            <Col xs={24} sm={8}>
              <Statistic
                title="总奖励"
                value={totalReward}
                prefix={<TrophyOutlined />}
                valueStyle={{ color: '#722ed1', fontWeight: 'bold' }}
              />
            </Col>
          </Row>
        </Space>
      </Card>

      {/* 任务详细信息 */}
      <Card title="详细信息">
        <Descriptions bordered column={{ xs: 1, sm: 1, md: 2 }}>
          <Descriptions.Item label="任务ID">#{taskDetail.task_id}</Descriptions.Item>
          <Descriptions.Item label="用户任务ID">#{taskDetail.id}</Descriptions.Item>
          <Descriptions.Item label="开始时间">
            {taskDetail.started_at ? dayjs(taskDetail.started_at).format('YYYY-MM-DD HH:mm:ss') : '未开始'}
          </Descriptions.Item>
          {taskDetail.expires_at && (
            <Descriptions.Item label="过期时间">
              <Space>
                <span>{dayjs(taskDetail.expires_at).format('YYYY-MM-DD HH:mm:ss')}</span>
                <Tag color={isExpiringSoon() ? 'warning' : 'default'}>{getRemainingTime()}</Tag>
              </Space>
            </Descriptions.Item>
          )}
          {taskDetail.completed_at && (
            <Descriptions.Item label="完成时间">
              {dayjs(taskDetail.completed_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
          )}
          {taskDetail.claimed_at && (
            <Descriptions.Item label="领取时间">
              {dayjs(taskDetail.claimed_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      {/* 任务时间线 */}
      <Card title="任务进展">
        <Timeline
          items={[
            {
              color: 'blue',
              children: (
                <div>
                  <strong>任务开始</strong>
                  <div style={{ color: '#999', fontSize: 12, marginTop: 4 }}>
                    {taskDetail.started_at
                      ? dayjs(taskDetail.started_at).format('YYYY-MM-DD HH:mm:ss')
                      : '待开始'}
                  </div>
                </div>
              )
            },
            taskDetail.is_completed && {
              color: 'green',
              dot: <CheckCircleOutlined />,
              children: (
                <div>
                  <strong>任务完成</strong>
                  <div style={{ color: '#999', fontSize: 12, marginTop: 4 }}>
                    {taskDetail.completed_at
                      ? dayjs(taskDetail.completed_at).format('YYYY-MM-DD HH:mm:ss')
                      : '刚刚完成'}
                  </div>
                </div>
              )
            },
            taskDetail.is_claimed && {
              color: 'purple',
              dot: <TrophyOutlined />,
              children: (
                <div>
                  <strong>奖励已领取</strong>
                  <div style={{ color: '#999', fontSize: 12, marginTop: 4 }}>
                    {taskDetail.claimed_at
                      ? dayjs(taskDetail.claimed_at).format('YYYY-MM-DD HH:mm:ss')
                      : '已领取'}
                  </div>
                  <div style={{ color: '#722ed1', fontWeight: 'bold', marginTop: 4 }}>
                    获得 {totalReward} 积分
                  </div>
                </div>
              )
            },
            taskDetail.status === UserTaskStatus.EXPIRED && {
              color: 'red',
              dot: <CloseCircleOutlined />,
              children: (
                <div>
                  <strong>任务已过期</strong>
                  <div style={{ color: '#999', fontSize: 12, marginTop: 4 }}>
                    {taskDetail.expires_at
                      ? dayjs(taskDetail.expires_at).format('YYYY-MM-DD HH:mm:ss')
                      : '已过期'}
                  </div>
                </div>
              )
            }
          ].filter(Boolean)}
        />
      </Card>

      {/* 操作按钮 */}
      <Card>
        <Space style={{ width: '100%', justifyContent: 'center' }}>
          {taskDetail.is_completed && !taskDetail.is_claimed && (
            <Button
              type="primary"
              size="large"
              icon={<TrophyOutlined />}
              onClick={handleClaimReward}
              loading={claiming}
            >
              领取奖励 ({totalReward} 积分)
            </Button>
          )}
          {taskDetail.is_claimed && (
            <Alert
              message="奖励已领取"
              description={`您已获得 ${totalReward} 积分奖励`}
              type="success"
              showIcon
            />
          )}
          {taskDetail.status === UserTaskStatus.EXPIRED && (
            <Alert message="任务已过期" description="该任务已超过有效期" type="warning" showIcon />
          )}
          {taskDetail.status === UserTaskStatus.IN_PROGRESS && !taskDetail.is_completed && (
            <Alert
              message="任务进行中"
              description={`当前进度: ${taskDetail.current_value}/${taskDetail.target_value}`}
              type="info"
              showIcon
            />
          )}
          {onClose && (
            <Button size="large" onClick={onClose}>
              返回列表
            </Button>
          )}
        </Space>
      </Card>
    </Space>
  )
}

export default TaskDetail
