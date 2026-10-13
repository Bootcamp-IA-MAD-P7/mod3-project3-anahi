import { Fragment, useEffect, useRef, useState } from 'react'

export default function Dropdown({ id, value, groups, onSelect }) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)

  const options = groups.flatMap((group) => group.options)
  const selected = options.find((option) => option.value === value)

  useEffect(() => {
    if (!open) return
    function handlePointer(event) {
      if (!rootRef.current?.contains(event.target)) setOpen(false)
    }
    function handleKey(event) {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', handlePointer)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handlePointer)
      document.removeEventListener('keydown', handleKey)
    }
  }, [open])

  return (
    <div className="dropdown" ref={rootRef}>
      <button
        type="button"
        id={id}
        className="dropdown-trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
        onKeyDown={(event) => {
          if (event.key === 'ArrowDown') {
            event.preventDefault()
            setOpen(true)
          }
        }}
      >
        <span>{selected?.label ?? value}</span>
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      {open && (
        <ul className="dropdown-menu" role="listbox" aria-labelledby={id}>
          {groups.map((group) => (
            <Fragment key={group.label ?? 'all'}>
              {group.label && (
                <li className="dropdown-group" role="presentation">
                  {group.label}
                </li>
              )}
              {group.options.map((option) => (
                <li key={option.value}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={option.value === value}
                    className={
                      option.value === value
                        ? 'dropdown-option is-active'
                        : 'dropdown-option'
                    }
                    onClick={() => {
                      onSelect(option.value)
                      setOpen(false)
                    }}
                  >
                    {option.label}
                  </button>
                </li>
              ))}
            </Fragment>
          ))}
        </ul>
      )}
    </div>
  )
}
