import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { Spinner } from '../components/Spinner'
import { useAuth } from './useAuth'

/** Gate a route on a bearer token; bounce to /login otherwise. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { token, loading } = useAuth()

  if (token && loading) return <Spinner label="Loading…" />
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}
