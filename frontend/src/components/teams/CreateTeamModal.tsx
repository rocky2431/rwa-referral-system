import React, { useState, useEffect } from 'react'
import { Modal, Form, Input, InputNumber, Switch, Button, Space, Alert, message } from 'antd'
import {
  TeamOutlined,
  PictureOutlined,
  UserOutlined,
  LockOutlined,
  SafetyOutlined
} from '@ant-design/icons'
import type { TeamCreateRequest } from '@/services/api'
import { teamsApi } from '@/services/api'

/**
 * CreateTeamModal 组件属性
 */
interface CreateTeamModalProps {
  /** 弹窗是否可见 */
  visible: boolean
  /** 队长用户ID */
  captainId: number
  /** 关闭回调 */
  onClose: () => void
  /** 创建成功回调 */
  onSuccess?: (teamId: number) => void
}

/**
 * 创建战队弹窗组件
 *
 * 提供战队创建表单，包括：
 * - 战队名称（必填）
 * - 战队描述（可选）
 * - Logo URL（可选）
 * - 是否公开（默认公开）
 * - 是否需要审批（默认不需要）
 * - 最大成员数（默认50）
 *
 * 设计原则：
 * - SRP：只负责战队创建表单的UI交互
 * - KISS：简单清晰的表单布局和提交流程
 * - DRY：复用 Ant Design 表单组件和验证规则
 *
 * @example
 * ```tsx
 * <CreateTeamModal
 *   visible={visible}
 *   captainId={userId}
 *   onClose={() => setVisible(false)}
 *   onSuccess={(teamId) => {
 *     message.success('战队创建成功！')
 *     navigate(`/teams/${teamId}`)
 *   }}
 * />
 * ```
 */
export const CreateTeamModal: React.FC<CreateTeamModalProps> = ({
  visible,
  captainId,
  onClose,
  onSuccess
}) => {
  // ==================== 状态管理 ====================

  /** 表单实例 */
  const [form] = Form.useForm<TeamCreateRequest>()

  /** 创建中 */
  const [creating, setCreating] = useState(false)

  /** 错误信息 */
  const [error, setError] = useState<string | null>(null)

  // ==================== 生命周期 ====================

  /**
   * 弹窗关闭时重置表单
   */
  useEffect(() => {
    if (!visible) {
      form.resetFields()
      setCreating(false)
      setError(null)
    }
  }, [visible, form])

  // ==================== 业务逻辑 ====================

  /**
   * 提交创建战队
   */
  const handleSubmit = async () => {
    setError(null)

    try {
      // 验证表单
      const values = await form.validateFields()

      setCreating(true)

      // 调用API创建战队
      const newTeam = await teamsApi.create(captainId, values)

      // 成功提示
      message.success(`战队 "${newTeam.name}" 创建成功！`)

      // 调用成功回调
      onSuccess?.(newTeam.id)

      // 关闭弹窗
      onClose()
    } catch (err: any) {
      console.error('创建战队失败:', err)

      // 显示错误信息
      if (err.message) {
        setError(err.message)
      } else if (err.errorFields) {
        // 表单验证失败
        message.warning('请检查表单输入')
      } else {
        setError('创建战队失败，请稍后重试')
      }
    } finally {
      setCreating(false)
    }
  }

  // ==================== 渲染 ====================

  return (
    <Modal
      title={
        <Space>
          <TeamOutlined />
          <span>创建战队</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={600}
      bodyStyle={{ padding: '24px' }}
      maskClosable={false}
    >
      {/* 欢迎提示 */}
      <div style={{ marginBottom: 16 }}>
        <Alert
          message="创建你的战队"
          description="组建战队，与队友一起完成任务、赢取奖励！战队创建后你将成为队长。"
          type="info"
          showIcon
        />
      </div>

      {/* 错误提示 */}
      {error && (
        <Alert
          message="创建失败"
          description={error}
          type="error"
          showIcon
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 创建表单 */}
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        autoComplete="off"
        initialValues={{
          is_public: true,
          require_approval: false,
          max_members: 50
        }}
      >
        {/* 战队名称（必填） */}
        <Form.Item
          label="战队名称"
          name="name"
          rules={[
            { required: true, message: '请输入战队名称' },
            { min: 2, message: '战队名称至少2个字符' },
            { max: 50, message: '战队名称最多50个字符' },
            {
              pattern: /^[a-zA-Z0-9\u4e00-\u9fa5_-]+$/,
              message: '只能包含中英文、数字、下划线和横线'
            }
          ]}
          extra="2-50个字符，支持中英文、数字、下划线和横线"
        >
          <Input
            prefix={<TeamOutlined />}
            placeholder="输入一个响亮的战队名称"
            maxLength={50}
            showCount
            allowClear
          />
        </Form.Item>

        {/* 战队描述（可选） */}
        <Form.Item
          label="战队描述"
          name="description"
          rules={[
            { max: 200, message: '描述最多200个字符' }
          ]}
          extra="选填，介绍你的战队理念和目标"
        >
          <Input.TextArea
            placeholder="战队宗旨、招募要求、活动安排等..."
            maxLength={200}
            showCount
            rows={4}
            allowClear
          />
        </Form.Item>

        {/* Logo URL（可选） */}
        <Form.Item
          label="战队Logo"
          name="logo_url"
          rules={[
            { type: 'url', message: '请输入有效的URL地址' }
          ]}
          extra="选填，可以使用图床链接或CDN地址"
        >
          <Input
            prefix={<PictureOutlined />}
            placeholder="https://example.com/logo.png（可选）"
            allowClear
          />
        </Form.Item>

        {/* 最大成员数 */}
        <Form.Item
          label="成员上限"
          name="max_members"
          rules={[
            { required: true, message: '请设置成员上限' },
            { type: 'number', min: 5, message: '至少需要5个成员名额' },
            { type: 'number', max: 200, message: '最多支持200个成员' }
          ]}
          extra="设置战队的最大成员数（5-200人）"
        >
          <InputNumber
            prefix={<UserOutlined />}
            placeholder="50"
            min={5}
            max={200}
            step={5}
            style={{ width: '100%' }}
          />
        </Form.Item>

        {/* 是否公开 */}
        <Form.Item
          label="战队类型"
          name="is_public"
          valuePropName="checked"
          extra="公开战队可被所有用户搜索和加入，私密战队只能通过邀请加入"
        >
          <Switch
            checkedChildren={<Space><SafetyOutlined />公开</Space>}
            unCheckedChildren={<Space><LockOutlined />私密</Space>}
          />
        </Form.Item>

        {/* 是否需要审批 */}
        <Form.Item
          label="加入审批"
          name="require_approval"
          valuePropName="checked"
          extra="开启后，用户申请加入需要队长或管理员审批"
        >
          <Switch
            checkedChildren="需要审批"
            unCheckedChildren="自由加入"
          />
        </Form.Item>

        {/* 提交按钮 */}
        <Form.Item style={{ marginBottom: 0, marginTop: 32 }}>
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button onClick={onClose} disabled={creating}>
              取消
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={creating}
              icon={<TeamOutlined />}
              size="large"
            >
              {creating ? '创建中...' : '立即创建'}
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default CreateTeamModal
