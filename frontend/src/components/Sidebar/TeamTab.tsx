import { useEffect, useState } from 'react'
import * as teamApi from '../../api/teams'
import type { Team } from '../../types/team'
import type { User } from '../../types/user'

interface TeamWithMembers extends Team {
  members: User[]
}

export function TeamTab() {
  const [teams, setTeams] = useState<TeamWithMembers[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const myTeams = await teamApi.listMyTeams()
        const withMembers = await Promise.all(
          myTeams.map(async (team) => ({
            ...team,
            members: await teamApi.listTeamMembers(team.team_id),
          })),
        )
        if (!cancelled) setTeams(withMembers)
      } catch {
        if (!cancelled) setError('불러오지 못했습니다.')
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [])

  if (error) return <p className="p-4 text-sm text-red-500">{error}</p>
  if (teams === null) return <p className="p-4 text-sm text-neutral-400">불러오는 중...</p>
  if (teams.length === 0) {
    return <p className="p-4 text-sm text-neutral-400">소속된 팀이 없습니다.</p>
  }

  return (
    <div className="flex flex-col gap-4 p-3">
      {teams.map((team) => (
        <div key={team.team_id}>
          <h4 className="mb-1.5 text-sm font-bold text-kakao-black">{team.name}</h4>
          <ul className="flex flex-col gap-1">
            {team.members.map((member) => (
              <li
                key={member.user_id}
                className="rounded-lg border border-neutral-100 px-2.5 py-1.5 text-sm text-neutral-600"
              >
                {member.nick_name ?? member.email}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
