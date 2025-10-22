import { Layout, Menu, Button, Space, Dropdown, Typography } from 'antd'
import { Link, useLocation } from 'react-router-dom'
import { WalletOutlined, DashboardOutlined, TrophyOutlined, UserOutlined, LogoutOutlined, GiftOutlined, TeamOutlined, CheckCircleOutlined, QuestionCircleOutlined, AppstoreAddOutlined } from '@ant-design/icons'
import { useWeb3 } from '@/contexts/Web3Context'
import type { MenuProps } from 'antd'

const { Header: AntHeader } = Layout
const { Text } = Typography

/**
 * 顶部导航栏组件
 */
function Header() {
  const location = useLocation()
  const { account, isConnected, isConnecting, connectWallet, disconnectWallet, chainId } = useWeb3()

  // 导航菜单项
  const menuItems: MenuProps['items'] = [
    {
      key: '/',
      icon: <WalletOutlined />,
      label: <Link to="/">首页</Link>
    },
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: <Link to="/dashboard">仪表板</Link>
    },
    {
      key: '/points',
      icon: <GiftOutlined />,
      label: <Link to="/points">我的积分</Link>
    },
    {
      key: '/teams',
      icon: <TeamOutlined />,
      label: <Link to="/teams">我的战队</Link>
    },
    {
      key: 'tasks',
      icon: <CheckCircleOutlined />,
      label: '任务系统',
      children: [
        {
          key: '/tasks/center',
          icon: <AppstoreAddOutlined />,
          label: <Link to="/tasks/center">任务中心</Link>
        },
        {
          key: '/tasks',
          icon: <CheckCircleOutlined />,
          label: <Link to="/tasks">我的任务</Link>
        }
      ]
    },
    {
      key: '/quiz',
      icon: <QuestionCircleOutlined />,
      label: <Link to="/quiz">每日答题</Link>
    },
    {
      key: '/leaderboard',
      icon: <TrophyOutlined />,
      label: <Link to="/leaderboard">排行榜</Link>
    }
  ]

  // 用户下拉菜单
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'address',
      icon: <UserOutlined />,
      label: (
        <div>
          <div style={{ fontSize: 12, opacity: 0.6 }}>钱包地址</div>
          <div style={{ fontSize: 14, fontFamily: 'monospace' }}>
            {account ? `${account.slice(0, 6)}...${account.slice(-4)}` : ''}
          </div>
        </div>
      ),
      disabled: true
    },
    {
      key: 'network',
      label: (
        <div>
          <div style={{ fontSize: 12, opacity: 0.6 }}>网络</div>
          <div style={{ fontSize: 14 }}>
            {chainId === 97 ? 'BSC Testnet' : chainId === 56 ? 'BSC Mainnet' : `Chain ${chainId}`}
          </div>
        </div>
      ),
      disabled: true
    },
    {
      type: 'divider'
    },
    {
      key: 'disconnect',
      icon: <LogoutOutlined />,
      label: '断开连接',
      danger: true,
      onClick: disconnectWallet
    }
  ]

  // 格式化地址显示
  const formatAddress = (address: string) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`
  }

  return (
    <AntHeader
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 1000,
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        padding: '0 24px',
        background: 'rgba(10, 14, 39, 0.9)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
      }}
    >
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', marginRight: 48 }}>
        <Link to="/" style={{ textDecoration: 'none' }}>
          <Space size={12}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 8,
                background: 'linear-gradient(135deg, #ff6b35 0%, #ff006e 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 800,
                fontSize: 18,
                color: '#fff'
              }}
            >
              R
            </div>
            <Text
              style={{
                fontSize: 20,
                fontWeight: 700,
                fontFamily: 'Space Grotesk, sans-serif',
                background: 'linear-gradient(135deg, #ff6b35 0%, #ff006e 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}
            >
              RWA Referral
            </Text>
          </Space>
        </Link>
      </div>

      {/* 导航菜单 */}
      <Menu
        mode="horizontal"
        selectedKeys={[location.pathname]}
        items={menuItems}
        style={{
          flex: 1,
          background: 'transparent',
          border: 'none',
          minWidth: 0
        }}
      />

      {/* 钱包连接按钮 */}
      <div style={{ marginLeft: 'auto' }}>
        {isConnected ? (
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" trigger={['click']}>
            <Button
              type="primary"
              icon={<WalletOutlined />}
              style={{
                height: 40,
                borderRadius: 8,
                fontWeight: 600
              }}
            >
              {formatAddress(account!)}
            </Button>
          </Dropdown>
        ) : (
          <Button
            type="primary"
            icon={<WalletOutlined />}
            loading={isConnecting}
            onClick={connectWallet}
            style={{
              height: 40,
              borderRadius: 8,
              fontWeight: 600
            }}
          >
            {isConnecting ? '连接中...' : '连接钱包'}
          </Button>
        )}
      </div>
    </AntHeader>
  )
}

export default Header
