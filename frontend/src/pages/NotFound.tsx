import { Button, Typography, Space } from 'antd'
import { HomeOutlined, SearchOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title, Paragraph } = Typography

/**
 * 404页面
 */
function NotFound() {
  const navigate = useNavigate()

  return (
    <div
      style={{
        minHeight: 'calc(100vh - 64px - 120px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
        textAlign: 'center'
      }}
    >
      <Space direction="vertical" size={24} style={{ maxWidth: 500 }}>
        {/* 404图标 */}
        <div>
          <Title
            level={1}
            style={{
              fontSize: 120,
              fontWeight: 800,
              margin: 0,
              background: 'linear-gradient(135deg, #ff6b35 0%, #ff006e 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              lineHeight: 1
            }}
          >
            404
          </Title>
        </div>

        {/* 描述 */}
        <Space direction="vertical" size={12}>
          <Title level={3} style={{ margin: 0 }}>
            页面未找到
          </Title>
          <Paragraph style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: 16, margin: 0 }}>
            抱歉，您访问的页面不存在或已被移除
          </Paragraph>
        </Space>

        {/* 操作按钮 */}
        <Space size={16}>
          <Button
            type="primary"
            size="large"
            icon={<HomeOutlined />}
            onClick={() => navigate('/')}
            style={{ height: 48, padding: '0 32px', fontSize: 16 }}
          >
            返回首页
          </Button>
          <Button
            size="large"
            icon={<SearchOutlined />}
            onClick={() => navigate('/leaderboard')}
            style={{ height: 48, padding: '0 32px', fontSize: 16 }}
          >
            查看排行榜
          </Button>
        </Space>

        {/* 装饰元素 */}
        <div
          style={{
            marginTop: 40,
            fontSize: 100,
            opacity: 0.1,
            userSelect: 'none'
          }}
        >
          🔍
        </div>
      </Space>
    </div>
  )
}

export default NotFound
