import { useEffect, useState } from 'react'
import * as usersApi from '../../api/users'
import type { User } from '../../types/user'

interface StudentsTabProps {
  onSelect: (student: User) => void
}

export function StudentsTab({ onSelect }: StudentsTabProps) {
  const [students, setStudents] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    usersApi
      .listStudents()
      .then((data) => {
        if (!cancelled) setStudents(data)
      })
      .catch(() => {
        if (!cancelled) setError('불러오지 못했습니다.')
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (isLoading) return <p className="p-4 text-sm text-neutral-400">불러오는 중...</p>
  if (error) return <p className="p-4 text-sm text-red-500">{error}</p>
  if (students.length === 0) return <p className="p-4 text-sm text-neutral-400">학생이 없습니다.</p>

  return (
    <ul className="flex flex-col gap-0.5 p-2">
      {students.map((s) => (
        <li key={s.user_id}>
          <button
            type="button"
            onClick={() => onSelect(s)}
            className="w-full rounded-lg px-2.5 py-2 text-left text-sm text-kakao-black hover:bg-neutral-100"
          >
            {s.nick_name ?? s.email}
          </button>
        </li>
      ))}
    </ul>
  )
}
