import React, { useState } from 'react'
import { Card, Radio, Button, Tag, Space, Progress, Statistic, message } from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  TrophyOutlined,
  ThunderboltOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons'
import type { QuestionResponse, AnswerResult } from '@/services/api'
import { QuestionDifficulty } from '@/services/api'

interface QuizCardProps {
  question: QuestionResponse | null
  loading?: boolean
  submitting?: boolean
  onSubmit?: (userAnswer: string, answerTime: number) => void
  result?: AnswerResult | null
  onNext?: () => void
}

/**
 * 答题卡片组件
 * 显示题目、选项和答题结果
 */
export const QuizCard: React.FC<QuizCardProps> = ({
  question,
  loading,
  submitting,
  onSubmit,
  result,
  onNext
}) => {
  const [selectedAnswer, setSelectedAnswer] = useState<string>('')
  const [startTime] = useState<number>(Date.now())

  // 难度配置
  const difficultyConfig = {
    [QuestionDifficulty.EASY]: {
      label: '简单',
      color: 'green'
    },
    [QuestionDifficulty.MEDIUM]: {
      label: '中等',
      color: 'orange'
    },
    [QuestionDifficulty.HARD]: {
      label: '困难',
      color: 'red'
    }
  }

  // 提交答案
  const handleSubmit = () => {
    if (!selectedAnswer) {
      message.warning('请先选择一个答案')
      return
    }

    const answerTime = Math.floor((Date.now() - startTime) / 1000)
    onSubmit?.(selectedAnswer, answerTime)
  }

  // 继续下一题
  const handleNext = () => {
    setSelectedAnswer('')
    onNext?.()
  }

  // 获取选项列表
  const getOptions = () => {
    if (!question) return []

    const options = [
      { value: 'A', label: question.option_a },
      { value: 'B', label: question.option_b }
    ]

    if (question.option_c) {
      options.push({ value: 'C', label: question.option_c })
    }

    if (question.option_d) {
      options.push({ value: 'D', label: question.option_d })
    }

    return options
  }

  return (
    <Card
      loading={loading}
      title={
        <Space>
          <QuestionCircleOutlined />
          <span>答题卡</span>
        </Space>
      }
      extra={
        question && (
          <Tag color={difficultyConfig[question.difficulty].color}>
            {difficultyConfig[question.difficulty].label}
          </Tag>
        )
      }
      style={{ marginBottom: 24 }}
    >
      {question && (
        <>
          {/* 题目信息 */}
          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>
              {question.question_text}
            </div>

            {question.category && (
              <Tag color="blue" style={{ marginBottom: 8 }}>
                {question.category}
              </Tag>
            )}

            <div style={{ display: 'flex', gap: 16, marginTop: 16 }}>
              <Statistic
                title="奖励积分"
                value={question.reward_points}
                prefix={<TrophyOutlined />}
                valueStyle={{ fontSize: 20 }}
              />
              <Statistic
                title="正确率"
                value={question.accuracy_rate}
                suffix="%"
                valueStyle={{ fontSize: 20 }}
              />
              <Statistic
                title="答题次数"
                value={question.times_answered}
                valueStyle={{ fontSize: 20 }}
              />
            </div>
          </div>

          {/* 选项 */}
          {!result && (
            <div style={{ marginBottom: 24 }}>
              <Radio.Group
                value={selectedAnswer}
                onChange={(e) => setSelectedAnswer(e.target.value)}
                style={{ width: '100%' }}
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  {getOptions().map((option) => (
                    <Radio
                      key={option.value}
                      value={option.value}
                      style={{
                        width: '100%',
                        padding: '12px',
                        border: '1px solid #d9d9d9',
                        borderRadius: 8,
                        marginBottom: 8
                      }}
                    >
                      <span style={{ fontWeight: 600, marginRight: 8 }}>{option.value}.</span>
                      {option.label}
                    </Radio>
                  ))}
                </Space>
              </Radio.Group>

              {question.hint && (
                <div
                  style={{
                    marginTop: 16,
                    padding: 12,
                    background: '#f0f5ff',
                    borderRadius: 8,
                    fontSize: 14
                  }}
                >
                  <ThunderboltOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                  提示: {question.hint}
                </div>
              )}
            </div>
          )}

          {/* 答题结果 */}
          {result && (
            <div style={{ marginBottom: 24 }}>
              <div
                style={{
                  padding: 24,
                  background: result.is_correct ? '#f6ffed' : '#fff2f0',
                  border: `2px solid ${result.is_correct ? '#52c41a' : '#ff4d4f'}`,
                  borderRadius: 12,
                  marginBottom: 16
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: 16
                  }}
                >
                  {result.is_correct ? (
                    <>
                      <CheckCircleOutlined
                        style={{ fontSize: 32, color: '#52c41a', marginRight: 12 }}
                      />
                      <div>
                        <div style={{ fontSize: 20, fontWeight: 600, color: '#52c41a' }}>
                          回答正确！
                        </div>
                        <div style={{ fontSize: 14, color: '#666', marginTop: 4 }}>
                          恭喜你获得 {result.points_earned} 积分
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      <CloseCircleOutlined
                        style={{ fontSize: 32, color: '#ff4d4f', marginRight: 12 }}
                      />
                      <div>
                        <div style={{ fontSize: 20, fontWeight: 600, color: '#ff4d4f' }}>
                          回答错误
                        </div>
                        <div style={{ fontSize: 14, color: '#666', marginTop: 4 }}>
                          正确答案是: {result.correct_answer}
                        </div>
                      </div>
                    </>
                  )}
                </div>

                {result.explanation && (
                  <div
                    style={{
                      padding: 12,
                      background: '#fff',
                      borderRadius: 8,
                      fontSize: 14
                    }}
                  >
                    <strong>解析:</strong> {result.explanation}
                  </div>
                )}

                {/* 连续答对天数 */}
                {result.streak_updated && (
                  <div style={{ marginTop: 16 }}>
                    <Tag icon={<ThunderboltOutlined />} color="gold" style={{ fontSize: 14 }}>
                      连续答对 {result.new_streak} 天！
                    </Tag>
                  </div>
                )}

                {/* 每日进度 */}
                <div style={{ marginTop: 16 }}>
                  <div style={{ marginBottom: 8, fontSize: 14, color: '#666' }}>
                    今日答题进度: {result.daily_count} / {result.daily_limit}
                  </div>
                  <Progress
                    percent={Math.round((result.daily_count / result.daily_limit) * 100)}
                    strokeColor={result.daily_count >= result.daily_limit ? '#52c41a' : '#1890ff'}
                  />
                </div>
              </div>
            </div>
          )}

          {/* 操作按钮 */}
          <div style={{ textAlign: 'center' }}>
            {!result ? (
              <Button
                type="primary"
                size="large"
                onClick={handleSubmit}
                loading={submitting}
                disabled={!selectedAnswer}
                style={{ minWidth: 120 }}
              >
                提交答案
              </Button>
            ) : (
              <Button type="primary" size="large" onClick={handleNext} style={{ minWidth: 120 }}>
                下一题
              </Button>
            )}
          </div>
        </>
      )}
    </Card>
  )
}

export default QuizCard
