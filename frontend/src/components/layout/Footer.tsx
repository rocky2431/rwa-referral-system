import { Layout, Space, Typography } from 'antd'
import { GithubOutlined, TwitterOutlined, GlobalOutlined } from '@ant-design/icons'

const { Footer: AntFooter } = Layout
const { Text, Link } = Typography

/**
 * 底部组件
 */
function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <AntFooter
      style={{
        textAlign: 'center',
        padding: '24px 50px',
        background: 'rgba(5, 8, 20, 0.8)',
        borderTop: '1px solid rgba(255, 255, 255, 0.1)'
      }}
    >
      <Space direction="vertical" size={16} style={{ width: '100%' }}>
        {/* 社交链接 */}
        <Space size={24}>
          <Link href="https://github.com" target="_blank" style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
            <GithubOutlined style={{ fontSize: 20 }} />
          </Link>
          <Link href="https://twitter.com" target="_blank" style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
            <TwitterOutlined style={{ fontSize: 20 }} />
          </Link>
          <Link href="https://example.com" target="_blank" style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
            <GlobalOutlined style={{ fontSize: 20 }} />
          </Link>
        </Space>

        {/* 版权信息 */}
        <Text style={{ color: 'rgba(255, 255, 255, 0.4)', fontSize: 14 }}>
          © {currentYear} RWA Referral System. All rights reserved.
        </Text>

        {/* 技术栈 */}
        <Text style={{ color: 'rgba(255, 255, 255, 0.3)', fontSize: 12 }}>
          Powered by React + FastAPI + BSC
        </Text>
      </Space>
    </AntFooter>
  )
}

export default Footer
