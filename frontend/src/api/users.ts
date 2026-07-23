import { api } from './client'
import type { User, UserPermission } from '../types/user'

export async function listUsers(): Promise<User[]> {
  return api.get<User[]>('/users')
}

export async function updatePermission(userId: string, permission: UserPermission): Promise<User> {
  return api.patch<User>(`/users/${userId}/permission`, { permission })
}
