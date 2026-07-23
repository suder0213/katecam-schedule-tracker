import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from './AuthContext'

export function DevRoute() {
  const { user } = useAuth()

  if (user?.permission !== 'dev') {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
