import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import * as authApi from '../api/auth'
import { ApiError } from '../api/client'

export function SignupPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [nickName, setNickName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDone, setIsDone] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.')
      return
    }
    setIsSubmitting(true)
    try {
      await authApi.signup(email, password, nickName)
      setIsDone(true)
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setError('이미 가입된 이메일입니다.')
      } else if (err instanceof ApiError && err.status === 422) {
        setError('입력값을 다시 확인해주세요 (비밀번호는 8자 이상이어야 합니다).')
      } else {
        setError('회원가입에 실패했습니다. 잠시 후 다시 시도해주세요.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isDone) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4">
        <div className="w-full max-w-sm rounded-2xl bg-white p-8 text-center shadow-sm">
          <h1 className="mb-2 text-xl font-bold text-kakao-black">가입 완료</h1>
          <p className="text-sm text-neutral-500">
            <strong>{email}</strong> 계정이 생성되었습니다.
            <br />
            바로 로그인해주세요.
          </p>
          <Link
            to="/login"
            className="mt-6 inline-block rounded-lg bg-kakao-yellow px-4 py-3 text-sm font-semibold text-kakao-black transition hover:bg-kakao-yellow-dark"
          >
            로그인 화면으로
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-sm">
        <h1 className="mb-1 text-center text-2xl font-bold text-kakao-black">🍪 카테캠 일정 트래커</h1>
        <p className="mb-6 text-center text-sm text-neutral-500">회원가입</p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <input
            type="email"
            required
            placeholder="이메일"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-lg border border-neutral-200 px-4 py-3 text-sm outline-none focus:border-kakao-yellow-dark"
          />
          <input
            type="text"
            placeholder="닉네임 (선택, 추천: 디스코드 닉네임)"
            value={nickName}
            onChange={(e) => setNickName(e.target.value)}
            className="rounded-lg border border-neutral-200 px-4 py-3 text-sm outline-none focus:border-kakao-yellow-dark"
          />
          <input
            type="password"
            required
            minLength={8}
            placeholder="비밀번호 (8자 이상)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-lg border border-neutral-200 px-4 py-3 text-sm outline-none focus:border-kakao-yellow-dark"
          />
          <input
            type="password"
            required
            minLength={8}
            placeholder="비밀번호 확인"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="rounded-lg border border-neutral-200 px-4 py-3 text-sm outline-none focus:border-kakao-yellow-dark"
          />

          {error && <p className="text-sm text-red-500">{error}</p>}

          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-2 rounded-lg bg-kakao-yellow px-4 py-3 text-sm font-semibold text-kakao-black transition hover:bg-kakao-yellow-dark disabled:opacity-60"
          >
            {isSubmitting ? '가입 중...' : '회원가입'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-neutral-500">
          이미 계정이 있으신가요?{' '}
          <Link to="/login" className="font-medium text-kakao-black underline">
            로그인
          </Link>
        </p>
      </div>
    </div>
  )
}
