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
    <>
      <main className="content">
        <section className="onboard-card">
          <button
            className="icon-btn onboard-close"
            type="button"
            aria-label="Close"
            onClick={handleSkip}
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            >
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
          </button>
          <div className="onboard-col">
            <h1 className="onboard-title">Shape your <em>voice</em></h1>
            <p className="onboard-intro">
              Share the context you want every draft to carry: what you do, who
              you write for, and how you like to sound
            </p>
            <label className="field-label" htmlFor="context">
              Your context
            </label>
            <textarea
              className="textarea onboard-input"
              id="context"
              placeholder="I write about design systems for early stage teams, in a warm and direct voice"
              value={value}
              onChange={(event) => setValue(event.target.value)}
            />
            <button
              className="btn btn-primary onboard-cta"
              type="button"
              onClick={handleContinue}
            >
              Continue
            </button>
            <p className="onboard-note">
              You can update this anytime in settings
            </p>
          </div>
        </section>
      </main>

      <div className="page-tail">
        <a
          className="corner-logo"
          href="#"
          onClick={(event) => {
            event.preventDefault()
            handleSkip()
          }}
        >
          <img className="brand-logo" src="/sayless-logo.png" alt="SayLess" />
        </a>
      </div>
      {toast.msg && <Toast key={toast.id} message={toast.msg} />}
    </>
  )
}
