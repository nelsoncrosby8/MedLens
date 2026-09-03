import { createContext } from 'react'
import type { User } from '../lib/types'

export interface AuthState {
  token: string | null
  user: User | null
  /** True while a stored token is being validated on first load. */
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthState | null>(null)

export const TOKEN_STORAGE_KEY = 'medlens_token'
