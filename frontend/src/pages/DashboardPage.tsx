import { useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import { AppHeader } from '../components/AppHeader'
import { Sidebar } from '../components/Sidebar/Sidebar'
import { MonthCalendar } from '../components/Calendar/MonthCalendar'
import { ScheduleSyncProvider } from '../context/ScheduleSyncContext'
import type { User } from '../types/user'

interface ViewingStudent {
  id: string
  label: string
}

export function DashboardPage() {
  const { user } = useAuth()
  const [viewingStudent, setViewingStudent] = useState<ViewingStudent | null>(null)
  const [warning, setWarning] = useState<string | null>(null)

  function handleSelectStudent(student: User) {
    if (!user) return
    if (student.user_id === user.user_id) {
      setViewingStudent(null)
      return
    }
    // Students can browse the student/team directory, but only manager/dev
    // may actually view someone else's schedule — the backend enforces this
    // too, this just avoids a round-trip to a 403 for the common case.
    if (user.permission === 'student') {
      setWarning('다른 학생의 일정은 조회할 수 없습니다.')
      return
    }
    setWarning(null)
    setViewingStudent({ id: student.user_id, label: student.nick_name ?? student.email })
  }

  const studentId = viewingStudent?.id ?? user?.user_id
  const studentLabel = viewingStudent?.label

  return (
    <div className="flex min-h-screen flex-col bg-neutral-50">
      <AppHeader />
      <ScheduleSyncProvider>
        <div className="flex flex-1">
          <Sidebar onSelectStudent={handleSelectStudent} />
          <div className="flex-1">
            {warning && (
              <div className="mx-6 mt-4 flex items-center justify-between rounded-lg bg-red-50 px-4 py-2.5 text-sm text-red-600">
                <span>{warning}</span>
                <button
                  type="button"
                  onClick={() => setWarning(null)}
                  className="ml-3 text-red-400 hover:text-red-600"
                >
                  ✕
                </button>
              </div>
            )}
            {viewingStudent && (
              <div className="mx-6 mt-4 flex items-center justify-between rounded-lg bg-neutral-100 px-4 py-2 text-sm text-neutral-600">
                <span>{viewingStudent.label}의 일정을 보고 있습니다.</span>
                <button
                  type="button"
                  onClick={() => setViewingStudent(null)}
                  className="font-medium text-kakao-black underline"
                >
                  내 일정으로 돌아가기
                </button>
              </div>
            )}
            {/* manager/dev must always pass student_id to GET /schedules (even for
                their own calendar) — student can omit it and the backend defaults
                to self, but passing it explicitly here works for all three roles. */}
            {user && studentId && <MonthCalendar studentId={studentId} studentLabel={studentLabel} />}
          </div>
        </div>
      </ScheduleSyncProvider>
    </div>
  )
}
