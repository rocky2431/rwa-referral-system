import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Progress, Tag } from 'antd'
import {
  TrophyOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  FireOutlined
} from '@ant-design/icons'
import type { QuizStatistics } from '@/services/api'
import { quizApi } from '@/services/api'
import dayjs from 'dayjs'

interface QuizStatisticsProps {
  userId: number
  loading?: boolean
}

/**
 * 答题统计组件
 * 显示用户的答题数据统计
 */
export const QuizStatisticsComponent: React.FC<QuizStatisticsProps> = ({
  userId,
  loading: externalLoading
}) => {
  const [loading, setLoading] = useState(false)
  const [statistics, setStatistics] = useState<QuizStatistics | null>(null)

  // 加载统计数据
  const loadStatistics = async () => {
    setLoading(true)
    try {
      const data = await quizApi.getStatistics(userId)
      setStatistics(data)
    } catch (error) {
      console.error('加载答题统计失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStatistics()
  }, [userId])

  // 计算总正确率
  const accuracyRate = statistics ? Math.round(statistics.accuracy_rate * 100) / 100 : 0

  return (
    <Card
      title="答题统计"
      loading={loading || externalLoading}
      style={{ marginBottom: 24 }}
    >
      {statistics && (
        <>
          {/* 正确率进度环 */}
          <div style={{ marginBottom: 24, textAlign: 'center' }}>
            <Progress
              type="circle"
              percent={accuracyRate}
              strokeColor={{
                '0%': accuracyRate >= 80 ? '#52c41a' : '#faad14',
                '100%': accuracyRate >= 80 ? '#87d068' : '#ff9c6e'
              }}
              format={(percent) => (
                <div>
                  <div style={{ fontSize: 24, fontWeight: 'bold' }}>{percent}%</div>
                  <div style={{ fontSize: 12, color: '#999' }}>正确率</div>
                </div>
              )}
            />
          </div>

          {/* 基础统计 */}
          <Row gutter={[16, 16]}>
            <Col xs={12} sm={8}>
              <Statistic
                title="总答题数"
                value={statistics.total_questions_answered}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col xs={12} sm={8}>
              <Statistic
                title="答对题数"
                value={statistics.correct_answers}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col xs={12} sm={8}>
              <Statistic
                title="答错题数"
                value={statistics.wrong_answers}
                prefix={<CloseCircleOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Col>
            <Col xs={12} sm={8}>
              <Statistic
                title="获得积分"
                value={statistics.total_points_earned}
                prefix={<TrophyOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Col>
            <Col xs={12} sm={8}>
              <Statistic
                title="当前连胜"
                value={statistics.current_streak_days}
                suffix="天"
                prefix={<FireOutlined />}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Col>
            <Col xs={12} sm={8}>
              <Statistic
                title="最高连胜"
                value={statistics.max_streak_days}
                suffix="天"
                prefix={<ThunderboltOutlined />}
                valueStyle={{ color: '#eb2f96' }}
              />
            </Col>
          </Row>

          {/* 难度统计 */}
          <div style={{ marginTop: 24 }}>
            <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>
              各难度统计
            </div>

            <div style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span>
                  <Tag color="green">简单</Tag>
                  {statistics.easy_answered} 题
                </span>
                <span style={{ color: '#52c41a', fontWeight: 600 }}>
                  {statistics.easy_answered > 0
                    ? Math.round((statistics.easy_correct / statistics.easy_answered) * 100)
                    : 0}
                  %
                </span>
              </div>
              <Progress
                percent={
                  statistics.easy_answered > 0
                    ? Math.round((statistics.easy_correct / statistics.easy_answered) * 100)
                    : 0
                }
                strokeColor="#52c41a"
                showInfo={false}
              />
            </div>

            <div style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span>
                  <Tag color="orange">中等</Tag>
                  {statistics.medium_answered} 题
                </span>
                <span style={{ color: '#faad14', fontWeight: 600 }}>
                  {statistics.medium_answered > 0
                    ? Math.round((statistics.medium_correct / statistics.medium_answered) * 100)
                    : 0}
                  %
                </span>
              </div>
              <Progress
                percent={
                  statistics.medium_answered > 0
                    ? Math.round((statistics.medium_correct / statistics.medium_answered) * 100)
                    : 0
                }
                strokeColor="#faad14"
                showInfo={false}
              />
            </div>

            <div style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span>
                  <Tag color="red">困难</Tag>
                  {statistics.hard_answered} 题
                </span>
                <span style={{ color: '#ff4d4f', fontWeight: 600 }}>
                  {statistics.hard_answered > 0
                    ? Math.round((statistics.hard_correct / statistics.hard_answered) * 100)
                    : 0}
                  %
                </span>
              </div>
              <Progress
                percent={
                  statistics.hard_answered > 0
                    ? Math.round((statistics.hard_correct / statistics.hard_answered) * 100)
                    : 0
                }
                strokeColor="#ff4d4f"
                showInfo={false}
              />
            </div>
          </div>

          {/* 其他信息 */}
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid #f0f0f0' }}>
            <Row gutter={16}>
              {statistics.average_answer_time && (
                <Col xs={12}>
                  <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>
                    <ClockCircleOutlined style={{ marginRight: 4 }} />
                    平均答题时间
                  </div>
                  <div style={{ fontSize: 16, fontWeight: 600 }}>
                    {Math.round(statistics.average_answer_time)} 秒
                  </div>
                </Col>
              )}
              {statistics.last_answer_date && (
                <Col xs={12}>
                  <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>
                    <ClockCircleOutlined style={{ marginRight: 4 }} />
                    最后答题时间
                  </div>
                  <div style={{ fontSize: 16, fontWeight: 600 }}>
                    {dayjs(statistics.last_answer_date).format('YYYY-MM-DD HH:mm')}
                  </div>
                </Col>
              )}
              {statistics.favorite_category && (
                <Col xs={12}>
                  <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>最擅长分类</div>
                  <div style={{ fontSize: 16, fontWeight: 600 }}>
                    <Tag color="blue">{statistics.favorite_category}</Tag>
                  </div>
                </Col>
              )}
            </Row>
          </div>
        </>
      )}
    </Card>
  )
}

export default QuizStatisticsComponent
