import { useState, useEffect } from 'react'
import { Input, Button, Space, message, QRCode, Tabs, Card } from 'antd'
import { CopyOutlined, LinkOutlined, QrcodeOutlined, ShareAltOutlined } from '@ant-design/icons'
import { useWeb3 } from '@/contexts/Web3Context'
import { referralApi } from '@/services/api'

/**
 * 推荐链接生成器组件
 */
function ReferralLinkGenerator() {
  const { account } = useWeb3()
  const [referralLink, setReferralLink] = useState('')
  const [inviteCode, setInviteCode] = useState('')

  // 自动生成推荐链接
  useEffect(() => {
    if (account) {
      generateLink()
    }
  }, [account])

  // 生成推荐链接
  const generateLink = async () => {
    if (!account) return

    try {
      const result = await referralApi.generateLink(account)
      setReferralLink(result.referral_link)
      setInviteCode(result.invite_code)
    } catch (error) {
      console.error('Failed to generate referral link:', error)
    }
  }

  // 复制链接
  const copyLink = () => {
    if (referralLink) {
      navigator.clipboard.writeText(referralLink)
      message.success('推荐链接已复制到剪贴板')
    }
  }

  // 复制邀请码
  const copyInviteCode = () => {
    if (inviteCode) {
      navigator.clipboard.writeText(inviteCode)
      message.success('邀请码已复制到剪贴板')
    }
  }

  // 分享到社交媒体
  const shareToSocial = (platform: 'twitter' | 'telegram' | 'discord') => {
    if (!referralLink) return

    const text = `🎁 加入RWA Referral赚取奖励！使用我的专属链接注册，立即开始：${referralLink}`

    let url = ''
    switch (platform) {
      case 'twitter':
        url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`
        break
      case 'telegram':
        url = `https://t.me/share/url?url=${encodeURIComponent(referralLink)}&text=${encodeURIComponent('加入RWA Referral赚取奖励！')}`
        break
      case 'discord':
        // Discord没有直接分享链接API，复制到剪贴板并提示用户
        navigator.clipboard.writeText(text)
        message.success('分享文本已复制到剪贴板，请在Discord中粘贴发送')
        return
    }

    window.open(url, '_blank')
  }

  const tabItems = [
    {
      key: 'link',
      label: (
        <span>
          <LinkOutlined /> 推荐链接
        </span>
      ),
      children: (
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          {/* 推荐链接 */}
          <Space.Compact style={{ width: '100%' }}>
            <Input
              size="large"
              value={referralLink}
              readOnly
              placeholder="生成中..."
              style={{
                height: 48,
                fontSize: 14,
                fontFamily: 'monospace'
              }}
            />
            <Button
              type="primary"
              size="large"
              icon={<CopyOutlined />}
              onClick={copyLink}
              disabled={!referralLink}
              style={{
                height: 48,
                minWidth: 100
              }}
            >
              复制
            </Button>
          </Space.Compact>

          {/* 邀请码 */}
          <div>
            <div style={{ marginBottom: 8, color: 'rgba(255, 255, 255, 0.6)', fontSize: 14 }}>
              邀请码
            </div>
            <Space.Compact style={{ width: '100%' }}>
              <Input
                size="large"
                value={inviteCode}
                readOnly
                placeholder="生成中..."
                style={{
                  height: 48,
                  fontSize: 20,
                  fontWeight: 600,
                  letterSpacing: 4,
                  textAlign: 'center',
                  fontFamily: 'monospace'
                }}
              />
              <Button
                type="primary"
                size="large"
                icon={<CopyOutlined />}
                onClick={copyInviteCode}
                disabled={!inviteCode}
                style={{
                  height: 48,
                  minWidth: 100
                }}
              >
                复制
              </Button>
            </Space.Compact>
          </div>
        </Space>
      )
    },
    {
      key: 'qrcode',
      label: (
        <span>
          <QrcodeOutlined /> 二维码
        </span>
      ),
      children: (
        <div style={{ textAlign: 'center', padding: '24px 0' }}>
          {referralLink ? (
            <Card
              style={{
                display: 'inline-block',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }}
              bodyStyle={{ padding: 16 }}
            >
              <QRCode
                value={referralLink}
                size={200}
                color="#fff"
                bgColor="transparent"
                bordered={false}
              />
              <div style={{ marginTop: 16, color: 'rgba(255, 255, 255, 0.6)', fontSize: 14 }}>
                扫描二维码访问推荐链接
              </div>
            </Card>
          ) : (
            <div style={{ color: 'rgba(255, 255, 255, 0.4)' }}>生成中...</div>
          )}
        </div>
      )
    },
    {
      key: 'share',
      label: (
        <span>
          <ShareAltOutlined /> 分享
        </span>
      ),
      children: (
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <div style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: 14 }}>
            一键分享到社交媒体
          </div>

          <Space size={12} style={{ width: '100%' }}>
            <Button
              block
              size="large"
              icon={
                <span style={{ fontSize: 18 }}>𝕏</span>
              }
              onClick={() => shareToSocial('twitter')}
              disabled={!referralLink}
              style={{
                height: 48,
                background: '#1DA1F2',
                borderColor: '#1DA1F2',
                color: '#fff'
              }}
            >
              Twitter
            </Button>

            <Button
              block
              size="large"
              icon={<span style={{ fontSize: 18 }}>✈️</span>}
              onClick={() => shareToSocial('telegram')}
              disabled={!referralLink}
              style={{
                height: 48,
                background: '#0088cc',
                borderColor: '#0088cc',
                color: '#fff'
              }}
            >
              Telegram
            </Button>

            <Button
              block
              size="large"
              icon={<span style={{ fontSize: 18 }}>💬</span>}
              onClick={() => shareToSocial('discord')}
              disabled={!referralLink}
              style={{
                height: 48,
                background: '#5865F2',
                borderColor: '#5865F2',
                color: '#fff'
              }}
            >
              Discord
            </Button>
          </Space>
        </Space>
      )
    }
  ]

  return (
    <div>
      <Tabs
        defaultActiveKey="link"
        items={tabItems}
        style={{
          color: '#fff'
        }}
      />
    </div>
  )
}

export default ReferralLinkGenerator
