import type { Source } from '../types'

function SourceList({ sources }: { sources: Source[] }) {
  if (sources.length === 0) return null

  return (
    <ul className="source-list">
      {sources.map((source) => (
        <li key={source.n}>
          [{source.n}] {source.filename ?? source.document_id} — p.{source.page} (score{' '}
          {source.score.toFixed(2)})
        </li>
      ))}
    </ul>
  )
}

export default SourceList
