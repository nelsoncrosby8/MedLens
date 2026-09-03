export type Label = 'NORMAL' | 'PNEUMONIA'

export interface User {
  id: number
  email: string
}

export interface Token {
  access_token: string
  token_type: string
}

/** Response from POST /predict. `heatmap` is a base64 JPEG data URI (not persisted). */
export interface PredictResponse {
  id: number
  label: Label
  probability: number
  created_at: string
  heatmap: string
}

/** One row from GET /history. */
export interface PredictionRead {
  id: number
  label: Label
  probability: number
  filename: string | null
  created_at: string
}
