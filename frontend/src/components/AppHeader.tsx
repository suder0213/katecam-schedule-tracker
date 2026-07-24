import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { AccountSettingsModal } from './AccountSettingsModal'

const PERMISSION_LABEL: Record<string, string> = {
  student: '학생',
  manager: '운영진',
  dev: '개발자',
}

export function AppHeader() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <header className="flex items-center justify-between border-b border-neutral-200 bg-kakao-yellow px-6 py-3">
      <div className="flex items-center gap-5">
        <Link to="/" className="text-lg font-bold text-kakao-black">
          🍪 카테캠 일정 트래커
        </Link>
        {(user?.permission === 'manager' || user?.permission === 'dev') && (
          <nav className="flex items-center gap-3 text-sm font-medium text-kakao-black">
            <Link to="/admin/users" className="hover:underline">
              계정 관리
            </Link>
            <Link to="/admin/agent" className="hover:underline">
              Agent 검토
            </Link>
          </nav>
        )}
      </div>
      <div className="flex items-center gap-3">
        {user && (
          <button
            type="button"
            onClick={() => setIsSettingsOpen(true)}
            className="text-sm text-kakao-black hover:underline"
          >
            {user.nick_name ?? user.email}
            <span className="ml-1 rounded-full bg-white/60 px-2 py-0.5 text-xs">
              {PERMISSION_LABEL[user.permission] ?? user.permission}
            </span>
          </button>
        )}
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-lg bg-kakao-black px-3 py-1.5 text-sm text-kakao-yellow transition hover:opacity-90"
        >
          로그아웃
        </button>
      </div>
      {isSettingsOpen && <AccountSettingsModal onClose={() => setIsSettingsOpen(false)} />}
    </header>
  )
}
