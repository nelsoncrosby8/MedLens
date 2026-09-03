import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { ApiError } from '../lib/api'
import { AuthContext, type AuthState } from './authContext'
import { LoginPage } from './LoginPage'

function renderLogin(overrides: Partial<AuthState> = {}) {
  const auth: AuthState = {
    token: null,
    user: null,
    loading: false,
    login: vi.fn().mockResolvedValue(undefined),
    signup: vi.fn(),
    logout: vi.fn(),
    ...overrides,
  }
  render(
    <MemoryRouter>
      <AuthContext value={auth}>
        <LoginPage />
      </AuthContext>
    </MemoryRouter>,
  )
  return auth
}

describe('LoginPage', () => {
  it('submits the entered credentials', async () => {
    const auth = renderLogin()

    await userEvent.type(screen.getByLabelText(/email/i), 'a@b.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'password123')
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))

    expect(auth.login).toHaveBeenCalledWith('a@b.com', 'password123')
  })

  it('shows the API error message when login fails', async () => {
    renderLogin({
      login: vi.fn().mockRejectedValue(new ApiError(401, 'Incorrect email or password')),
    })

    await userEvent.type(screen.getByLabelText(/email/i), 'a@b.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'wrongpassword')
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Incorrect email or password')
  })
})
