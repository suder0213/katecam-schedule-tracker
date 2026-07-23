import { useEffect, useState, type FormEvent } from 'react'
import * as teamsApi from '../../api/teams'
import { useAuth } from '../../auth/AuthContext'
import type { Team } from '../../types/team'
import type { User } from '../../types/user'

interface AllTeamsTabProps {
  onSelect: (student: User) => void
}

export function AllTeamsTab({ onSelect }: AllTeamsTabProps) {
  const { user } = useAuth()
  const [teams, setTeams] = useState<Team[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedTeamId, setExpandedTeamId] = useState<string | null>(null)
  const [membersByTeam, setMembersByTeam] = useState<Record<string, User[]>>({})
  const [memberError, setMemberError] = useState<string | null>(null)
  const [newTeamName, setNewTeamName] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [membershipError, setMembershipError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    teamsApi
      .listTeams()
      .then((data) => {
        if (!cancelled) setTeams([...data].sort((a, b) => a.name.localeCompare(b.name, 'ko')))
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
  }, [])

  async function loadMembers(teamId: string) {
    try {
      const members = await teamsApi.listTeamMembers(teamId)
      setMembersByTeam((prev) => ({ ...prev, [teamId]: members }))
    } catch {
      setMemberError('팀원을 불러오지 못했습니다.')
    }
  }

  async function toggleTeam(team: Team) {
    if (expandedTeamId === team.team_id) {
      setExpandedTeamId(null)
      return
    }
    setExpandedTeamId(team.team_id)
    if (!membersByTeam[team.team_id]) {
      await loadMembers(team.team_id)
    }
  }

  async function handleCreateTeam(e: FormEvent) {
    e.preventDefault()
    const name = newTeamName.trim()
    if (!name) return

    setIsCreating(true)
    setCreateError(null)
    try {
      const team = await teamsApi.createTeam(name)
      setTeams((prev) => [...prev, team].sort((a, b) => a.name.localeCompare(b.name, 'ko')))
      setNewTeamName('')
    } catch {
      setCreateError('팀을 만들지 못했습니다.')
    } finally {
      setIsCreating(false)
    }
  }

  async function handleJoin(teamId: string) {
    if (!user) return
    setMembershipError(null)
    try {
      await teamsApi.joinTeam(teamId, user.user_id)
      await loadMembers(teamId)
    } catch {
      setMembershipError('가입하지 못했습니다.')
    }
  }

  async function handleLeave(teamId: string) {
    if (!user) return
    setMembershipError(null)
    try {
      await teamsApi.leaveTeam(teamId, user.user_id)
      await loadMembers(teamId)
    } catch {
      setMembershipError('탈퇴하지 못했습니다.')
    }
  }

  const canCreateTeam = user?.permission === 'manager' || user?.permission === 'dev'

  return (
    <div className="flex flex-col">
      {canCreateTeam && (
        <form onSubmit={(e) => void handleCreateTeam(e)} className="flex gap-1 border-b border-neutral-100 p-2">
          <input
            type="text"
            value={newTeamName}
            onChange={(e) => setNewTeamName(e.target.value)}
            placeholder="새 팀 이름"
            className="min-w-0 flex-1 rounded-lg border border-neutral-200 px-2 py-1.5 text-sm"
          />
          <button
            type="submit"
            disabled={isCreating || !newTeamName.trim()}
            className="shrink-0 rounded-lg bg-kakao-yellow px-2.5 py-1.5 text-sm font-medium text-kakao-black disabled:opacity-50"
          >
            추가
          </button>
        </form>
      )}
      {createError && <p className="px-2 pt-1 text-xs text-red-500">{createError}</p>}
      {membershipError && <p className="px-2 pt-1 text-xs text-red-500">{membershipError}</p>}

      {isLoading ? (
        <p className="p-4 text-sm text-neutral-400">불러오는 중...</p>
      ) : error ? (
        <p className="p-4 text-sm text-red-500">{error}</p>
      ) : teams.length === 0 ? (
        <p className="p-4 text-sm text-neutral-400">팀이 없습니다.</p>
      ) : (
        <ul className="flex flex-col gap-0.5 p-2">
          {teams.map((team) => {
            const members = membersByTeam[team.team_id]
            const isMember = members?.some((m) => m.user_id === user?.user_id) ?? false
            return (
              <li key={team.team_id}>
                <button
                  type="button"
                  onClick={() => void toggleTeam(team)}
                  className="flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-left text-sm font-medium text-kakao-black hover:bg-neutral-100"
                >
                  <span>{team.name}</span>
                  <span className="text-xs text-neutral-400">{expandedTeamId === team.team_id ? '▲' : '▼'}</span>
                </button>
                {expandedTeamId === team.team_id && (
                  <div className="ml-3 border-l border-neutral-100 pl-2">
                    {members && (
                      <button
                        type="button"
                        onClick={() => void (isMember ? handleLeave(team.team_id) : handleJoin(team.team_id))}
                        className="w-full rounded-lg px-2 py-1.5 text-left text-sm font-medium text-kakao-yellow-dark hover:bg-neutral-100"
                      >
                        {isMember ? '이 팀 탈퇴' : '이 팀 가입'}
                      </button>
                    )}
                    <ul className="flex flex-col gap-0.5">
                      {memberError && <li className="py-1 text-xs text-red-500">{memberError}</li>}
                      {(members ?? []).map((member) => (
                        <li key={member.user_id}>
                          <button
                            type="button"
                            onClick={() => onSelect(member)}
                            className="w-full rounded-lg px-2 py-1.5 text-left text-sm text-neutral-600 hover:bg-neutral-100"
                          >
                            {member.nick_name ?? member.email}
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
