import { useState, useEffect } from 'react'
import { Row, Col, Typography, Button, Space, Statistic, Card, Spin } from 'antd'
import { TeamOutlined, TrophyOutlined, GiftOutlined, RocketOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useWeb3 } from '@/contexts/Web3Context'
import { useReferral } from '@/hooks/useReferral'
import { dashboardApi, type DashboardResponse } from '@/services/api'
import ReferralInput from '@/components/referral/ReferralInput'
import ReferralLinkGenerator from '@/components/referral/ReferralLinkGenerator'

const { Title, Paragraph, Text } = Typography

/**
 * 首页组件
 */
function Home() {
  const navigate = useNavigate()
  const { account, isConnected, connectWallet, isConnecting } = useWeb3()
  const { config, userInfo } = useReferral()
  const [dashboardData, setDashboardData] = useState<DashboardResponse | null>(null)
  const [loading, setLoading] = useState(false)

  // 获取仪表板数据
  useEffect(() => {
    if (account) {
      fetchDashboardData()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [account])

  // 从后端API获取真实数据
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

  // 计算推荐奖励比例
  const level1Percentage = config ? (config.level1Rate / config.decimals) * 100 : 15
  const level2Percentage = config ? (config.level2Rate / config.decimals) * 100 : 5

  // 特性列表
  const features = [
    {
      icon: <GiftOutlined style={{ fontSize: 48, color: '#ff6b35' }} />,
      title: '双层奖励',
      description: `一级推荐获得${level1Percentage.toFixed(0)}%奖励，二级推荐获得${level2Percentage.toFixed(0)}%奖励`
    },
    {
      icon: <TeamOutlined style={{ fontSize: 48, color: '#4ecdc4' }} />,
      title: '无限推荐',
      description: '推荐人数无上限，建立自己的推荐网络'
    },
    {
      icon: <TrophyOutlined style={{ fontSize: 48, color: '#ffe66d' }} />,
      title: '实时排行',
      description: '实时更新的排行榜，展示顶级推荐者'
    },
    {
      icon: <RocketOutlined style={{ fontSize: 48, color: '#00d9ff' }} />,
      title: '即时到账',
      description: '链上自动分发，奖励即时到账'
    }
  ]

  return (
    <div style={{ minHeight: 'calc(100vh - 64px - 120px)', padding: '48px 24px' }}>
      {/* Hero区域 */}
      <div
        style={{
          maxWidth: 1200,
          margin: '0 auto 80px',
          textAlign: 'center'
        }}
      >
        <div className="fade-in">
          <Title
            level={1}
            style={{
              fontSize: 56,
              fontWeight: 800,
              marginBottom: 24,
              background: 'linear-gradient(135deg, #ff6b35 0%, #ff006e 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}
          >
            RWA推荐系统
          </Title>

          <Paragraph
            style={{
              fontSize: 20,
              color: 'rgba(255, 255, 255, 0.7)',
              maxWidth: 600,
              margin: '0 auto 40px'
            }}
          >
            通过推荐好友赚取奖励，建立您的被动收入网络
          </Paragraph>

          {/* CTA按钮 */}
          {!isConnected ? (
            <Button
              type="primary"
              size="large"
              loading={isConnecting}
              onClick={connectWallet}
              style={{
                height: 56,
                padding: '0 48px',
                fontSize: 18,
                fontWeight: 600
              }}
            >
              {isConnecting ? '连接中...' : '开始使用'}
            </Button>
          ) : (
            <Button
              size="large"
              onClick={() => navigate('/leaderboard')}
              style={{
                height: 56,
                padding: '0 48px',
                fontSize: 18,
                fontWeight: 600
              }}
            >
              查看排行榜
            </Button>
          )}
        </div>

        {/* 个人数据统计 - 仅连接钱包后显示 */}
        {isConnected && dashboardData && (
          <Row gutter={[24, 24]} style={{ marginTop: 60 }}>
            {loading ? (
              <Col span={24} style={{ textAlign: 'center', padding: 60 }}>
                <Spin size="large" />
              </Col>
            ) : (
              <>
                <Col xs={24} sm={12} lg={6}>
                  <Card
                    style={{
                      background: 'rgba(255, 107, 53, 0.1)',
                      border: '1px solid rgba(255, 107, 53, 0.3)'
                    }}
                  >
                    <Statistic
                      title="总积分"
                      value={dashboardData.total_rewards}
                      valueStyle={{ color: '#ff6b35', fontSize: 32, fontWeight: 700 }}
                      prefix={<GiftOutlined />}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                  <Card
                    style={{
                      background: 'rgba(78, 205, 196, 0.1)',
                      border: '1px solid rgba(78, 205, 196, 0.3)'
                    }}
                  >
                    <Statistic
                      title="推荐人数"
                      value={dashboardData.referred_count}
                      valueStyle={{ color: '#4ecdc4', fontSize: 32, fontWeight: 700 }}
                      prefix={<TeamOutlined />}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                  <Card
                    style={{
                      background: 'rgba(255, 230, 109, 0.1)',
                      border: '1px solid rgba(255, 230, 109, 0.3)'
                    }}
                  >
                    <Statistic
                      title="最后活跃"
                      value={dashboardData.days_since_active >= 0 ? dashboardData.days_since_active : '从未'}
                      suffix={dashboardData.days_since_active >= 0 ? "天前" : ""}
                      valueStyle={{ color: '#ffe66d', fontSize: 32, fontWeight: 700 }}
                      prefix={<ClockCircleOutlined />}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                  <Card
                    style={{
                      background: 'rgba(0, 217, 255, 0.1)',
                      border: '1px solid rgba(0, 217, 255, 0.3)'
                    }}
                  >
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
              </>
            )}
          </Row>
        )}
      </div>

      {/* 推荐功能区 */}
      {isConnected && (
        <div style={{ maxWidth: 800, margin: '0 auto 80px' }}>
          <Card
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 16
            }}
          >
            <Space direction="vertical" size={24} style={{ width: '100%' }}>
              <Title level={3} style={{ margin: 0 }}>
                开始推荐
              </Title>

              {/* 如果用户还没有绑定推荐人 */}
              {userInfo && userInfo.referrer === '0x0000000000000000000000000000000000000000' && (
                <>
                  <Paragraph style={{ color: 'rgba(255, 255, 255, 0.6)', margin: 0 }}>
                    输入推荐人地址以绑定推荐关系，获得加入奖励
                  </Paragraph>
                  <ReferralInput />
                </>
              )}

              {/* 生成推荐链接 */}
              <div style={{ marginTop: userInfo?.referrer !== '0x0000000000000000000000000000000000000000' ? 0 : 24 }}>
                <Paragraph style={{ color: 'rgba(255, 255, 255, 0.6)', margin: '0 0 16px 0' }}>
                  生成您的专属推荐链接，分享给好友获得奖励
                </Paragraph>
                <ReferralLinkGenerator />
              </div>
            </Space>
          </Card>
        </div>
      )}

      {/* 特性介绍 */}
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <Title level={2} style={{ textAlign: 'center', marginBottom: 48 }}>
          为什么选择我们
        </Title>

        <Row gutter={[32, 32]}>
          {features.map((feature, index) => (
            <Col xs={24} sm={12} lg={6} key={index}>
              <Card
                hoverable
                style={{
                  height: '100%',
                  textAlign: 'center',
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  transition: 'all 0.3s ease'
                }}
                bodyStyle={{ padding: 32 }}
              >
                <div style={{ marginBottom: 16 }}>{feature.icon}</div>
                <Title level={4} style={{ marginBottom: 12 }}>
                  {feature.title}
                </Title>
                <Paragraph style={{ color: 'rgba(255, 255, 255, 0.6)', margin: 0 }}>
                  {feature.description}
                </Paragraph>
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    </div>
  )
}

export default Home
