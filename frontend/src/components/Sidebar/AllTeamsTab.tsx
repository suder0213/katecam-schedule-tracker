import { useEffect, useState } from 'react'
import * as teamsApi from '../../api/teams'
import type { Team } from '../../types/team'
import type { User } from '../../types/user'

interface AllTeamsTabProps {
  onSelect: (student: User) => void
}

export function AllTeamsTab({ onSelect }: AllTeamsTabProps) {
  const [teams, setTeams] = useState<Team[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedTeamId, setExpandedTeamId] = useState<string | null>(null)
  const [membersByTeam, setMembersByTeam] = useState<Record<string, User[]>>({})
  const [memberError, setMemberError] = useState<string | null>(null)

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

  async function toggleTeam(team: Team) {
    if (expandedTeamId === team.team_id) {
      setExpandedTeamId(null)
      return
    }
    setExpandedTeamId(team.team_id)
    if (!membersByTeam[team.team_id]) {
      try {
        const members = await teamsApi.listTeamMembers(team.team_id)
        setMembersByTeam((prev) => ({ ...prev, [team.team_id]: members }))
      } catch {
        setMemberError('팀원을 불러오지 못했습니다.')
      }
    }
  }

  if (isLoading) return <p className="p-4 text-sm text-neutral-400">불러오는 중...</p>
  if (error) return <p className="p-4 text-sm text-red-500">{error}</p>
  if (teams.length === 0) return <p className="p-4 text-sm text-neutral-400">팀이 없습니다.</p>

  return (
    <ul className="flex flex-col gap-0.5 p-2">
      {teams.map((team) => (
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
            <ul className="ml-3 flex flex-col gap-0.5 border-l border-neutral-100 pl-2">
              {memberError && <li className="py-1 text-xs text-red-500">{memberError}</li>}
              {(membersByTeam[team.team_id] ?? []).map((member) => (
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
          )}
        </li>
      ))}
    </ul>
  )
}
