import { useEffect, useState } from 'react'
import { signIn, signUp } from '../auth'
import { getMe } from '../api'
import Toast from '../components/Toast'

export default function Login({ onSuccess }) {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [toast, setToast] = useState({ id: 0, msg: '' })

  useEffect(() => {
    document.title = 'SayLess — Sign in'
  }, [])

  const showToast = (msg) => setToast((t) => ({ id: t.id + 1, msg }))

  async function handleSubmit(event) {
    event.preventDefault()
    try {
      if (mode === 'login') await signIn(email, password)
      else await signUp(email, password)
      const me = await getMe().catch(() => null)
      onSuccess(me?.user_context || '')
    } catch (err) {
      showToast(err.message || 'Could not sign you in')
    }
  }

  return (
    <div className="page-login">
      <main className="login-card">
        <div className="login-hero">
          <img className="login-photo" src="/login-hero.jpg" alt="" />
          <div className="login-wash"></div>
          <img className="hero-logo" src="/sayless-logo.png" alt="SayLess" />
          <div className="hero-copy">
            <h2 className="hero-title">
              Your voice.
              <br />
              Room to grow.
            </h2>
            <p className="hero-body">
              Write posts that sound like you for the platforms your audience
              already lives on
            </p>
            <p className="hero-italic">Made for meaningful words.</p>
          </div>
        </div>
        <div className="login-panel">
          <div className="login-col">
            <p className="eyebrow">Your creative space</p>
            <h1 className="login-h1">
              {mode === 'login' ? 'Welcome back' : 'Create an account'}
            </h1>
            <p className="login-sub">
              Good ideas start here. Sign in to make them yours.
            </p>
            <form id="login-form" onSubmit={handleSubmit}>
              <div className="login-field">
                <label className="login-label" htmlFor="email">
                  Email address
                </label>
                <input
                  className="login-input"
                  type="email"
                  id="email"
                  name="email"
                  placeholder="you@example.com"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </div>
              <div className="login-pw-row">
                <label className="login-label" htmlFor="password">
                  Password
                </label>
                <button
                  className="login-forgot"
                  type="button"
                  onClick={() => showToast('Check your inbox for a reset link')}
                >
                  Forgot password?
                </button>
              </div>
              <input
                className="login-input"
                type="password"
                id="password"
                name="password"
                placeholder="Your password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
              <button className="btn-login" type="submit">
                {mode === 'login' ? 'Sign in' : 'Create account'}
              </button>
            </form>
            <p className="login-new">
              {mode === 'login' ? (
                <>
                  {'New? '}
                  <button type="button" onClick={() => setMode('signup')}>
                    Create an account
                  </button>
                </>
              ) : (
                <>
                  {'Already have an account? '}
                  <button type="button" onClick={() => setMode('login')}>
                    Sign in
                  </button>
                </>
              )}
            </p>
            <p className="login-tagline">
              Bring the idea. We'll help you find the words.
            </p>
          </div>
        </div>
      </main>
      {toast.msg && <Toast key={toast.id} message={toast.msg} />}
    </div>
  )
}
