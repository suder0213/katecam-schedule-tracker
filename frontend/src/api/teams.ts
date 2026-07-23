import { api } from './client'
import type { Team } from '../types/team'
import type { User } from '../types/user'

export async function listTeams(): Promise<Team[]> {
  return api.get<Team[]>('/teams')
}

export async function listTeamMembers(teamId: string): Promise<User[]> {
  return api.get<User[]>(`/teams/${teamId}/members`)
}
