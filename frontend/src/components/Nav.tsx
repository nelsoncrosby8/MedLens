import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'

const linkBase = 'rounded px-3 py-1.5 text-sm font-medium transition-colors'
const linkClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? `${linkBase} bg-slate-900 text-white` : `${linkBase} text-slate-600 hover:bg-slate-100`

export function Nav() {
  const { user, token, logout } = useAuth()

  return (
    <header className="border-b border-slate-200 bg-white">
      <nav className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
        <span className="text-lg font-semibold text-slate-900">
          Med<span className="text-sky-600">Lens</span>
        </span>

        {token && (
          <div className="flex items-center gap-2">
            <NavLink to="/" className={linkClass} end>
              Upload
            </NavLink>
            <NavLink to="/history" className={linkClass}>
              History
            </NavLink>
            {user && <span className="ml-2 hidden text-sm text-slate-500 sm:inline">{user.email}</span>}
            <button
              type="button"
              onClick={logout}
              className="rounded px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Log out
            </button>
          </div>
        )}
      </nav>
    </header>
  )
}
