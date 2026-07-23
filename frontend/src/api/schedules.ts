import { api } from './client'
import type { Schedule, ScheduleKind } from '../types/schedule'

interface ListParams {
  year: number
  month: number
  studentId?: string
}

export async function listSchedules({ year, month, studentId }: ListParams): Promise<Schedule[]> {
  const params = new URLSearchParams({ year: String(year), month: String(month) })
  if (studentId) params.set('student_id', studentId)
  return api.get<Schedule[]>(`/schedules?${params.toString()}`)
}

export interface ScheduleCreateInput {
  kind: ScheduleKind
  title: string
  contents: string
  deadline: string
}

export async function createSchedule(input: ScheduleCreateInput): Promise<Schedule> {
  return api.post<Schedule>('/schedules', input)
}

export interface ScheduleUpdateInput {
  title?: string
  contents?: string
  deadline?: string
}

export async function updateSchedule(id: string, input: ScheduleUpdateInput): Promise<Schedule> {
  return api.patch<Schedule>(`/schedules/${id}`, input)
}

export async function deleteSchedule(id: string): Promise<void> {
  return api.delete(`/schedules/${id}`)
}

export async function updateCompletion(id: string, done: boolean): Promise<{ done: boolean }> {
  return api.put<{ done: boolean }>(`/schedules/${id}/completion`, { done })
}

export async function listTodoSchedules(limit = 20): Promise<Schedule[]> {
  return api.get<Schedule[]>(`/schedules/todo?limit=${limit}`)
}
