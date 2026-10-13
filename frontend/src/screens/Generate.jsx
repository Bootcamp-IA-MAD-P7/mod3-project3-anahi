import { useEffect, useRef, useState } from 'react'
import { signOut } from '../auth'
import { streamGenerate } from '../api'
import PlatformGrid from '../components/PlatformGrid'
import ToneSelector from '../components/ToneSelector'
import ResultCard from '../components/ResultCard'
import ProgressOverlay from '../components/ProgressOverlay'
import Toast from '../components/Toast'

const MODEL = 'openai/gpt-oss-120b'
const PROVIDER = 'groq'
const LONGFORM_PLATFORMS = ['medium', 'substack']
const CITATIONS_PLATFORMS = ['medium', 'substack']
const PLATFORM_URLS = {
  linkedin: 'https://www.linkedin.com',
  instagram: 'https://www.instagram.com',
  medium: 'https://medium.com',
  substack: 'https://substack.com',
}
const PLATFORM_NAMES = {
  linkedin: 'LinkedIn',
  instagram: 'Instagram',
  medium: 'Medium',
  substack: 'Substack',
}
const PLATFORM_ICONS = {
  linkedin: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <path d="M4.98 3.5A2.5 2.5 0 1 1 0 3.5a2.5 2.5 0 0 1 4.98 0zM.5 8.5h4.9V24H.5V8.5zM8.5 8.5h4.7v2.1h.07c.65-1.2 2.25-2.5 4.63-2.5 4.95 0 5.87 3.15 5.87 7.2V24h-4.9v-7.4c0-1.76-.03-4.03-2.46-4.03-2.46 0-2.84 1.92-2.84 3.9V24H8.5V8.5z" />
    </svg>
  ),
  instagram: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2.16c3.2 0 3.58.01 4.85.07 3.25.15 4.77 1.69 4.92 4.92.06 1.27.07 1.65.07 4.85s-.01 3.58-.07 4.85c-.15 3.23-1.66 4.77-4.92 4.92-1.27.06-1.64.07-4.85.07s-3.58-.01-4.85-.07c-3.26-.15-4.77-1.7-4.92-4.92-.06-1.27-.07-1.64-.07-4.85s.01-3.58.07-4.85C2.38 3.92 3.9 2.38 7.15 2.23 8.42 2.17 8.8 2.16 12 2.16zM12 0C8.74 0 8.33.01 7.05.07 2.7.27.27 2.69.07 7.05.01 8.33 0 8.74 0 12s.01 3.67.07 4.95c.2 4.36 2.62 6.78 6.98 6.98C8.33 23.99 8.74 24 12 24s3.67-.01 4.95-.07c4.35-.2 6.78-2.62 6.98-6.98.06-1.28.07-1.69.07-4.95s-.01-3.67-.07-4.95c-.2-4.35-2.62-6.78-6.98-6.98C15.67.01 15.26 0 12 0zm0 5.84A6.16 6.16 0 1 0 12 18.16 6.16 6.16 0 0 0 12 5.84zm0 10.16A4 4 0 1 1 12 8a4 4 0 0 1 0 8zm6.41-11.85a1.44 1.44 0 1 1-2.88 0 1.44 1.44 0 0 1 2.88 0z" />
    </svg>
  ),
  medium: (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V4H6.5A2.5 2.5 0 0 0 4 6.5v13z" />
      <path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5" />
    </svg>
  ),
  substack: (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M3 7l9 6 9-6" />
    </svg>
  ),
}

export default function Generate({ userContext, onSettings }) {
  const [platform, setPlatform] = useState('linkedin')
  const [tone, setTone] = useState('professional')
  const [topic, setTopic] = useState('')
  const [audience, setAudience] = useState('')
  const [language, setLanguage] = useState('English')
  const [image, setImage] = useState(false)
  const [citations, setCitations] = useState(false)
  const [busy, setBusy] = useState(false)
  const [lines, setLines] = useState([])
  const [overlayVisible, setOverlayVisible] = useState(false)
  const [result, setResult] = useState(null)
  const [toast, setToast] = useState({ id: 0, msg: '' })
  const topicRef = useRef(null)
  const nextLineId = useRef(0)

  useEffect(() => {
    document.title = 'SayLess — Generate'
  }, [])

  useEffect(() => {
    document.body.classList.toggle('is-generating', overlayVisible)
    return () => document.body.classList.remove('is-generating')
  }, [overlayVisible])

  const showToast = (msg) => setToast((t) => ({ id: t.id + 1, msg }))
  const citationsAllowed = CITATIONS_PLATFORMS.includes(platform)

  function handlePlatform(id) {
    setPlatform(id)
    if (!CITATIONS_PLATFORMS.includes(id)) setCitations(false)
  }

  function startProgress() {
    nextLineId.current += 1
    setLines([
      { id: nextLineId.current, text: 'Reading your brief', done: false },
    ])
    setOverlayVisible(true)
  }

  function addLine(text) {
    nextLineId.current += 1
    const id = nextLineId.current
    setLines((prev) => [
      ...prev.map((line) => ({ ...line, done: true })),
      { id, text, done: false },
    ])
  }

  function finishProgress() {
    setLines((prev) => prev.map((line) => ({ ...line, done: true })))
    setTimeout(() => setOverlayVisible(false), 400)
  }

  async function runGenerate() {
    if (busy) return
    const trimmedTopic = topic.trim()
    if (!trimmedTopic) {
      showToast('Add a topic to get started')
      topicRef.current?.focus()
      return
    }
    setBusy(true)
    setResult(null)
    startProgress()
    const payload = {
      topic: trimmedTopic,
      platform: platform.toLowerCase(),
      tone: tone.toLowerCase(),
      audience: audience.trim(),
      language,
      model: MODEL,
      provider: PROVIDER,
      image_enabled: image,
      citations_enabled:
        citations && CITATIONS_PLATFORMS.includes(platform.toLowerCase()),
      user_context: userContext,
    }
    try {
      await streamGenerate(
        payload,
        addLine,
        (data) => {
          finishProgress()
          setResult({
            text: data.generated_text || '',
            image: data.image_data || null,
          })
          showToast('Draft ready to review')
          setBusy(false)
        },
        (message) => {
          finishProgress()
          showToast(message)
          setBusy(false)
        },
      )
    } catch (err) {
      finishProgress()
      showToast(err.message || 'Cannot reach the server')
      setBusy(false)
    }
  }

  async function handleLogout() {
    try {
      await signOut()
    } catch {
      // redirect even if the server call fails
    }
    window.location.href = '/login'
  }

  function handleCopy() {
    navigator.clipboard
      .writeText(result.text)
      .then(() => showToast('Copied to clipboard'))
      .catch(() => showToast('Could not copy the text'))
  }

  function handleOpen() {
    window.open(PLATFORM_URLS[platform], '_blank', 'noopener')
  }

  function handleAgain() {
    window.scrollTo({ top: 0, behavior: 'smooth' })
    runGenerate()
  }

  return (
    <>
      <header className="topbar">
        <a
          className="topbar-brand"
          href="#"
          onClick={(event) => event.preventDefault()}
        >
          <img className="brand-logo" src="/sayless-logo.png" alt="SayLess" />
        </a>
        <nav className="nav-tabs">
          <a
            className="nav-tab is-active"
            href="#"
            onClick={(event) => event.preventDefault()}
          >
            Generate
          </a>
          <a
            className="nav-tab"
            href="#"
            onClick={(event) => {
              event.preventDefault()
              onSettings()
            }}
          >
            Settings
          </a>
          <button
            className="nav-tab nav-tab-btn"
            id="logout-btn"
            type="button"
            onClick={handleLogout}
          >
            Log out
          </button>
        </nav>
      </header>

      <main className="content content-tall">
        <section className="workspace" id="workspace">
          <div className="ws-head">
            <div>
              <p className="eyebrow">From a small idea to a great post</p>
              <h1 className="ws-title">Generate post</h1>
              <p className="ws-sub">
                Bring the idea. We'll help you find the words
              </p>
            </div>
          </div>

          <PlatformGrid selected={platform} onSelect={handlePlatform} />

          <div className="field field-topic">
            <label className="field-label" htmlFor="topic">
              Topic
            </label>
            <textarea
              className="textarea"
              id="topic"
              placeholder="What would you like to write about?"
              ref={topicRef}
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
            />
            <p className="hint">One clear idea gives a strong start</p>
          </div>

          <div className="fields-2col">
            <div className="field">
              <label className="field-label" htmlFor="audience">
                Audience
              </label>
              <input
                className="input"
                type="text"
                id="audience"
                placeholder="Who is this for?"
                value={audience}
                onChange={(event) => setAudience(event.target.value)}
              />
            </div>
            <div className="field">
              <label className="field-label" htmlFor="language">
                Language
              </label>
              <select
                className="select"
                id="language"
                value={language}
                onChange={(event) => setLanguage(event.target.value)}
              >
                <option value="English">English</option>
                <option value="Spanish">Spanish</option>
                <option value="French">French</option>
                <option value="Italian">Italian</option>
              </select>
            </div>
          </div>

          <div className="field">
            <span className="field-label">Tone</span>
            <ToneSelector selected={tone} onSelect={setTone} />
          </div>

          <div className="options-row">
            <div className="toggle-unit">
              <button
                type="button"
                className={image ? 'toggle is-on' : 'toggle'}
                id="toggle-image"
                data-toggle="image"
                aria-pressed={String(image)}
                onClick={() => setImage((current) => !current)}
              ></button>
              <span className="toggle-meta">
                <span className="toggle-title">Include an image</span>
                <span className="toggle-desc">
                  Add a matching visual to the draft
                </span>
              </span>
            </div>
            <div className="toggle-unit">
              <button
                type="button"
                className={citations ? 'toggle is-on' : 'toggle'}
                id="toggle-citations"
                data-toggle="citations"
                aria-pressed={String(citations)}
                disabled={!citationsAllowed}
                onClick={() => setCitations((current) => !current)}
              ></button>
              <span className="toggle-meta">
                <span className="toggle-title">Include citations</span>
                <span className="toggle-desc">
                  Reference sources from the research pass
                </span>
              </span>
            </div>
          </div>

          <div className="ws-footer">
            <p className="ws-note">Every draft uses your saved context</p>
            <button
              className="btn btn-primary"
              type="button"
              onClick={runGenerate}
            >
              Generate
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
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </button>
          </div>

          <ProgressOverlay visible={overlayVisible} lines={lines} />
        </section>

        {result && (
          <ResultCard
            icon={PLATFORM_ICONS[platform]}
            platformName={PLATFORM_NAMES[platform]}
            text={result.text}
            isLongform={LONGFORM_PLATFORMS.includes(platform)}
            image={result.image}
            onClose={() => setResult(null)}
            onOpen={handleOpen}
            onCopy={handleCopy}
            onAgain={handleAgain}
          />
        )}
      </main>
      {toast.msg && <Toast key={toast.id} message={toast.msg} />}
    </>
  )
}
