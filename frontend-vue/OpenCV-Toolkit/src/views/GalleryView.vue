<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { deleteGallery, fetchGallery, type GalleryRecord } from '@/api/gallery'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const galleryItems = ref<GalleryRecord[]>([])
const page = ref(1)
const pageSize = ref(8)
const total = ref(0)
const dateRange = ref<[Date, Date] | null>(null)
const viewerVisible = ref(false)
const viewerUrls = ref<string[]>([])
const viewerIndex = ref(0)

const hasData = computed(() => galleryItems.value.length > 0)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value) || 0)

const formatDateParam = (value: Date | undefined) =>
  value ? value.toISOString().slice(0, 10) : undefined

const resolveDateParam = (index: 0 | 1) => formatDateParam(dateRange.value?.[index])

const formatDisplayDate = (value: string) =>
  new Date(value).toLocaleString(undefined, { hour12: false })

const loadGallery = async () => {
  const userId = authStore.user?.id
  if (!userId) {
    router.push({ name: 'login' })
    return
  }

  loading.value = true
  try {
    const response = await fetchGallery({
      userId,
      page: page.value,
      pageSize: pageSize.value,
      startDate: resolveDateParam(0),
      endDate: resolveDateParam(1),
    })
    galleryItems.value = response.items
    total.value = response.total
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleDelete = async (item: GalleryRecord) => {
  try {
    await ElMessageBox.confirm(`确定删除图片「${item.file_name || item.id}」吗？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }

  await deleteGallery(item.id, authStore.user?.id)
  ElMessage.success('删除成功')
  await loadGallery()
}

const handlePageChange = (value: number) => {
  page.value = value
  loadGallery()
}

const handleSizeChange = (value: number) => {
  pageSize.value = value
  page.value = 1
  loadGallery()
}

const handleDateChange = () => {
  page.value = 1
  loadGallery()
}

const resetFilters = () => {
  dateRange.value = null
  page.value = 1
  loadGallery()
}

const openViewer = (url: string) => {
  viewerUrls.value = [url]
  viewerIndex.value = 0
  viewerVisible.value = true
}

const downloadImage = (item: GalleryRecord) => {
  const link = document.createElement('a')
  link.href = item.filePreviewUrl
  link.target = '_blank'
  link.rel = 'noopener'
  link.download = item.file_name || 'image.png'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const handleViewerClose = () => {
  viewerVisible.value = false
  viewerUrls.value = []
  viewerIndex.value = 0
}

onMounted(() => {
  if (!authStore.user) {
    router.push({ name: 'login' })
    return
  }
  loadGallery()
})
</script>

<template>
  <section class="gallery-view">
    <header class="gallery-header">
      <div>
        <p class="eyebrow">图库管理</p>
        <h1>查看并管理你的图片资源</h1>
        <p class="subtitle">支持按日期筛选、预览、分页浏览与删除操作。</p>
      </div>
      <el-button text type="primary" @click="router.push({ name: 'home' })">返回首页</el-button>
    </header>

    <el-card class="gallery-filters" shadow="never">
      <div class="filter-row">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          @change="handleDateChange"
        />
        <div class="filter-actions">
          <el-button @click="resetFilters">重置筛选</el-button>
          <el-button type="primary" @click="loadGallery" :loading="loading">刷新列表</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="always">
      <el-table v-loading="loading" :data="galleryItems" style="width: 100%">
        <el-table-column label="预览" width="160">
          <template #default="{ row }">
            <el-image class="preview-thumb" :src="row.filePreviewUrl" fit="cover" @click="openViewer(row.filePreviewUrl)" />
          </template>
        </el-table-column>
        <el-table-column label="文件信息" min-width="220">
          <template #default="{ row }">
            <p class="table-name">{{ row.file_name || '未命名图片' }}</p>
            <p class="table-path">{{ row.file_url }}</p>
          </template>
        </el-table-column>
        <el-table-column label="添加时间" width="200">
          <template #default="{ row }">
            {{ formatDisplayDate(row.stored_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="() => openViewer(row.filePreviewUrl)">预览</el-button>
            <el-button size="small" text type="success" @click="() => downloadImage(row)">下载</el-button>
            <el-button size="small" text type="danger" @click="() => handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && !hasData" description="暂无图片，先去工作台处理图片再回来看看吧" />

      <div class="pagination-row" v-if="hasData">
        <el-pagination
          :current-page="page"
          :page-size="pageSize"
          :total="total"
          :page-sizes="[8, 12, 20, 40]"
          background
          layout="total, sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
        <span class="pagination-meta">共 {{ totalPages }} 页</span>
      </div>
    </el-card>
    <el-image-viewer
      v-if="viewerVisible"
      :url-list="viewerUrls"
      :initial-index="viewerIndex"
      @close="handleViewerClose"
    />
  </section>
</template>

<style scoped>
.gallery-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.gallery-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  background: rgba(248, 250, 252, 0.85);
  padding: 24px 28px;
  border-radius: 18px;
}

.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.12rem;
  font-size: 0.85rem;
  color: #38bdf8;
}

.gallery-header h1 {
  margin: 6px 0;
  font-size: clamp(1.4rem, 3vw, 2.2rem);
  color: #0f172a;
}

.subtitle {
  color: #475569;
  margin: 0;
}

.gallery-filters {
  --el-card-padding: 16px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.preview-thumb {
  width: 120px;
  height: 80px;
  border-radius: 8px;
  object-fit: cover;
  cursor: pointer;
}

.table-name {
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.table-path {
  color: #475569;
  margin: 4px 0 0;
  font-size: 0.85rem;
}

.pagination-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
}

.pagination-meta {
  color: #475569;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .gallery-header {
    flex-direction: column;
  }

  .pagination-row {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
