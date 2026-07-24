import { useState, type MouseEvent } from 'react'
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
  const [showPermissionAlert, setShowPermissionAlert] = useState(false)
  const canAccessAdmin = user?.permission === 'manager' || user?.permission === 'dev'

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  function handleAdminLinkClick(e: MouseEvent) {
    if (!canAccessAdmin) {
      e.preventDefault()
      setShowPermissionAlert(true)
    }
  }

  return (
    <header className="flex items-center justify-between border-b border-neutral-200 bg-kakao-yellow px-6 py-3">
      <div className="flex items-center gap-5">
        <Link to="/" className="text-lg font-bold text-kakao-black">
          🍪 카테캠 일정 트래커
        </Link>
        {user && (
          <nav className="flex items-center gap-3 text-sm font-medium text-kakao-black">
            <Link to="/admin/users" onClick={handleAdminLinkClick} className="hover:underline">
              계정 관리
            </Link>
            <Link to="/admin/agent" onClick={handleAdminLinkClick} className="hover:underline">
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
      {showPermissionAlert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 text-center shadow-lg">
            <p className="mb-4 text-sm text-kakao-black">개발자/매니저 권한이 필요합니다.</p>
            <button
              type="button"
              onClick={() => setShowPermissionAlert(false)}
              className="w-full rounded-lg bg-kakao-yellow px-4 py-2 text-sm font-semibold text-kakao-black transition hover:bg-kakao-yellow-dark"
            >
              확인
            </button>
          </div>
        </div>
      )}
    </header>
  )
}
