import React, { useState, useEffect } from 'react'
import { Space, Select, Button, Empty, message, Spin, Alert, Tabs } from 'antd'
import {
  SyncOutlined,
  AppstoreAddOutlined,
  WalletOutlined,
  UserAddOutlined
} from '@ant-design/icons'
import { useWeb3 } from '@/contexts/Web3Context'
import { useUser } from '@/hooks/useUser'
import { tasksApi, teamsApi, TaskType, type TaskResponse } from '@/services/api'
import { AvailableTaskCard } from '@/components/tasks/AvailableTaskCard'
import { RegisterModal } from '@/components/user/RegisterModal'

const { Option } = Select

/**
 * 任务中心页面 - 展示所有可领取的任务
 */
const TaskCenter: React.FC = () => {
  const { isConnected } = useWeb3()
  const { userId, isRegistered, isLoading: isUserLoading, refreshUser } = useUser()

  const [loading, setLoading] = useState(false)
  const [tasks, setTasks] = useState<TaskResponse[]>([])
  const [total, setTotal] = useState(0)
  const [typeFilter, setTypeFilter] = useState<TaskType | undefined>(undefined)
  const [claimingTaskId, setClaimingTaskId] = useState<number | null>(null)
  const [userTaskIds, setUserTaskIds] = useState<Set<number>>(new Set())
  const [registerModalVisible, setRegisterModalVisible] = useState(false)
  const [hasTeam, setHasTeam] = useState(false)  // ✅ 新增:用户是否已有战队

  // 加载所有可用任务
  const loadTasks = async () => {
    setLoading(true)
    try {
      const response = await tasksApi.getList(
        1,
        100,
        typeFilter,
        true,  // 只显示激活的任务
        true   // 只显示可见的任务
      )
      setTasks(response.data)
      setTotal(response.total)

      // 如果用户已登录,加载已领取的任务ID和战队状态
      if (userId) {
        try {
          // 并行加载用户任务和战队信息
          const [userTasksResponse, userTeam] = await Promise.all([
            tasksApi.getUserTasks(userId, 1, 100),
            teamsApi.getUserTeam(userId).catch(() => null)  // ✅ 如果用户无战队,返回null而非抛出错误
          ])

          const taskIds = new Set(userTasksResponse.data.map(ut => ut.task_id))
          setUserTaskIds(taskIds)

          // ✅ 设置用户是否已有战队
          setHasTeam(!!userTeam)
        } catch (error) {
          console.error('加载已领取任务失败:', error)
        }
      } else {
        // 未登录时重置战队状态
        setHasTeam(false)
      }
    } catch (error) {
      console.error('加载任务列表失败:', error)
      message.error('加载任务列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTasks()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [typeFilter, userId])  // ✅ 只依赖typeFilter和userId,避免循环

  // ✅ 辅助函数:判断任务是否应该禁用
  const isTaskDisabled = (task: TaskResponse): boolean => {
    // 如果用户已有战队,禁用"加入战队"和"创建战队"任务
    if (hasTeam && (task.task_key === 'join_team' || task.task_key === 'create_team')) {
      return true
    }
    return false
  }

  // ✅ 辅助函数:获取任务禁用原因
  const getDisabledReason = (task: TaskResponse): string | undefined => {
    if (hasTeam && (task.task_key === 'join_team' || task.task_key === 'create_team')) {
      return '您已在战队中,无法领取此任务'
    }
    return undefined
  }

  // 领取任务
  const handleClaimTask = async (taskId: number) => {
    if (!userId) {
      message.warning('请先注册账户')
      setRegisterModalVisible(true)
      return
    }

    // ✅ 检查战队相关任务的前置条件
    const task = tasks.find(t => t.id === taskId)
    if (task) {
      // 如果是"加入战队"或"创建战队"任务,检查用户是否已有战队
      if ((task.task_key === 'join_team' || task.task_key === 'create_team') && hasTeam) {
        message.warning('您已在战队中,无法领取此任务')
        return
      }
    }

    setClaimingTaskId(taskId)
    try {
      await tasksApi.assignToUser(userId, taskId)
      message.success('任务领取成功!')
      // 添加到已领取集合
      setUserTaskIds(prev => new Set([...prev, taskId]))
      loadTasks()
    } catch (error: any) {
      console.error('领取任务失败:', error)
      message.error(error.response?.data?.detail || '领取任务失败')
    } finally {
      setClaimingTaskId(null)
    }
  }

  // 未连接钱包提示
  if (!isConnected) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="请先连接钱包"
          description="浏览任务中心需要先连接您的Web3钱包"
          type="warning"
          showIcon
          icon={<WalletOutlined />}
          action={
            <Button size="small" onClick={() => window.location.href = '/'}>
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

  // 未注册提示（但允许浏览任务）
  const notRegisteredAlert = !isRegistered && (
    <Alert
      message="您还未注册"
      description="注册后即可领取任务并获得奖励"
      type="info"
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
      style={{ marginBottom: 16 }}
    />
  )

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 页面标题 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ margin: 0 }}>
            <AppstoreAddOutlined style={{ marginRight: 8 }} />
            任务中心
          </h1>
          <Button icon={<SyncOutlined />} onClick={loadTasks} loading={loading}>
            刷新
          </Button>
        </div>

        {/* 未注册提示 */}
        {notRegisteredAlert}

        {/* 筛选栏 */}
        <div>
          <Select
            placeholder="任务类型"
            style={{ width: 200 }}
            allowClear
            value={typeFilter}
            onChange={setTypeFilter}
          >
            <Option value={TaskType.DAILY}>每日任务</Option>
            <Option value={TaskType.WEEKLY}>每周任务</Option>
            <Option value={TaskType.ONCE}>一次性任务</Option>
            <Option value={TaskType.TEAM}>战队任务</Option>
          </Select>
        </div>

        {/* 任务列表 */}
        {loading && tasks.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" tip="加载中..." />
          </div>
        ) : tasks.length === 0 ? (
          <Empty description="暂无任务" />
        ) : (
          <Tabs
            defaultActiveKey="all"
            items={[
              {
                key: 'all',
                label: `全部任务 (${tasks.length})`,
                children: (
                  <div>
                    {tasks.map((task) => (
                      <AvailableTaskCard
                        key={task.id}
                        task={task}
                        onClaim={handleClaimTask}
                        claiming={claimingTaskId === task.id}
                        alreadyClaimed={userTaskIds.has(task.id)}
                        disabled={isTaskDisabled(task)}
                        disabledReason={getDisabledReason(task)}
                      />
                    ))}
                  </div>
                )
              },
              {
                key: 'unclaimed',
                label: `未领取 (${tasks.filter(t => !userTaskIds.has(t.id)).length})`,
                children: (
                  <div>
                    {tasks.filter(t => !userTaskIds.has(t.id)).map((task) => (
                      <AvailableTaskCard
                        key={task.id}
                        task={task}
                        onClaim={handleClaimTask}
                        claiming={claimingTaskId === task.id}
                        alreadyClaimed={false}
                        disabled={isTaskDisabled(task)}
                        disabledReason={getDisabledReason(task)}
                      />
                    ))}
                    {tasks.filter(t => !userTaskIds.has(t.id)).length === 0 && (
                      <Empty description="所有任务已领取" />
                    )}
                  </div>
                )
              },
              {
                key: 'claimed',
                label: `已领取 (${userTaskIds.size})`,
                children: (
                  <div>
                    {tasks.filter(t => userTaskIds.has(t.id)).map((task) => (
                      <AvailableTaskCard
                        key={task.id}
                        task={task}
                        onClaim={handleClaimTask}
                        claiming={claimingTaskId === task.id}
                        alreadyClaimed={true}
                        disabled={isTaskDisabled(task)}
                        disabledReason={getDisabledReason(task)}
                      />
                    ))}
                    {userTaskIds.size === 0 && (
                      <Empty description="暂未领取任何任务" />
                    )}
                  </div>
                )
              }
            ]}
          />
        )}
      </Space>

      {/* 注册弹窗 */}
      <RegisterModal
        visible={registerModalVisible}
        onClose={() => setRegisterModalVisible(false)}
        onSuccess={() => {
          setRegisterModalVisible(false)
          refreshUser()
          loadTasks()
        }}
      />
    </div>
  )
}

export default TaskCenter
