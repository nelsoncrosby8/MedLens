import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { ApiError, api } from '../lib/api'
import type { User } from '../lib/types'
import { AuthContext, TOKEN_STORAGE_KEY, type AuthState } from './authContext'

function readStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY)
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(readStoredToken)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState<boolean>(token !== null)

  const persistToken = useCallback((next: string | null) => {
    setToken(next)
    try {
      if (next) localStorage.setItem(TOKEN_STORAGE_KEY, next)
      else localStorage.removeItem(TOKEN_STORAGE_KEY)
    } catch {
      // storage unavailable (private mode etc.) — the in-memory token still works for this session
    }
  }, [])

  const logout = useCallback(() => {
    persistToken(null)
    setUser(null)
  }, [persistToken])

  // Validate the current token (on first load, or after login sets a new one) and
  // load the user. `loading` is only cleared from the async continuations below.
  useEffect(() => {
    if (!token) return
    let cancelled = false
    api
      .me(token)
      .then((u) => {
        if (!cancelled) setUser(u)
      })
      .catch((err) => {
        if (!cancelled && err instanceof ApiError && err.status === 401) logout()
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [token, logout])

  const login = useCallback(
    async (email: string, password: string) => {
      const { access_token } = await api.login(email, password)
      // Storing the token triggers the effect above, which loads the user.
      persistToken(access_token)
    },
    [persistToken],
  )

  const signup = useCallback(
    async (email: string, password: string) => {
      await api.signup(email, password)
      await login(email, password)
    },
    [login],
  )

  const value: AuthState = { token, user, loading, login, signup, logout }
  return <AuthContext value={value}>{children}</AuthContext>
}
