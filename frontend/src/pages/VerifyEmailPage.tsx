import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import * as authApi from '../api/auth'

type Status = 'loading' | 'success' | 'error'

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [status, setStatus] = useState<Status>('loading')

  useEffect(() => {
    if (!token) {
      setStatus('error')
      return
    }
    authApi
      .verifyEmail(token)
      .then(() => setStatus('success'))
      .catch(() => setStatus('error'))
  }, [token])

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 text-center shadow-sm">
        {status === 'loading' && <p className="text-neutral-500">이메일 인증 확인 중...</p>}
        {status === 'success' && (
          <>
            <h1 className="mb-2 text-xl font-bold text-kakao-black">인증 완료</h1>
            <p className="text-sm text-neutral-500">이메일 인증이 완료되었습니다. 로그인해주세요.</p>
          </>
        )}
        {status === 'error' && (
          <>
            <h1 className="mb-2 text-xl font-bold text-kakao-black">인증 실패</h1>
            <p className="text-sm text-neutral-500">
              인증 링크가 올바르지 않거나 만료되었습니다.
            </p>
          </>
        )}
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
