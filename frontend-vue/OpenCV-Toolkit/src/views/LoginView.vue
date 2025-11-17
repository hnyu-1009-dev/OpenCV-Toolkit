<script setup lang="ts">
import { reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { login as loginRequest } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

interface LoginForm {
  email: string
  password: string
}

const router = useRouter()
const authStore = useAuthStore()
const loginFormRef = ref<FormInstance>()
const loading = ref(false)
const loginForm = reactive<LoginForm>({
  email: '',
  password: '',
})

const loginRules: FormRules<LoginForm> = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: ['blur', 'change'] },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码不少于 6 位', trigger: 'blur' },
  ],
}

const handleLogin = async () => {
  if (!loginFormRef.value || loading.value) return
  const isValid = await loginFormRef.value.validate().catch(() => false)
  if (!isValid) return

  loading.value = true
  try {
    const response = await loginRequest({ ...loginForm })
    authStore.setAuth(response.token, response.user)
    ElMessage.success('登录成功，正在跳转首页')
    router.push({ name: 'home' })
  } finally {
    loading.value = false
  }
}

const goToRegister = () => {
  router.push({ name: 'register' })
}
</script>

<template>
  <div class="auth-layout">
    <div class="auth-hero">
      <p class="eyebrow">OpenCV Toolkit</p>
      <h1>统一身份认证</h1>
      <p>使用企业邮箱与密码登录，快速进入前端工作台。</p>
    </div>

    <el-card class="auth-card" shadow="hover">
      <h2>登录</h2>
      <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" label-position="top" size="large">
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="loginForm.email" placeholder="请输入邮箱" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="loginForm.password" placeholder="请输入密码" clearable show-password />
        </el-form-item>
        <div class="form-actions">
          <el-button :loading="loading" type="primary" round class="submit-btn" @click="handleLogin">
            登录并进入首页
          </el-button>
        </div>
        <p class="form-footer">
          还没有账号？
          <el-link type="primary" :underline="false" @click="goToRegister">立即注册</el-link>
        </p>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.auth-layout {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: clamp(24px, 4vw, 48px);
  align-items: center;
}

.auth-hero {
  color: #e2e8f0;
  max-width: 460px;
}

.auth-hero h1 {
  font-size: clamp(2rem, 5vw, 3rem);
  margin-bottom: 12px;
}

.auth-hero p {
  font-size: 1.05rem;
  color: #cbd5f5;
}

.auth-card {
  border: 1px solid rgba(226, 232, 240, 0.7);
  border-radius: 24px;
  padding: 8px 4px 24px;
}

.auth-card h2 {
  font-size: 1.4rem;
  font-weight: 600;
  margin-bottom: 12px;
  color: #0f172a;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.14rem;
  color: #7dd3fc;
  font-size: 0.85rem;
  margin-bottom: 12px;
}

.form-actions {
  margin-top: 8px;
}

.submit-btn {
  width: 100%;
}

.form-footer {
  text-align: center;
  margin-top: 12px;
  font-size: 0.95rem;
  color: #475569;
}
</style>
