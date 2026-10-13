export default function ResultCard({
  icon,
  platformName,
  text,
  isLongform,
  image,
  onClose,
  onOpen,
  onCopy,
  onAgain,
}) {
  return (
    <section className="result" id="result">
      <div className="result-head">
        <div>
          <h2 className="result-title">Ready to share</h2>
        </div>
        <button className="btn-text" type="button" onClick={onClose}>
          Close
        </button>
      </div>
      <article className="result-card">
        <header className="result-strip">
          <div className="strip-left">
            <span className="p-icon" id="result-icon">
              {icon}
            </span>
            <span id="result-platform">{platformName}</span>
          </div>
          <button
            className="icon-btn"
            type="button"
            aria-label="Open platform"
            onClick={onOpen}
          >
            <svg
              width="13"
              height="13"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M14 4h6v6M20 4L10 14M18 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h6" />
            </svg>
          </button>
        </header>
        <div
          className={isLongform ? 'result-body is-longform' : 'result-body'}
          id="result-body"
        >
          {text}
          {image && (
            <img
              src={`data:image/png;base64,${image}`}
              alt="Generated visual"
            />
          )}
        </div>
        <footer className="result-actions">
          <button className="btn btn-secondary" type="button" onClick={onCopy}>
            Copy text
          </button>
          <button className="btn btn-primary" type="button" onClick={onAgain}>
            Generate again
          </button>
        </footer>
      </article>
    </section>
  )
}
