import React, { useState, useEffect } from 'react'
import { Card, Table, Tag, Progress, Space, Button, Select, Tooltip } from 'antd'
import {
  SyncOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  GiftOutlined,
  FireOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { TeamTaskResponse } from '@/services/api'
import { teamsApi, TeamTaskStatus } from '@/services/api'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { Option } = Select

interface TeamTaskListProps {
  teamId: number
}

// 任务状态配置
const STATUS_CONFIG: Record<TeamTaskStatus, { label: string; color: string }> = {
  [TeamTaskStatus.NOT_STARTED]: { label: '未开始', color: 'default' },
  [TeamTaskStatus.IN_PROGRESS]: { label: '进行中', color: 'processing' },
  [TeamTaskStatus.COMPLETED]: { label: '已完成', color: 'success' },
  [TeamTaskStatus.EXPIRED]: { label: '已过期', color: 'error' }
}

// 任务类型图标映射
const TASK_TYPE_ICONS: Record<string, React.ReactNode> = {
  daily: <ClockCircleOutlined />,
  weekly: <ClockCircleOutlined />,
  special: <FireOutlined />,
  default: <CheckCircleOutlined />
}

export const TeamTaskList: React.FC<TeamTaskListProps> = ({ teamId }) => {
  const [loading, setLoading] = useState(false)
  const [tasks, setTasks] = useState<TeamTaskResponse[]>([])
  const [total, setTotal] = useState(0)
  const [statusFilter, setStatusFilter] = useState<TeamTaskStatus | undefined>(undefined)

  // 加载任务列表
  const loadTasks = async () => {
    setLoading(true)
    try {
      const response = await teamsApi.getTasks(teamId, statusFilter)
      setTasks(response.data)
      setTotal(response.total)
    } catch (error) {
      console.error('加载任务列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTasks()
  }, [teamId, statusFilter])

  // 判断任务是否即将过期
  const isExpiringSoon = (endTime: string) => {
    const diffHours = dayjs(endTime).diff(dayjs(), 'hours')
    return diffHours > 0 && diffHours <= 24
  }

  // 表格列定义
  const columns: ColumnsType<TeamTaskResponse> = [
    {
      title: '任务',
      key: 'task',
      width: 300,
      render: (_, record) => (
        <div>
          <Space>
            {TASK_TYPE_ICONS[record.task_type] || TASK_TYPE_ICONS.default}
            <span style={{ fontWeight: 'bold' }}>{record.title}</span>
            {isExpiringSoon(record.end_time) && (
              <Tag color="warning" icon={<ClockCircleOutlined />}>
                即将过期
              </Tag>
            )}
          </Space>
          {record.description && (
            <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
              {record.description}
            </div>
          )}
        </div>
      )
    },
    {
      title: '进度',
      key: 'progress',
      width: 200,
      render: (_, record) => (
        <div>
          <Progress
            percent={Math.round(record.progress_percentage)}
            size="small"
            status={record.is_completed ? 'success' : 'active'}
            strokeColor={record.is_completed ? '#52c41a' : '#1890ff'}
          />
          <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
            {record.current_value} / {record.target_value}
          </div>
        </div>
      )
    },
    {
      title: '奖励',
      key: 'reward',
      width: 120,
      align: 'center',
      render: (_, record) => (
        <div>
          <div style={{ color: '#52c41a', fontWeight: 'bold' }}>
            <GiftOutlined style={{ marginRight: 4 }} />
            {record.reward_points}
          </div>
          {record.bonus_points > 0 && (
            <div style={{ fontSize: 12, color: '#faad14' }}>
              +{record.bonus_points} 奖励
            </div>
          )}
        </div>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: TeamTaskStatus) => {
        const config = STATUS_CONFIG[status]
        return <Tag color={config.color}>{config.label}</Tag>
      }
    },
    {
      title: '时间',
      key: 'time',
      width: 180,
      render: (_, record) => (
        <div>
          <Tooltip title={`开始: ${dayjs(record.start_time).format('YYYY-MM-DD HH:mm')}`}>
            <div style={{ fontSize: 12 }}>
              开始: {dayjs(record.start_time).fromNow()}
            </div>
          </Tooltip>
          <Tooltip title={`结束: ${dayjs(record.end_time).format('YYYY-MM-DD HH:mm')}`}>
            <div
              style={{
                fontSize: 12,
                color: isExpiringSoon(record.end_time) ? '#ff4d4f' : '#999'
              }}
            >
              结束: {dayjs(record.end_time).fromNow()}
            </div>
          </Tooltip>
          {record.completed_at && (
            <Tooltip title={dayjs(record.completed_at).format('YYYY-MM-DD HH:mm')}>
              <div style={{ fontSize: 12, color: '#52c41a' }}>
                ✓ {dayjs(record.completed_at).fromNow()}完成
              </div>
            </Tooltip>
          )}
        </div>
      )
    }
  ]

  return (
    <Card
      title="战队任务"
      extra={
        <Space>
          <Select
            placeholder="筛选状态"
            style={{ width: 120 }}
            allowClear
            value={statusFilter}
            onChange={(value) => setStatusFilter(value)}
          >
            {Object.entries(STATUS_CONFIG).map(([key, config]) => (
              <Option key={key} value={key}>
                {config.label}
              </Option>
            ))}
          </Select>
          <Button icon={<SyncOutlined />} onClick={loadTasks} loading={loading}>
            刷新
          </Button>
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={tasks}
        rowKey="id"
        loading={loading}
        pagination={{
          total: total,
          showTotal: (total) => `共 ${total} 个任务`,
          showSizeChanger: false,
          pageSize: 20
        }}
        scroll={{ x: 1000 }}
      />
    </Card>
  )
}

export default TeamTaskList
