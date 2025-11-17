import http from '@/services/http'
import type { UserProfile } from '@/stores/auth'

export interface UpdateProfilePayload {
  name?: string
  phone?: string | null
  currentPassword?: string
  newPassword?: string
}

export const getUserProfile = (userId: string) =>
  http.get<UserProfile>(`/users/${userId}`)

export const updateUserProfile = (userId: string, payload: UpdateProfilePayload) =>
  http.patch<UserProfile>(`/users/${userId}`, payload)
