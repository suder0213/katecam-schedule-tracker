import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'

interface ScheduleSyncContextValue {
  version: number
  notifyChanged: () => void
}

const ScheduleSyncContext = createContext<ScheduleSyncContextValue | null>(null)

// TODO 사이드바와 달력은 각자 독립적으로 일정을 불러온다. 한쪽에서 완료 상태를
// 바꾸거나 일정을 추가/삭제/수정하면 notifyChanged()로 버전을 올려서, 다른 쪽도
// 새로고침 없이 재조회하도록 한다.
export function ScheduleSyncProvider({ children }: { children: ReactNode }) {
  const [version, setVersion] = useState(0)
  const notifyChanged = useCallback(() => setVersion((v) => v + 1), [])
  return (
    <ScheduleSyncContext.Provider value={{ version, notifyChanged }}>
      {children}
    </ScheduleSyncContext.Provider>
  )
}

export function useScheduleSync(): ScheduleSyncContextValue {
  const ctx = useContext(ScheduleSyncContext)
  if (!ctx) throw new Error('useScheduleSync must be used within ScheduleSyncProvider')
  return ctx
}
