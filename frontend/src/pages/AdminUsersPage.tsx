import { useEffect, useState } from 'react'
import * as usersApi from '../api/users'
import { useAuth } from '../auth/AuthContext'
import { AppHeader } from '../components/AppHeader'
import type { User, UserPermission } from '../types/user'

const PERMISSION_LABEL: Record<UserPermission, string> = {
  student: '학생',
  manager: '운영진',
  dev: '개발자',
}

// dev 대상 권한 변경은 백엔드가 이 엔드포인트로는 막아둔다 — student/manager만 승격·강등 가능.
const CHANGEABLE_PERMISSIONS: UserPermission[] = ['student', 'manager']

const PERMISSION_ORDER: Record<UserPermission, number> = {
  dev: 0,
  manager: 1,
  student: 2,
}

export function AdminUsersPage() {
  const { user: currentUser } = useAuth()
  const isDev = currentUser?.permission === 'dev'
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pendingId, setPendingId] = useState<string | null>(null)
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<string | null>(null)
  const [permissionDeniedId, setPermissionDeniedId] = useState<string | null>(null)

  function handleDeleteClick(userId: string) {
    if (isDev) {
      setConfirmingDeleteId(userId)
    } else {
      setPermissionDeniedId(userId)
    }
  }

  function load() {
    setIsLoading(true)
    usersApi
      .listUsers()
      .then((data) =>
        setUsers([...data].sort((a, b) => PERMISSION_ORDER[a.permission] - PERMISSION_ORDER[b.permission])),
      )
      .catch(() => setError('불러오지 못했습니다.'))
      .finally(() => setIsLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  async function handleChangePermission(user: User, permission: UserPermission) {
    if (permission === user.permission) return
    setPendingId(user.user_id)
    setError(null)
    try {
      await usersApi.updatePermission(user.user_id, permission)
      load()
    } catch {
      setError('권한 변경에 실패했습니다.')
    } finally {
      setPendingId(null)
    }
  }

  async function handleDelete(user: User) {
    setPendingId(user.user_id)
    setError(null)
    try {
      await usersApi.deleteUser(user.user_id)
      setConfirmingDeleteId(null)
      load()
    } catch {
      setError('삭제에 실패했습니다.')
    } finally {
      setPendingId(null)
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-neutral-50">
      <AppHeader />
      <div className="mx-auto w-full max-w-3xl p-6">
        <h2 className="mb-4 text-lg font-bold text-kakao-black">계정 관리</h2>

        {error && <p className="mb-3 text-sm text-red-500">{error}</p>}

        {isLoading ? (
          <p className="text-sm text-neutral-400">불러오는 중...</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {users.map((u) => (
              <li
                key={u.user_id}
                className="flex items-center justify-between rounded-lg border border-neutral-200 bg-white px-4 py-3"
              >
                <div>
                  <p className="font-medium text-kakao-black">{u.nick_name ?? u.email}</p>
                  <p className="text-xs text-neutral-400">{u.email}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-neutral-100 px-2.5 py-1 text-xs font-medium text-neutral-600">
                    {PERMISSION_LABEL[u.permission]}
                  </span>
                  {CHANGEABLE_PERMISSIONS.includes(u.permission) && (
                    <select
                      value={u.permission}
                      disabled={pendingId === u.user_id}
                      onChange={(e) =>
                        void handleChangePermission(u, e.target.value as UserPermission)
                      }
                      className="rounded-lg border border-neutral-200 px-2 py-1.5 text-sm"
                    >
                      <option value="student">학생</option>
                      <option value="manager">운영진</option>
                    </select>
                  )}
                  {u.permission !== 'dev' &&
                    (confirmingDeleteId === u.user_id ? (
                      <span className="flex items-center gap-1.5 text-xs">
                        <span className="text-red-500">정말 삭제?</span>
                        <button
                          type="button"
                          onClick={() => setConfirmingDeleteId(null)}
                          disabled={pendingId === u.user_id}
                          className="rounded border border-neutral-200 px-1.5 py-0.5 text-neutral-500 hover:bg-neutral-100 disabled:opacity-50"
                        >
                          취소
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleDelete(u)}
                          disabled={pendingId === u.user_id}
                          className="rounded bg-red-500 px-1.5 py-0.5 font-semibold text-white hover:bg-red-600 disabled:opacity-50"
                        >
                          삭제
                        </button>
                      </span>
                    ) : permissionDeniedId === u.user_id ? (
                      <span className="flex items-center gap-1.5 text-xs">
                        <span className="text-red-500">dev 권한이 필요합니다</span>
                        <button
                          type="button"
                          onClick={() => setPermissionDeniedId(null)}
                          className="rounded border border-neutral-200 px-1.5 py-0.5 text-neutral-500 hover:bg-neutral-100"
                        >
                          확인
                        </button>
                      </span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleDeleteClick(u.user_id)}
                        disabled={pendingId === u.user_id}
                        className="text-xs text-red-400 underline hover:text-red-600 disabled:opacity-50"
                      >
                        삭제
                      </button>
                    ))}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
