import { useEffect, useState } from 'react'
import { getToken } from '../auth'
import { getMe, saveContext } from '../api'
import Toast from '../components/Toast'

export default function Onboarding({ onSave }) {
  const [value, setValue] = useState('')
  const [loaded, setLoaded] = useState('')
  const [toast, setToast] = useState({ id: 0, msg: '' })

  useEffect(() => {
    document.title = 'SayLess — Onboarding'
    getMe()
      .then((me) => {
        if (me?.user_context) {
          setValue(me.user_context)
          setLoaded(me.user_context)
        }
      })
      .catch(() => {})
  }, [])

  const showToast = (msg) => setToast((t) => ({ id: t.id + 1, msg }))

  async function handleContinue() {
    const text = value.trim()
    if (!text) {
      onSave(loaded)
      return
    }
    const token = await getToken().catch(() => null)
    if (!token) {
      showToast('Cannot reach the server')
      return
    }
    try {
      await saveContext(text, true)
    } catch {
      showToast('Cannot reach the server')
      return
    }
    onSave(text)
  }

  function handleSkip() {
    onSave(loaded)
  }

  return (
    <div className="page-onboarding">
      <main className="content content-tall">
        <header className="page-head">
          <p className="eyebrow">
            Welcome to <span className="eyebrow-brand">SayLess</span>
          </p>
          <h1 className="page-title">Onboarding</h1>
          <p className="page-sub">
            Tell us about you so every draft starts in your voice
          </p>
        </header>

        <div className="onboard-stage">
          <a
            className="corner-logo onboard-brand"
            href="#"
            onClick={(event) => {
              event.preventDefault()
              handleSkip()
            }}
          >
            <img className="brand-logo" src="/sayless-logo.png" alt="SayLess" />
          </a>
          <section className="settings-split">
            <div className="settings-form">
              <div className="settings-form-head">
                <h2 className="ws-title">Publishing context</h2>
              </div>
              <p className="settings-lead">
                Give SayLess the background behind your words. This context is
                used as a starting point for every post.
              </p>
              <label className="field-label" htmlFor="onboarding-context">
                About you or your company
              </label>
              <textarea
                className="textarea textarea-settings"
                id="onboarding-context"
                placeholder="Share what you do, who you write for, and how you like to sound"
                value={value}
                onChange={(event) => setValue(event.target.value)}
              />
              <p className="hint">
                Include what you do, what you believe, and how you like to sound.
              </p>
              <p className="privacy-note">
                <svg
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <rect x="5" y="11" width="14" height="10" rx="2" />
                  <path d="M8 11V7a4 4 0 0 1 8 0v4" />
                </svg>
                <span>
                  Only used to personalise your drafts. It won't appear as public
                  content.
                </span>
              </p>
              <div className="settings-actions">
                <button className="btn btn-clay" type="button" onClick={handleContinue}>
                  Continue
                </button>
                <button className="btn btn-secondary" type="button" onClick={handleSkip}>
                  Skip for now
                </button>
              </div>
            </div>
            <aside className="settings-tip">
              <img className="tip-photo" src="/login-hero.jpg" alt="" />
              <div className="tip-content">
                <h2 className="tip-title">
                  The roots of a
                  <br />
                  great post.
                </h2>
                <p className="tip-desc">
                  A few useful details to give your writing a
                  <br />
                  natural starting point:
                </p>
              </div>
              <div className="tip-items">
                <div className="tip-item">
                  <p className="tip-label">Who you are</p>
                  <p className="tip-text">Your role, company, or creative practice.</p>
                </div>
                <div className="tip-item">
                  <p className="tip-label">What you care about</p>
                  <p className="tip-text">
                    The ideas and values you want to share.
                  </p>
                </div>
                <div className="tip-item">
                  <p className="tip-label">How you sound</p>
                  <p className="tip-text">
                    Your personality, style, and point of view.
                  </p>
                </div>
              </div>
            </aside>
          </section>
        </div>
      </main>

      {toast.msg && <Toast key={toast.id} message={toast.msg} />}
    </div>
  )
}
