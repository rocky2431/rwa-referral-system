import React, { useState, useEffect } from 'react'
import {
  Card,
  Descriptions,
  Tag,
  Alert,
  Spin,
  Space,
  Button,
  Statistic,
  Timeline,
  message
} from 'antd'
import {
  PlusOutlined,
  MinusOutlined,
  UserAddOutlined,
  CheckCircleOutlined,
  QuestionCircleOutlined,
  TeamOutlined,
  GiftOutlined,
  InfoCircleOutlined,
  WalletOutlined
} from '@ant-design/icons'
import type { PointTransactionResponse } from '@/services/api'
import { pointsApi } from '@/services/api'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

/**
 * PointsDetail 组件属性
 */
interface PointsDetailProps {
  /** 积分交易ID */
  transactionId: number
  /** 用户ID */
  userId: number
  /** 关闭回调 */
  onClose?: () => void
}

/**
 * 积分交易详情组件
 *
 * 显示单笔积分交易的详细信息，包括：
 * - 交易基本信息（类型、金额、状态、时间）
 * - 关联对象信息（任务/用户/战队/题目）
 * - 交易元数据（附加信息）
 * - 余额变化记录
 *
 * 设计原则：
 * - SRP：只负责交易详情展示
 * - DRY：复用交易类型配置和图标
 * - KISS：清晰的信息层级展示
 */
export const PointsDetail: React.FC<PointsDetailProps> = ({
  transactionId,
  userId,
  onClose
}) => {
  // ==================== 状态管理 ====================

  /** 交易详情数据 */
  const [transaction, setTransaction] = useState<PointTransactionResponse | null>(null)

  /** 加载中 */
  const [loading, setLoading] = useState(false)

  // ==================== 配置常量 ====================

  /** 交易类型配置 */
  const TRANSACTION_TYPE_CONFIG: Record<string, { label: string; icon: React.ReactNode; color: string; description: string }> = {
    referral_l1: {
      label: '一级推荐奖励',
      icon: <UserAddOutlined />,
      color: 'blue',
      description: '直接推荐用户注册获得的奖励'
    },
    referral_l2: {
      label: '二级推荐奖励',
      icon: <UserAddOutlined />,
      color: 'cyan',
      description: '间接推荐用户注册获得的奖励'
    },
    task_daily: {
      label: '每日任务奖励',
      icon: <CheckCircleOutlined />,
      color: 'green',
      description: '完成每日任务获得的积分奖励'
    },
    task_weekly: {
      label: '每周任务奖励',
      icon: <CheckCircleOutlined />,
      color: 'lime',
      description: '完成每周任务获得的积分奖励'
    },
    task_once: {
      label: '一次性任务奖励',
      icon: <CheckCircleOutlined />,
      color: 'orange',
      description: '完成一次性任务获得的积分奖励'
    },
    quiz_correct: {
      label: '答题正确奖励',
      icon: <QuestionCircleOutlined />,
      color: 'purple',
      description: '答题正确获得的积分奖励'
    },
    team_reward: {
      label: '战队奖励',
      icon: <TeamOutlined />,
      color: 'magenta',
      description: '战队奖励池分配获得的积分'
    },
    purchase: {
      label: '购买获得',
      icon: <GiftOutlined />,
      color: 'gold',
      description: '通过购买获得的积分'
    },
    admin_grant: {
      label: '管理员发放',
      icon: <GiftOutlined />,
      color: 'volcano',
      description: '管理员手动发放的积分'
    },
    exchange_token: {
      label: '兑换代币',
      icon: <MinusOutlined />,
      color: 'red',
      description: '使用积分兑换代币的消费'
    },
    spend_item: {
      label: '消费物品',
      icon: <MinusOutlined />,
      color: 'red',
      description: '使用积分购买物品的消费'
    }
  }

  /** 交易状态配置 */
  const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
    completed: { label: '已完成', color: 'success' },
    pending: { label: '待处理', color: 'processing' },
    cancelled: { label: '已取消', color: 'error' },
    failed: { label: '失败', color: 'error' }
  }

  // ==================== 业务逻辑 ====================

  /**
   * 加载交易详情
   */
  const loadTransactionDetail = async () => {
    setLoading(true)
    try {
      // 注意：这里需要后端提供单笔交易详情的API
      // 暂时通过获取交易列表并过滤来实现
      const response = await pointsApi.getTransactions(userId, 1, 100)
      const found = response.data.find(t => t.id === transactionId)

      if (found) {
        setTransaction(found)
      } else {
        message.error('交易记录未找到')
      }
    } catch (error: any) {
      console.error('加载交易详情失败:', error)
      message.error(error.message || '加载交易详情失败')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 格式化元数据
   */
  const formatMetadata = (metadata: Record<string, any> | undefined): string => {
    if (!metadata || Object.keys(metadata).length === 0) {
      return '无附加信息'
    }
    return JSON.stringify(metadata, null, 2)
  }

  // ==================== 生命周期 ====================

  useEffect(() => {
    loadTransactionDetail()
  }, [transactionId, userId])

  // ==================== 渲染 ====================

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0' }}>
        <Spin size="large" tip="加载交易详情中..." />
      </div>
    )
  }

  if (!transaction) {
    return (
      <Alert
        message="交易未找到"
        description="无法加载交易详情，请返回积分流水列表重试"
        type="error"
        showIcon
        action={
          onClose && (
            <Button size="small" onClick={onClose}>
              返回
            </Button>
          )
        }
      />
    )
  }

  const typeConfig = TRANSACTION_TYPE_CONFIG[transaction.transaction_type] || {
    label: transaction.transaction_type,
    icon: <GiftOutlined />,
    color: 'default',
    description: '未知交易类型'
  }
  const statusConfig = STATUS_CONFIG[transaction.status] || { label: transaction.status, color: 'default' }
  const isPositive = transaction.amount > 0

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* 交易头部信息 */}
      <Card
        title={
          <Space>
            <InfoCircleOutlined />
            <span>交易详情</span>
          </Space>
        }
        extra={
          <Space>
            <Tag icon={typeConfig.icon} color={typeConfig.color}>
              {typeConfig.label}
            </Tag>
            <Tag color={statusConfig.color}>{statusConfig.label}</Tag>
          </Space>
        }
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 交易金额展示 */}
          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            <Statistic
              title="交易金额"
              value={Math.abs(transaction.amount)}
              prefix={
                isPositive ? (
                  <PlusOutlined style={{ color: '#52c41a' }} />
                ) : (
                  <MinusOutlined style={{ color: '#ff4d4f' }} />
                )
              }
              valueStyle={{
                color: isPositive ? '#52c41a' : '#ff4d4f',
                fontSize: 48,
                fontWeight: 'bold'
              }}
              suffix="积分"
            />
            <div style={{ marginTop: 12, fontSize: 16, color: '#666' }}>
              <WalletOutlined style={{ marginRight: 8 }} />
              交易后余额: {transaction.balance_after.toLocaleString()} 积分
            </div>
          </div>

          {/* 类型说明 */}
          <Alert
            message={typeConfig.label}
            description={typeConfig.description}
            type="info"
            showIcon
            icon={typeConfig.icon}
          />
        </Space>
      </Card>

      {/* 交易基本信息 */}
      <Card title="交易信息">
        <Descriptions bordered column={{ xs: 1, sm: 2 }}>
          <Descriptions.Item label="交易ID">#{transaction.id}</Descriptions.Item>
          <Descriptions.Item label="用户ID">#{transaction.user_id}</Descriptions.Item>
          <Descriptions.Item label="交易类型">{typeConfig.label}</Descriptions.Item>
          <Descriptions.Item label="交易状态">
            <Tag color={statusConfig.color}>{statusConfig.label}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="交易金额" span={2}>
            <span
              style={{
                color: isPositive ? '#52c41a' : '#ff4d4f',
                fontWeight: 'bold',
                fontSize: 16
              }}
            >
              {isPositive ? '+' : '-'}{Math.abs(transaction.amount)} 积分
            </span>
          </Descriptions.Item>
          <Descriptions.Item label="交易前余额">
            {(transaction.balance_after - transaction.amount).toLocaleString()} 积分
          </Descriptions.Item>
          <Descriptions.Item label="交易后余额">
            {transaction.balance_after.toLocaleString()} 积分
          </Descriptions.Item>
          <Descriptions.Item label="创建时间" span={2}>
            {dayjs(transaction.created_at).format('YYYY-MM-DD HH:mm:ss')}
            <span style={{ color: '#999', marginLeft: 8 }}>
              ({dayjs(transaction.created_at).fromNow()})
            </span>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 关联对象信息 */}
      {(transaction.related_task_id ||
        transaction.related_user_id ||
        transaction.related_team_id ||
        transaction.related_question_id) && (
        <Card title="关联对象">
          <Descriptions bordered column={1}>
            {transaction.related_task_id && (
              <Descriptions.Item label="关联任务">
                <Space>
                  <CheckCircleOutlined />
                  <span>任务 ID: {transaction.related_task_id}</span>
                </Space>
              </Descriptions.Item>
            )}
            {transaction.related_user_id && (
              <Descriptions.Item label="关联用户">
                <Space>
                  <UserAddOutlined />
                  <span>用户 ID: {transaction.related_user_id}</span>
                </Space>
              </Descriptions.Item>
            )}
            {transaction.related_team_id && (
              <Descriptions.Item label="关联战队">
                <Space>
                  <TeamOutlined />
                  <span>战队 ID: {transaction.related_team_id}</span>
                </Space>
              </Descriptions.Item>
            )}
            {transaction.related_question_id && (
              <Descriptions.Item label="关联题目">
                <Space>
                  <QuestionCircleOutlined />
                  <span>题目 ID: {transaction.related_question_id}</span>
                </Space>
              </Descriptions.Item>
            )}
          </Descriptions>
        </Card>
      )}

      {/* 交易描述 */}
      {transaction.description && (
        <Card title="交易描述">
          <p style={{ margin: 0, fontSize: 15, lineHeight: 1.8, color: '#333' }}>
            {transaction.description}
          </p>
        </Card>
      )}

      {/* 元数据 */}
      {transaction.metadata && Object.keys(transaction.metadata).length > 0 && (
        <Card title="附加信息">
          <pre
            style={{
              background: '#f5f5f5',
              padding: 16,
              borderRadius: 4,
              fontSize: 13,
              fontFamily: 'monospace',
              overflow: 'auto'
            }}
          >
            {formatMetadata(transaction.metadata)}
          </pre>
        </Card>
      )}

      {/* 交易时间线 */}
      <Card title="交易流程">
        <Timeline
          items={[
            {
              color: 'blue',
              children: (
                <div>
                  <strong>交易创建</strong>
                  <div style={{ color: '#999', fontSize: 12, marginTop: 4 }}>
                    {dayjs(transaction.created_at).format('YYYY-MM-DD HH:mm:ss')}
                  </div>
                </div>
              )
            },
            transaction.status === 'completed' && {
              color: 'green',
              dot: <CheckCircleOutlined />,
              children: (
                <div>
                  <strong>交易完成</strong>
                  <div style={{ color: '#999', fontSize: 12, marginTop: 4 }}>
                    积分已到账
                  </div>
                </div>
              )
            },
            transaction.status === 'cancelled' && {
              color: 'red',
              dot: <MinusOutlined />,
              children: (
                <div>
                  <strong>交易取消</strong>
                  <div style={{ color: '#999', fontSize: 12, marginTop: 4 }}>
                    交易已取消
                  </div>
                </div>
              )
            },
            transaction.status === 'pending' && {
              color: 'orange',
              children: (
                <div>
                  <strong>待处理</strong>
                  <div style={{ color: '#999', fontSize: 12, marginTop: 4 }}>
                    交易正在处理中...
                  </div>
                </div>
              )
            }
          ].filter(Boolean)}
        />
      </Card>

      {/* 操作按钮 */}
      {onClose && (
        <Card>
          <Space style={{ width: '100%', justifyContent: 'center' }}>
            <Button size="large" onClick={onClose}>
              返回积分流水
            </Button>
          </Space>
        </Card>
      )}
    </Space>
  )
}

export default PointsDetail
