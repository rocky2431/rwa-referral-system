import React, { useState, useEffect } from 'react'
import { Table, Card, Tag, Select, Space, Button, Tooltip } from 'antd'
import {
  SyncOutlined,
  PlusOutlined,
  MinusOutlined,
  UserAddOutlined,
  CheckCircleOutlined,
  QuestionCircleOutlined,
  TeamOutlined,
  GiftOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { PointTransactionResponse } from '@/services/api'
import { pointsApi } from '@/services/api'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { Option } = Select

interface PointsHistoryProps {
  userId: number
}

// 交易类型配置
const TRANSACTION_TYPES: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  referral_l1: { label: '一级推荐', icon: <UserAddOutlined />, color: 'blue' },
  referral_l2: { label: '二级推荐', icon: <UserAddOutlined />, color: 'cyan' },
  task_daily: { label: '每日任务', icon: <CheckCircleOutlined />, color: 'green' },
  task_weekly: { label: '每周任务', icon: <CheckCircleOutlined />, color: 'lime' },
  task_once: { label: '一次性任务', icon: <CheckCircleOutlined />, color: 'orange' },
  quiz_correct: { label: '答题正确', icon: <QuestionCircleOutlined />, color: 'purple' },
  team_reward: { label: '战队奖励', icon: <TeamOutlined />, color: 'magenta' },
  purchase: { label: '购买奖励', icon: <GiftOutlined />, color: 'gold' },
  admin_grant: { label: '管理员发放', icon: <GiftOutlined />, color: 'volcano' },
  exchange_token: { label: '兑换代币', icon: <MinusOutlined />, color: 'red' },
  spend_item: { label: '消费物品', icon: <MinusOutlined />, color: 'red' }
}

export const PointsHistory: React.FC<PointsHistoryProps> = ({ userId }) => {
  const [loading, setLoading] = useState(false)
  const [transactions, setTransactions] = useState<PointTransactionResponse[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [transactionType, setTransactionType] = useState<string | undefined>(undefined)

  // 加载积分流水数据
  const loadTransactions = async () => {
    setLoading(true)
    try {
      const response = await pointsApi.getTransactions(userId, page, pageSize, transactionType)
      setTransactions(response.data)
      setTotal(response.total)
    } catch (error) {
      console.error('加载积分流水失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTransactions()
  }, [userId, page, pageSize, transactionType])

  // 表格列定义
  const columns: ColumnsType<PointTransactionResponse> = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => (
        <Tooltip title={dayjs(time).format('YYYY-MM-DD HH:mm:ss')}>
          <span>{dayjs(time).fromNow()}</span>
        </Tooltip>
      )
    },
    {
      title: '交易类型',
      dataIndex: 'transaction_type',
      key: 'transaction_type',
      width: 140,
      render: (type: string) => {
        const config = TRANSACTION_TYPES[type] || {
          label: type,
          icon: <GiftOutlined />,
          color: 'default'
        }
        return (
          <Tag icon={config.icon} color={config.color}>
            {config.label}
          </Tag>
        )
      }
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      align: 'right',
      render: (amount: number) => {
        const isPositive = amount > 0
        return (
          <span
            style={{
              color: isPositive ? '#52c41a' : '#ff4d4f',
              fontWeight: 'bold',
              fontSize: '16px'
            }}
          >
            {isPositive ? <PlusOutlined style={{ marginRight: 4 }} /> : <MinusOutlined style={{ marginRight: 4 }} />}
            {Math.abs(amount)}
          </span>
        )
      }
    },
    {
      title: '余额',
      dataIndex: 'balance_after',
      key: 'balance_after',
      width: 100,
      align: 'right',
      render: (balance: number) => (
        <span style={{ color: '#666' }}>{balance.toLocaleString()}</span>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (desc: string) => desc || '-'
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => {
        const statusConfig: Record<string, { label: string; color: string }> = {
          completed: { label: '已完成', color: 'success' },
          pending: { label: '待处理', color: 'processing' },
          cancelled: { label: '已取消', color: 'error' }
        }
        const config = statusConfig[status] || { label: status, color: 'default' }
        return <Tag color={config.color}>{config.label}</Tag>
      }
    }
  ]

  return (
    <Card
      title="积分流水"
      extra={
        <Space>
          <Select
            placeholder="筛选类型"
            style={{ width: 140 }}
            allowClear
            value={transactionType}
            onChange={(value) => {
              setTransactionType(value)
              setPage(1) // 重置页码
            }}
          >
            {Object.entries(TRANSACTION_TYPES).map(([key, config]) => (
              <Option key={key} value={key}>
                {config.icon} {config.label}
              </Option>
            ))}
          </Select>
          <Button icon={<SyncOutlined />} onClick={loadTransactions}>
            刷新
          </Button>
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={transactions}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`,
          onChange: (newPage, newPageSize) => {
            setPage(newPage)
            setPageSize(newPageSize || 20)
          }
        }}
        scroll={{ x: 800 }}
      />
    </Card>
  )
}

export default PointsHistory
