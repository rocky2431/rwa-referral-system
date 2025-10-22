import { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Progress, Empty } from 'antd'
import { TeamOutlined, GiftOutlined, TrophyOutlined, RiseOutlined } from '@ant-design/icons'
import { useReferral } from '@/hooks/useReferral'

/**
 * 推荐统计组件
 * 显示用户的推荐数据统计和分析
 */
function ReferralStats() {
  const { userInfo, config, formatReward } = useReferral()
  const [stats, setStats] = useState({
    level1Referrals: 0,
    level2Referrals: 0,
    estimatedMonthlyIncome: '0',
    activityRate: 0
  })

  // 计算统计数据
  useEffect(() => {
    if (userInfo && config) {
      calculateStats()
    }
  }, [userInfo, config])

  const calculateStats = () => {
    if (!userInfo || !config) return

    // 这里是简化的计算，实际应该从后端获取详细数据
    const level1Count = userInfo.referredCount
    const level2Count = Math.floor(level1Count * 1.5) // 假设平均每人推荐1.5个二级用户

    // 估算月收入（基于平均活跃度）
    const avgDailyActivity = 0.1 // 假设每人每天平均0.1 BNB交易
    const level1Income = level1Count * avgDailyActivity * 30 * (config.level1Rate / config.decimals)
    const level2Income = level2Count * avgDailyActivity * 30 * (config.level2Rate / config.decimals)
    const monthlyIncome = (level1Income + level2Income).toFixed(4)

    // 活跃率（基于最后活跃时间）
    const daysSinceActive = userInfo.lastActiveTimestamp === 0
      ? 30
      : Math.floor((Date.now() / 1000 - userInfo.lastActiveTimestamp) / 86400)
    const activityRate = Math.max(0, Math.min(100, (30 - daysSinceActive) / 30 * 100))

    setStats({
      level1Referrals: level1Count,
      level2Referrals: level2Count,
      estimatedMonthlyIncome: monthlyIncome,
      activityRate: Math.round(activityRate)
    })
  }

  // 如果没有数据
  if (!userInfo) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <Empty
          description="暂无推荐数据"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </div>
    )
  }

  return (
    <Row gutter={[16, 16]}>
      {/* 一级推荐 */}
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="一级推荐"
            value={stats.level1Referrals}
            prefix={<TeamOutlined style={{ color: '#ff6b35' }} />}
            valueStyle={{ color: '#ff6b35', fontSize: 24, fontWeight: 700 }}
            suffix="人"
          />
          <div style={{ marginTop: 12 }}>
            <Progress
              percent={Math.min(100, (stats.level1Referrals / 100) * 100)}
              strokeColor="#ff6b35"
              showInfo={false}
              size="small"
            />
            <div style={{ fontSize: 12, color: 'rgba(255, 255, 255, 0.4)', marginTop: 4 }}>
              目标: 100人
            </div>
          </div>
        </Card>
      </Col>

      {/* 二级推荐 */}
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="二级推荐"
            value={stats.level2Referrals}
            prefix={<TrophyOutlined style={{ color: '#4ecdc4' }} />}
            valueStyle={{ color: '#4ecdc4', fontSize: 24, fontWeight: 700 }}
            suffix="人"
          />
          <div style={{ marginTop: 12 }}>
            <Progress
              percent={Math.min(100, (stats.level2Referrals / 200) * 100)}
              strokeColor="#4ecdc4"
              showInfo={false}
              size="small"
            />
            <div style={{ fontSize: 12, color: 'rgba(255, 255, 255, 0.4)', marginTop: 4 }}>
              目标: 200人
            </div>
          </div>
        </Card>
      </Col>

      {/* 总奖励 */}
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="累计奖励"
            value={formatReward(userInfo.reward)}
            prefix={<GiftOutlined style={{ color: '#ffe66d' }} />}
            valueStyle={{ color: '#ffe66d', fontSize: 24, fontWeight: 700 }}
            suffix="BNB"
          />
          <div style={{ marginTop: 12 }}>
            <Progress
              percent={Math.min(100, (Number(formatReward(userInfo.reward)) / 10) * 100)}
              strokeColor="#ffe66d"
              showInfo={false}
              size="small"
            />
            <div style={{ fontSize: 12, color: 'rgba(255, 255, 255, 0.4)', marginTop: 4 }}>
              目标: 10 BNB
            </div>
          </div>
        </Card>
      </Col>

      {/* 预估月收入 */}
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="预估月收入"
            value={stats.estimatedMonthlyIncome}
            prefix={<RiseOutlined style={{ color: '#00d9ff' }} />}
            valueStyle={{ color: '#00d9ff', fontSize: 24, fontWeight: 700 }}
            suffix="BNB"
          />
          <div style={{ marginTop: 12, fontSize: 12, color: 'rgba(255, 255, 255, 0.4)' }}>
            基于当前推荐网络活跃度估算
          </div>
        </Card>
      </Col>

      {/* 活跃度 */}
      <Col xs={24}>
        <Card>
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 14, color: 'rgba(255, 255, 255, 0.6)', marginBottom: 8 }}>
              账户活跃度
            </div>
            <Progress
              percent={stats.activityRate}
              strokeColor={{
                '0%': '#ff006e',
                '50%': '#ffe66d',
                '100%': '#4ecdc4'
              }}
              status={stats.activityRate < 30 ? 'exception' : stats.activityRate < 70 ? 'normal' : 'success'}
            />
          </div>
          <div style={{ fontSize: 12, color: 'rgba(255, 255, 255, 0.4)' }}>
            {stats.activityRate >= 70 && '🎉 活跃度良好！继续保持'}
            {stats.activityRate >= 30 && stats.activityRate < 70 && '💪 活跃度一般，建议增加交易频率'}
            {stats.activityRate < 30 && '⚠️ 活跃度较低，可能影响推荐奖励'}
          </div>
        </Card>
      </Col>

      {/* 推荐网络可视化 */}
      <Col xs={24}>
        <Card>
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 20 }}>
              推荐网络结构
            </div>

            {/* 简单的网络可视化 */}
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 40 }}>
              {/* 中心节点（用户） */}
              <div
                style={{
                  width: 80,
                  height: 80,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #ff6b35 0%, #ff006e 100%)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#fff',
                  fontWeight: 700,
                  boxShadow: '0 4px 20px rgba(255, 107, 53, 0.4)'
                }}
              >
                <div style={{ fontSize: 24 }}>👤</div>
                <div style={{ fontSize: 12 }}>您</div>
              </div>

              {/* 连接线 */}
              <div style={{ flex: 1, height: 2, background: 'rgba(255, 255, 255, 0.2)', position: 'relative' }}>
                <div
                  style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    background: 'rgba(10, 14, 39, 0.9)',
                    padding: '4px 12px',
                    borderRadius: 12,
                    fontSize: 12,
                    color: 'rgba(255, 255, 255, 0.6)'
                  }}
                >
                  一级
                </div>
              </div>

              {/* 一级推荐节点 */}
              <div
                style={{
                  width: 60,
                  height: 60,
                  borderRadius: '50%',
                  background: 'rgba(78, 205, 196, 0.3)',
                  border: '2px solid #4ecdc4',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#4ecdc4',
                  fontWeight: 600
                }}
              >
                <div style={{ fontSize: 18 }}>👥</div>
                <div style={{ fontSize: 11 }}>{stats.level1Referrals}</div>
              </div>

              {/* 连接线 */}
              <div style={{ flex: 1, height: 2, background: 'rgba(255, 255, 255, 0.2)', position: 'relative' }}>
                <div
                  style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    background: 'rgba(10, 14, 39, 0.9)',
                    padding: '4px 12px',
                    borderRadius: 12,
                    fontSize: 12,
                    color: 'rgba(255, 255, 255, 0.6)'
                  }}
                >
                  二级
                </div>
              </div>

              {/* 二级推荐节点 */}
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: '50%',
                  background: 'rgba(255, 230, 109, 0.3)',
                  border: '2px solid #ffe66d',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#ffe66d',
                  fontWeight: 600
                }}
              >
                <div style={{ fontSize: 16 }}>👥</div>
                <div style={{ fontSize: 10 }}>{stats.level2Referrals}</div>
              </div>
            </div>

            <div style={{ marginTop: 20, fontSize: 12, color: 'rgba(255, 255, 255, 0.4)' }}>
              您的推荐网络共 {stats.level1Referrals + stats.level2Referrals} 人
            </div>
          </div>
        </Card>
      </Col>
    </Row>
  )
}

export default ReferralStats
