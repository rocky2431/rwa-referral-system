import React, { useState, useEffect } from 'react'
import { Alert, Space, message } from 'antd'
import { QuizCard } from './QuizCard'
import { quizApi } from '@/services/api'
import type { QuestionResponse, AnswerResult, DailyLimit } from '@/services/api'

/**
 * QuizAnswer 组件属性
 */
interface QuizAnswerProps {
  /** 用户ID */
  userId: number
  /** 刷新回调（用于更新外部统计数据） */
  onRefresh?: () => void
  /** 自动加载第一题（默认true） */
  autoLoad?: boolean
}

/**
 * 答题交互组件
 *
 * 封装完整的答题逻辑和状态管理，包括：
 * - 题目加载
 * - 答案提交
 * - 每日限制检查
 * - 结果展示
 *
 * 设计原则：
 * - SRP：专注于答题交互逻辑，UI展示委托给QuizCard
 * - DRY：封装可复用的答题逻辑，避免在多个页面重复
 * - KISS：提供简洁的props接口，内部处理所有复杂逻辑
 */
export const QuizAnswer: React.FC<QuizAnswerProps> = ({
  userId,
  onRefresh,
  autoLoad = true
}) => {
  // ==================== 状态管理 ====================

  /** 当前题目 */
  const [currentQuestion, setCurrentQuestion] = useState<QuestionResponse | null>(null)

  /** 答题结果 */
  const [answerResult, setAnswerResult] = useState<AnswerResult | null>(null)

  /** 题目加载中 */
  const [loadingQuestion, setLoadingQuestion] = useState(false)

  /** 提交答案中 */
  const [submitting, setSubmitting] = useState(false)

  /** 每日答题限制 */
  const [dailyLimit, setDailyLimit] = useState<DailyLimit | null>(null)

  // ==================== 业务逻辑 ====================

  /**
   * 检查每日答题限制
   * @returns 是否可以继续答题
   */
  const checkDailyLimit = async (): Promise<boolean> => {
    try {
      const limit = await quizApi.checkDailyLimit(userId)
      setDailyLimit(limit)
      return limit.can_answer
    } catch (error) {
      console.error('检查每日限制失败:', error)
      message.error('检查答题限制失败，请稍后重试')
      return false
    }
  }

  /**
   * 加载随机题目
   */
  const loadRandomQuestion = async () => {
    setLoadingQuestion(true)
    setAnswerResult(null) // 清空上一题的结果

    try {
      // 检查每日限制
      const canAnswer = await checkDailyLimit()
      if (!canAnswer) {
        message.warning('今日答题次数已达上限，请明天再来！')
        return
      }

      // 获取随机题目
      const question = await quizApi.getRandomQuestion(userId)
      setCurrentQuestion(question)
    } catch (error: any) {
      console.error('加载题目失败:', error)
      message.error(error.message || '加载题目失败，请稍后重试')
    } finally {
      setLoadingQuestion(false)
    }
  }

  /**
   * 提交答案
   * @param userAnswer 用户选择的答案（A/B/C/D）
   * @param answerTime 答题用时（秒）
   */
  const handleSubmitAnswer = async (userAnswer: string, answerTime: number) => {
    if (!currentQuestion) {
      message.error('题目加载失败，请刷新重试')
      return
    }

    setSubmitting(true)

    try {
      // 提交答案到后端
      const result = await quizApi.submitAnswer(userId, {
        question_id: currentQuestion.id,
        user_answer: userAnswer,
        answer_time: answerTime
      })

      setAnswerResult(result)

      // 通知外部刷新统计数据
      onRefresh?.()

      // 答对时显示成功消息
      if (result.is_correct) {
        message.success(`🎉 回答正确！获得 ${result.points_earned} 积分`)
      } else {
        message.info(`正确答案是 ${result.correct_answer}`)
      }
    } catch (error: any) {
      console.error('提交答案失败:', error)
      message.error(error.message || '提交答案失败，请稍后重试')
    } finally {
      setSubmitting(false)
    }
  }

  /**
   * 继续下一题
   */
  const handleNextQuestion = () => {
    loadRandomQuestion()
  }

  // ==================== 生命周期 ====================

  /**
   * 组件挂载时自动加载第一题
   */
  useEffect(() => {
    if (autoLoad && userId) {
      loadRandomQuestion()
    }
  }, [userId, autoLoad])

  // ==================== 渲染 ====================

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* 每日限制提示 */}
      {dailyLimit && (
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
          description={
            !dailyLimit.can_answer && `下次重置时间: ${new Date(dailyLimit.next_reset_time).toLocaleString()}`
          }
          showIcon
        />
      )}

      {/* 答题卡片 */}
      <QuizCard
        question={currentQuestion}
        loading={loadingQuestion}
        submitting={submitting}
        onSubmit={handleSubmitAnswer}
        result={answerResult}
        onNext={handleNextQuestion}
      />
    </Space>
  )
}

export default QuizAnswer
