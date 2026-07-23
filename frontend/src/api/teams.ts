import { api } from './client'
import type { Team } from '../types/team'
import type { User } from '../types/user'

export async function listTeams(): Promise<Team[]> {
  return api.get<Team[]>('/teams')
}

export async function listTeamMembers(teamId: string): Promise<User[]> {
  return api.get<User[]>(`/teams/${teamId}/members`)
}

export async function createTeam(name: string): Promise<Team> {
  return api.post<Team>('/teams', { name })
}

export async function deleteTeam(teamId: string): Promise<void> {
  await api.delete(`/teams/${teamId}`)
}

export async function joinTeam(teamId: string, userId: string): Promise<void> {
  await api.post(`/teams/${teamId}/members`, { user_id: userId })
}

export async function leaveTeam(teamId: string, userId: string): Promise<void> {
  await api.delete(`/teams/${teamId}/members/${userId}`)
}
