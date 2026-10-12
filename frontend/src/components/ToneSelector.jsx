const TONES = [
  { id: 'professional', label: 'Professional' },
  { id: 'casual', label: 'Casual' },
  { id: 'inspirational', label: 'Inspirational' },
  { id: 'technical', label: 'Technical' },
]

export default function ToneSelector({ selected, onSelect }) {
  return (
    <div className="tone-row" id="tone-row">
      {TONES.map((tone) => (
        <button
          key={tone.id}
          type="button"
          className={selected === tone.id ? 'tone-pill is-active' : 'tone-pill'}
          data-tone={tone.id}
          onClick={() => onSelect(tone.id)}
        >
          {tone.label}
        </button>
      ))}
    </div>
  )
}
