import React from 'react'
import { Card, Progress, Tag, Button, Space, Tooltip } from 'antd'
import {
  CheckCircleOutlined,
  GiftOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  FireOutlined,
  CalendarOutlined
} from '@ant-design/icons'
import type { UserTaskDetailResponse } from '@/services/api'
import { TaskType, UserTaskStatus } from '@/services/api'
import dayjs from 'dayjs'

interface TaskCardProps {
  task: UserTaskDetailResponse
  onClaim?: (taskId: number) => void
  onAssign?: (taskId: number) => void
  claiming?: boolean
}

// 任务类型配置
const TASK_TYPE_CONFIG: Record<TaskType, { label: string; icon: React.ReactNode; color: string }> = {
  [TaskType.DAILY]: { label: '每日任务', icon: <CalendarOutlined />, color: 'blue' },
  [TaskType.WEEKLY]: { label: '每周任务', icon: <CalendarOutlined />, color: 'cyan' },
  [TaskType.ONCE]: { label: '一次性', icon: <CheckCircleOutlined />, color: 'green' },
  [TaskType.TEAM]: { label: '战队任务', icon: <TrophyOutlined />, color: 'volcano' }
}

// 任务状态配置
const STATUS_CONFIG: Record<UserTaskStatus, { label: string; color: string }> = {
  [UserTaskStatus.AVAILABLE]: { label: '可领取', color: 'default' },
  [UserTaskStatus.IN_PROGRESS]: { label: '进行中', color: 'processing' },
  [UserTaskStatus.COMPLETED]: { label: '待领奖', color: 'warning' },
  [UserTaskStatus.REWARDED]: { label: '已领奖', color: 'success' },
  [UserTaskStatus.EXPIRED]: { label: '已过期', color: 'error' },
  [UserTaskStatus.CLAIMED]: { label: '已领奖', color: 'success' }  // 兼容旧状态
}

/**
 * 任务卡片组件
 */
export const TaskCard: React.FC<TaskCardProps> = ({ task, onClaim, onAssign, claiming }) => {
  const taskTypeConfig = task.task_type ? TASK_TYPE_CONFIG[task.task_type] : TASK_TYPE_CONFIG[TaskType.ONCE]
  const statusConfig = STATUS_CONFIG[task.status]

  // 判断任务是否即将过期
  const isExpiringSoon = () => {
    if (!task.expires_at) return false
    const diffHours = dayjs(task.expires_at).diff(dayjs(), 'hours')
    return diffHours > 0 && diffHours <= 24
  }

  return (
    <Card
      hoverable
      className="task-card"
      style={{ marginBottom: 16 }}
      extra={
        <Space>
          {task.task_type && (
            <Tag icon={taskTypeConfig.icon} color={taskTypeConfig.color}>
              {taskTypeConfig.label}
            </Tag>
          )}
          <Tag color={statusConfig.color}>{statusConfig.label}</Tag>
          {isExpiringSoon() && (
            <Tag color="warning" icon={<ClockCircleOutlined />}>
              即将过期
            </Tag>
          )}
        </Space>
      }
    >
      {/* 任务头部 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <h3 style={{ margin: 0, marginBottom: 8 }}>
            {task.task_title || `任务 #${task.task_id}`}
          </h3>
          {task.completion_count > 0 && (
            <Tag icon={<FireOutlined />} color="orange">
              已完成 {task.completion_count} 次
            </Tag>
          )}
        </div>
        {task.task_description && (
          <p style={{ margin: 0, color: '#666', fontSize: 14 }}>
            {task.task_description}
          </p>
        )}
      </div>

      {/* 进度条 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
          <span style={{ fontSize: 14, color: '#666' }}>任务进度</span>
          <span style={{ fontSize: 14, fontWeight: 'bold' }}>
            {task.current_value} / {task.target_value}
          </span>
        </div>
        <Progress
          percent={Math.round(task.progress_percentage)}
          status={task.is_completed ? 'success' : 'active'}
          strokeColor={task.is_completed ? '#52c41a' : '#1890ff'}
        />
      </div>

      {/* 奖励信息 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space size={24}>
          <div>
            <GiftOutlined style={{ marginRight: 8, color: '#52c41a' }} />
            <span style={{ color: '#666' }}>积分奖励:</span>
            <span style={{ fontWeight: 'bold', marginLeft: 8, color: '#52c41a' }}>
              {task.reward_points}
            </span>
            {task.bonus_points > 0 && (
              <span style={{ color: '#faad14', marginLeft: 4 }}>
                +{task.bonus_points}
              </span>
            )}
          </div>

          {task.expires_at && (
            <Tooltip title={dayjs(task.expires_at).format('YYYY-MM-DD HH:mm')}>
              <div>
                <ClockCircleOutlined style={{ marginRight: 8, color: '#999' }} />
                <span style={{ color: '#666' }}>过期时间:</span>
                <span style={{ marginLeft: 8 }}>{dayjs(task.expires_at).fromNow()}</span>
              </div>
            </Tooltip>
          )}
        </Space>

        {/* 操作按钮 */}
        <Space>
          {task.status === UserTaskStatus.COMPLETED && (
            <Button
              type="primary"
              icon={<TrophyOutlined />}
              onClick={() => onClaim?.(task.id)}
              loading={claiming}
            >
              领取奖励
            </Button>
          )}
          {task.status === UserTaskStatus.REWARDED && (
            <Button disabled icon={<CheckCircleOutlined />}>
              已领奖
            </Button>
          )}
          {task.status === UserTaskStatus.AVAILABLE && (
            <Button type="dashed" disabled>
              未开始
            </Button>
          )}
        </Space>
      </div>
    </Card>
  )
}

export default TaskCard
