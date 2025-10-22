import { useEffect, useState } from 'react'
import { Table, Card, Typography, Space, Tag, Avatar } from 'antd'
import { TrophyOutlined, CrownOutlined, FireOutlined } from '@ant-design/icons'
import { leaderboardApi, LeaderboardEntry } from '@/services/api'
import type { ColumnsType } from 'antd/es/table'

const { Title, Paragraph, Text } = Typography

/**
 * 排行榜页面
 */
function Leaderboard() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<LeaderboardEntry[]>([])
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
    total: 0
  })

  // 获取排行榜数据
  useEffect(() => {
    fetchLeaderboard()
  }, [pagination.current, pagination.pageSize])

  const fetchLeaderboard = async () => {
    setLoading(true)
    try {
      const result = await leaderboardApi.getList(pagination.current, pagination.pageSize)
      setData(result.data)
      setPagination({
        ...pagination,
        total: result.total
      })
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error)
    } finally {
      setLoading(false)
    }
  }

  // 分页变化处理
  const handleTableChange = (newPagination: any) => {
    setPagination({
      current: newPagination.current,
      pageSize: newPagination.pageSize,
      total: pagination.total
    })
  }

  // 获取排名图标
  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <CrownOutlined style={{ fontSize: 24, color: '#ffd700' }} />
      case 2:
        return <TrophyOutlined style={{ fontSize: 24, color: '#c0c0c0' }} />
      case 3:
        return <TrophyOutlined style={{ fontSize: 24, color: '#cd7f32' }} />
      default:
        return <Text style={{ fontSize: 18, fontWeight: 600 }}>{rank}</Text>
    }
  }

  // 获取排名标签
  const getRankTag = (rank: number) => {
    if (rank === 1) {
      return <Tag color="gold" icon={<FireOutlined />}>冠军</Tag>
    }
    if (rank <= 3) {
      return <Tag color="orange">前三</Tag>
    }
    if (rank <= 10) {
      return <Tag color="blue">前十</Tag>
    }
    return null
  }

  // 表格列定义
  const columns: ColumnsType<LeaderboardEntry> = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 100,
      align: 'center',
      render: (rank: number) => (
        <Space>
          {getRankIcon(rank)}
        </Space>
      )
    },
    {
      title: '地址',
      dataIndex: 'address',
      key: 'address',
      render: (address: string, record) => (
        <Space>
          <Avatar
            style={{
              background: `linear-gradient(135deg, ${getColorFromAddress(address)})`,
              border: record.rank <= 3 ? '2px solid #ffd700' : 'none'
            }}
          >
            {address.slice(2, 4).toUpperCase()}
          </Avatar>
          <Text
            copyable
            style={{
              fontFamily: 'monospace',
              fontSize: 14,
              color: record.rank === 1 ? '#ffd700' : '#fff'
            }}
          >
            {`${address.slice(0, 8)}...${address.slice(-6)}`}
          </Text>
          {getRankTag(record.rank)}
        </Space>
      )
    },
    {
      title: '总奖励积分',
      dataIndex: 'total_rewards',
      key: 'total_rewards',
      width: 200,
      align: 'right',
      sorter: (a, b) => parseFloat(a.total_rewards) - parseFloat(b.total_rewards),
      render: (rewards: string) => (
        <Text
          strong
          style={{
            fontSize: 16,
            color: '#4ecdc4'
          }}
        >
          {parseInt(rewards).toLocaleString()} 积分
        </Text>
      )
    },
    {
      title: '推荐人数',
      dataIndex: 'referred_count',
      key: 'referred_count',
      width: 150,
      align: 'right',
      sorter: (a, b) => a.referred_count - b.referred_count,
      render: (count: number) => (
        <Text
          strong
          style={{
            fontSize: 16,
            color: '#ffe66d'
          }}
        >
          {count}
        </Text>
      )
    }
  ]

  // 根据地址生成颜色
  const getColorFromAddress = (address: string): string => {
    const hash = parseInt(address.slice(2, 10), 16)
    const hue = hash % 360
    return `hsl(${hue}, 70%, 50%), hsl(${(hue + 60) % 360}, 70%, 60%)`
  }

  return (
    <div style={{ minHeight: 'calc(100vh - 64px - 120px)', padding: '48px 24px' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        {/* 页面标题 */}
        <div style={{ marginBottom: 32, textAlign: 'center' }}>
          <Space direction="vertical" size={8}>
            <TrophyOutlined style={{ fontSize: 48, color: '#ffd700' }} />
            <Title level={2} style={{ margin: 0 }}>
              推荐排行榜
            </Title>
            <Paragraph style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: 16, margin: 0 }}>
              查看顶级推荐者的实时排名
            </Paragraph>
          </Space>
        </div>

        {/* 排行榜表格 */}
        <Card
          style={{
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}
        >
          <Table
            columns={columns}
            dataSource={data}
            loading={loading}
            rowKey="rank"
            pagination={{
              ...pagination,
              showSizeChanger: true,
              showTotal: (total) => `总共 ${total} 位推荐者`,
              pageSizeOptions: ['10', '20', '50', '100']
            }}
            onChange={handleTableChange}
            rowClassName={(record) => {
              if (record.rank === 1) return 'rank-1'
              if (record.rank === 2) return 'rank-2'
              if (record.rank === 3) return 'rank-3'
              return ''
            }}
            style={{
              background: 'transparent'
            }}
          />
        </Card>

        {/* 说明 */}
        <div style={{ marginTop: 24, textAlign: 'center' }}>
          <Paragraph style={{ color: 'rgba(255, 255, 255, 0.4)', fontSize: 14 }}>
            排行榜每小时更新一次 • 数据基于链上真实记录
          </Paragraph>
        </div>
      </div>

      <style>
        {`
          .rank-1 {
            background: rgba(255, 215, 0, 0.05) !important;
          }
          .rank-2 {
            background: rgba(192, 192, 192, 0.05) !important;
          }
          .rank-3 {
            background: rgba(205, 127, 50, 0.05) !important;
          }
          .ant-table-thead > tr > th {
            background: rgba(255, 255, 255, 0.05) !important;
            color: rgba(255, 255, 255, 0.8) !important;
            font-weight: 600;
          }
          .ant-table-tbody > tr > td {
            border-color: rgba(255, 255, 255, 0.05) !important;
          }
          .ant-table-tbody > tr:hover > td {
            background: rgba(255, 107, 53, 0.05) !important;
          }
        `}
      </style>
    </div>
  )
}

export default Leaderboard
