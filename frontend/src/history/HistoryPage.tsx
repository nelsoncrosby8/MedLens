import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { ErrorBanner } from '../components/ErrorBanner'
import { Spinner } from '../components/Spinner'
import { ApiError, api } from '../lib/api'
import type { PredictionRead } from '../lib/types'

const PAGE = 20

export function HistoryPage() {
  const { token, logout } = useAuth()
  const navigate = useNavigate()
  const [rows, setRows] = useState<PredictionRead[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [atEnd, setAtEnd] = useState(false)

  const handleError = useCallback(
    (err: unknown) => {
      if (err instanceof ApiError && err.status === 401) {
        logout()
        navigate('/login', { replace: true })
        return
      }
      setError(err instanceof ApiError ? err.detail : 'Could not load your history.')
    },
    [logout, navigate],
  )

  useEffect(() => {
    if (!token) return
    let cancelled = false
    api
      .history(token, { limit: PAGE, offset: 0 })
      .then((page) => {
        if (cancelled) return
        setRows(page)
        if (page.length < PAGE) setAtEnd(true)
      })
      .catch((err) => {
        if (!cancelled) handleError(err)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [token, handleError])

  async function onLoadMore() {
    if (!token) return
    setLoadingMore(true)
    try {
      const page = await api.history(token, { limit: PAGE, offset: rows.length })
      setRows((prev) => [...prev, ...page])
      if (page.length < PAGE) setAtEnd(true)
    } catch (err) {
      handleError(err)
    } finally {
      setLoadingMore(false)
    }
  }

  if (loading) return <Spinner label="Loading history…" />

  return (
    <div>
      <h1 className="text-2xl font-semibold">Your predictions</h1>

      {error && (
        <div className="mt-4">
          <ErrorBanner message={error} />
        </div>
      )}

      {rows.length === 0 && !error ? (
        <p className="mt-6 text-slate-600">No predictions yet. Upload an X-ray to get started.</p>
      ) : (
        <div className="mt-6 overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-slate-500">
              <tr>
                <th className="px-4 py-2 font-medium">Date</th>
                <th className="px-4 py-2 font-medium">File</th>
                <th className="px-4 py-2 font-medium">Result</th>
                <th className="px-4 py-2 font-medium">Probability</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-b border-slate-100 last:border-0">
                  <td className="px-4 py-2 text-slate-600">
                    {new Date(row.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-2 text-slate-600">{row.filename ?? '—'}</td>
                  <td className="px-4 py-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                        row.label === 'PNEUMONIA'
                          ? 'bg-red-100 text-red-700'
                          : 'bg-emerald-100 text-emerald-700'
                      }`}
                    >
                      {row.label}
                    </span>
                  </td>
                  <td className="px-4 py-2 tabular-nums text-slate-700">
                    {(row.probability * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!atEnd && rows.length > 0 && (
        <button
          type="button"
          onClick={onLoadMore}
          disabled={loadingMore}
          className="mt-4 rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50"
        >
          {loadingMore ? 'Loading…' : 'Load more'}
        </button>
      )}
    </div>
  )
}
