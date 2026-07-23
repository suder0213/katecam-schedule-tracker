import { useEffect, useState } from 'react'
import { useAuth } from '../../auth/AuthContext'
import * as scheduleApi from '../../api/schedules'
import type { Schedule } from '../../types/schedule'
import { ScheduleForm } from './ScheduleForm'
import { formatFullDeadline } from './dateUtils'

interface ScheduleDetailModalProps {
  schedule: Schedule
  onClose: () => void
  onChanged: () => Promise<void> | void
}

export function ScheduleDetailModal({ schedule, onClose, onChanged }: ScheduleDetailModalProps) {
  const { user } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  const canEdit =
    schedule.kind === 'shared'
      ? user?.permission === 'manager' || user?.permission === 'dev'
      : schedule.owner_id === user?.user_id

  async function handleToggleDone() {
    setError(null)
    try {
      await scheduleApi.updateCompletion(schedule.schedule_id, !schedule.done)
      await onChanged()
    } catch {
      setError('완료 상태 변경에 실패했습니다.')
    }
  }

  async function handleDelete() {
    setError(null)
    try {
      await scheduleApi.deleteSchedule(schedule.schedule_id)
      await onChanged()
      onClose()
    } catch {
      setError('삭제에 실패했습니다.')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-lg">
        {isEditing ? (
          <ScheduleForm
            date={new Date(schedule.deadline)}
            existing={schedule}
            allowShared={canEdit}
            onCancel={() => setIsEditing(false)}
            onSaved={async () => {
              setIsEditing(false)
              await onChanged()
              onClose()
            }}
          />
        ) : (
          <>
            <div className="mb-4 flex items-center justify-between">
              <span
                className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                  schedule.kind === 'shared'
                    ? 'bg-kakao-yellow text-kakao-black'
                    : 'bg-neutral-200 text-neutral-700'
                }`}
              >
                {schedule.kind === 'shared' ? '공유' : '개인'}
              </span>
              <button
                type="button"
                onClick={onClose}
                className="text-neutral-400 hover:text-neutral-600"
              >
                ✕
              </button>
            </div>

            <div className="flex items-start gap-2">
              <input
                type="checkbox"
                checked={schedule.done}
                onChange={() => void handleToggleDone()}
                className="mt-1.5"
              />
              <div className="flex-1">
                <h3
                  className={`text-lg font-bold ${
                    schedule.done ? 'text-neutral-400 line-through' : 'text-kakao-black'
                  }`}
                >
                  {schedule.title}
                </h3>
                <p className="mt-2 whitespace-pre-wrap text-sm text-neutral-600">
                  {schedule.contents}
                </p>
                <p className="mt-3 text-xs text-neutral-400">
                  마감: {formatFullDeadline(schedule.deadline)}
                </p>
              </div>
            </div>

            {error && <p className="mt-2 text-sm text-red-500">{error}</p>}

            {canEdit && (
              <div className="mt-4 flex justify-end gap-3 text-xs">
                <button
                  type="button"
                  onClick={() => setIsEditing(true)}
                  className="text-neutral-500 underline hover:text-kakao-black"
                >
                  수정
                </button>
                <button
                  type="button"
                  onClick={() => void handleDelete()}
                  className="text-red-400 underline hover:text-red-600"
                >
                  삭제
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
