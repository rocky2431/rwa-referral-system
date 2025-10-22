import { useState, useEffect } from 'react'
import { Input, Button, Space, Alert } from 'antd'
import { UserAddOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { useReferral } from '@/hooks/useReferral'
import { useReferralCode } from '@/contexts/ReferralContext'

/**
 * 推荐人输入组件
 * 用于绑定推荐关系 - 支持邀请码和钱包地址两种输入方式
 */
function ReferralInput() {
  const [referrerInput, setReferrerInput] = useState('')
  const [validationError, setValidationError] = useState<string | null>(null)
  const { bindReferrer, bindReferrerByCode, validateReferrerAddress, loading } = useReferral()
  const { inviteCode, clearInviteCode } = useReferralCode()

  // 自动填充URL中的邀请码
  useEffect(() => {
    if (inviteCode && !referrerInput) {
      setReferrerInput(inviteCode)
    }
  }, [inviteCode])

  // 检测输入类型：邀请码 (USER000001) 或钱包地址 (0x...)
  const detectInputType = (input: string): 'invite_code' | 'wallet_address' | 'invalid' => {
    if (!input) return 'invalid'

    // 检查是否是邀请码格式 (USER + 6位数字)
    if (/^USER\d{6}$/i.test(input)) {
      return 'invite_code'
    }

    // 检查是否是钱包地址格式 (0x + 40位十六进制)
    if (/^0x[a-fA-F0-9]{40}$/.test(input)) {
      return 'wallet_address'
    }

    return 'invalid'
  }

  // 处理输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.trim()
    setReferrerInput(value)

    // 实时验证
    if (value) {
      const inputType = detectInputType(value)

      if (inputType === 'invite_code') {
        setValidationError(null) // 邀请码格式正确
      } else if (inputType === 'wallet_address') {
        const validation = validateReferrerAddress(value)
        setValidationError(validation.valid ? null : validation.error || null)
      } else {
        setValidationError('请输入有效的邀请码(USER000001)或钱包地址(0x...)')
      }
    } else {
      setValidationError(null)
    }
  }

  // 处理绑定
  const handleBind = async () => {
    if (!referrerInput) {
      setValidationError('请输入邀请码或推荐人钱包地址')
      return
    }

    const inputType = detectInputType(referrerInput)

    if (inputType === 'invalid') {
      setValidationError('请输入有效的邀请码(USER000001)或钱包地址(0x...)')
      return
    }

    let success = false

    if (inputType === 'invite_code') {
      // 使用邀请码绑定
      success = await bindReferrerByCode(referrerInput.toUpperCase())
    } else {
      // 使用钱包地址绑定
      const validation = validateReferrerAddress(referrerInput)
      if (!validation.valid) {
        setValidationError(validation.error || '地址验证失败')
        return
      }
      success = await bindReferrer(referrerInput)
    }

    if (success) {
      setReferrerInput('')
      setValidationError(null)
      clearInviteCode() // 清除已保存的邀请码
    }
  }

  return (
    <Space direction="vertical" size={12} style={{ width: '100%' }}>
      {/* 输入框 */}
      <Space.Compact style={{ width: '100%' }}>
        <Input
          size="large"
          placeholder="输入邀请码（USER000001）或推荐人钱包地址（0x...）"
          value={referrerInput}
          onChange={handleInputChange}
          status={validationError ? 'error' : undefined}
          prefix={<UserAddOutlined style={{ color: 'rgba(255, 255, 255, 0.3)' }} />}
          style={{
            height: 48,
            fontSize: 14,
            fontFamily: 'monospace'
          }}
          onPressEnter={handleBind}
        />
        <Button
          type="primary"
          size="large"
          icon={<CheckCircleOutlined />}
          loading={loading}
          onClick={handleBind}
          disabled={!!validationError || !referrerInput}
          style={{
            height: 48,
            minWidth: 120
          }}
        >
          {loading ? '绑定中...' : '绑定'}
        </Button>
      </Space.Compact>

      {/* 错误提示 */}
      {validationError && (
        <Alert
          message={validationError}
          type="error"
          showIcon
          closable
          onClose={() => setValidationError(null)}
        />
      )}

      {/* URL邀请码提示 */}
      {inviteCode && (
        <Alert
          message="检测到邀请码"
          description={`已自动填入邀请码: ${inviteCode}，点击"绑定"按钮完成绑定`}
          type="success"
          showIcon
          closable
          onClose={() => {
            clearInviteCode()
            setReferrerInput('')
          }}
        />
      )}

      {/* 说明文字 */}
      <Alert
        message="提示"
        description={
          <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
            <li>支持两种绑定方式：邀请码（如 USER000001）或钱包地址（如 0x...）</li>
            <li>每个地址只能绑定一次推荐人，请谨慎操作</li>
            <li>不能推荐自己或形成循环推荐</li>
            <li>绑定后，您的推荐人将获得您的推荐奖励</li>
          </ul>
        }
        type="info"
        showIcon
      />
    </Space>
  )
}

export default ReferralInput
