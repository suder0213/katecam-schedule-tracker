import { api } from './client'
import type { User, UserPermission } from '../types/user'

export async function listUsers(): Promise<User[]> {
  return api.get<User[]>('/users')
}

export async function updatePermission(userId: string, permission: UserPermission): Promise<User> {
  return api.patch<User>(`/users/${userId}/permission`, { permission })
}

export async function updateMyNickname(nickName: string): Promise<User> {
  return api.patch<User>('/users/me/nick-name', { nick_name: nickName })
}

export async function updateMyPassword(currentPassword: string, newPassword: string): Promise<void> {
  await api.patch<void>('/users/me/password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}
