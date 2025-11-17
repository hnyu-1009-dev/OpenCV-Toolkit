import { defineStore } from 'pinia'

export interface UserProfile {
  id: string
  name: string
  email: string
  phone?: string | null
}

interface AuthState {
  token: string
  user: UserProfile | null
}

const TOKEN_KEY = 'access_token'
const USER_KEY = 'user_profile'

const readUserFromStorage = (): UserProfile | null => {
  const stored = localStorage.getItem(USER_KEY)
  if (!stored) return null
  try {
    return JSON.parse(stored) as UserProfile
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: readUserFromStorage(),
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },
  actions: {
    setAuth(token: string, user: UserProfile) {
      this.token = token
      this.user = user
      localStorage.setItem(TOKEN_KEY, token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    },
    updateProfile(user: UserProfile) {
      this.user = user
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
  },
})

export const getStoredToken = () => localStorage.getItem(TOKEN_KEY) || ''
