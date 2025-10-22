import React from 'react'
import { Card, Row, Col, Statistic, Divider, Tag } from 'antd'
import {
  WalletOutlined,
  LockOutlined,
  TrophyOutlined,
  ShoppingOutlined,
  TeamOutlined,
  CheckCircleOutlined,
  QuestionCircleOutlined,
  UserAddOutlined
} from '@ant-design/icons'
import type { UserPointsResponse } from '@/services/api'

interface PointsCardProps {
  points: UserPointsResponse
  loading?: boolean
}

export const PointsCard: React.FC<PointsCardProps> = ({ points, loading }) => {
  // 计算总积分（可用+冻结）
  const totalPoints = points.available_points + points.frozen_points

  return (
    <Card
      title={
        <span>
          <WalletOutlined style={{ marginRight: 8 }} />
          我的积分
        </span>
      }
      loading={loading}
      className="points-card"
    >
      {/* 主要积分数据 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Statistic
            title="可用积分"
            value={points.available_points}
            prefix={<WalletOutlined />}
            valueStyle={{ color: '#3f8600' }}
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Statistic
            title="冻结积分"
            value={points.frozen_points}
            prefix={<LockOutlined />}
            valueStyle={{ color: '#cf1322' }}
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Statistic
            title="累计获得"
            value={points.total_earned}
            prefix={<TrophyOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Statistic
            title="累计消费"
            value={points.total_spent}
            prefix={<ShoppingOutlined />}
            valueStyle={{ color: '#faad14' }}
          />
        </Col>
      </Row>

      <Divider />

      {/* 积分来源分布 */}
      <div className="points-sources">
        <h4 style={{ marginBottom: 16 }}>积分来源</h4>
        <Row gutter={[16, 8]}>
          <Col span={12}>
            <div className="source-item">
              <UserAddOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              <span className="source-label">推荐奖励:</span>
              <Tag color="blue">{points.points_from_referral}</Tag>
            </div>
          </Col>
          <Col span={12}>
            <div className="source-item">
              <CheckCircleOutlined style={{ marginRight: 8, color: '#52c41a' }} />
              <span className="source-label">任务完成:</span>
              <Tag color="green">{points.points_from_tasks}</Tag>
            </div>
          </Col>
          <Col span={12}>
            <div className="source-item">
              <QuestionCircleOutlined style={{ marginRight: 8, color: '#722ed1' }} />
              <span className="source-label">答题奖励:</span>
              <Tag color="purple">{points.points_from_quiz}</Tag>
            </div>
          </Col>
          <Col span={12}>
            <div className="source-item">
              <TeamOutlined style={{ marginRight: 8, color: '#eb2f96' }} />
              <span className="source-label">战队奖励:</span>
              <Tag color="magenta">{points.points_from_team}</Tag>
            </div>
          </Col>
          <Col span={12}>
            <div className="source-item">
              <ShoppingOutlined style={{ marginRight: 8, color: '#faad14' }} />
              <span className="source-label">购买获得:</span>
              <Tag color="orange">{points.points_from_purchase}</Tag>
            </div>
          </Col>
        </Row>
      </div>

      <style jsx>{`
        .points-card {
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .points-sources {
          margin-top: 16px;
        }

        .source-item {
          display: flex;
          align-items: center;
          padding: 8px 0;
        }

        .source-label {
          margin-right: 8px;
          color: #666;
          font-size: 14px;
        }
      `}</style>
    </Card>
  )
}

export default PointsCard
