const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'

// Backend errors are FastAPI's default HTTPException body: {"detail": "..."}.
// Wrapping that in a real Error (with the HTTP status attached) lets callers
// tell "no results" apart from "the request itself failed" without parsing
// response bodies at every call site.
export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(response.status, body?.detail ?? response.statusText)
  }

  return response.json() as Promise<T>
}

export function apiPost<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  // No Content-Type here — the browser sets multipart/form-data with the
  // right boundary itself. Setting it manually breaks the upload.
  return request<T>(path, { method: 'POST', body: formData })
}
