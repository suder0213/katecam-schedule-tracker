import { useEffect, useState } from 'react'
import * as scheduleApi from '../../api/schedules'
import type { Schedule } from '../../types/schedule'
import { useScheduleSync } from '../../context/ScheduleSyncContext'
import { ScheduleDetailModal } from '../Calendar/ScheduleDetailModal'

function formatDeadline(iso: string): string {
  const d = new Date(iso)
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${d.getMonth() + 1}/${d.getDate()} ${hh}:${mm}`
}

export function TodoTab() {
  const { version, notifyChanged } = useScheduleSync()
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Schedule | null>(null)

  useEffect(() => {
    let cancelled = false
    scheduleApi
      .listTodoSchedules()
      .then((data) => {
        if (!cancelled) setSchedules(data)
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
  }, [version])

  async function handleComplete(schedule: Schedule) {
    // Optimistic removal — the todo list only ever shows incomplete items, so
    // checking one off here always means "mark done and drop it from view".
    setSchedules((prev) => prev.filter((s) => s.schedule_id !== schedule.schedule_id))
    try {
      await scheduleApi.updateCompletion(schedule.schedule_id, true)
      notifyChanged()
    } catch {
      setSchedules((prev) => [...prev, schedule].sort((a, b) => a.deadline.localeCompare(b.deadline)))
      setError('완료 처리에 실패했습니다.')
    }
  }

  if (isLoading) return <p className="p-4 text-sm text-neutral-400">불러오는 중...</p>
  if (error) return <p className="p-4 text-sm text-red-500">{error}</p>
  if (schedules.length === 0) {
    return <p className="p-4 text-sm text-neutral-400">미완료 일정이 없습니다.</p>
  }

  return (
    <>
      <ul className="flex flex-col gap-1.5 p-3">
        {schedules.map((s) => (
          <li
            key={s.schedule_id}
            onClick={() => setSelected(s)}
            className="flex cursor-pointer items-start gap-2 rounded-lg border border-neutral-100 px-2.5 py-2 text-sm hover:bg-neutral-50"
          >
            <input
              type="checkbox"
              checked={false}
              onClick={(e) => e.stopPropagation()}
              onChange={() => void handleComplete(s)}
              className="mt-0.5 shrink-0"
            />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span
                  className={`shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${
                    s.kind === 'shared'
                      ? 'bg-kakao-yellow text-kakao-black'
                      : 'bg-neutral-200 text-neutral-700'
                  }`}
                >
                  {s.kind === 'shared' ? '공유' : '개인'}
                </span>
                <span className="flex-1 truncate text-kakao-black">{s.title}</span>
              </div>
              {s.contents && <p className="mt-0.5 truncate text-xs text-neutral-500">{s.contents}</p>}
              <span className="mt-0.5 block text-xs text-neutral-400">{formatDeadline(s.deadline)}</span>
            </div>
          </li>
        ))}
      </ul>

      {selected && (
        <ScheduleDetailModal
          schedule={selected}
          onClose={() => setSelected(null)}
          onChanged={async () => {
            notifyChanged()
          }}
        />
      )}
    </>
  )
}
