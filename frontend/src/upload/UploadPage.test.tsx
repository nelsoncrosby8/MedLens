import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthState } from '../auth/authContext'
import { api } from '../lib/api'
import { UploadPage } from './UploadPage'

const authed: AuthState = {
  token: 'tok',
  user: { id: 1, email: 'a@b.com' },
  loading: false,
  login: vi.fn(),
  signup: vi.fn(),
  logout: vi.fn(),
}

function renderUpload() {
  render(
    <MemoryRouter>
      <AuthContext value={authed}>
        <UploadPage />
      </AuthContext>
    </MemoryRouter>,
  )
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('UploadPage', () => {
  it('uploads the chosen image and renders the result with a heatmap', async () => {
    const predict = vi.spyOn(api, 'predict').mockResolvedValue({
      id: 7,
      label: 'PNEUMONIA',
      probability: 0.91,
      created_at: new Date().toISOString(),
      heatmap: 'data:image/jpeg;base64,AAAA',
    })
    renderUpload()

    const file = new File([new Uint8Array([1, 2, 3])], 'chest.png', { type: 'image/png' })
    await userEvent.upload(screen.getByLabelText(/chest x-ray image/i), file)
    await userEvent.click(screen.getByRole('button', { name: /analyze/i }))

    expect(predict).toHaveBeenCalledWith(file, 'tok')
    expect(await screen.findByText('PNEUMONIA')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: /heatmap/i })).toHaveAttribute(
      'src',
      'data:image/jpeg;base64,AAAA',
    )
  })

  it('rejects a non-image file before calling the API', async () => {
    const predict = vi.spyOn(api, 'predict')
    renderUpload()

    // applyAccept:false so the input's accept="image/*" doesn't filter the file out
    // before our own client-side check runs.
    const user = userEvent.setup({ applyAccept: false })
    const txt = new File(['hello'], 'notes.txt', { type: 'text/plain' })
    await user.upload(screen.getByLabelText(/chest x-ray image/i), txt)

    expect(await screen.findByRole('alert')).toHaveTextContent(/image file/i)
    expect(screen.getByRole('button', { name: /analyze/i })).toBeDisabled()
    expect(predict).not.toHaveBeenCalled()
  })
})
