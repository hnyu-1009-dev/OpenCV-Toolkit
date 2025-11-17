<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const userName = computed(() => authStore.user?.name || '访客')
const userEmail = computed(() => authStore.user?.email || '')

const goBackToLogin = () => {
  authStore.logout()
  router.push({ name: 'login' })
}

const goWorkspace = () => {
  router.push({ name: 'workspace' })
}

const goGallery = () => {
  router.push({ name: 'gallery' })
}

const goProfile = () => {
  router.push({ name: 'profile' })
}
</script>

<template>
  <section class="home-view">
    <el-card class="hero-card" shadow="hover">
      <p class="eyebrow">OpenCV Toolkit</p>
      <h1>你好，{{ userName }}</h1>
      <p class="hero-subtitle">
        当前账号：
        <span>{{ userEmail }}</span>
      </p>
      <p class="hero-subtitle">统一登录后即可快速开始配置、调试并预览你的图像算法任务。</p>
      <div class="hero-actions">
        <el-button type="primary" size="large" @click="goWorkspace">进入工作台</el-button>
        <el-button size="large" @click="goGallery">打开图库</el-button>
        <el-button size="large" @click="goProfile">个人中心</el-button>
        <el-button size="large" text @click="goBackToLogin">退出登录</el-button>
      </div>
    </el-card>

    <el-row :gutter="20" class="home-grid">
      <el-col :xs="24" :md="8">
        <el-card shadow="never">
          <h3>文件扫描</h3>
          <p>批量扫描本地文件夹，提取图像元数据，制作扫描版文档。</p>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="never">
          <h3>图片处理</h3>
          <p>提供裁剪、滤镜、识别等常用图像处理工具，一键预览效果。</p>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="never">
          <h3>图库管理</h3>
          <p>集中管理上传图片，支持检索、删除的批量操作任务。</p>
        </el-card>
      </el-col>
    </el-row>

  </section>
</template>

<style scoped>
.home-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.hero-card {
  padding: 32px;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.16rem;
  color: #38bdf8;
  font-size: 0.85rem;
  margin-bottom: 8px;
}

.hero-card h1 {
  font-size: clamp(1.8rem, 4vw, 2.8rem);
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 12px;
}

.hero-subtitle {
  color: #475569;
  font-size: 1rem;
  margin-bottom: 12px;
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.home-grid {
  --el-card-padding: 20px;
}

.home-grid h3 {
  font-weight: 600;
  margin-bottom: 8px;
  color: #0f172a;
}

.home-grid p {
  color: #475569;
  font-size: 0.95rem;
}
</style>
