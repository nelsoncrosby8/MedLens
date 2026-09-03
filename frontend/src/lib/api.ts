import type { PredictionRead, PredictResponse, Token, User } from './types'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/** Thrown for any non-2xx API response. `detail` is the human-readable message. */
export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

/** Pull a readable message out of FastAPI's `{detail: string}` or `{detail: [{msg}]}` (422). */
function extractDetail(body: unknown, fallback: string): string {
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      const msgs = detail
        .map((d) => (d && typeof d === 'object' && 'msg' in d ? String((d as { msg: unknown }).msg) : null))
        .filter(Boolean)
      if (msgs.length) return msgs.join('; ')
    }
  }
  return fallback
}

interface RequestOptions {
  method?: string
  token?: string | null
  json?: unknown
  form?: FormData | URLSearchParams
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {}
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`

  let body: BodyInit | undefined
  if (opts.json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(opts.json)
  } else if (opts.form !== undefined) {
    body = opts.form // browser sets the right Content-Type (incl. multipart boundary)
  }

  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, {
      method: opts.method ?? (body ? 'POST' : 'GET'),
      headers,
      body,
    })
  } catch {
    throw new ApiError(0, `Could not reach the API at ${BASE}.`)
  }

  const raw = await res.text()
  const parsed = raw ? safeJson(raw) : null

  if (!res.ok) {
    throw new ApiError(res.status, extractDetail(parsed, `Request failed (${res.status}).`))
  }
  return parsed as T
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

export const api = {
  signup(email: string, password: string): Promise<User> {
    return request<User>('/auth/signup', { json: { email, password } })
  },

  login(email: string, password: string): Promise<Token> {
    // OAuth2 password flow: form-encoded `username` / `password`.
    const form = new URLSearchParams({ username: email, password })
    return request<Token>('/auth/login', { form })
  },

  me(token: string): Promise<User> {
    return request<User>('/auth/me', { token })
  },

  predict(file: File, token: string): Promise<PredictResponse> {
    const form = new FormData()
    form.append('file', file)
    return request<PredictResponse>('/predict', { form, token })
  },

  history(token: string, { limit = 20, offset = 0 } = {}): Promise<PredictionRead[]> {
    return request<PredictionRead[]>(`/history?limit=${limit}&offset=${offset}`, { token })
  },
}
