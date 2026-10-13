const CHECK_ICON = (
  <svg
    width="10"
    height="10"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M4 12.5l5 5L20 6.5" />
  </svg>
)

export default function ProgressOverlay({ visible, lines }) {
  return (
    <div
      className={visible ? 'gen-overlay is-visible' : 'gen-overlay'}
      id="gen-overlay"
    >
      <div className="gen-card">
        <div className="gen-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2l1.9 5.8L19.7 9.7l-5.8 1.9L12 17.4l-1.9-5.8L4.3 9.7l5.8-1.9L12 2zm7 12l.95 2.9L22.85 18.05 18.95 15.15 18l2.9-.95L19 14zM5 15l.75 2.25L8 18l-2.25.75L5 21l-.75-2.25L2 18l2.25-.75L5 15z" />
          </svg>
        </div>
        <p className="eyebrow">Generating draft</p>
        <h3 className="gen-h3">Finding the right words…</h3>
        <ul className="gen-list" id="gen-list">
          {lines.map((line) => (
            <li key={line.id} className={line.done ? 'is-done' : undefined}>
              <span className="marker spinner">{line.done && CHECK_ICON}</span>
              <span className="label">{line.text}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
