import { api } from './client'
import type { Team } from '../types/team'
import type { User } from '../types/user'

export async function listMyTeams(): Promise<Team[]> {
  return api.get<Team[]>('/teams/mine')
}

export async function listTeamMembers(teamId: string): Promise<User[]> {
  return api.get<User[]>(`/teams/${teamId}/members`)
}
