import { useEffect, useState } from 'react'
import { signIn, signUp } from '../auth'
import { getMe } from '../api'

export default function Login({ onSuccess }) {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fieldErrors, setFieldErrors] = useState({ email: '', password: '' })

  useEffect(() => {
    document.title = 'SayLess — Sign in'
  }, [])

  async function handleSubmit(event) {
    event.preventDefault()
    try {
      if (mode === 'login') await signIn(email, password)
      else await signUp(email, password)
      const me = await getMe().catch(() => null)
      onSuccess(me?.user_context || '')
    } catch (err) {
      const message = err.message || 'Could not sign you in'
      const lower = message.toLowerCase()
      if (lower.includes('password') || lower === 'invalid credentials') {
        setFieldErrors({ email: '', password: message })
      } else if (
        lower.includes('not found') ||
        lower.includes('no user') ||
        lower.includes('email')
      ) {
        setFieldErrors({ email: message, password: '' })
      } else {
        setFieldErrors({ email: message, password: message })
      }
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
                  className={
                    fieldErrors.email
                      ? 'login-input auth-input-wrap--error'
                      : 'login-input'
                  }
                  type="email"
                  id="email"
                  name="email"
                  placeholder="you@example.com"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(event) => {
                    setEmail(event.target.value)
                    setFieldErrors((prev) => ({ ...prev, email: '' }))
                  }}
                />
                {fieldErrors.email && (
                  <span className="field-error" role="alert">
                    {fieldErrors.email}
                  </span>
                )}
              </div>
              <div className="login-pw-row">
                <label className="login-label" htmlFor="password">
                  Password
                </label>
                {/* TODO: password reset — implement once Neon Auth reset flow is confirmed */}
                <button className="login-forgot" type="button" disabled>
                  Forgot password?
                </button>
              </div>
              <div>
                <input
                  className={
                    fieldErrors.password
                      ? 'login-input auth-input-wrap--error'
                      : 'login-input'
                  }
                  type="password"
                  id="password"
                  name="password"
                  placeholder="Your password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(event) => {
                    setPassword(event.target.value)
                    setFieldErrors((prev) => ({ ...prev, password: '' }))
                  }}
                />
                {fieldErrors.password && (
                  <span className="field-error" role="alert">
                    {fieldErrors.password}
                  </span>
                )}
              </div>
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
    </div>
  )
}
