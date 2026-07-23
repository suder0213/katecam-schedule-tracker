import { api } from './client'
import type { User } from '../types/user'

export async function listStudents(): Promise<User[]> {
  return api.get<User[]>('/users')
}
