import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from './api'

function mockFetch(status: number, body: unknown) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    text: () => Promise.resolve(typeof body === 'string' ? body : JSON.stringify(body)),
  } as Response)
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('api client', () => {
  it('login posts form-encoded credentials and returns the token', async () => {
    const fetchMock = mockFetch(200, { access_token: 'jwt-abc', token_type: 'bearer' })
    vi.stubGlobal('fetch', fetchMock)

    const token = await api.login('a@b.com', 'password123')

    expect(token.access_token).toBe('jwt-abc')
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('http://localhost:8000/auth/login')
    expect(init.method).toBe('POST')
    expect(init.body).toBeInstanceOf(URLSearchParams)
    const params = init.body as URLSearchParams
    expect(params.get('username')).toBe('a@b.com')
    expect(params.get('password')).toBe('password123')
  })

  it('predict sends multipart form data with a bearer header', async () => {
    const fetchMock = mockFetch(200, {
      id: 1,
      label: 'NORMAL',
      probability: 0.1,
      created_at: 'now',
      heatmap: 'data:,',
    })
    vi.stubGlobal('fetch', fetchMock)
    const file = new File([new Uint8Array([1, 2, 3])], 'x.png', { type: 'image/png' })

    await api.predict(file, 'jwt-xyz')

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('http://localhost:8000/predict')
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer jwt-xyz')
    expect(init.body).toBeInstanceOf(FormData)
    expect((init.body as FormData).get('file')).toBeInstanceOf(File)
  })

  it('throws ApiError carrying the detail string on a non-ok response', async () => {
    vi.stubGlobal('fetch', mockFetch(400, { detail: 'Expected an image upload' }))

    await expect(api.predict(new File([''], 'x.txt'), 't')).rejects.toMatchObject({
      name: 'ApiError',
      status: 400,
      detail: 'Expected an image upload',
    })
  })

  it('flattens FastAPI 422 validation detail arrays', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch(422, { detail: [{ msg: 'field required' }, { msg: 'too short' }] }),
    )

    await expect(api.me('t')).rejects.toMatchObject({
      status: 422,
      detail: 'field required; too short',
    })
  })
})
