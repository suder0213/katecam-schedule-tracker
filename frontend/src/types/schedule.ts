export type ScheduleKind = 'personal' | 'shared'

export interface Schedule {
  schedule_id: string
  kind: ScheduleKind
  title: string
  contents: string
  deadline: string
  owner_id: string | null
  created_at: string
  updated_at: string
  done: boolean
}
