import React from 'react'
import { Card, Row, Col, Statistic, Tag, Avatar, Space, Progress, Divider } from 'antd'
import {
  TeamOutlined,
  UserOutlined,
  TrophyOutlined,
  GiftOutlined,
  CrownOutlined,
  RiseOutlined
} from '@ant-design/icons'
import type { TeamResponse } from '@/services/api'
import dayjs from 'dayjs'

interface TeamCardProps {
  team: TeamResponse
  loading?: boolean
}

/**
 * 战队信息展示卡片
 */
export const TeamCard: React.FC<TeamCardProps> = ({ team, loading }) => {
  // 计算等级进度（简化计算，实际应该根据后端逻辑）
  const levelProgress = (team.experience % 1000) / 10

  return (
    <Card
      title={
        <Space>
          <TeamOutlined />
          <span>战队信息</span>
        </Space>
      }
      loading={loading}
      className="team-card"
    >
      {/* 战队头部信息 */}
      <div style={{ marginBottom: 24 }}>
        <Space size={16} align="start">
          {/* 战队Logo */}
          <Avatar
            size={80}
            src={team.logo_url}
            icon={<TeamOutlined />}
            style={{
              backgroundColor: '#1890ff',
              border: '3px solid #f0f0f0'
            }}
          />

          {/* 战队基本信息 */}
          <div style={{ flex: 1 }}>
            <Space direction="vertical" size={4}>
              <Space size={8}>
                <h2 style={{ margin: 0, fontSize: 24 }}>{team.name}</h2>
                {team.is_public ? (
                  <Tag color="green">公开</Tag>
                ) : (
                  <Tag color="orange">私密</Tag>
                )}
                {team.require_approval && <Tag color="blue">需审批</Tag>}
              </Space>

              <p style={{ margin: 0, color: '#666' }}>
                {team.description || '暂无战队描述'}
              </p>

              <Space size={16}>
                <span>
                  <CrownOutlined style={{ color: '#faad14', marginRight: 4 }} />
                  队长ID: {team.captain_id}
                </span>
                <span>
                  创建于 {dayjs(team.created_at).format('YYYY-MM-DD')}
                </span>
              </Space>
            </Space>
          </div>
        </Space>
      </div>

      <Divider />

      {/* 战队统计数据 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Statistic
            title="战队等级"
            value={team.level}
            prefix={<TrophyOutlined />}
            valueStyle={{ color: '#faad14' }}
            suffix={
              <div style={{ fontSize: 14, color: '#999' }}>
                级
              </div>
            }
          />
          <Progress
            percent={levelProgress}
            size="small"
            showInfo={false}
            strokeColor="#faad14"
            style={{ marginTop: 8 }}
          />
          <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
            经验: {team.experience}
          </div>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Statistic
            title="总积分"
            value={team.total_points}
            prefix={<RiseOutlined />}
            valueStyle={{ color: '#52c41a' }}
          />
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Statistic
            title="成员数量"
            value={team.member_count}
            prefix={<UserOutlined />}
            suffix={`/ ${team.max_members}`}
            valueStyle={{ color: '#1890ff' }}
          />
          <div style={{ fontSize: 12, color: '#999', marginTop: 8 }}>
            活跃成员: {team.active_member_count}
          </div>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Statistic
            title="奖励池"
            value={team.reward_pool}
            prefix={<GiftOutlined />}
            valueStyle={{ color: '#eb2f96' }}
          />
          {team.last_distribution_at && (
            <div style={{ fontSize: 12, color: '#999', marginTop: 8 }}>
              上次分配: {dayjs(team.last_distribution_at).fromNow()}
            </div>
          )}
        </Col>
      </Row>

      <style jsx>{`
        .team-card {
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
      `}</style>
    </Card>
  )
}

export default TeamCard
