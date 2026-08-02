import { apiUpload } from './client'
import type { UploadResponse } from '../types'

export function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  return apiUpload<UploadResponse>('/upload', formData)
}
