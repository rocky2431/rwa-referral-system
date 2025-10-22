import React, { useState, useEffect } from 'react'
import {
  Card,
  Avatar,
  Descriptions,
  Tabs,
  Row,
  Col,
  Statistic,
  Progress,
  Space,
  Button,
  Tag,
  Modal,
  Form,
  Input,
  message,
  Alert,
  Spin
} from 'antd'
import {
  UserOutlined,
  WalletOutlined,
  TrophyOutlined,
  CheckCircleOutlined,
  QuestionCircleOutlined,
  TeamOutlined,
  EditOutlined,
  GiftOutlined,
  FireOutlined,
  RiseOutlined
} from '@ant-design/icons'
import type {
  UserDetailResponse,
  UserPointsResponse,
  UserTaskSummary,
  UserAnswerStatistics,
  UserUpdateRequest
} from '@/services/api'
import { usersApi, pointsApi, tasksApi, quizApi } from '@/services/api'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

/**
 * UserProfile 组件属性
 */
interface UserProfileProps {
  /** 用户ID */
  userId: number
  /** 刷新回调 */
  onRefresh?: () => void
}

/**
 * 用户个人中心组件
 *
 * 完整展示用户的所有信息，包括：
 * - 用户基本信息（头像、用户名、等级、经验）
 * - 数据统计（积分、任务、答题、战队）
 * - 个人资料编辑
 * - 快捷操作入口
 *
 * 设计原则：
 * - SRP：专注于用户信息展示和基本管理
 * - DRY：复用现有的API和组件
 * - KISS：清晰的信息层级和简洁的操作流程
 */
export const UserProfile: React.FC<UserProfileProps> = ({ userId, onRefresh }) => {
  // ==================== 状态管理 ====================

  /** 用户详情 */
  const [userDetail, setUserDetail] = useState<UserDetailResponse | null>(null)

  /** 积分信息 */
  const [pointsInfo, setPointsInfo] = useState<UserPointsResponse | null>(null)

  /** 任务统计 */
  const [taskSummary, setTaskSummary] = useState<UserTaskSummary | null>(null)

  /** 答题统计 */
  const [quizStats, setQuizStats] = useState<UserAnswerStatistics | null>(null)

  /** 加载中 */
  const [loading, setLoading] = useState(false)

  /** 编辑弹窗可见性 */
  const [editModalVisible, setEditModalVisible] = useState(false)

  /** 编辑表单 */
  const [form] = Form.useForm<UserUpdateRequest>()

  /** 保存中 */
  const [saving, setSaving] = useState(false)

  /** 当前激活的标签页 */
  const [activeTab, setActiveTab] = useState('overview')

  // ==================== 业务逻辑 ====================

  /**
   * 加载用户详情
   */
  const loadUserDetail = async () => {
    setLoading(true)
    try {
      const detail = await usersApi.getDetail(userId)
      setUserDetail(detail)
    } catch (error: any) {
      console.error('加载用户详情失败:', error)
      message.error(error.message || '加载用户详情失败')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 加载积分信息
   */
  const loadPointsInfo = async () => {
    try {
      const points = await pointsApi.getUserPoints(userId)
      setPointsInfo(points)
    } catch (error) {
      console.error('加载积分信息失败:', error)
    }
  }

  /**
   * 加载任务统计
   */
  const loadTaskSummary = async () => {
    try {
      const summary = await tasksApi.getUserSummary(userId)
      setTaskSummary(summary)
    } catch (error) {
      console.error('加载任务统计失败:', error)
    }
  }

  /**
   * 加载答题统计
   */
  const loadQuizStats = async () => {
    try {
      const stats = await quizApi.getUserStatistics(userId)
      setQuizStats(stats)
    } catch (error) {
      console.error('加载答题统计失败:', error)
    }
  }

  /**
   * 加载所有数据
   */
  const loadAllData = async () => {
    await Promise.all([
      loadUserDetail(),
      loadPointsInfo(),
      loadTaskSummary(),
      loadQuizStats()
    ])
  }

  /**
   * 打开编辑弹窗
   */
  const handleOpenEdit = () => {
    if (userDetail) {
      form.setFieldsValue({
        username: userDetail.username,
        avatar_url: userDetail.avatar_url,
        email: userDetail.email
      })
      setEditModalVisible(true)
    }
  }

  /**
   * 保存用户信息
   */
  const handleSaveProfile = async () => {
    setSaving(true)
    try {
      const values = await form.validateFields()
      await usersApi.update(userId, values)
      message.success('个人信息更新成功！')
      setEditModalVisible(false)
      await loadUserDetail()
      onRefresh?.()
    } catch (error: any) {
      console.error('更新用户信息失败:', error)
      if (!error.errorFields) {
        message.error(error.message || '更新失败，请稍后重试')
      }
    } finally {
      setSaving(false)
    }
  }

  /**
   * 计算等级进度
   */
  const getLevelProgress = (): number => {
    if (!userDetail) return 0
    // 简化计算：每1000经验升一级
    const currentLevelExp = userDetail.experience % 1000
    return Math.round((currentLevelExp / 1000) * 100)
  }

  /**
   * 计算答题正确率
   */
  const getAccuracyRate = (): number => {
    if (!quizStats || quizStats.total_answers === 0) return 0
    return Math.round((quizStats.correct_answers / quizStats.total_answers) * 100)
  }

  // ==================== 生命周期 ====================

  useEffect(() => {
    loadAllData()
  }, [userId])

  // ==================== 渲染 ====================

  if (loading && !userDetail) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0' }}>
        <Spin size="large" tip="加载个人信息中..." />
      </div>
    )
  }

  if (!userDetail) {
    return (
      <Alert
        message="用户未找到"
        description="无法加载用户信息，请刷新页面重试"
        type="error"
        showIcon
      />
    )
  }

  // 标签页配置
  const tabItems = [
    {
      key: 'overview',
      label: (
        <span>
          <UserOutlined />
          数据总览
        </span>
      ),
      children: (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 统计卡片 */}
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="总积分"
                  value={pointsInfo?.available_points || 0}
                  prefix={<WalletOutlined />}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="已完成任务"
                  value={userDetail.total_tasks_completed}
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="答题总数"
                  value={userDetail.total_questions_answered}
                  prefix={<QuestionCircleOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="推荐人数"
                  value={userDetail.total_invited}
                  prefix={<TeamOutlined />}
                  valueStyle={{ color: '#eb2f96' }}
                />
              </Card>
            </Col>
          </Row>

          {/* 详细数据 */}
          {pointsInfo && (
            <Card title="积分来源分析">
              <Row gutter={[16, 16]}>
                <Col xs={12} sm={8}>
                  <Statistic
                    title="推荐奖励"
                    value={pointsInfo.points_from_referral}
                    prefix={<GiftOutlined />}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Col>
                <Col xs={12} sm={8}>
                  <Statistic
                    title="任务奖励"
                    value={pointsInfo.points_from_tasks}
                    prefix={<CheckCircleOutlined />}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
                <Col xs={12} sm={8}>
                  <Statistic
                    title="答题奖励"
                    value={pointsInfo.points_from_quiz}
                    prefix={<QuestionCircleOutlined />}
                    valueStyle={{ color: '#722ed1' }}
                  />
                </Col>
                <Col xs={12} sm={8}>
                  <Statistic
                    title="战队奖励"
                    value={pointsInfo.points_from_team}
                    prefix={<TeamOutlined />}
                    valueStyle={{ color: '#eb2f96' }}
                  />
                </Col>
                <Col xs={12} sm={8}>
                  <Statistic
                    title="累计获得"
                    value={pointsInfo.total_earned}
                    prefix={<RiseOutlined />}
                    valueStyle={{ color: '#fa8c16' }}
                  />
                </Col>
                <Col xs={12} sm={8}>
                  <Statistic
                    title="累计消费"
                    value={pointsInfo.total_spent}
                    prefix={<FireOutlined />}
                    valueStyle={{ color: '#f5222d' }}
                  />
                </Col>
              </Row>
            </Card>
          )}

          {/* 任务和答题统计 */}
          <Row gutter={16}>
            {taskSummary && (
              <Col xs={24} md={12}>
                <Card title="任务统计">
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    <div>
                      <div style={{ marginBottom: 8 }}>
                        总任务: {taskSummary.total_tasks}
                      </div>
                      <Progress
                        percent={Math.round(
                          ((taskSummary.completed_tasks + taskSummary.claimed_tasks) /
                            Math.max(taskSummary.total_tasks, 1)) *
                            100
                        )}
                        strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
                      />
                    </div>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Statistic
                          title="进行中"
                          value={taskSummary.in_progress_tasks}
                          valueStyle={{ fontSize: 20 }}
                        />
                      </Col>
                      <Col span={12}>
                        <Statistic
                          title="已完成"
                          value={taskSummary.completed_tasks}
                          valueStyle={{ fontSize: 20, color: '#52c41a' }}
                        />
                      </Col>
                    </Row>
                  </Space>
                </Card>
              </Col>
            )}
            {quizStats && (
              <Col xs={24} md={12}>
                <Card title="答题统计">
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    <div>
                      <div style={{ marginBottom: 8 }}>
                        正确率: {getAccuracyRate()}%
                      </div>
                      <Progress
                        percent={getAccuracyRate()}
                        strokeColor={getAccuracyRate() >= 80 ? '#52c41a' : '#faad14'}
                      />
                    </div>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Statistic
                          title="答题总数"
                          value={quizStats.total_answers}
                          valueStyle={{ fontSize: 20 }}
                        />
                      </Col>
                      <Col span={12}>
                        <Statistic
                          title="正确数"
                          value={quizStats.correct_answers}
                          valueStyle={{ fontSize: 20, color: '#52c41a' }}
                        />
                      </Col>
                    </Row>
                    <div>
                      <Tag color="gold">
                        连续答对 {quizStats.current_streak} 天
                      </Tag>
                      <Tag color="purple">
                        最长连胜 {quizStats.max_streak} 天
                      </Tag>
                    </div>
                  </Space>
                </Card>
              </Col>
            )}
          </Row>
        </Space>
      )
    },
    {
      key: 'info',
      label: (
        <span>
          <InfoCircleOutlined />
          个人信息
        </span>
      ),
      children: (
        <Card
          title="基本信息"
          extra={
            <Button icon={<EditOutlined />} onClick={handleOpenEdit}>
              编辑资料
            </Button>
          }
        >
          <Descriptions bordered column={{ xs: 1, sm: 2 }}>
            <Descriptions.Item label="用户ID">#{userDetail.id}</Descriptions.Item>
            <Descriptions.Item label="用户名">{userDetail.username}</Descriptions.Item>
            <Descriptions.Item label="钱包地址" span={2}>
              <code style={{ fontSize: 12, fontFamily: 'monospace' }}>
                {userDetail.wallet_address}
              </code>
            </Descriptions.Item>
            {userDetail.email && (
              <Descriptions.Item label="邮箱" span={2}>
                {userDetail.email}
              </Descriptions.Item>
            )}
            <Descriptions.Item label="等级">
              <Tag color="gold">Lv.{userDetail.level}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="经验值">
              {userDetail.experience} XP
            </Descriptions.Item>
            <Descriptions.Item label="账户状态">
              {userDetail.is_active ? (
                <Tag color="success">活跃</Tag>
              ) : (
                <Tag color="default">非活跃</Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="注册时间">
              {dayjs(userDetail.created_at).format('YYYY-MM-DD HH:mm')}
            </Descriptions.Item>
            {userDetail.last_active_at && (
              <Descriptions.Item label="最后活跃" span={2}>
                {dayjs(userDetail.last_active_at).format('YYYY-MM-DD HH:mm')}
              </Descriptions.Item>
            )}
            <Descriptions.Item label="连续登录">
              {userDetail.consecutive_login_days} 天
            </Descriptions.Item>
            {userDetail.last_login_date && (
              <Descriptions.Item label="最后登录">
                {dayjs(userDetail.last_login_date).format('YYYY-MM-DD')}
              </Descriptions.Item>
            )}
          </Descriptions>
        </Card>
      )
    }
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* 用户头部信息 */}
      <Card>
        <Space size={24} align="start" style={{ width: '100%' }}>
          {/* 头像 */}
          <Avatar
            size={100}
            src={userDetail.avatar_url}
            icon={<UserOutlined />}
            style={{ backgroundColor: '#1890ff' }}
          />

          {/* 基本信息 */}
          <div style={{ flex: 1 }}>
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
              <Space size={12}>
                <h2 style={{ margin: 0 }}>{userDetail.username}</h2>
                <Tag color="gold">Lv.{userDetail.level}</Tag>
                {userDetail.is_active && <Tag color="success">活跃用户</Tag>}
              </Space>

              <div style={{ color: '#666', fontSize: 13, fontFamily: 'monospace' }}>
                {userDetail.wallet_address.slice(0, 10)}...{userDetail.wallet_address.slice(-8)}
              </div>

              <div>
                <div style={{ marginBottom: 8, fontSize: 13, color: '#666' }}>
                  经验值: {userDetail.experience} XP
                </div>
                <Progress percent={getLevelProgress()} size="small" />
                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                  距离下一级还需 {1000 - (userDetail.experience % 1000)} XP
                </div>
              </div>
            </Space>
          </div>

          {/* 快捷统计 */}
          <div>
            <Row gutter={[16, 8]}>
              <Col span={12}>
                <Statistic
                  title="总积分"
                  value={userDetail.total_points}
                  prefix={<TrophyOutlined />}
                  valueStyle={{ fontSize: 24 }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="正确答案"
                  value={userDetail.correct_answers}
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ fontSize: 24, color: '#52c41a' }}
                />
              </Col>
            </Row>
          </div>
        </Space>
      </Card>

      {/* 标签页内容 */}
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />

      {/* 编辑资料弹窗 */}
      <Modal
        title="编辑个人资料"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        footer={null}
        width={500}
      >
        <Form form={form} layout="vertical" onFinish={handleSaveProfile}>
          <Form.Item
            label="用户名"
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 2, max: 50, message: '用户名长度为2-50个字符' }
            ]}
          >
            <Input placeholder="输入您的昵称" />
          </Form.Item>

          <Form.Item
            label="头像URL"
            name="avatar_url"
            rules={[{ type: 'url', message: '请输入有效的URL地址' }]}
          >
            <Input placeholder="https://example.com/avatar.jpg" />
          </Form.Item>

          <Form.Item
            label="邮箱"
            name="email"
            rules={[{ type: 'email', message: '请输入有效的邮箱地址' }]}
          >
            <Input placeholder="your@email.com" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, marginTop: 24 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setEditModalVisible(false)} disabled={saving}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={saving}>
                保存
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  )
}

export default UserProfile
