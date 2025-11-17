<script setup lang="ts">
import { reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { register as registerRequest } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

interface RegisterForm {
  name: string
  email: string
  password: string
  confirmPassword: string
  phone: string
}

const router = useRouter()
const authStore = useAuthStore()
const registerFormRef = ref<FormInstance>()
const loading = ref(false)
const registerForm = reactive<RegisterForm>({
  name: '',
  email: '',
  password: '',
  confirmPassword: '',
  phone: '',
})

const registerRules: FormRules<RegisterForm> = {
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, message: '姓名至少为 2 位字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: ['blur', 'change'] },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    {
      min: 6,
      message: '密码长度不少于 6 位，包含字母和数字更安全',
      trigger: 'blur',
    },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: ['blur', 'change'],
    },
  ],
  phone: [
    { required: true, message: '请输入电话', trigger: 'blur' },
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入 11 位手机号码',
      trigger: ['blur', 'change'],
    },
  ],
}

const handleRegister = async () => {
  if (!registerFormRef.value || loading.value) return
  const isValid = await registerFormRef.value.validate().catch(() => false)
  if (!isValid) return

  loading.value = true
  try {
    const response = await registerRequest({
      name: registerForm.name,
      email: registerForm.email,
      password: registerForm.password,
      confirmPassword: registerForm.confirmPassword,
      phone: registerForm.phone,
    })
    authStore.setAuth(response.token, response.user)
    ElMessage.success('注册成功，已自动登录')
    router.push({ name: 'home' })
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push({ name: 'login' })
}
</script>

<template>
  <section class="auth-layout">
    <el-card class="auth-card" shadow="always">
      <div class="auth-card__header">
        <div>
          <p class="eyebrow">加入 OpenCV Toolkit</p>
          <h2>创建新账号</h2>
          <p class="subtitle">完善下列信息，提交后即可直接进入系统首页。</p>
        </div>
        <el-button text type="primary" @click="goToLogin">我已有账号</el-button>
      </div>
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        label-position="top"
        size="large"
        class="register-form"
      >
        <el-row :gutter="16">
          <el-col :xs="24" :md="12">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="registerForm.name" placeholder="请输入姓名" clearable />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="电话" prop="phone">
              <el-input v-model="registerForm.phone" placeholder="请输入 11 位手机号" clearable />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="registerForm.email" placeholder="请输入常用邮箱" clearable />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :xs="24" :md="12">
            <el-form-item label="密码" prop="password">
              <el-input v-model="registerForm.password" placeholder="设置登录密码" show-password />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="registerForm.confirmPassword" placeholder="再次输入密码" show-password />
            </el-form-item>
          </el-col>
        </el-row>
        <el-button :loading="loading" type="primary" round class="submit-btn" @click="handleRegister">
          注册并进入首页
        </el-button>
      </el-form>
    </el-card>
  </section>
</template>

<style scoped>
.auth-layout {
  display: flex;
  justify-content: center;
}

.auth-card {
  width: min(920px, 100%);
  border-radius: 24px;
  padding: 32px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  box-shadow: 0 30px 60px rgba(15, 23, 42, 0.2);
  background: rgba(255, 255, 255, 0.95);
}

.auth-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.12rem;
  color: #0ea5e9;
  font-size: 0.85rem;
  margin-bottom: 8px;
}

.auth-card__header h2 {
  font-size: 1.8rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 4px;
}

.subtitle {
  color: #475569;
}

.register-form {
  margin-top: 16px;
}

.submit-btn {
  width: 100%;
  margin-top: 8px;
}

@media (max-width: 640px) {
  .auth-card__header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
