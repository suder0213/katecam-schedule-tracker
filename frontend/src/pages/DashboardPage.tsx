import { useAuth } from '../auth/AuthContext'
import { AppHeader } from '../components/AppHeader'
import { MonthCalendar } from '../components/Calendar/MonthCalendar'

export function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-neutral-50">
      <AppHeader />
      {/* manager/dev must always pass student_id to GET /schedules (even for their
          own calendar) — student can omit it and the backend defaults to self, but
          passing it explicitly here works for all three roles uniformly. */}
      {user && <MonthCalendar studentId={user.user_id} />}
    </div>
  )
}
