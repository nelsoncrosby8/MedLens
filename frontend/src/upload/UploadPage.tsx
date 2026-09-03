import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { ErrorBanner } from '../components/ErrorBanner'
import { Spinner } from '../components/Spinner'
import { ApiError, api } from '../lib/api'
import type { PredictResponse } from '../lib/types'
import { ResultView } from './ResultView'

const MAX_BYTES = 5 * 1024 * 1024

export function UploadPage() {
  const { token, logout } = useAuth()
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [result, setResult] = useState<PredictResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  function choose(next: File | null) {
    setError(null)
    setResult(null)
    setPreviewUrl((old) => {
      if (old) URL.revokeObjectURL(old)
      return null
    })
    setFile(null)

    if (!next) return
    if (!next.type.startsWith('image/')) {
      setError('Please choose an image file.')
      return
    }
    if (next.size > MAX_BYTES) {
      setError('That image is larger than the 5 MB limit.')
      return
    }
    setFile(next)
    setPreviewUrl(URL.createObjectURL(next))
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!file || !token) return
    setBusy(true)
    setError(null)
    setResult(null)
    try {
      setResult(await api.predict(file, token))
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        logout()
        navigate('/login', { replace: true })
        return
      }
      setError(err instanceof ApiError ? err.detail : 'Prediction failed. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Analyze a chest X-ray</h1>
      <p className="mt-1 text-sm text-slate-600">
        Upload an image; MedLens returns a pneumonia triage estimate and a Grad-CAM heatmap.
      </p>

      <form
        onSubmit={onSubmit}
        className="mt-6 space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
      >
        {error && <ErrorBanner message={error} />}
        <input
          type="file"
          accept="image/*"
          aria-label="Chest X-ray image"
          onChange={(e) => choose(e.target.files?.[0] ?? null)}
          className="block w-full text-sm text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-slate-900 file:px-4 file:py-2 file:text-white hover:file:bg-slate-800"
        />
        {file && <p className="text-sm text-slate-500">Selected: {file.name}</p>}
        <button
          type="submit"
          disabled={!file || busy}
          className="rounded-md bg-sky-600 px-4 py-2 font-medium text-white hover:bg-sky-700 disabled:opacity-50"
        >
          {busy ? 'Analyzing…' : 'Analyze'}
        </button>
      </form>

      {busy && <Spinner label="Running the model…" />}
      {result && previewUrl && <ResultView result={result} previewUrl={previewUrl} />}
    </div>
  )
}
