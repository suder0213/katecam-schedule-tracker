import { useState, type FormEvent } from 'react'
import * as scheduleApi from '../../api/schedules'
import type { Schedule, ScheduleKind } from '../../types/schedule'

interface ScheduleFormProps {
  date: Date
  existing?: Schedule
  allowShared: boolean
  onCancel: () => void
  onSaved: () => Promise<void> | void
}

function toLocalTimeInput(date: Date): string {
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  return `${hh}:${mm}`
}

export function ScheduleForm({ date, existing, allowShared, onCancel, onSaved }: ScheduleFormProps) {
  const existingDeadline = existing ? new Date(existing.deadline) : null
  const [kind, setKind] = useState<ScheduleKind>(existing?.kind ?? 'personal')
  const [title, setTitle] = useState(existing?.title ?? '')
  const [contents, setContents] = useState(existing?.contents ?? '')
  const [time, setTime] = useState(existingDeadline ? toLocalTimeInput(existingDeadline) : '23:59')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      const [hh, mm] = time.split(':').map(Number)
      const deadline = new Date(date)
      deadline.setHours(hh, mm, 0, 0)

      if (existing) {
        await scheduleApi.updateSchedule(existing.schedule_id, {
          title,
          contents,
          deadline: deadline.toISOString(),
        })
      } else {
        await scheduleApi.createSchedule({
          kind,
          title,
          contents,
          deadline: deadline.toISOString(),
        })
      }
      await onSaved()
    } catch {
      setError('저장에 실패했습니다.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <h3 className="text-xl font-bold text-kakao-black">
        {existing ? '일정 수정' : '새 일정'} · {date.getMonth() + 1}월 {date.getDate()}일
      </h3>

      {!existing && allowShared && (
        <div className="flex gap-4 text-sm">
          <label className="flex items-center gap-1.5">
            <input type="radio" checked={kind === 'personal'} onChange={() => setKind('personal')} />
            개인 일정
          </label>
          <label className="flex items-center gap-1.5">
            <input type="radio" checked={kind === 'shared'} onChange={() => setKind('shared')} />
            공유 일정
          </label>
        </div>
      )}

      <input
        type="text"
        required
        placeholder="제목"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-kakao-yellow-dark"
      />
      <textarea
        required
        placeholder="내용"
        value={contents}
        onChange={(e) => setContents(e.target.value)}
        rows={3}
        className="rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-kakao-yellow-dark"
      />
      <label className="flex items-center gap-2 text-sm text-neutral-500">
        마감 시각
        <input
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
          className="rounded-lg border border-neutral-200 px-2 py-1.5 text-sm"
        />
      </label>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <div className="mt-2 flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg px-4 py-2 text-sm text-neutral-500 hover:bg-neutral-100"
        >
          취소
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-lg bg-kakao-yellow px-4 py-2 text-sm font-semibold text-kakao-black transition hover:bg-kakao-yellow-dark disabled:opacity-60"
        >
          {isSubmitting ? '저장 중...' : '저장'}
        </button>
      </div>
    </form>
  )
}
