export interface MonthGridCell {
  date: Date
  inCurrentMonth: boolean
}

export function getMonthGrid(year: number, month: number): MonthGridCell[] {
  const firstOfMonth = new Date(year, month - 1, 1)
  const startOffset = firstOfMonth.getDay()
  const gridStart = new Date(year, month - 1, 1 - startOffset)

  const cells: MonthGridCell[] = []
  for (let i = 0; i < 42; i++) {
    const date = new Date(gridStart)
    date.setDate(gridStart.getDate() + i)
    cells.push({ date, inCurrentMonth: date.getMonth() === month - 1 })
  }
  return cells
}

export function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}

export function formatDateKey(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function formatTime(date: Date): string {
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  return `${hh}:${mm}`
}

export function formatFullDeadline(iso: string): string {
  const d = new Date(iso)
  return `${d.getFullYear()}년 ${d.getMonth() + 1}월 ${d.getDate()}일 ${formatTime(d)}`
}
