import React, { useState, useEffect } from 'react'
import { Tabs, Alert, Button, Space, Divider, message, Spin, Card, Result } from 'antd'
import {
  QuestionCircleOutlined,
  BarChartOutlined,
  HistoryOutlined,
  WalletOutlined,
  ReloadOutlined,
  UserAddOutlined,
  CheckCircleOutlined,
  TrophyOutlined
} from '@ant-design/icons'
import { useWeb3 } from '@/contexts/Web3Context'
import { useUser } from '@/hooks/useUser'
import { QuizCard } from '@/components/quiz/QuizCard'
import { QuizStatisticsComponent } from '@/components/quiz/QuizStatistics'
import { QuizHistory } from '@/components/quiz/QuizHistory'
import { RegisterModal } from '@/components/user/RegisterModal'
import type { QuestionResponse, AnswerResult, DailyLimit } from '@/services/api'
import { quizApi } from '@/services/api'

const Quiz: React.FC = () => {
  const { isConnected } = useWeb3()
  const { userId, isRegistered, isLoading: isUserLoading, refreshUser } = useUser()
  const [currentQuestion, setCurrentQuestion] = useState<QuestionResponse | null>(null)
  const [answerResult, setAnswerResult] = useState<AnswerResult | null>(null)
  const [loadingQuestion, setLoadingQuestion] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [dailyLimit, setDailyLimit] = useState<DailyLimit | null>(null)
  const [activeTab, setActiveTab] = useState('quiz')
  const [refreshKey, setRefreshKey] = useState(0)
  const [registerModalVisible, setRegisterModalVisible] = useState(false)
  const [quizFinished, setQuizFinished] = useState(false)

  // 检查每日答题限制
  const checkDailyLimit = async () => {
    if (!userId) return false
    try {
      const limit = await quizApi.checkDailyLimit(userId)
      setDailyLimit(limit)
      return limit.can_answer
    } catch (error) {
      console.error('检查每日限制失败:', error)
      return false
    }
  }

  // 加载随机题目
  const loadRandomQuestion = async () => {
    setLoadingQuestion(true)
    setAnswerResult(null)
    try {
      const canAnswer = await checkDailyLimit()
      if (!canAnswer) {
        message.warning('今日答题次数已达上限')
        return
      }

      const question = await quizApi.getRandomQuestion(userId!)
      setCurrentQuestion(question)
    } catch (error: any) {
      console.error('加载题目失败:', error)
      message.error(error.message || '加载题目失败')
    } finally {
      setLoadingQuestion(false)
    }
  }

  // 提交答案
  const handleSubmitAnswer = async (userAnswer: string, answerTime: number) => {
    if (!currentQuestion) return

    setSubmitting(true)
    try {
      const result = await quizApi.submitAnswer(userId!, {
        question_id: currentQuestion.id,
        user_answer: userAnswer,
        answer_time: answerTime
      })

      setAnswerResult(result)

      // 刷新统计数据
      setRefreshKey((prev) => prev + 1)

      // 检查是否答题完成
      if (result.daily_count >= result.daily_limit) {
        setQuizFinished(true)
      }

      // 如果答对了，显示恭喜信息
      if (result.is_correct) {
        message.success(`回答正确！获得 ${result.points_earned} 积分`)
      }
    } catch (error: any) {
      console.error('提交答案失败:', error)
      message.error(error.message || '提交答案失败')
    } finally {
      setSubmitting(false)
    }
  }

  // 继续下一题
  const handleNextQuestion = () => {
    if (quizFinished) {
      // 答题已结束，不加载新题目
      return
    }
    loadRandomQuestion()
  }

  // 刷新所有数据
  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1)
    loadRandomQuestion()
  }

  // 初始加载
  useEffect(() => {
    if (isConnected && userId) {
      loadRandomQuestion()
    }
  }, [isConnected, userId])

  // 未连接钱包提示
  if (!isConnected) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="请先连接钱包"
          description="参与答题需要先连接您的Web3钱包"
          type="warning"
          showIcon
          icon={<WalletOutlined />}
          action={
            <Button size="small" onClick={() => (window.location.href = '/')}>
              前往首页
            </Button>
          }
        />
      </div>
    )
  }

  // 用户加载中
  if (isUserLoading) {
    return (
      <div style={{ padding: '100px', textAlign: 'center' }}>
        <Spin size="large" tip="加载用户信息中..." />
      </div>
    )
  }

  // 用户未注册
  if (!isRegistered || !userId) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="用户未注册"
          description="请先注册账户后再参与答题"
          type="warning"
          showIcon
          action={
            <Button
              type="primary"
              icon={<UserAddOutlined />}
              onClick={() => setRegisterModalVisible(true)}
            >
              立即注册
            </Button>
          }
        />

        {/* 注册弹窗 */}
        <RegisterModal
          visible={registerModalVisible}
          onClose={() => setRegisterModalVisible(false)}
          onSuccess={() => {
            setRegisterModalVisible(false)
            refreshUser()
          }}
        />
      </div>
    )
  }

  // Tabs 配置
  const tabItems = [
    {
      key: 'quiz',
      label: (
        <span>
          <QuestionCircleOutlined />
          答题
        </span>
      ),
      children: (
        <div>
          {/* 每日限制提示 */}
          {dailyLimit && !quizFinished && (
            <Alert
              message={
                <Space>
                  <span>
                    今日答题进度: {dailyLimit.today_count} / {dailyLimit.daily_limit}
                  </span>
                  <span style={{ color: '#999' }}>
                    剩余: {dailyLimit.remaining_count} 题
                  </span>
                </Space>
              }
              type={dailyLimit.can_answer ? 'info' : 'warning'}
              showIcon
              style={{ marginBottom: 24 }}
            />
          )}

          {/* 答题完成页面 */}
          {quizFinished ? (
            <Card
              style={{
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: 16
              }}
            >
              <Result
                icon={
                  <div style={{ fontSize: 72 }}>
                    <TrophyOutlined style={{ color: '#ffd700' }} />
                  </div>
                }
                title={
                  <div style={{ fontSize: 28, fontWeight: 600, color: '#fff' }}>
                    🎉 今日答题已完成！
                  </div>
                }
                subTitle={
                  <div style={{ fontSize: 16, color: 'rgba(255, 255, 255, 0.6)', marginTop: 16 }}>
                    {dailyLimit && (
                      <Space direction="vertical" size={8}>
                        <div>
                          已完成 <span style={{ color: '#4ecdc4', fontWeight: 600, fontSize: 18 }}>{dailyLimit.today_count}</span> 题答题
                        </div>
                        <div style={{ fontSize: 14, color: 'rgba(255, 255, 255, 0.4)' }}>
                          明天再来挑战更多题目吧！
                        </div>
                      </Space>
                    )}
                  </div>
                }
                extra={[
                  <Button
                    key="statistics"
                    type="primary"
                    size="large"
                    icon={<BarChartOutlined />}
                    onClick={() => setActiveTab('statistics')}
                    style={{
                      height: 48,
                      fontSize: 16,
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      border: 'none'
                    }}
                  >
                    查看统计
                  </Button>,
                  <Button
                    key="history"
                    size="large"
                    icon={<HistoryOutlined />}
                    onClick={() => setActiveTab('history')}
                    style={{
                      height: 48,
                      fontSize: 16
                    }}
                  >
                    答题历史
                  </Button>
                ]}
              />

              {/* 每日完成信息 */}
              <div style={{ marginTop: 32, textAlign: 'center' }}>
                <Space direction="vertical" size={16} style={{ width: '100%' }}>
                  <Alert
                    message={
                      <Space>
                        <CheckCircleOutlined style={{ color: '#52c41a' }} />
                        <span>今日答题任务已完成</span>
                      </Space>
                    }
                    type="success"
                    showIcon={false}
                    style={{
                      background: 'rgba(82, 196, 26, 0.1)',
                      border: '1px solid rgba(82, 196, 26, 0.3)'
                    }}
                  />
                  <div style={{ color: 'rgba(255, 255, 255, 0.4)', fontSize: 14 }}>
                    每日答题将在北京时间 00:00 重置
                  </div>
                </Space>
              </div>
            </Card>
          ) : (
            <>
              {/* 答题卡片 */}
              <QuizCard
                question={currentQuestion}
                loading={loadingQuestion}
                submitting={submitting}
                onSubmit={handleSubmitAnswer}
                result={answerResult}
                onNext={handleNextQuestion}
              />

              {/* 刷新按钮 */}
              <div style={{ textAlign: 'center', marginTop: 16 }}>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={handleRefresh}
                  disabled={loadingQuestion || submitting}
                >
                  刷新
                </Button>
              </div>
            </>
          )}
        </div>
      )
    },
    {
      key: 'statistics',
      label: (
        <span>
          <BarChartOutlined />
          统计
        </span>
      ),
      children: <QuizStatisticsComponent key={`stats-${refreshKey}`} userId={userId} />
    },
    {
      key: 'history',
      label: (
        <span>
          <HistoryOutlined />
          历史记录
        </span>
      ),
      children: <QuizHistory key={`history-${refreshKey}`} userId={userId} />
    }
  ]

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 页面标题 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ margin: 0 }}>
            <QuestionCircleOutlined style={{ marginRight: 8 }} />
            每日答题
          </h1>
        </div>

        <Divider style={{ margin: '12px 0' }} />

        {/* Tab 切换 */}
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          destroyInactiveTabPane={false}
        />
      </Space>
    </div>
  )
}

export default Quiz
