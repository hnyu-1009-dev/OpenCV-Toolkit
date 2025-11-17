<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  ElMessage,
  type UploadFile,
  type UploadFiles,
  type UploadInstance,
  type UploadProps,
  type UploadRawFile,
} from 'element-plus'
import { transformColorBlind, scanDocument, type ColorBlindMode } from '@/api/vision'

const router = useRouter()
const authStore = useAuthStore()

const featureTabs = [
  {
    key: 'color-blind',
    name: '色盲模式转换',
    description: '上传图片并模拟常见色盲视角，辅助检查配色可访问性。',
  },
  {
    key: 'document-scan',
    name: '扫描件生成',
    description: '框选图像区域，透视矫正并输出扫描风效果。',
  },
  {
    key: 'coming-soon',
    name: '更多图像能力',
    description: '批量修图、OCR、图像检索等功能即将上线。',
    disabled: true,
  },
]

const activeFeature = ref(featureTabs[0].key)
const activeFeatureInfo = computed(() => featureTabs.find((tab) => tab.key === activeFeature.value))
const topNavActive = ref(`workspace-${activeFeature.value}`)

const uploadRef = ref<UploadInstance>()
const selectedMode = ref<ColorBlindMode>('red_green')
const uploadFile = ref<File | null>(null)
const originalPreview = ref('')
const processedPreview = ref('')
const loading = ref(false)
const saveOriginal = ref(false)
const saveProcessed = ref(true)
const documentPoints = ref<{ x: number; y: number }[]>([])
const overlayRef = ref<HTMLDivElement>()
const scanImageRef = ref<HTMLImageElement>()
const draggingPointIndex = ref<number | null>(null)
const activePointerId = ref<number | null>(null)

const colorBlindModes: { label: string; value: ColorBlindMode; description: string }[] = [
  { value: 'red_green', label: '红绿色盲', description: '对红绿通道进行增强/替换，模拟常见红绿色弱视角。' },
  { value: 'blue_green', label: '蓝绿色盲', description: '对蓝绿通道进行增强/替换，模拟蓝绿色弱视角。' },
]

const canTransform = computed(() => Boolean(uploadFile.value) && !loading.value)
const hasProcessedResult = computed(() => Boolean(processedPreview.value))
const canDocumentScan = computed(
  () => Boolean(uploadFile.value) && documentPoints.value.length === 4 && !loading.value,
)
const documentPointsPercent = computed(() =>
  documentPoints.value.map((point) => ({
    left: `${point.x * 100}%`,
    top: `${point.y * 100}%`,
  })),
)
const documentPolylinePoints = computed(() =>
  documentPoints.value.map((point) => `${point.x * 100},${point.y * 100}`).join(' '),
)
const documentPointStatus = computed(() => `${documentPoints.value.length}/4`)

const cleanupPreview = () => {
  if (originalPreview.value.startsWith('blob:')) {
    URL.revokeObjectURL(originalPreview.value)
  }
  originalPreview.value = ''
}

onBeforeUnmount(() => {
  cleanupPreview()
  window.removeEventListener('pointermove', handlePointDragMove)
  window.removeEventListener('pointerup', stopPointDrag)
})

const assignFile = (file: File | null) => {
  cleanupPreview()
  uploadFile.value = file
  processedPreview.value = ''
  saveOriginal.value = false
  saveProcessed.value = true
  documentPoints.value = []

  if (file) {
    originalPreview.value = URL.createObjectURL(file)
  }
}

const handleFileChange: UploadProps['onChange'] = (file, _files) => {
  if (!file?.raw) {
    assignFile(null)
    return
  }
  assignFile(file.raw)
}

const handleExceed: UploadProps['onExceed'] = (files, _uploadFiles) => {
  if (files.length === 0) return
  uploadRef.value?.clearFiles()
  const [file] = files
  uploadRef.value?.handleStart(file as UploadRawFile)
  assignFile(file)
}

const handleRemove: UploadProps['onRemove'] = (_file?: UploadFile, _files?: UploadFiles) => {
  assignFile(null)
  uploadRef.value?.clearFiles()
}

const handleColorBlindTransform = async () => {
  if (!uploadFile.value) {
    ElMessage.warning('请先上传需要处理的图片')
    return
  }

  loading.value = true

  try {
    const response = await transformColorBlind({
      file: uploadFile.value,
      mode: selectedMode.value,
      saveOriginal: saveOriginal.value,
      saveProcessed: saveProcessed.value,
      userId: authStore.user?.id,
    })

    processedPreview.value = response.processedImage
    if (response.savedOriginal) {
      ElMessage.success('原始图片已保存到图库')
    }
    if (response.savedProcessed) {
      ElMessage.success('处理后的图片已保存到图库')
    }
    ElMessage.success('色盲模式转换完成')
  } catch (error) {
    console.error(error)
    ElMessage.error('处理失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const handleDocumentScan = async () => {
  if (!uploadFile.value) {
    ElMessage.warning('请先上传需要处理的图片')
    return
  }
  if (documentPoints.value.length !== 4) {
    ElMessage.warning('请框选四个角点再进行扫描转换')
    return
  }

  loading.value = true
  try {
    const response = await scanDocument({
      file: uploadFile.value,
      points: documentPoints.value,
      saveOriginal: saveOriginal.value,
      saveProcessed: saveProcessed.value,
      userId: authStore.user?.id,
    })
    processedPreview.value = response.processedImage
    documentPoints.value = []
    if (response.savedOriginal) {
      ElMessage.success('原始图片已保存到图库')
    }
    if (response.savedProcessed) {
      ElMessage.success('扫描件已保存到图库')
    }
    ElMessage.success('扫描件生成成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('扫描处理失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const handleToggleGallery = (type: 'original' | 'processed', value: boolean) => {
  const label = type === 'original' ? '原始图片' : '处理后图像'
  const action = value ? '将在转换后保存到图库' : '将在转换后不保存'
  ElMessage.info(`${label}${action}`)
}

const handleFeatureSelect = (key: string) => {
  const target = featureTabs.find((tab) => tab.key === key)
  if (!target || target.disabled) return
  activeFeature.value = key
}

const handleTopMenuSelect = (key: string, _keyPath: string[]) => {
  topNavActive.value = key
  if (key === 'home') {
    handleBackHome()
    return
  }
  if (key === 'gallery') {
    router.push({ name: 'gallery' })
    return
  }
  if (key.startsWith('workspace-')) {
    const featureKey = key.replace('workspace-', '')
    handleFeatureSelect(featureKey)
    return
  }
}

watch(
  () => activeFeature.value,
  (val) => {
    topNavActive.value = `workspace-${val}`
    if (val !== 'document-scan') {
      documentPoints.value = []
    }
  },
)

const handleBackHome = () => {
  router.push({ name: 'home' })
}

const getImageRect = () => scanImageRef.value?.getBoundingClientRect()

const handleScanAreaClick = (event: MouseEvent) => {
  if (documentPoints.value.length >= 4 || !originalPreview.value) return
  const rect = getImageRect()
  if (!rect) return
  const x = (event.clientX - rect.left) / rect.width
  const y = (event.clientY - rect.top) / rect.height
  if (x < 0 || x > 1 || y < 0 || y > 1) return
  documentPoints.value.push({ x, y })
}

const startPointDrag = (index: number, event: PointerEvent) => {
  event.stopPropagation()
  const rect = getImageRect()
  if (!rect) return
  overlayRef.value?.setPointerCapture?.(event.pointerId)
  draggingPointIndex.value = index
  activePointerId.value = event.pointerId
  window.addEventListener('pointermove', handlePointDragMove)
  window.addEventListener('pointerup', stopPointDrag)
}

const handlePointDragMove = (event: PointerEvent) => {
  if (draggingPointIndex.value === null) return
  if (activePointerId.value !== null && event.pointerId !== activePointerId.value) return
  const rect = getImageRect()
  if (!rect) return
  const x = (event.clientX - rect.left) / rect.width
  const y = (event.clientY - rect.top) / rect.height
  if (x < 0 || x > 1 || y < 0 || y > 1) return
  documentPoints.value[draggingPointIndex.value] = { x, y }
  documentPoints.value = [...documentPoints.value]
}

const stopPointDrag = () => {
  if (activePointerId.value !== null) {
    overlayRef.value?.releasePointerCapture?.(activePointerId.value)
  }
  draggingPointIndex.value = null
  activePointerId.value = null
  window.removeEventListener('pointermove', handlePointDragMove)
  window.removeEventListener('pointerup', stopPointDrag)
}

const undoDocumentPoint = () => {
  documentPoints.value.pop()
}

const resetDocumentPoints = () => {
  documentPoints.value = []
}

</script>

<template>
  <section class="workspace-view">
    <header class="workspace-header">
      <div>
        <p class="eyebrow">OpenCV Toolkit · 工作台</p>
        <h1>功能导航</h1>
        <p class="subtitle">在统一工作台中体验与调度图像处理和管理能力。</p>
      </div>
      <el-button text type="primary" @click="handleBackHome">返回首页</el-button>
    </header>

    <div class="workspace-nav">
      <el-menu :default-active="topNavActive" mode="horizontal" class="workspace-top-menu"
        @select="handleTopMenuSelect">
        <el-menu-item index="home">首页概览</el-menu-item>
        <el-sub-menu index="workspace">
          <template #title>图像工作台</template>
          <el-menu-item index="workspace-color-blind">色盲模式转换</el-menu-item>
          <el-menu-item index="workspace-document-scan">扫描件生成</el-menu-item>
          <el-menu-item index="workspace-coming-soon" disabled>更多图像能力</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="gallery">图库管理</el-menu-item>
        <el-menu-item index="settings" disabled>个人中心</el-menu-item>
      </el-menu>
    </div>

    <section v-if="activeFeature === 'color-blind'" class="feature-panel">
      <el-card shadow="hover" class="tool-card">
        <template #header>
          <div class="card-header">
            <div>
              <p class="eyebrow">Step 01</p>
              <h2>上传图片并选择色盲模式</h2>
            </div>
            <div class="mode-hints">
              <p v-for="mode in colorBlindModes" :key="mode.value">
                <strong>{{ mode.label }}：</strong>{{ mode.description }}
              </p>
            </div>
          </div>
        </template>

        <el-form label-position="top" class="tool-form">
          <el-form-item label="上传待处理图片">
            <el-upload ref="uploadRef" drag accept="image/*" :auto-upload="false" :limit="1" :show-file-list="false"
              :on-change="handleFileChange" :on-remove="handleRemove" :on-exceed="handleExceed">
              <div class="upload-placeholder-icon">⇪</div>
              <div class="el-upload__text">拖拽图片到此处 或 <em>点击上传</em></div>
              <template #tip>
                <div class="el-upload__tip">支持常见 png/jpg/webp，单次仅处理一张图片。</div>
              </template>
            </el-upload>
          </el-form-item>

          <el-form-item label="选择色盲模式">
            <el-radio-group v-model="selectedMode">
              <el-radio-button v-for="mode in colorBlindModes" :key="mode.value" :label="mode.value">
                {{ mode.label }}
              </el-radio-button>
            </el-radio-group>
          </el-form-item>

          <div class="form-actions">
            <el-button @click="handleRemove" :disabled="!uploadFile">重新选择</el-button>
            <el-button type="primary" :loading="loading" :disabled="!canTransform" @click="handleColorBlindTransform">
              开始转换
            </el-button>
          </div>
        </el-form>
      </el-card>

      <el-row :gutter="20">
        <el-col :xs="24" :md="12">
          <el-card shadow="never" class="preview-card">
            <div class="preview-header">
              <div>
                <p class="eyebrow">Step 02</p>
                <h3>原始图片</h3>
              </div>
              <el-switch v-model="saveOriginal" :disabled="!uploadFile" active-text="保存至图库"
                @change="(val) => handleToggleGallery('original', Boolean(val))" />
            </div>
            <div class="preview-body" v-if="originalPreview">
              <img :src="originalPreview" alt="原始图片预览" />
            </div>
            <p v-else class="preview-placeholder">上传后展示原始图像预览</p>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="12">
          <el-card shadow="never" class="preview-card">
            <div class="preview-header">
              <div>
                <p class="eyebrow">Step 03</p>
                <h3>处理结果</h3>
              </div>
              <el-switch v-model="saveProcessed" :disabled="!hasProcessedResult" active-text="保存至图库"
                @change="(val) => handleToggleGallery('processed', Boolean(val))" />
            </div>
            <div class="preview-body" v-if="processedPreview">
              <img :src="processedPreview" alt="色盲模式转换结果" />
            </div>
            <p v-else class="preview-placeholder">完成转换后将在此展示处理结果</p>
          </el-card>
        </el-col>
      </el-row>
    </section>

    <section v-else-if="activeFeature === 'document-scan'" class="feature-panel">
      <el-card shadow="hover" class="tool-card">
        <template #header>
          <div class="card-header">
            <div>
              <p class="eyebrow">Step 01</p>
              <h2>上传图片并框选扫描区域</h2>
            </div>
            <p class="subtitle">在原图上依次点击四个角点，可按“撤销/清空”重新选择。</p>
          </div>
        </template>

        <el-form label-position="top" class="tool-form">
          <el-form-item label="上传待处理图片">
            <el-upload ref="uploadRef" drag accept="image/*" :auto-upload="false" :limit="1" :show-file-list="false"
              :on-change="handleFileChange" :on-remove="handleRemove" :on-exceed="handleExceed">
              <div class="upload-placeholder-icon">⇪</div>
              <div class="el-upload__text">拖拽图片到此处 或 <em>点击上传</em></div>
              <template #tip>
                <div class="el-upload__tip">建议选择扫描纸张的边缘四角，以便更好矫正。</div>
              </template>
            </el-upload>
          </el-form-item>

          <div class="form-actions">
            <el-button @click="undoDocumentPoint" :disabled="!documentPoints.length">撤销一点</el-button>
            <el-button @click="resetDocumentPoints" :disabled="!documentPoints.length">清空选区</el-button>
            <el-button type="primary" :loading="loading" :disabled="!canDocumentScan" @click="handleDocumentScan">
              生成扫描件
            </el-button>
          </div>
        </el-form>
      </el-card>

      <el-row :gutter="20">
        <el-col :xs="24" :md="12">
          <el-card shadow="never" class="preview-card">
            <div class="preview-header">
              <div>
                <p class="eyebrow">Step 02</p>
                <h3>框选区域 ({{ documentPointStatus }})</h3>
              </div>
              <el-switch v-model="saveOriginal" :disabled="!uploadFile" active-text="保存原图"
                @change="(val) => handleToggleGallery('original', Boolean(val))" />
            </div>
            <div class="preview-body scan-body" v-if="originalPreview">
              <div class="scan-overlay" ref="overlayRef" @click="handleScanAreaClick">
                <img :src="originalPreview" alt="原始图片预览" ref="scanImageRef" />
                <span v-for="(point, index) in documentPointsPercent" :key="index" class="scan-point"
                  :style="{ left: point.left, top: point.top }"
                  @pointerdown.stop.prevent="(event) => startPointDrag(index, event)">
                  {{ index + 1 }}
                </span>
              </div>
              <p class="scan-instruction">提示：依次点击左上/右上/右下/左下角，点击画面可继续补点。</p>
            </div>
            <p v-else class="preview-placeholder">上传后可在此框选扫描区域</p>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="12">
          <el-card shadow="never" class="preview-card">
            <div class="preview-header">
              <div>
                <p class="eyebrow">Step 03</p>
                <h3>扫描件预览</h3>
              </div>
              <el-switch v-model="saveProcessed" :disabled="!hasProcessedResult" active-text="保存扫描件"
                @change="(val) => handleToggleGallery('processed', Boolean(val))" />
            </div>
            <div class="preview-body" v-if="processedPreview">
              <img :src="processedPreview" alt="扫描件结果" />
            </div>
            <p v-else class="preview-placeholder">完成扫描后将在此展示结果</p>
          </el-card>
        </el-col>
      </el-row>
    </section>
  </section>
</template>

<style scoped>
.workspace-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.workspace-header {
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

.workspace-header h1 {
  margin: 6px 0;
  font-size: clamp(1.4rem, 3vw, 2.2rem);
  color: #0f172a;
}

.subtitle {
  color: #475569;
  margin: 0;
}

.workspace-nav {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.workspace-top-menu {
  border-bottom: none;
  border-radius: 16px;
  padding: 0 16px;
  background: #fff;
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.08);
  overflow-x: auto;
}

:deep(.workspace-top-menu .el-menu-item),
:deep(.workspace-top-menu .el-sub-menu__title) {
  border-bottom: none !important;
  min-width: 150px;
  font-weight: 600;
}

.feature-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.tool-card {
  --el-card-padding: 20px;
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.card-header h2 {
  margin: 4px 0 0;
  font-size: 1.4rem;
  color: #0f172a;
}

.mode-hints {
  max-width: 380px;
  font-size: 0.9rem;
  color: #475569;
}

.mode-hints p {
  margin: 0 0 6px;
}

.tool-form {
  margin-top: 12px;
}

.upload-placeholder-icon {
  font-size: 42px;
  color: #38bdf8;
  margin-bottom: 8px;
}

.form-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
  margin-top: 8px;
}

.preview-card {
  min-height: 320px;
  display: flex;
  flex-direction: column;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.preview-body {
  flex: 1;
  border-radius: 12px;
  background: #0f172a0d;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.preview-body img {
  max-width: 100%;
  max-height: 360px;
  border-radius: 10px;
  object-fit: contain;
}

.preview-placeholder {
  color: #94a3b8;
  text-align: center;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
}

.scan-body {
  flex-direction: column;
}

.scan-overlay {
  position: relative;
  width: 100%;
  cursor: crosshair;
}

.scan-overlay img {
  width: 100%;
  max-height: 360px;
  border-radius: 10px;
  display: block;
}

.scan-point {
  position: absolute;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #38bdf8;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  transform: translate(-50%, -50%);
  cursor: grab;
  touch-action: none;
}

.scan-lines {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.scan-instruction {
  width: 100%;
  margin-top: 8px;
  color: #475569;
  font-size: 0.9rem;
  text-align: left;
}

@media (max-width: 768px) {
  .workspace-header {
    flex-direction: column;
  }

  .workspace-top-menu {
    padding: 0 8px;
  }

  .form-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
