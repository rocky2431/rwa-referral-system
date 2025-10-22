import React, { useState, useEffect } from 'react'
import { Modal, Table, Tag, Avatar, Space, Button, Input, message } from 'antd'
import {
  TeamOutlined,
  UserOutlined,
  TrophyOutlined,
  SearchOutlined,
  LockOutlined,
  UnlockOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { TeamResponse } from '@/services/api'
import { teamsApi } from '@/services/api'

interface JoinTeamModalProps {
  visible: boolean
  userId: number
  onClose: () => void
  onSuccess?: () => void
}

/**
 * 加入战队弹窗
 */
export const JoinTeamModal: React.FC<JoinTeamModalProps> = ({
  visible,
  userId,
  onClose,
  onSuccess
}) => {
  const [loading, setLoading] = useState(false)
  const [joining, setJoining] = useState(false)
  const [teams, setTeams] = useState<TeamResponse[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [searchText, setSearchText] = useState('')

  // 加载战队列表
  const loadTeams = async () => {
    setLoading(true)
    try {
      const response = await teamsApi.getList(page, pageSize, true) // 只显示公开战队
      setTeams(response.data)
      setTotal(response.total)
    } catch (error) {
      console.error('加载战队列表失败:', error)
      message.error('加载战队列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (visible) {
      loadTeams()
    }
  }, [visible, page])

  // 加入战队
  const handleJoinTeam = async (teamId: number, requireApproval: boolean) => {
    setJoining(true)
    try {
      await teamsApi.join(teamId, userId)

      if (requireApproval) {
        message.success('已提交申请，等待队长审批')
      } else {
        message.success('成功加入战队！')
      }

      onSuccess?.()
      onClose()
    } catch (error: any) {
      console.error('加入战队失败:', error)
      message.error(error.message || '加入战队失败')
    } finally {
      setJoining(false)
    }
  }

  // 过滤战队列表
  const filteredTeams = teams.filter(team =>
    team.name.toLowerCase().includes(searchText.toLowerCase()) ||
    team.description?.toLowerCase().includes(searchText.toLowerCase())
  )

  // 表格列定义
  const columns: ColumnsType<TeamResponse> = [
    {
      title: '战队',
      key: 'team',
      width: 250,
      render: (_, record) => (
        <Space>
          <Avatar
            size={40}
            src={record.logo_url}
            icon={<TeamOutlined />}
            style={{ backgroundColor: '#1890ff' }}
          />
          <div>
            <div style={{ fontWeight: 'bold' }}>{record.name}</div>
            <div style={{ fontSize: 12, color: '#999' }}>
              {record.description?.slice(0, 30) || '暂无描述'}
              {record.description && record.description.length > 30 ? '...' : ''}
            </div>
          </div>
        </Space>
      )
    },
    {
      title: '积分',
      dataIndex: 'total_points',
      key: 'total_points',
      width: 100,
      align: 'center',
      sorter: (a, b) => a.total_points - b.total_points,
      render: (points: number) => (
        <span style={{ color: '#52c41a', fontWeight: 'bold' }}>
          <TrophyOutlined style={{ marginRight: 4 }} />
          {points.toLocaleString()}
        </span>
      )
    },
    {
      title: '成员',
      key: 'members',
      width: 120,
      align: 'center',
      render: (_, record) => (
        <div>
          <div>
            <UserOutlined style={{ marginRight: 4 }} />
            {record.member_count} / {record.max_members}
          </div>
          <div style={{ fontSize: 12, color: '#999' }}>
            活跃: {record.active_member_count}
          </div>
        </div>
      )
    },
    {
      title: '等级',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      align: 'center',
      sorter: (a, b) => a.level - b.level,
      render: (level: number) => (
        <Tag color="gold">Lv.{level}</Tag>
      )
    },
    {
      title: '审批',
      dataIndex: 'require_approval',
      key: 'require_approval',
      width: 80,
      align: 'center',
      render: (requireApproval: boolean) =>
        requireApproval ? (
          <Tag icon={<LockOutlined />} color="orange">
            需审批
          </Tag>
        ) : (
          <Tag icon={<UnlockOutlined />} color="green">
            自由加入
          </Tag>
        )
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      align: 'center',
      render: (_, record) => {
        const isFull = record.member_count >= record.max_members
        return (
          <Button
            type="primary"
            size="small"
            disabled={isFull || joining}
            loading={joining}
            onClick={() => handleJoinTeam(record.id, record.require_approval)}
          >
            {isFull ? '已满' : '加入'}
          </Button>
        )
      }
    }
  ]

  return (
    <Modal
      title={
        <Space>
          <TeamOutlined />
          <span>加入战队</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={900}
      bodyStyle={{ padding: '16px 24px' }}
    >
      {/* 搜索框 */}
      <div style={{ marginBottom: 16 }}>
        <Input
          placeholder="搜索战队名称或描述..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          allowClear
        />
      </div>

      {/* 战队列表 */}
      <Table
        columns={columns}
        dataSource={filteredTeams}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize: pageSize,
          total: total,
          onChange: (newPage) => setPage(newPage),
          showTotal: (total) => `共 ${total} 个战队`,
          showSizeChanger: false
        }}
        scroll={{ y: 400 }}
      />
    </Modal>
  )
}

export default JoinTeamModal
