import { Link } from 'react-router-dom'
import { AuthForm } from './AuthForm'
import { useAuth } from './useAuth'

export function SignupPage() {
  const { signup } = useAuth()
  return (
    <AuthForm
      title="Create your MedLens account"
      submitLabel="Sign up"
      action={signup}
      passwordAutoComplete="new-password"
      footer={
        <>
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-sky-600 hover:underline">
            Log in
          </Link>
        </>
      }
    />
  )
}
