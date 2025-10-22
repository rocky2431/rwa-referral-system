import React, { useState, useEffect } from 'react'
import { Table, Tag, Select, Space } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import type { UserAnswerDetailResponse } from '@/services/api'
import { quizApi, QuestionDifficulty } from '@/services/api'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { Option } = Select

interface QuizHistoryProps {
  userId: number
}

/**
 * 答题历史组件
 * 显示用户的答题记录
 */
export const QuizHistory: React.FC<QuizHistoryProps> = ({ userId }) => {
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<UserAnswerDetailResponse[]>([])
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [isCorrectFilter, setIsCorrectFilter] = useState<boolean | undefined>(undefined)
  const [difficultyFilter, setDifficultyFilter] = useState<QuestionDifficulty | undefined>(
    undefined
  )

  // 加载答题历史
  const loadHistory = async () => {
    setLoading(true)
    try {
      const response = await quizApi.getUserAnswers(
        userId,
        currentPage,
        pageSize,
        isCorrectFilter,
        difficultyFilter
      )
      setHistory(response.data)
      setTotal(response.total)
    } catch (error) {
      console.error('加载答题历史失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHistory()
  }, [userId, currentPage, pageSize, isCorrectFilter, difficultyFilter])

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

  // 表格列定义
  const columns = [
    {
      title: '题目',
      dataIndex: 'question_text',
      key: 'question_text',
      width: '30%',
      ellipsis: true
    },
    {
      title: '难度',
      dataIndex: 'difficulty',
      key: 'difficulty',
      width: 80,
      render: (difficulty: QuestionDifficulty) => (
        <Tag color={difficultyConfig[difficulty]?.color}>
          {difficultyConfig[difficulty]?.label}
        </Tag>
      )
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (category: string) => (category ? <Tag color="blue">{category}</Tag> : '-')
    },
    {
      title: '你的答案',
      dataIndex: 'user_answer',
      key: 'user_answer',
      width: 80,
      align: 'center' as const,
      render: (answer: string) => (
        <Tag style={{ fontWeight: 600, fontSize: 14 }}>{answer}</Tag>
      )
    },
    {
      title: '正确答案',
      dataIndex: 'correct_answer',
      key: 'correct_answer',
      width: 80,
      align: 'center' as const,
      render: (answer: string) =>
        answer ? <Tag color="green" style={{ fontWeight: 600, fontSize: 14 }}>{answer}</Tag> : '-'
    },
    {
      title: '结果',
      dataIndex: 'is_correct',
      key: 'is_correct',
      width: 80,
      align: 'center' as const,
      render: (isCorrect: boolean) =>
        isCorrect ? (
          <Tag icon={<CheckCircleOutlined />} color="success">
            正确
          </Tag>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="error">
            错误
          </Tag>
        )
    },
    {
      title: '获得积分',
      dataIndex: 'points_earned',
      key: 'points_earned',
      width: 100,
      align: 'center' as const,
      render: (points: number) => (
        <span style={{ color: points > 0 ? '#52c41a' : '#999', fontWeight: 600 }}>
          {points > 0 ? `+${points}` : 0}
        </span>
      )
    },
    {
      title: '答题时间',
      dataIndex: 'answer_time',
      key: 'answer_time',
      width: 100,
      align: 'center' as const,
      render: (time: number) => (time ? `${time}秒` : '-')
    },
    {
      title: '答题时刻',
      dataIndex: 'answered_at',
      key: 'answered_at',
      width: 180,
      render: (date: string) => (
        <div>
          <div>{dayjs(date).format('YYYY-MM-DD HH:mm')}</div>
          <div style={{ fontSize: 12, color: '#999' }}>{dayjs(date).fromNow()}</div>
        </div>
      )
    }
  ]

  return (
    <div>
      {/* 筛选栏 */}
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Select
            placeholder="答题结果"
            style={{ width: 120 }}
            allowClear
            value={isCorrectFilter}
            onChange={setIsCorrectFilter}
          >
            <Option value={true}>正确</Option>
            <Option value={false}>错误</Option>
          </Select>

          <Select
            placeholder="题目难度"
            style={{ width: 120 }}
            allowClear
            value={difficultyFilter}
            onChange={setDifficultyFilter}
          >
            <Option value={QuestionDifficulty.EASY}>简单</Option>
            <Option value={QuestionDifficulty.MEDIUM}>中等</Option>
            <Option value={QuestionDifficulty.HARD}>困难</Option>
          </Select>
        </Space>
      </div>

      {/* 答题历史表格 */}
      <Table
        columns={columns}
        dataSource={history}
        loading={loading}
        rowKey="id"
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`,
          onChange: (page, size) => {
            setCurrentPage(page)
            setPageSize(size || 20)
          }
        }}
        scroll={{ x: 1200 }}
      />
    </div>
  )
}

export default QuizHistory
