import { useCallback, useEffect, useMemo, useState, type ChangeEvent } from 'react'
import { useAuth } from '../../auth/AuthContext'
import { useScheduleSync } from '../../context/ScheduleSyncContext'
import * as scheduleApi from '../../api/schedules'
import type { Schedule } from '../../types/schedule'
import { getMonthGrid, isSameDay, formatDateKey } from './dateUtils'
import { DayDetailModal } from './DayDetailModal'

const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토']

interface MonthCalendarProps {
  studentId?: string
  studentLabel?: string
}

export function MonthCalendar({ studentId, studentLabel }: MonthCalendarProps) {
  const { user } = useAuth()
  const { version, notifyChanged } = useScheduleSync()
  const today = useMemo(() => new Date(), [])
  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth() + 1)
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedDate, setSelectedDate] = useState<Date | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await scheduleApi.listSchedules({ year, month, studentId })
      setSchedules(data)
    } catch {
      setError('일정을 불러오지 못했습니다.')
    } finally {
      setIsLoading(false)
    }
  }, [year, month, studentId])

  useEffect(() => {
    void load()
  }, [load, version])

  const grid = useMemo(() => getMonthGrid(year, month), [year, month])

  const schedulesByDay = useMemo(() => {
    const map = new Map<string, Schedule[]>()
    for (const s of schedules) {
      const key = formatDateKey(new Date(s.deadline))
      const list = map.get(key) ?? []
      list.push(s)
      map.set(key, list)
    }
    for (const list of map.values()) {
      list.sort((a, b) => {
        if (a.kind !== b.kind) return a.kind === 'shared' ? -1 : 1
        return new Date(a.deadline).getTime() - new Date(b.deadline).getTime()
      })
    }
    return map
  }, [schedules])

  function goToPrevMonth() {
    if (month === 1) {
      setYear((y) => y - 1)
      setMonth(12)
    } else {
      setMonth((m) => m - 1)
    }
  }

  function goToNextMonth() {
    if (month === 12) {
      setYear((y) => y + 1)
      setMonth(1)
    } else {
      setMonth((m) => m + 1)
    }
  }

  function handleMonthPick(e: ChangeEvent<HTMLInputElement>) {
    if (!e.target.value) return
    const [y, m] = e.target.value.split('-').map(Number)
    setYear(y)
    setMonth(m)
  }

  async function handleToggleDone(schedule: Schedule) {
    try {
      await scheduleApi.updateCompletion(schedule.schedule_id, !schedule.done)
      await load()
      notifyChanged()
    } catch {
      setError('완료 상태 변경에 실패했습니다.')
    }
  }

  const canCreateShared = user?.permission === 'manager' || user?.permission === 'dev'
  const isOwnCalendar = !studentId || studentId === user?.user_id

  return (
    <div className="mx-auto max-w-6xl p-6">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={goToPrevMonth}
            className="rounded-lg border border-neutral-200 px-3 py-1.5 text-sm hover:bg-neutral-100"
          >
            ◀
          </button>
          <h2 className="min-w-36 text-center text-xl font-bold text-kakao-black">
            {year}년 {month}월
          </h2>
          <button
            type="button"
            onClick={goToNextMonth}
            className="rounded-lg border border-neutral-200 px-3 py-1.5 text-sm hover:bg-neutral-100"
          >
            ▶
          </button>
          <input
            type="month"
            value={`${year}-${String(month).padStart(2, '0')}`}
            onChange={handleMonthPick}
            className="ml-1 rounded-lg border border-neutral-200 px-2 py-1.5 text-sm text-neutral-500"
          />
        </div>
        {studentLabel && <span className="text-sm text-neutral-500">{studentLabel}의 일정</span>}
      </div>

      {error && <p className="mb-2 text-sm text-red-500">{error}</p>}

      <div className="grid grid-cols-7 overflow-hidden rounded-xl border border-neutral-200 bg-white">
        {WEEKDAYS.map((w) => (
          <div
            key={w}
            className="border-b border-neutral-200 bg-neutral-50 py-2.5 text-center text-sm font-medium text-neutral-500"
          >
            {w}
          </div>
        ))}
        {grid.map(({ date, inCurrentMonth }) => {
          const key = formatDateKey(date)
          const daySchedules = schedulesByDay.get(key) ?? []
          const visible = daySchedules.slice(0, 5)
          const overflowCount = daySchedules.length - visible.length
          const isToday = isSameDay(date, today)

          return (
            <div
              key={key}
              onClick={() => setSelectedDate(date)}
              className={`flex min-h-36 cursor-pointer flex-col items-stretch gap-1.5 border-b border-r border-neutral-100 p-2 text-left last:border-r-0 hover:bg-neutral-50 ${
                inCurrentMonth ? 'bg-white' : 'bg-neutral-50 text-neutral-300'
              }`}
            >
              <span
                className={`text-sm ${
                  isToday
                    ? 'flex h-6 w-6 items-center justify-center rounded-full bg-kakao-yellow font-bold text-kakao-black'
                    : ''
                }`}
              >
                {date.getDate()}
              </span>
              <div className="flex flex-1 flex-col gap-1">
                {visible.map((s) => (
                  <label
                    key={s.schedule_id}
                    onClick={(e) => e.stopPropagation()}
                    className={`flex items-center gap-1.5 truncate rounded px-1.5 py-1 text-xs ${
                      s.kind === 'shared'
                        ? 'bg-kakao-yellow/70 text-kakao-black'
                        : 'bg-neutral-200 text-neutral-700'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={s.done}
                      onChange={() => void handleToggleDone(s)}
                      className="h-3 w-3 shrink-0"
                    />
                    <span className={`truncate ${s.done ? 'line-through opacity-50' : ''}`}>
                      {s.title}
                    </span>
                  </label>
                ))}
                {overflowCount > 0 && (
                  <span className="text-xs text-neutral-400">+{overflowCount}개 더보기</span>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {isLoading && <p className="mt-3 text-sm text-neutral-400">불러오는 중...</p>}

      {selectedDate && (
        <DayDetailModal
          date={selectedDate}
          schedules={schedulesByDay.get(formatDateKey(selectedDate)) ?? []}
          canCreateShared={canCreateShared}
          canCreatePersonal={isOwnCalendar}
          onClose={() => setSelectedDate(null)}
          onChanged={async () => {
            await load()
            notifyChanged()
          }}
        />
      )}
    </div>
  )
}
