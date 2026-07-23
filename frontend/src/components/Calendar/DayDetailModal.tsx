import { useEffect, useState } from 'react'
import { useAuth } from '../../auth/AuthContext'
import * as scheduleApi from '../../api/schedules'
import type { Schedule } from '../../types/schedule'
import { ScheduleForm } from './ScheduleForm'

interface DayDetailModalProps {
  date: Date
  schedules: Schedule[]
  canCreateShared: boolean
  canCreatePersonal: boolean
  onClose: () => void
  onChanged: () => Promise<void> | void
}

type Mode = 'list' | 'create' | { edit: Schedule }

export function DayDetailModal({
  date,
  schedules,
  canCreateShared,
  canCreatePersonal,
  onClose,
  onChanged,
}: DayDetailModalProps) {
  const { user } = useAuth()
  const [mode, setMode] = useState<Mode>('list')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  function canEdit(schedule: Schedule): boolean {
    if (schedule.kind === 'shared') {
      return user?.permission === 'manager' || user?.permission === 'dev'
    }
    return schedule.owner_id === user?.user_id
  }

  async function handleToggleDone(schedule: Schedule) {
    setError(null)
    try {
      await scheduleApi.updateCompletion(schedule.schedule_id, !schedule.done)
      await onChanged()
    } catch {
      setError('완료 상태 변경에 실패했습니다.')
    }
  }

  async function handleDelete(schedule: Schedule) {
    setError(null)
    try {
      await scheduleApi.deleteSchedule(schedule.schedule_id)
      await onChanged()
    } catch {
      setError('삭제에 실패했습니다.')
    }
  }

  const canCreateAny = canCreateShared || canCreatePersonal

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <div className="max-h-[80vh] w-full max-w-md overflow-y-auto rounded-2xl bg-white p-6 shadow-lg">
        {mode === 'list' && (
          <>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-bold text-kakao-black">
                {date.getMonth() + 1}월 {date.getDate()}일
              </h3>
              <button
                type="button"
                onClick={onClose}
                className="text-neutral-400 hover:text-neutral-600"
              >
                ✕
              </button>
            </div>

            {error && <p className="mb-2 text-sm text-red-500">{error}</p>}

            {schedules.length === 0 && (
              <p className="py-6 text-center text-sm text-neutral-400">등록된 일정이 없습니다.</p>
            )}

            <ul className="flex flex-col gap-2">
              {schedules.map((s) => (
                <li key={s.schedule_id} className="rounded-lg border border-neutral-200 p-3">
                  <div className="flex items-start gap-2">
                    <input
                      type="checkbox"
                      checked={s.done}
                      onChange={() => void handleToggleDone(s)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                            s.kind === 'shared'
                              ? 'bg-kakao-yellow text-kakao-black'
                              : 'bg-neutral-200 text-neutral-700'
                          }`}
                        >
                          {s.kind === 'shared' ? '공유' : '개인'}
                        </span>
                        <span
                          className={`font-medium ${s.done ? 'text-neutral-400 line-through' : 'text-kakao-black'}`}
                        >
                          {s.title}
                        </span>
                      </div>
                      <p className="mt-1 whitespace-pre-wrap text-sm text-neutral-500">
                        {s.contents}
                      </p>
                    </div>
                  </div>
                  {canEdit(s) && (
                    <div className="mt-2 flex justify-end gap-3 text-xs">
                      <button
                        type="button"
                        onClick={() => setMode({ edit: s })}
                        className="text-neutral-500 underline hover:text-kakao-black"
                      >
                        수정
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleDelete(s)}
                        className="text-red-400 underline hover:text-red-600"
                      >
                        삭제
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>

            {canCreateAny && (
              <button
                type="button"
                onClick={() => setMode('create')}
                className="mt-4 w-full rounded-lg bg-kakao-yellow px-4 py-2.5 text-sm font-semibold text-kakao-black transition hover:bg-kakao-yellow-dark"
              >
                + 새 일정 추가
              </button>
            )}
          </>
        )}

        {mode === 'create' && (
          <ScheduleForm
            date={date}
            allowShared={canCreateShared}
            onCancel={() => setMode('list')}
            onSaved={async () => {
              setMode('list')
              await onChanged()
            }}
          />
        )}

        {typeof mode === 'object' && (
          <ScheduleForm
            date={date}
            existing={mode.edit}
            allowShared={canCreateShared}
            onCancel={() => setMode('list')}
            onSaved={async () => {
              setMode('list')
              await onChanged()
            }}
          />
        )}
      </div>
    </div>
  )
}
