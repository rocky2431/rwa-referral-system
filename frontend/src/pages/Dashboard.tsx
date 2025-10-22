import { useEffect, useState } from 'react'
import { Row, Col, Card, Typography, Statistic, Space, Button, Alert, Spin } from 'antd'
import { WalletOutlined, TeamOutlined, GiftOutlined, ClockCircleOutlined, CopyOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useWeb3 } from '@/contexts/Web3Context'
import { dashboardApi, type DashboardResponse } from '@/services/api'
import ReferralLinkGenerator from '@/components/referral/ReferralLinkGenerator'
import ReferralStats from '@/components/referral/ReferralStats'

const { Title, Paragraph, Text } = Typography

/**
 * 仪表板页面
 */
function Dashboard() {
  const navigate = useNavigate()
  const { account, isConnected } = useWeb3()
  const [dashboardData, setDashboardData] = useState<DashboardResponse | null>(null)
  const [loading, setLoading] = useState(false)

  // 获取仪表板数据
  useEffect(() => {
    if (account) {
      fetchDashboardData()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [account])  // ✅ 只依赖account,避免循环

  // 获取仪表板数据（从后端API）
  const fetchDashboardData = async () => {
    if (!account) return

    setLoading(true)
    try {
      const data = await dashboardApi.getData(account)
      setDashboardData(data)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  // 如果未连接钱包
  if (!isConnected) {
    return (
      <div
        style={{
          minHeight: 'calc(100vh - 64px - 120px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 24
        }}
      >
        <Card style={{ maxWidth: 500, textAlign: 'center' }}>
          <WalletOutlined style={{ fontSize: 64, color: '#ff6b35', marginBottom: 24 }} />
          <Title level={3}>请先连接钱包</Title>
          <Paragraph style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
            连接您的钱包以查看推荐仪表板
          </Paragraph>
          <Button type="primary" size="large" onClick={() => navigate('/')}>
            返回首页
          </Button>
        </Card>
      </div>
    )
  }

  return (
    <div style={{ minHeight: 'calc(100vh - 64px - 120px)', padding: '48px 24px' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        {/* 页面标题 */}
        <div style={{ marginBottom: 32 }}>
          <Title level={2}>推荐仪表板</Title>
          <Paragraph style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: 16 }}>
            查看您的推荐数据和奖励统计
          </Paragraph>
        </div>

        {/* 加载状态 */}
        {loading && (
          <div style={{ textAlign: 'center', padding: 60 }}>
            <Spin size="large" />
            <Paragraph style={{ marginTop: 16, color: 'rgba(255, 255, 255, 0.6)' }}>
              加载数据中...
            </Paragraph>
          </div>
        )}

        {/* 数据展示 */}
        {!loading && dashboardData && (
          <Space direction="vertical" size={24} style={{ width: '100%' }}>
            {/* 活跃状态提示 */}
            {dashboardData.is_active ? (
              <Alert
                message="账户活跃"
                description="您的账户当前处于活跃状态，可以获得推荐奖励"
                type="success"
                showIcon
                icon={<ClockCircleOutlined />}
              />
            ) : (
              <Alert
                message="账户未激活"
                description={dashboardData.days_since_active >= 0
                  ? `您已${dashboardData.days_since_active}天未活跃，需要进行交易以重新激活`
                  : '请开始您的第一次活动以激活账户'}
                type="warning"
                showIcon
                icon={<ClockCircleOutlined />}
              />
            )}

            {/* 核心数据卡片 */}
            <Row gutter={[24, 24]}>
              <Col xs={24} sm={12} lg={6}>
                <Card>
                  <Statistic
                    title="总积分"
                    value={dashboardData.total_rewards}
                    valueStyle={{ color: '#ff6b35', fontSize: 28, fontWeight: 700 }}
                    prefix={<GiftOutlined />}
                  />
                </Card>
              </Col>

              <Col xs={24} sm={12} lg={6}>
                <Card>
                  <Statistic
                    title="推荐人数"
                    value={dashboardData.referred_count}
                    valueStyle={{ color: '#4ecdc4', fontSize: 28, fontWeight: 700 }}
                    prefix={<TeamOutlined />}
                  />
                </Card>
              </Col>

              <Col xs={24} sm={12} lg={6}>
                <Card>
                  <Statistic
                    title="最后活跃"
                    value={dashboardData.days_since_active >= 0 ? dashboardData.days_since_active : '从未'}
                    suffix={dashboardData.days_since_active >= 0 ? "天前" : ""}
                    valueStyle={{ color: '#ffe66d', fontSize: 28, fontWeight: 700 }}
                    prefix={<ClockCircleOutlined />}
                  />
                </Card>
              </Col>

              <Col xs={24} sm={12} lg={6}>
                <Card>
                  <div>
                    <Text style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: 14 }}>我的推荐人</Text>
                    <div style={{ marginTop: 8 }}>
                      {dashboardData.referrer === '0x0000000000000000000000000000000000000000' ? (
                        <Text style={{ fontSize: 16, color: 'rgba(255, 255, 255, 0.4)' }}>未绑定</Text>
                      ) : (
                        <Text
                          copyable
                          style={{
                            fontSize: 14,
                            fontFamily: 'monospace',
                            color: '#00d9ff'
                          }}
                        >
                          {`${dashboardData.referrer.slice(0, 6)}...${dashboardData.referrer.slice(-4)}`}
                        </Text>
                      )}
                    </div>
                  </div>
                </Card>
              </Col>
            </Row>

            {/* 推荐链接生成 - 暂时隐藏，等待智能合约部署 */}
            {/* <Card
              title={
                <Space>
                  <CopyOutlined />
                  <span>我的推荐链接</span>
                </Space>
              }
            >
              <ReferralLinkGenerator />
            </Card> */}

            {/* 推荐统计图表 - 暂时隐藏，等待智能合约部署 */}
            {/* <Card title="推荐统计">
              <ReferralStats />
            </Card> */}

            {/* 功能开发中提示 */}
            <Alert
              message="更多功能即将上线"
              description="推荐链接生成、推荐统计等功能正在开发中，敬请期待！"
              type="info"
              showIcon
            />
          </Space>
        )}
      </div>
    </div>
  )
}

export default Dashboard
