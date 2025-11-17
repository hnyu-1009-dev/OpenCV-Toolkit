import http from '@/services/http'
import type { GalleryRecord } from './gallery'

export type ColorBlindMode = 'red_green' | 'blue_green'

export interface ColorBlindPayload {
  file: File
  mode: ColorBlindMode
  saveOriginal?: boolean
  saveProcessed?: boolean
  userId?: string
  rotation?: number
}

export interface ColorBlindResponse {
  processedImage: string
  savedOriginal?: GalleryRecord | null
  savedProcessed?: GalleryRecord | null
}

export interface DocumentScanPayload {
  file: File
  points: Array<{ x: number; y: number }>
  saveOriginal?: boolean
  saveProcessed?: boolean
  userId?: string
  rotation?: number
}

export type DocumentScanResponse = ColorBlindResponse

export const transformColorBlind = (payload: ColorBlindPayload) => {
  const formData = new FormData()
  formData.append('mode', payload.mode)
  formData.append('file', payload.file)

  if (typeof payload.saveOriginal !== 'undefined') {
    formData.append('save_original', String(payload.saveOriginal))
  }

  if (typeof payload.saveProcessed !== 'undefined') {
    formData.append('save_processed', String(payload.saveProcessed))
  }

  if (payload.userId) {
    formData.append('user_id', payload.userId)
  }

  if (typeof payload.rotation === 'number') {
    formData.append('rotation', String(payload.rotation))
  }

  return http.post<ColorBlindResponse>('/dashboard/vision/color-blind', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const scanDocument = (payload: DocumentScanPayload) => {
  const formData = new FormData()
  formData.append('file', payload.file)
  formData.append('points', JSON.stringify(payload.points))

  if (typeof payload.saveOriginal !== 'undefined') {
    formData.append('save_original', String(payload.saveOriginal))
  }

  if (typeof payload.saveProcessed !== 'undefined') {
    formData.append('save_processed', String(payload.saveProcessed))
  }

  if (payload.userId) {
    formData.append('user_id', payload.userId)
  }

  if (typeof payload.rotation === 'number') {
    formData.append('rotation', String(payload.rotation))
  }

  return http.post<DocumentScanResponse>('/dashboard/vision/document-scan', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export interface RotatePayload {
  file: File
  rotation: number
  saveOriginal?: boolean
  saveProcessed?: boolean
  userId?: string
}

export const rotateImage = (payload: RotatePayload) => {
  const formData = new FormData()
  formData.append('file', payload.file)
  formData.append('rotation', String(payload.rotation))

  if (typeof payload.saveOriginal !== 'undefined') {
    formData.append('save_original', String(payload.saveOriginal))
  }

  if (typeof payload.saveProcessed !== 'undefined') {
    formData.append('save_processed', String(payload.saveProcessed))
  }

  if (payload.userId) {
    formData.append('user_id', payload.userId)
  }

  return http.post<ColorBlindResponse>('/dashboard/vision/rotate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export interface ContrastPayload {
  file: File
  contrast: number
  saveOriginal?: boolean
  saveProcessed?: boolean
  userId?: string
}

export const adjustContrast = (payload: ContrastPayload) => {
  const formData = new FormData()
  formData.append('file', payload.file)
  formData.append('contrast', String(payload.contrast))

  if (typeof payload.saveOriginal !== 'undefined') {
    formData.append('save_original', String(payload.saveOriginal))
  }

  if (typeof payload.saveProcessed !== 'undefined') {
    formData.append('save_processed', String(payload.saveProcessed))
  }

  if (payload.userId) {
    formData.append('user_id', payload.userId)
  }

  return http.post<ColorBlindResponse>('/dashboard/vision/contrast', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export interface BrightnessPayload {
  file: File
  brightness: number
  saveOriginal?: boolean
  saveProcessed?: boolean
  userId?: string
}

export const adjustBrightness = (payload: BrightnessPayload) => {
  const formData = new FormData()
  formData.append('file', payload.file)
  formData.append('brightness', String(payload.brightness))

  if (typeof payload.saveOriginal !== 'undefined') {
    formData.append('save_original', String(payload.saveOriginal))
  }

  if (typeof payload.saveProcessed !== 'undefined') {
    formData.append('save_processed', String(payload.saveProcessed))
  }

  if (payload.userId) {
    formData.append('user_id', payload.userId)
  }

  return http.post<ColorBlindResponse>('/dashboard/vision/brightness', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export interface WatermarkPayload {
  file: File
  watermark: File
  position: { x: number; y: number }
  saveOriginal?: boolean
  saveProcessed?: boolean
  userId?: string
}

export const applyWatermark = (payload: WatermarkPayload) => {
  const formData = new FormData()
  formData.append('file', payload.file)
  formData.append('watermark', payload.watermark)
  formData.append('position', JSON.stringify(payload.position))

  if (typeof payload.saveOriginal !== 'undefined') {
    formData.append('save_original', String(payload.saveOriginal))
  }

  if (typeof payload.saveProcessed !== 'undefined') {
    formData.append('save_processed', String(payload.saveProcessed))
  }

  if (payload.userId) {
    formData.append('user_id', payload.userId)
  }

  return http.post<ColorBlindResponse>('/dashboard/vision/watermark', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
