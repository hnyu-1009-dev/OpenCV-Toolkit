import http from '@/services/http'

// 登录接口所需字段约束
export interface LoginPayload {
  email: string
  password: string
}

// 注册接口在登录字段基础上，增加姓名/手机号/确认密码
export interface RegisterPayload extends LoginPayload {
  name: string
  confirmPassword: string
  phone: string
}

// 后端返回的鉴权数据结构
export interface AuthResponse {
  token: string
  user: {
    id: string
    name: string
    email: string
    phone?: string
  }
}

// 登录接口：返回 token 与用户信息
export const login = (payload: LoginPayload) => http.post<AuthResponse>('/auth/login', payload)

// 注册接口：创建用户后同样返回 token 与用户信息
export const register = (payload: RegisterPayload) => http.post<AuthResponse>('/auth/register', payload)
