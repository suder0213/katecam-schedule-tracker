import { api, refreshAccessToken, setAccessToken } from './client'
import type { User } from '../types/user'

interface TokenResponse {
  access_token: string
  token_type: string
}

export async function signup(email: string, password: string, nickName: string): Promise<User> {
  return api.post<User>('/auth/signup', { email, password, nick_name: nickName || null })
}

export async function verifyEmail(token: string): Promise<User> {
  return api.get<User>(`/auth/verify?token=${encodeURIComponent(token)}`)
}

export async function fetchCurrentUser(): Promise<User> {
  return api.get<User>('/users/me')
}

export async function login(email: string, password: string): Promise<User> {
  const { access_token } = await api.post<TokenResponse>('/auth/login', { email, password })
  setAccessToken(access_token)
  return fetchCurrentUser()
}

export async function logout(): Promise<void> {
  try {
    await api.post('/auth/logout')
  } finally {
    setAccessToken(null)
  }
}

export async function refreshSession(): Promise<User | null> {
  const refreshed = await refreshAccessToken()
  if (!refreshed) return null
  try {
    return await fetchCurrentUser()
  } catch {
    return null
  }
}
