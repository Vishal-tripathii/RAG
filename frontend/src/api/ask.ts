import { apiPost } from './client'
import type { AskResponse } from '../types'

export function askQuestion(query: string, top_k = 5): Promise<AskResponse> {
  return apiPost<AskResponse>('/ask', { query, top_k })
}
