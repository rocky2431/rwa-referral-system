import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Progress } from 'antd'
import {
  CheckCircleOutlined,
  SyncOutlined,
  TrophyOutlined,
  GiftOutlined,
  ClockCircleOutlined
} from '@ant-design/icons'
import type { UserTaskSummary } from '@/services/api'
import { tasksApi } from '@/services/api'

interface TaskProgressProps {
  userId: number
  loading?: boolean
}

/**
 * 任务进度统计组件
 */
export const TaskProgress: React.FC<TaskProgressProps> = ({ userId, loading: externalLoading }) => {
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState<UserTaskSummary | null>(null)

  // 加载任务汇总
  const loadSummary = async () => {
    setLoading(true)
    try {
      const data = await tasksApi.getUserSummary(userId)
      setSummary(data)
    } catch (error) {
      console.error('加载任务汇总失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSummary()
  }, [userId])

  // 计算完成率
  const completionRate = summary
    ? Math.round(((summary.completed_tasks + summary.claimed_tasks) / Math.max(summary.total_tasks, 1)) * 100)
    : 0

  return (
    <Card
      title="任务统计"
      loading={loading || externalLoading}
      style={{ marginBottom: 24 }}
    >
      {summary && (
        <>
          {/* 完成率 */}
          <div style={{ marginBottom: 24, textAlign: 'center' }}>
            <Progress
              type="circle"
              percent={completionRate}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068'
              }}
              format={(percent) => (
                <div>
                  <div style={{ fontSize: 24, fontWeight: 'bold' }}>{percent}%</div>
                  <div style={{ fontSize: 12, color: '#999' }}>完成率</div>
                </div>
              )}
            />
          </div>

          {/* 统计数据 */}
          <Row gutter={[16, 16]}>
            <Col xs={12} sm={8}>
              <Statistic
                title="总任务数"
                value={summary.total_tasks}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col xs={12} sm={8}>
              <Statistic
                title="进行中"
                value={summary.in_progress_tasks}
                prefix={<SyncOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Col>
            <Col xs={12} sm={8}>
              <Statistic
                title="已完成"
                value={summary.completed_tasks}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col xs={12} sm={8}>
              <Statistic
                title="已领取"
                value={summary.claimed_tasks}
                prefix={<TrophyOutlined />}
                valueStyle={{ color: '#13c2c2' }}
              />
            </Col>
            <Col xs={12} sm={8}>
              <Statistic
                title="已过期"
                value={summary.expired_tasks}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Col>
            <Col xs={12} sm={8}>
              <Statistic
                title="总获得积分"
                value={summary.total_points_earned}
                prefix={<GiftOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Col>
          </Row>
        </>
      )}
    </Card>
  )
}

export default TaskProgress
