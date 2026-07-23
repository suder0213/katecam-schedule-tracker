import { useAuth } from '../auth/AuthContext'
import { AppHeader } from '../components/AppHeader'
import { Sidebar } from '../components/Sidebar/Sidebar'
import { MonthCalendar } from '../components/Calendar/MonthCalendar'
import { ScheduleSyncProvider } from '../context/ScheduleSyncContext'

export function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="flex min-h-screen flex-col bg-neutral-50">
      <AppHeader />
      <ScheduleSyncProvider>
        <div className="flex flex-1">
          <Sidebar />
          <div className="flex-1">
            {/* manager/dev must always pass student_id to GET /schedules (even for
                their own calendar) — student can omit it and the backend defaults
                to self, but passing it explicitly here works for all three roles. */}
            {user && <MonthCalendar studentId={user.user_id} />}
          </div>
        </div>
      </ScheduleSyncProvider>
    </div>
  )
}
