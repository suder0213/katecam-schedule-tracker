import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from './AuthContext'

export function ManagerRoute() {
  const { user } = useAuth()

  if (user?.permission !== 'manager' && user?.permission !== 'dev') {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
