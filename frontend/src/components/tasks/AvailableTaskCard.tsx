import React from 'react'
import { Card, Tag, Button, Space, Tooltip, Descriptions } from 'antd'
import {
  GiftOutlined,
  TrophyOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  FireOutlined,
  TeamOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'
import type { TaskResponse } from '@/services/api'
import { TaskType } from '@/services/api'
import dayjs from 'dayjs'

interface AvailableTaskCardProps {
  task: TaskResponse
  onClaim?: (taskId: number) => void
  claiming?: boolean
  alreadyClaimed?: boolean
  disabled?: boolean  // ✅ 新增:是否禁用领取按钮
  disabledReason?: string  // ✅ 新增:禁用原因提示
}

// 任务类型配置
const TASK_TYPE_CONFIG: Record<TaskType, { label: string; icon: React.ReactNode; color: string }> = {
  [TaskType.DAILY]: { label: '每日任务', icon: <CalendarOutlined />, color: 'blue' },
  [TaskType.WEEKLY]: { label: '每周任务', icon: <CalendarOutlined />, color: 'cyan' },
  [TaskType.ONCE]: { label: '一次性', icon: <CheckCircleOutlined />, color: 'green' },
  [TaskType.TEAM]: { label: '战队任务', icon: <TrophyOutlined />, color: 'volcano' }
}

/**
 * 可领取任务卡片组件
 */
export const AvailableTaskCard: React.FC<AvailableTaskCardProps> = ({
  task,
  onClaim,
  claiming,
  alreadyClaimed,
  disabled = false,
  disabledReason
}) => {
  const taskTypeConfig = task.task_type ? TASK_TYPE_CONFIG[task.task_type] : TASK_TYPE_CONFIG[TaskType.ONCE]

  // 判断任务是否即将过期
  const isExpiringSoon = () => {
    if (!task.end_time) return false
    const diffHours = dayjs(task.end_time).diff(dayjs(), 'hours')
    return diffHours > 0 && diffHours <= 24
  }

  // 判断是否可重复任务
  const isRepeatable = !task.max_completions_per_user

  return (
    <Card
      hoverable
      className="available-task-card"
      style={{ marginBottom: 16 }}
      extra={
        <Space>
          <Tag icon={taskTypeConfig.icon} color={taskTypeConfig.color}>
            {taskTypeConfig.label}
          </Tag>
          {isRepeatable && (
            <Tag color="purple" icon={<FireOutlined />}>
              可重复
            </Tag>
          )}
          {isExpiringSoon() && (
            <Tag color="warning" icon={<ClockCircleOutlined />}>
              即将过期
            </Tag>
          )}
          {alreadyClaimed && (
            <Tag color="success" icon={<CheckCircleOutlined />}>
              已领取
            </Tag>
          )}
        </Space>
      }
    >
      {/* 任务头部 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <h3 style={{ margin: 0, marginBottom: 8 }}>
            {task.title}
          </h3>
        </div>
        {task.description && (
          <p style={{ margin: 0, color: '#666', fontSize: 14 }}>
            {task.description}
          </p>
        )}
      </div>

      {/* 任务详情 */}
      <Descriptions size="small" column={2} style={{ marginBottom: 16 }}>
        <Descriptions.Item label="目标">
          完成 {task.target_value} 次 {task.target_type || '任务'}
        </Descriptions.Item>
        <Descriptions.Item label="等级要求">
          Level {task.min_level_required}+
        </Descriptions.Item>
        {task.max_completions_per_user && (
          <Descriptions.Item label="完成限制">
            最多 {task.max_completions_per_user} 次
          </Descriptions.Item>
        )}
        {task.end_time && (
          <Descriptions.Item label="截止时间">
            <Tooltip title={dayjs(task.end_time).format('YYYY-MM-DD HH:mm')}>
              {dayjs(task.end_time).fromNow()}
            </Tooltip>
          </Descriptions.Item>
        )}
      </Descriptions>

      {/* 奖励和操作 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space size={24}>
          <div>
            <GiftOutlined style={{ marginRight: 8, color: '#52c41a' }} />
            <span style={{ color: '#666' }}>积分:</span>
            <span style={{ fontWeight: 'bold', marginLeft: 8, color: '#52c41a' }}>
              {task.reward_points}
            </span>
          </div>

          {task.reward_experience > 0 && (
            <div>
              <TrophyOutlined style={{ marginRight: 8, color: '#fa8c16' }} />
              <span style={{ color: '#666' }}>经验:</span>
              <span style={{ fontWeight: 'bold', marginLeft: 8, color: '#fa8c16' }}>
                {task.reward_experience}
              </span>
            </div>
          )}

          {task.bonus_multiplier > 1 && (
            <Tooltip title={`奖励倍数: ${task.bonus_multiplier}x`}>
              <Tag color="gold" icon={<FireOutlined />}>
                {task.bonus_multiplier}x 奖励
              </Tag>
            </Tooltip>
          )}
        </Space>

        {/* 领取按钮 */}
        <Tooltip title={disabled ? disabledReason : undefined}>
          <Button
            type="primary"
            icon={alreadyClaimed ? <CheckCircleOutlined /> : <TeamOutlined />}
            onClick={() => onClaim?.(task.id)}
            loading={claiming}
            disabled={alreadyClaimed || disabled}
          >
            {alreadyClaimed ? '已领取' : disabled ? '不可领取' : '领取任务'}
          </Button>
        </Tooltip>
      </div>
    </Card>
  )
}

export default AvailableTaskCard
