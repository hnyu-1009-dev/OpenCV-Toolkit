import http from '@/services/http'

export interface GalleryRecord {
  id: string
  user_id: string
  file_url: string
  file_name?: string | null
  stored_at: string
  filePreviewUrl: string
}

export interface GalleryListResponse {
  items: GalleryRecord[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface GalleryQuery {
  userId: string
  page?: number
  pageSize?: number
  startDate?: string | null
  endDate?: string | null
}

export const fetchGallery = (query: GalleryQuery) => {
  const { userId, page, pageSize, startDate, endDate } = query
  return http.get<GalleryListResponse>(`/dashboard/gallery/${userId}`, {
    params: {
      page,
      page_size: pageSize,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    },
  })
}

export const deleteGallery = (itemId: string, userId?: string) => {
  return http.delete(`/dashboard/gallery/${itemId}`, {
    params: userId ? { user_id: userId } : undefined,
  })
}

