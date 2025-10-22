/**
 * RegisterModal - 用户注册弹窗组件
 *
 * 职责：提供用户注册表单UI
 *
 * 设计原则：
 * - SRP: 只负责注册UI交互，业务逻辑由useUser处理
 * - KISS: 简单直接的表单提交流程
 * - DRY: 复用useUser hook的registerNewUser方法
 */

import React, { useState, useEffect } from 'react'
import { Modal, Form, Input, Button, Space, Alert, message } from 'antd'
import {
  UserAddOutlined,
  UserOutlined,
  PictureOutlined
} from '@ant-design/icons'
import { useUser } from '@/hooks/useUser'
import { useReferral } from '@/hooks/useReferral'
import { useReferralCode } from '@/contexts/ReferralContext'

interface RegisterModalProps {
  visible: boolean
  onClose: () => void
  onSuccess?: () => void
}

/**
 * 用户注册弹窗
 */
export const RegisterModal: React.FC<RegisterModalProps> = ({
  visible,
  onClose,
  onSuccess
}) => {
  const { registerNewUser, isLoading, error } = useUser()
  const { bindReferrerByCode } = useReferral()
  const { inviteCode, clearInviteCode, markAsAutobound } = useReferralCode()
  const [form] = Form.useForm()
  const [registering, setRegistering] = useState(false)
  const [autoBinding, setAutoBinding] = useState(false)

  // 重置表单
  useEffect(() => {
    if (!visible) {
      form.resetFields()
      setRegistering(false)
      setAutoBinding(false)
    }
  }, [visible, form])

  // 提交注册
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setRegistering(true)

      const result = await registerNewUser(
        values.username || undefined,
        values.avatar_url || undefined
      )

      if (result) {
        message.success('注册成功！欢迎加入')

        // 注册成功后，检查是否需要自动绑定推荐人
        if (inviteCode) {
          setAutoBinding(true)
          try {
            const bindResult = await bindReferrerByCode(inviteCode)
            if (bindResult) {
              message.success('已自动绑定推荐人！')
              clearInviteCode()
              markAsAutobound()
            } else {
              message.warning('推荐人绑定失败，您可以稍后手动绑定')
            }
          } catch (err) {
            console.error('自动绑定推荐人失败:', err)
            message.warning('推荐人绑定失败，您可以稍后手动绑定')
          } finally {
            setAutoBinding(false)
          }
        }

        onSuccess?.()
        onClose()
      } else {
        message.error(error || '注册失败，请重试')
      }
    } catch (err) {
      console.error('表单验证失败:', err)
    } finally {
      setRegistering(false)
    }
  }

  return (
    <Modal
      title={
        <Space>
          <UserAddOutlined />
          <span>用户注册</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={500}
      bodyStyle={{ padding: '24px' }}
      maskClosable={false}
    >
      <div style={{ marginBottom: 16 }}>
        <Alert
          message="欢迎加入"
          description="完成注册后即可参与答题、组队、完成任务并获得积分奖励！"
          type="info"
          showIcon
        />
      </div>

      {/* 邀请码提示 */}
      {inviteCode && (
        <Alert
          message="检测到邀请码"
          description={`邀请码: ${inviteCode} - 注册成功后将自动绑定推荐人`}
          type="success"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 错误提示 */}
      {error && (
        <Alert
          message="注册失败"
          description={error}
          type="error"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        autoComplete="off"
      >
        {/* 用户名（可选） */}
        <Form.Item
          label="用户名"
          name="username"
          rules={[
            { min: 2, message: '用户名至少2个字符' },
            { max: 50, message: '用户名最多50个字符' }
          ]}
          extra="选填，留空将自动生成默认用户名"
        >
          <Input
            prefix={<UserOutlined />}
            placeholder="输入您的昵称（可选）"
            maxLength={50}
            allowClear
          />
        </Form.Item>

        {/* 头像URL（可选） */}
        <Form.Item
          label="头像URL"
          name="avatar_url"
          rules={[
            { type: 'url', message: '请输入有效的URL地址' }
          ]}
          extra="选填，可以使用您的社交媒体头像链接"
        >
          <Input
            prefix={<PictureOutlined />}
            placeholder="https://example.com/avatar.jpg（可选）"
            allowClear
          />
        </Form.Item>

        {/* 提交按钮 */}
        <Form.Item style={{ marginBottom: 0, marginTop: 24 }}>
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button onClick={onClose} disabled={registering || autoBinding}>
              取消
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={registering || isLoading || autoBinding}
              icon={<UserAddOutlined />}
            >
              {autoBinding ? '绑定推荐人中...' : registering ? '注册中...' : '立即注册'}
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default RegisterModal
