import { Link } from 'react-router-dom'
import { AuthForm } from './AuthForm'
import { useAuth } from './useAuth'

export function LoginPage() {
  const { login } = useAuth()
  return (
    <AuthForm
      title="Log in to MedLens"
      submitLabel="Log in"
      action={login}
      passwordAutoComplete="current-password"
      footer={
        <>
          No account?{' '}
          <Link to="/signup" className="font-medium text-sky-600 hover:underline">
            Sign up
          </Link>
        </>
      }
    />
  )
}
