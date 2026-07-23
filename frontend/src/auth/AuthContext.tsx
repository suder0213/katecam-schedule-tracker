import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import * as authApi from '../api/auth'
import { setUnauthorizedHandler } from '../api/client'
import type { User } from '../types/user'

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    setUnauthorizedHandler(() => setUser(null))

    void (async () => {
      const refreshedUser = await authApi.refreshSession()
      setUser(refreshedUser)
      setIsLoading(false)
    })()
  }, [])

  async function login(email: string, password: string) {
    const loggedInUser = await authApi.login(email, password)
    setUser(loggedInUser)
  }

  async function logout() {
    await authApi.logout()
    setUser(null)
  }

  async function refreshUser() {
    const current = await authApi.fetchCurrentUser()
    setUser(current)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
