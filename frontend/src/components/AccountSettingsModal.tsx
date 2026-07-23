import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import * as usersApi from '../api/users'
import { ApiError } from '../api/client'

interface AccountSettingsModalProps {
  onClose: () => void
}

export function AccountSettingsModal({ onClose }: AccountSettingsModalProps) {
  const { user, refreshUser } = useAuth()

  const [nickName, setNickName] = useState(user?.nick_name ?? '')
  const [nickNameError, setNickNameError] = useState<string | null>(null)
  const [nickNameSuccess, setNickNameSuccess] = useState(false)
  const [isSavingNickName, setIsSavingNickName] = useState(false)

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [passwordSuccess, setPasswordSuccess] = useState(false)
  const [isSavingPassword, setIsSavingPassword] = useState(false)

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  async function handleSaveNickName() {
    setNickNameError(null)
    setNickNameSuccess(false)
    if (!nickName.trim()) {
      setNickNameError('닉네임을 입력하세요.')
      return
    }
    setIsSavingNickName(true)
    try {
      await usersApi.updateMyNickname(nickName.trim())
      await refreshUser()
      setNickNameSuccess(true)
    } catch {
      setNickNameError('닉네임 변경에 실패했습니다.')
    } finally {
      setIsSavingNickName(false)
    }
  }

  async function handleSavePassword() {
    setPasswordError(null)
    setPasswordSuccess(false)
    if (newPassword.length < 8) {
      setPasswordError('새 비밀번호는 8자 이상이어야 합니다.')
      return
    }
    setIsSavingPassword(true)
    try {
      await usersApi.updateMyPassword(currentPassword, newPassword)
      setCurrentPassword('')
      setNewPassword('')
      setPasswordSuccess(true)
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        setPasswordError('현재 비밀번호가 올바르지 않습니다.')
      } else {
        setPasswordError('비밀번호 변경에 실패했습니다.')
      }
    } finally {
      setIsSavingPassword(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-bold text-kakao-black">계정 정보</h3>
          <button
            type="button"
            onClick={onClose}
            className="text-neutral-400 hover:text-neutral-600"
          >
            ✕
          </button>
        </div>

        <p className="mb-4 text-sm text-neutral-500">{user?.email}</p>

        <div className="mb-6">
          <label className="mb-1 block text-sm font-medium text-kakao-black">닉네임</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={nickName}
              onChange={(e) => {
                setNickName(e.target.value)
                setNickNameSuccess(false)
              }}
              className="flex-1 rounded-lg border border-neutral-200 px-3 py-1.5 text-sm"
            />
            <button
              type="button"
              onClick={() => void handleSaveNickName()}
              disabled={isSavingNickName}
              className="rounded-lg bg-kakao-yellow px-3 py-1.5 text-sm font-semibold text-kakao-black transition hover:bg-kakao-yellow-dark disabled:opacity-50"
            >
              변경
            </button>
          </div>
          {nickNameError && <p className="mt-1 text-xs text-red-500">{nickNameError}</p>}
          {nickNameSuccess && <p className="mt-1 text-xs text-green-600">변경되었습니다.</p>}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-kakao-black">비밀번호 변경</label>
          <div className="flex flex-col gap-2">
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => {
                setCurrentPassword(e.target.value)
                setPasswordSuccess(false)
              }}
              placeholder="현재 비밀번호"
              className="rounded-lg border border-neutral-200 px-3 py-1.5 text-sm"
            />
            <input
              type="password"
              value={newPassword}
              onChange={(e) => {
                setNewPassword(e.target.value)
                setPasswordSuccess(false)
              }}
              placeholder="새 비밀번호 (8자 이상)"
              className="rounded-lg border border-neutral-200 px-3 py-1.5 text-sm"
            />
            <button
              type="button"
              onClick={() => void handleSavePassword()}
              disabled={isSavingPassword}
              className="rounded-lg bg-kakao-yellow px-3 py-1.5 text-sm font-semibold text-kakao-black transition hover:bg-kakao-yellow-dark disabled:opacity-50"
            >
              비밀번호 변경
            </button>
          </div>
          {passwordError && <p className="mt-1 text-xs text-red-500">{passwordError}</p>}
          {passwordSuccess && <p className="mt-1 text-xs text-green-600">변경되었습니다.</p>}
        </div>
      </div>
    </div>
  )
}
