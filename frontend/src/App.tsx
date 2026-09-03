import { Navigate, Route, Routes } from 'react-router-dom'
import { LoginPage } from './auth/LoginPage'
import { RequireAuth } from './auth/RequireAuth'
import { SignupPage } from './auth/SignupPage'
import { DisclaimerFooter } from './components/DisclaimerFooter'
import { Nav } from './components/Nav'
import { HistoryPage } from './history/HistoryPage'
import { UploadPage } from './upload/UploadPage'

function App() {
  return (
    <div className="flex min-h-screen flex-col bg-slate-100 text-slate-900">
      <Nav />
      <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-8">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route
            path="/"
            element={
              <RequireAuth>
                <UploadPage />
              </RequireAuth>
            }
          />
          <Route
            path="/history"
            element={
              <RequireAuth>
                <HistoryPage />
              </RequireAuth>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <DisclaimerFooter />
    </div>
  )
}

export default App
