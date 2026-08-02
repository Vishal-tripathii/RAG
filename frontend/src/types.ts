export type Source = {
  n: number
  filename: string | null
  document_id: string
  page: number
  score: number
  text: string
}

export type AskResponse = {
  query: string
  answer: string
  sources: Source[]
}

export type UploadResponse = {
  doc_id: string
  filename: string
  content_type: string | null
  size_bytes: number
  saved_path: string
}
