import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import Header from '@/components/layout/Header'
import Footer from '@/components/layout/Footer'
import Home from '@/pages/Home'
import Dashboard from '@/pages/Dashboard'
import Leaderboard from '@/pages/Leaderboard'
import Points from '@/pages/Points'
import Teams from '@/pages/Teams'
import Tasks from '@/pages/Tasks'
import TaskCenter from '@/pages/TaskCenter'
import Quiz from '@/pages/Quiz'
import NotFound from '@/pages/NotFound'

const { Content } = Layout

function App() {
  return (
    <Layout className="min-h-screen">
      {/* 顶部导航 */}
      <Header />

      {/* 主内容区域 */}
      <Content className="flex-1">
        <Routes>
          {/* 首页 */}
          <Route path="/" element={<Home />} />

          {/* 仪表板 */}
          <Route path="/dashboard" element={<Dashboard />} />

          {/* 排行榜 */}
          <Route path="/leaderboard" element={<Leaderboard />} />

          {/* 积分系统 */}
          <Route path="/points" element={<Points />} />

          {/* 战队系统 */}
          <Route path="/teams" element={<Teams />} />

          {/* 任务系统 */}
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/tasks/center" element={<TaskCenter />} />

          {/* Quiz 答题系统 */}
          <Route path="/quiz" element={<Quiz />} />

          {/* 404页面 */}
          <Route path="/404" element={<NotFound />} />

          {/* 重定向到404 */}
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Routes>
      </Content>

      {/* 底部 */}
      <Footer />
    </Layout>
  )
}

export default App
