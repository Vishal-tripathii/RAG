import { useState, type FormEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import { askQuestion } from '../api/ask'
import { uploadDocument } from '../api/documents'
import { ApiError } from '../api/client'
import type { Source } from '../types'
import SourceList from '../components/SourceList'

type Turn = {
  id: string
  query: string
  answer: string
  sources: Source[]
}

function Chat() {
  const [turns, setTurns] = useState<Turn[]>([])
  const [query, setQuery] = useState('')
  const [asking, setAsking] = useState(false)
  const [askError, setAskError] = useState<string | null>(null)

  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadMessage, setUploadMessage] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)

  async function handleAsk(event: FormEvent) {
    event.preventDefault()
    if (!query.trim() || asking) return

    setAsking(true)
    setAskError(null)
    try {
      const response = await askQuestion(query)
      setTurns((prev) => [
        ...prev,
        { id: crypto.randomUUID(), query: response.query, answer: response.answer, sources: response.sources },
      ])
      setQuery('')
    } catch (err) {
      setAskError(err instanceof ApiError ? err.message : 'Something went wrong asking that.')
    } finally {
      setAsking(false)
    }
  }

  async function handleUpload(event: FormEvent) {
    event.preventDefault()
    if (!file || uploading) return

    setUploading(true)
    setUploadError(null)
    setUploadMessage(null)
    try {
      const result = await uploadDocument(file)
      setUploadMessage(`Uploaded "${result.filename}" (${(result.size_bytes / 1024).toFixed(1)} KB)`)
      setFile(null)
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="chat-page">
      <form className="upload-bar" onSubmit={handleUpload}>
        <input
          type="file"
          accept=".pdf,application/pdf"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        <button type="submit" disabled={!file || uploading}>
          {uploading ? 'Uploading…' : 'Upload PDF'}
        </button>
        {uploadMessage && <span className="upload-status success">{uploadMessage}</span>}
        {uploadError && <span className="upload-status error">{uploadError}</span>}
      </form>

      <div className="chat-turns">
        {turns.length === 0 && <p className="chat-empty">Ask a question about your uploaded documents.</p>}
        {turns.map((turn) => (
          <div key={turn.id} className="chat-turn">
            <p className="chat-query">{turn.query}</p>
            <div className="chat-answer">
              <ReactMarkdown>{turn.answer}</ReactMarkdown>
            </div>
            <SourceList sources={turn.sources} />
          </div>
        ))}
      </div>

      <form className="chat-input-bar" onSubmit={handleAsk}>
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Ask a question…"
          disabled={asking}
        />
        <button type="submit" disabled={asking || !query.trim()}>
          {asking ? 'Asking…' : 'Ask'}
        </button>
      </form>
      {askError && <p className="chat-error">{askError}</p>}
    </div>
  )
}

export default Chat
