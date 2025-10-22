import React, { useState, useEffect } from 'react'
import { Table, Card, Tag, Avatar, Space, Button, Select } from 'antd'
import {
  SyncOutlined,
  CrownOutlined,
  SafetyOutlined,
  UserOutlined,
  TrophyOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { TeamMemberDetailResponse } from '@/services/api'
import { teamsApi, TeamMemberStatus, TeamMemberRole } from '@/services/api'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { Option } = Select

interface TeamMemberListProps {
  teamId: number
}

// 成员角色配置
const ROLE_CONFIG: Record<TeamMemberRole, { label: string; icon: React.ReactNode; color: string }> = {
  [TeamMemberRole.CAPTAIN]: { label: '队长', icon: <CrownOutlined />, color: 'gold' },
  [TeamMemberRole.ADMIN]: { label: '管理员', icon: <SafetyOutlined />, color: 'blue' },
  [TeamMemberRole.MEMBER]: { label: '成员', icon: <UserOutlined />, color: 'default' }
}

// 成员状态配置
const STATUS_CONFIG: Record<TeamMemberStatus, { label: string; color: string }> = {
  [TeamMemberStatus.ACTIVE]: { label: '活跃', color: 'success' },
  [TeamMemberStatus.PENDING]: { label: '待审批', color: 'processing' },
  [TeamMemberStatus.REJECTED]: { label: '已拒绝', color: 'error' },
  [TeamMemberStatus.LEFT]: { label: '已离开', color: 'default' }
}

export const TeamMemberList: React.FC<TeamMemberListProps> = ({ teamId }) => {
  const [loading, setLoading] = useState(false)
  const [members, setMembers] = useState<TeamMemberDetailResponse[]>([])
  const [total, setTotal] = useState(0)
  const [statusFilter, setStatusFilter] = useState<TeamMemberStatus | undefined>(undefined)

  // 加载成员列表
  const loadMembers = async () => {
    setLoading(true)
    try {
      const response = await teamsApi.getMembers(teamId, statusFilter)
      setMembers(response.data)
      setTotal(response.total)
    } catch (error) {
      console.error('加载成员列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadMembers()
  }, [teamId, statusFilter])

  // 表格列定义
  const columns: ColumnsType<TeamMemberDetailResponse> = [
    {
      title: '成员',
      key: 'member',
      width: 250,
      render: (_, record) => (
        <Space>
          <Avatar
            size={40}
            src={record.avatar_url}
            icon={<UserOutlined />}
            style={{ backgroundColor: '#1890ff' }}
          />
          <div>
            <div style={{ fontWeight: 'bold' }}>
              {record.username || `用户 ${record.user_id}`}
            </div>
            <div style={{ fontSize: 12, color: '#999', fontFamily: 'monospace' }}>
              {record.wallet_address
                ? `${record.wallet_address.slice(0, 6)}...${record.wallet_address.slice(-4)}`
                : '-'}
            </div>
          </div>
        </Space>
      )
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      width: 100,
      render: (role: TeamMemberRole) => {
        const config = ROLE_CONFIG[role]
        return (
          <Tag icon={config.icon} color={config.color}>
            {config.label}
          </Tag>
        )
      }
    },
    {
      title: '贡献积分',
      dataIndex: 'contribution_points',
      key: 'contribution_points',
      width: 120,
      align: 'right',
      sorter: (a, b) => a.contribution_points - b.contribution_points,
      render: (points: number) => (
        <span style={{ color: '#52c41a', fontWeight: 'bold' }}>
          <TrophyOutlined style={{ marginRight: 4 }} />
          {points.toLocaleString()}
        </span>
      )
    },
    {
      title: '完成任务',
      dataIndex: 'tasks_completed',
      key: 'tasks_completed',
      width: 100,
      align: 'center',
      sorter: (a, b) => a.tasks_completed - b.tasks_completed,
      render: (tasks: number) => (
        <span>
          <CheckCircleOutlined style={{ marginRight: 4, color: '#52c41a' }} />
          {tasks}
        </span>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: TeamMemberStatus) => {
        const config = STATUS_CONFIG[status]
        return <Tag color={config.color}>{config.label}</Tag>
      }
    },
    {
      title: '加入时间',
      dataIndex: 'joined_at',
      key: 'joined_at',
      width: 150,
      sorter: (a, b) => {
        if (!a.joined_at || !b.joined_at) return 0
        return new Date(a.joined_at).getTime() - new Date(b.joined_at).getTime()
      },
      render: (joinedAt: string) => {
        if (!joinedAt) return '-'
        return (
          <div>
            <div>{dayjs(joinedAt).format('YYYY-MM-DD')}</div>
            <div style={{ fontSize: 12, color: '#999' }}>
              {dayjs(joinedAt).fromNow()}
            </div>
          </div>
        )
      }
    }
  ]

  return (
    <Card
      title="战队成员"
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
          <Button icon={<SyncOutlined />} onClick={loadMembers} loading={loading}>
            刷新
          </Button>
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={members}
        rowKey="id"
        loading={loading}
        pagination={{
          total: total,
          showTotal: (total) => `共 ${total} 名成员`,
          showSizeChanger: false,
          pageSize: 100
        }}
        scroll={{ x: 900 }}
      />
    </Card>
  )
}

export default TeamMemberList
