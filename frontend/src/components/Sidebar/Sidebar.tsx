import { useState, type ReactNode } from 'react'
import { TodoTab } from './TodoTab'
import { StudentsTab } from './StudentsTab'
import { AllTeamsTab } from './AllTeamsTab'
import type { User } from '../../types/user'

export interface SidebarTab {
  key: string
  label: string
  content: ReactNode
}

interface SidebarProps {
  // Anyone can browse the student/team directory — viewing another student's
  // schedule from it is what's actually access-controlled, not the listing.
  onSelectStudent: (student: User) => void
  // Dev-only tabs (account management, Agent review) get appended here later.
  extraTabs?: SidebarTab[]
}

export function Sidebar({ onSelectStudent, extraTabs = [] }: SidebarProps) {
  const tabs: SidebarTab[] = [
    { key: 'todo', label: 'TODO', content: <TodoTab /> },
    { key: 'students', label: '학생', content: <StudentsTab onSelect={onSelectStudent} /> },
    { key: 'all-teams', label: '팀', content: <AllTeamsTab onSelect={onSelectStudent} /> },
    ...extraTabs,
  ]
  const [activeKey, setActiveKey] = useState(tabs[0].key)
  const activeTab = tabs.find((t) => t.key === activeKey) ?? tabs[0]

  return (
    <aside className="w-64 shrink-0 border-r border-neutral-200 bg-white">
      <div className="flex border-b border-neutral-200">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveKey(tab.key)}
            className={`flex-1 px-3 py-2.5 text-sm font-medium transition ${
              activeKey === tab.key
                ? 'border-b-2 border-kakao-yellow-dark text-kakao-black'
                : 'text-neutral-400 hover:text-neutral-600'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="max-h-[calc(100vh-7rem)] overflow-y-auto">{activeTab.content}</div>
    </aside>
  )
}
