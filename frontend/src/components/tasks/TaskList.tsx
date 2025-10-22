import React, { useState, useEffect } from 'react'
import { Space, Select, Button, Empty, message } from 'antd'
import { SyncOutlined } from '@ant-design/icons'
import type { UserTaskDetailResponse } from '@/services/api'
import { tasksApi, TaskType, UserTaskStatus } from '@/services/api'
import { TaskCard } from './TaskCard'

const { Option } = Select

interface TaskListProps {
  userId: number
  onRefresh?: () => void
}

/**
 * 任务列表组件
 */
export const TaskList: React.FC<TaskListProps> = ({ userId, onRefresh }) => {
  const [loading, setLoading] = useState(false)
  const [tasks, setTasks] = useState<UserTaskDetailResponse[]>([])
  const [total, setTotal] = useState(0)
  const [statusFilter, setStatusFilter] = useState<UserTaskStatus | undefined>(undefined)
  const [typeFilter, setTypeFilter] = useState<TaskType | undefined>(undefined)
  const [claimingTaskId, setClaimingTaskId] = useState<number | null>(null)

  // 加载任务列表
  const loadTasks = async () => {
    setLoading(true)
    try {
      const response = await tasksApi.getUserTasks(userId, 1, 100, statusFilter, typeFilter)
      setTasks(response.data)
      setTotal(response.total)
    } catch (error) {
      console.error('加载任务列表失败:', error)
      message.error('加载任务列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTasks()
  }, [userId, statusFilter, typeFilter])

  // 领取任务奖励
  const handleClaimReward = async (userTaskId: number) => {
    setClaimingTaskId(userTaskId)
    try {
      await tasksApi.claimReward(userTaskId, userId)
      message.success('奖励领取成功！')
      loadTasks()
      onRefresh?.()
    } catch (error: any) {
      console.error('领取奖励失败:', error)
      message.error(error.message || '领取奖励失败')
    } finally {
      setClaimingTaskId(null)
    }
  }

  return (
    <div>
      {/* 筛选栏 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <Select
            placeholder="任务状态"
            style={{ width: 120 }}
            allowClear
            value={statusFilter}
            onChange={setStatusFilter}
          >
            <Option value={UserTaskStatus.AVAILABLE}>可领取</Option>
            <Option value={UserTaskStatus.IN_PROGRESS}>进行中</Option>
            <Option value={UserTaskStatus.COMPLETED}>已完成</Option>
            <Option value={UserTaskStatus.REWARDED}>已领奖</Option>
            <Option value={UserTaskStatus.EXPIRED}>已过期</Option>
          </Select>

          <Select
            placeholder="任务类型"
            style={{ width: 120 }}
            allowClear
            value={typeFilter}
            onChange={setTypeFilter}
          >
            <Option value={TaskType.DAILY}>每日</Option>
            <Option value={TaskType.WEEKLY}>每周</Option>
            <Option value={TaskType.ONCE}>一次性</Option>
            <Option value={TaskType.TEAM}>战队</Option>
          </Select>
        </Space>

        <Button icon={<SyncOutlined />} onClick={loadTasks} loading={loading}>
          刷新
        </Button>
      </div>

      {/* 任务列表 */}
      {loading && tasks.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <SyncOutlined spin style={{ fontSize: 24 }} />
          <div style={{ marginTop: 16, color: '#999' }}>加载中...</div>
        </div>
      ) : tasks.length === 0 ? (
        <Empty description="暂无任务" />
      ) : (
        tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            onClaim={handleClaimReward}
            claiming={claimingTaskId === task.id}
          />
        ))
      )}
    </div>
  )
}

export default TaskList
