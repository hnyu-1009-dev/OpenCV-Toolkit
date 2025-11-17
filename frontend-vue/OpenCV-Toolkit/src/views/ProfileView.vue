<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { getUserProfile, updateUserProfile, type UpdateProfilePayload } from '@/api/user'
import { useAuthStore, type UserProfile } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const loading = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  id: '',
  email: '',
  name: '',
  phone: '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const originalProfile = ref<UserProfile | null>(null)

const rules: FormRules = {
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, max: 50, message: '姓名长度需在 2-50 个字符之间', trigger: 'blur' },
  ],
  phone: [
    {
      validator: (_rule, value, callback) => {
        if (!value) {
          callback()
          return
        }
        const phonePattern = /^[0-9+()\- ]{6,20}$/
        if (!phonePattern.test(value)) {
          callback(new Error('请输入有效的手机号'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
  currentPassword: [
    {
      validator: (_rule, value, callback) => {
        if (form.newPassword && !value) {
          callback(new Error('修改密码需要填写当前密码'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
  newPassword: [
    {
      validator: (_rule, value, callback) => {
        if (value && value.length < 6) {
          callback(new Error('新密码至少 6 位'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
  confirmPassword: [
    {
      validator: (_rule, value, callback) => {
        if (form.newPassword && value !== form.newPassword) {
          callback(new Error('两次输入的密码不一致'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

const loadProfile = async () => {
  if (!authStore.user) {
    router.push({ name: 'login' })
    return
  }
  loading.value = true
  try {
    const profile = await getUserProfile(authStore.user.id)
    setProfile(profile)
  } catch (error) {
    console.error(error)
    ElMessage.error('加载个人资料失败，请稍后再试')
  } finally {
    loading.value = false
  }
}

const setProfile = (profile: UserProfile) => {
  form.id = profile.id
  form.email = profile.email
  form.name = profile.name
  form.phone = profile.phone ?? ''
  originalProfile.value = profile
  authStore.updateProfile(profile)
}

const resetForm = () => {
  if (!originalProfile.value) return
  form.name = originalProfile.value.name
  form.phone = originalProfile.value.phone ?? ''
  resetPasswordFields()
}

const resetPasswordFields = () => {
  form.currentPassword = ''
  form.newPassword = ''
  form.confirmPassword = ''
}

const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  if (!originalProfile.value) {
    ElMessage.error('未找到个人资料')
    return
  }

  const nameChanged = form.name !== originalProfile.value.name
  const phoneChanged = (form.phone || '') !== (originalProfile.value.phone || '')
  const passwordChanged = Boolean(form.newPassword)

  if (!nameChanged && !phoneChanged && !passwordChanged) {
    ElMessage.info('暂无变更需要保存')
    return
  }

  const payload: UpdateProfilePayload = {}
  if (nameChanged || phoneChanged) {
    payload.name = form.name
    payload.phone = form.phone ? form.phone : null
  }
  if (passwordChanged) {
    payload.currentPassword = form.currentPassword
    payload.newPassword = form.newPassword
  }

  saving.value = true
  try {
    const updated = await updateUserProfile(form.id, payload)
    setProfile(updated)
    resetPasswordFields()
    ElMessage.success('个人信息已更新')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<template>
  <section class="profile-view">
    <el-card class="profile-card" shadow="hover" v-loading="loading">
      <template #header>
        <div class="profile-card__header">
          <div>
            <p class="eyebrow">Personal Center</p>
            <h2>个人中心</h2>
            <p class="subtitle">管理账号资料、联系方式及可选的密码修改。</p>
          </div>
          <el-button text type="primary" @click="router.push({ name: 'home' })">
            返回首页
          </el-button>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="profile-form">
        <el-row :gutter="20">
          <el-col :xs="24" :md="12">
            <el-form-item label="昵称 / 显示名" prop="name">
              <el-input v-model="form.name" maxlength="50" placeholder="请输入昵称" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="邮箱">
              <el-input v-model="form.email" disabled />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="form.phone" placeholder="可选，便于联系" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">密码修改（可选）</el-divider>
        <el-row :gutter="20">
          <el-col :xs="24" :md="8">
            <el-form-item label="当前密码" prop="currentPassword">
              <el-input v-model="form.currentPassword" type="password" show-password />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="form.newPassword" type="password" show-password />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input v-model="form.confirmPassword" type="password" show-password />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="form-actions">
          <el-button @click="resetForm" :disabled="saving">重置</el-button>
          <el-button type="primary" :loading="saving" @click="handleSubmit">
            保存修改
          </el-button>
        </div>
      </el-form>
    </el-card>
  </section>
</template>

<style scoped>
.profile-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.profile-card {
  --el-card-padding: 24px;
}

.profile-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.2rem;
  color: #38bdf8;
  font-size: 0.85rem;
  margin-bottom: 6px;
}

.profile-card__header h2 {
  margin: 0 0 6px;
  font-size: clamp(1.5rem, 3vw, 2.2rem);
  color: #0f172a;
}

.subtitle {
  margin: 0;
  color: #475569;
}

.profile-form {
  margin-top: 12px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 12px;
}

@media (max-width: 768px) {
  .profile-card__header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
