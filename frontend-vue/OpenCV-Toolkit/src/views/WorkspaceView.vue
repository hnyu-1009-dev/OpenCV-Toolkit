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
import {
  transformColorBlind,
  scanDocument,
  rotateImage,
  adjustContrast,
  adjustBrightness,
  applyWatermark,
  type ColorBlindMode,
} from '@/api/vision'

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
    key: 'watermark',
    name: '水印添加',
    description: '上传水印并点击原图位置，快速生成带水印的图片。',
  },
  {
    key: 'brightness',
    name: '亮度调节',
    description: '通过滑杆整体提升或压暗画面亮度，快速统一曝光。',
  },
  {
    key: 'contrast',
    name: '对比度调节',
    description: '通过滑杆增强或减弱图片对比度，突出细节或柔化画面。',
  },
  {
    key: 'rotate',
    name: '图片旋转',
    description: '通过滑杆调整角度，矫正翻转或方向错误的图片。',
  },
  // {
  //   key: 'coming-soon',
  //   name: '更多图像能力',
  //   description: '批量修图、OCR、图像检索等功能即将上线。',
  //   disabled: true,
  // },
]

const activeFeature = ref(featureTabs[0].key)
const activeFeatureInfo = computed(() => featureTabs.find((tab) => tab.key === activeFeature.value))
const topNavActive = ref(`workspace-${activeFeature.value}`)

const uploadRef = ref<UploadInstance>()
const watermarkUploadRef = ref<UploadInstance>()
const selectedMode = ref<ColorBlindMode>('red_green')
const rotationColorBlind = ref(0)
const rotationDocument = ref(0)
const rotationOnly = ref(0)
const contrastLevel = ref(0)
const brightnessLevel = ref(0)
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
const watermarkFile = ref<File | null>(null)
const watermarkPreview = ref('')
const watermarkPoint = ref<{ x: number; y: number } | null>(null)
const watermarkOverlayRef = ref<HTMLDivElement>()
const watermarkImageRef = ref<HTMLImageElement>()

const colorBlindModes: { label: string; value: ColorBlindMode; description: string }[] = [
  { value: 'red_green', label: '红绿色盲', description: '对红绿通道进行增强/替换，模拟常见红绿色弱视角。' },
  { value: 'blue_green', label: '蓝绿色盲', description: '对蓝绿通道进行增强/替换，模拟蓝绿色弱视角。' },
]

const canTransform = computed(() => Boolean(uploadFile.value) && !loading.value)
const hasProcessedResult = computed(() => Boolean(processedPreview.value))
const canDocumentScan = computed(
  () => Boolean(uploadFile.value) && documentPoints.value.length === 4 && !loading.value,
)
const canAdjustContrast = computed(() => Boolean(uploadFile.value) && !loading.value)
const canAdjustBrightness = computed(() => Boolean(uploadFile.value) && !loading.value)
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
const canApplyWatermark = computed(
  () => Boolean(uploadFile.value && watermarkFile.value && watermarkPoint.value) && !loading.value,
)
const watermarkPointPercent = computed(() =>
  watermarkPoint.value
    ? {
      left: `${watermarkPoint.value.x * 100}%`,
      top: `${watermarkPoint.value.y * 100}%`,
    }
    : null,
)
const viewerVisible = ref(false)
const viewerUrls = ref<string[]>([])
const viewerIndex = ref(0)
const openImageViewer = (url: string) => {
  viewerUrls.value = [url]
  viewerIndex.value = 0
  viewerVisible.value = true
}
const closeImageViewer = () => {
  viewerVisible.value = false
  viewerUrls.value = []
}

const cleanupPreview = () => {
  if (originalPreview.value.startsWith('blob:')) {
    URL.revokeObjectURL(originalPreview.value)
  }
  originalPreview.value = ''
}

const cleanupWatermarkPreview = () => {
  if (watermarkPreview.value.startsWith('blob:')) {
    URL.revokeObjectURL(watermarkPreview.value)
  }
  watermarkPreview.value = ''
}

onBeforeUnmount(() => {
  cleanupPreview()
  cleanupWatermarkPreview()
  window.removeEventListener('pointermove', handlePointDragMove)
  window.removeEventListener('pointerup', stopPointDrag)
})

const assignFile = (file: File | null) => {
  cleanupPreview()
  uploadFile.value = file
  processedPreview.value = ''
  saveOriginal.value = false
  saveProcessed.value = true
  rotationColorBlind.value = 0
  rotationDocument.value = 0
  rotationOnly.value = 0
  contrastLevel.value = 0
  brightnessLevel.value = 0
  documentPoints.value = []
  watermarkPoint.value = null

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

const assignWatermarkFile = (file: File | null) => {
  cleanupWatermarkPreview()
  watermarkFile.value = file
  watermarkPoint.value = null

  if (file) {
    watermarkPreview.value = URL.createObjectURL(file)
  }
}

const handleWatermarkChange: UploadProps['onChange'] = (file) => {
  if (!file?.raw) {
    assignWatermarkFile(null)
    return
  }
  assignWatermarkFile(file.raw)
}

const handleWatermarkExceed: UploadProps['onExceed'] = (files) => {
  if (files.length === 0) return
  watermarkUploadRef.value?.clearFiles()
  const [file] = files
  watermarkUploadRef.value?.handleStart(file as UploadRawFile)
  assignWatermarkFile(file as File)
}

const handleWatermarkRemove: UploadProps['onRemove'] = (_file?: UploadFile, _files?: UploadFiles) => {
  assignWatermarkFile(null)
  watermarkUploadRef.value?.clearFiles()
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
      rotation: rotationColorBlind.value,
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
      rotation: rotationDocument.value,
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

const handleImageRotate = async () => {
  if (!uploadFile.value) {
    ElMessage.warning('请先上传需要旋转的图片')
    return
  }

  loading.value = true
  try {
    const response = await rotateImage({
      file: uploadFile.value,
      rotation: rotationOnly.value,
      saveOriginal: saveOriginal.value,
      saveProcessed: saveProcessed.value,
      userId: authStore.user?.id,
    })
    processedPreview.value = response.processedImage

    if (response.savedOriginal) {
      ElMessage.success('原始图片已保存到图库')
    }
    if (response.savedProcessed) {
      ElMessage.success('旋转后的图片已保存到图库')
    }
    ElMessage.success('图片旋转完成')
  } catch (error) {
    console.error(error)
    ElMessage.error('旋转失败，请稍后再试')
  } finally {
    loading.value = false
  }
}

const handleContrastAdjust = async () => {
  if (!uploadFile.value) {
    ElMessage.warning('请先上传需要调整的图片')
    return
  }

  loading.value = true
  try {
    const response = await adjustContrast({
      file: uploadFile.value,
      contrast: contrastLevel.value / 100,
      saveOriginal: saveOriginal.value,
      saveProcessed: saveProcessed.value,
      userId: authStore.user?.id,
    })
    processedPreview.value = response.processedImage

    if (response.savedOriginal) {
      ElMessage.success('原始图片已保存到图库')
    }
    if (response.savedProcessed) {
      ElMessage.success('对比度处理结果已保存到图库')
    }
    ElMessage.success('对比度调节完成')
  } catch (error) {
    console.error(error)
    ElMessage.error('对比度调节失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const handleBrightnessAdjust = async () => {
  if (!uploadFile.value) {
    ElMessage.warning('请先上传需要处理的图片')
    return
  }

  loading.value = true
  try {
    const response = await adjustBrightness({
      file: uploadFile.value,
      brightness: brightnessLevel.value,
      saveOriginal: saveOriginal.value,
      saveProcessed: saveProcessed.value,
      userId: authStore.user?.id,
    })
    processedPreview.value = response.processedImage

    if (response.savedOriginal) {
      ElMessage.success('原始图片已保存到图库')
    }
    if (response.savedProcessed) {
      ElMessage.success('亮度处理结果已保存到图库')
    }
    ElMessage.success('亮度调节完成')
  } catch (error) {
    console.error(error)
    ElMessage.error('亮度调节失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const handleWatermarkApply = async () => {
  if (!uploadFile.value) {
    ElMessage.warning('请先上传需要添加水印的原图')
    return
  }
  if (!watermarkFile.value) {
    ElMessage.warning('请上传水印图片')
    return
  }
  if (!watermarkPoint.value) {
    ElMessage.warning('请在原图上点击选择水印落点')
    return
  }

  loading.value = true
  try {
    const response = await applyWatermark({
      file: uploadFile.value,
      watermark: watermarkFile.value,
      position: watermarkPoint.value,
      saveOriginal: saveOriginal.value,
      saveProcessed: saveProcessed.value,
      userId: authStore.user?.id,
    })
    processedPreview.value = response.processedImage

    if (response.savedOriginal) {
      ElMessage.success('原始图片已保存到图库')
    }
    if (response.savedProcessed) {
      ElMessage.success('水印图片已保存到图库')
    }
    ElMessage.success('水印添加完成')
  } catch (error) {
    console.error(error)
    ElMessage.error('水印处理失败，请稍后重试')
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
  if (key === 'profile') {
    router.push({ name: 'profile' })
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
    if (val !== 'rotate') {
      rotationOnly.value = 0
    }
    if (val !== 'contrast') {
      contrastLevel.value = 0
    }
    if (val !== 'brightness') {
      brightnessLevel.value = 0
    }
    if (val !== 'watermark') {
      watermarkPoint.value = null
    }
    if (val !== 'color-blind') {
      rotationColorBlind.value = 0
    }
    if (val !== 'document-scan') {
      rotationDocument.value = 0
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

const getWatermarkRect = () => watermarkImageRef.value?.getBoundingClientRect()

const handleWatermarkClick = (event: MouseEvent) => {
  if (!originalPreview.value) return
  const rect = getWatermarkRect()
  if (!rect) return
  const x = (event.clientX - rect.left) / rect.width
  const y = (event.clientY - rect.top) / rect.height
  if (x < 0 || x > 1 || y < 0 || y > 1) return
  watermarkPoint.value = { x, y }
}

const resetWatermarkPoint = () => {
  watermarkPoint.value = null
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
          <el-menu-item index="workspace-watermark">水印添加</el-menu-item>
          <el-menu-item index="workspace-brightness">亮度调节</el-menu-item>
          <el-menu-item index="workspace-contrast">对比度调节</el-menu-item>
          <el-menu-item index="workspace-rotate">图片旋转</el-menu-item>
          <el-menu-item index="workspace-coming-soon" disabled>更多图像能力</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="gallery">图库管理</el-menu-item>
        <el-menu-item index="profile">个人中心</el-menu-item>
      </el-menu>
    </div>

    <section v-if="activeFeature === 'color-blind'" class="feature-panel">
      <el-row :gutter="20">
        <el-col :xs="24" :md="8">
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

              <!-- 上传区域 -->
              <el-form-item label="上传待处理图片">
                <el-upload ref="uploadRef" drag accept="image/*" :auto-upload="false" :limit="1" :show-file-list="false"
                  :on-change="handleFileChange" :on-remove="handleRemove" :on-exceed="handleExceed" class="upload-box">
                  <div class="upload-placeholder-icon">⇪</div>
                  <div class="el-upload__text">拖拽图片到此处 或 <em>点击上传</em></div>

                  <template #tip>
                    <div class="el-upload__tip">
                      支持常见 png/jpg/webp，单次仅处理一张图片。
                    </div>
                  </template>
                </el-upload>
              </el-form-item>

              <!-- 色盲模式选择 -->
              <el-form-item label="选择色盲模式">
                <el-radio-group v-model="selectedMode" class="mode-group">
                  <el-radio-button v-for="mode in colorBlindModes" :key="mode.value" :label="mode.value">
                    {{ mode.label }}
                  </el-radio-button>
                </el-radio-group>
              </el-form-item>
              <!-- 操作按钮 -->
              <div class="form-actions column">
                <el-button @click="handleRemove" :disabled="!uploadFile">重新选择</el-button>

                <el-button type="primary" :loading="loading" :disabled="!canTransform"
                  @click="handleColorBlindTransform">
                  开始转换
                </el-button>
              </div>

            </el-form>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="8">
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

        <el-col :xs="24" :md="8">
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
              <img :src="processedPreview" alt="色盲模式转换结果" @click="openImageViewer(processedPreview)" />
            </div>
            <p v-else class="preview-placeholder">完成转换后将在此展示处理结果</p>
          </el-card>
        </el-col>
      </el-row>
    </section>

    <section v-else-if="activeFeature === 'document-scan'" class="feature-panel">
      <el-row :gutter="20">
        <el-col :xs="24" :md="8">
          <el-card shadow="hover" class="tool-card compact-card">
            <template #header>
              <div class="card-header">
                <div>
                  <p class="eyebrow">Step 01</p>
                  <h2 class="title">上传图片并框选扫描区域</h2>
                </div>
                <p class="subtitle">
                  在原图上依次点击四个角点，可按“撤销/清空”重新选择。
                </p>
              </div>
            </template>

            <div class="form-wrapper">
              <el-form label-position="top" class="tool-form compact-form">

                <!-- 上传区域 -->
                <el-form-item label="上传待处理图片">
                  <el-upload ref="uploadRef" drag accept="image/*" :auto-upload="false" :limit="1"
                    :show-file-list="false" :on-change="handleFileChange" :on-remove="handleRemove"
                    :on-exceed="handleExceed" class="upload-box">
                    <div class="upload-placeholder-icon">⇪</div>
                    <div class="el-upload__text">
                      拖拽图片到此处 或 <em>点击上传</em>
                    </div>
                    <template #tip>
                      <div class="el-upload__tip">
                        建议选择扫描纸张的边缘四角，以便更好矫正。
                      </div>
                    </template>
                  </el-upload>
                </el-form-item>
                <!-- 操作按钮 -->
                <div class="form-actions column">
                  <el-button @click="undoDocumentPoint" :disabled="!documentPoints.length">
                    撤销一点
                  </el-button>

                  <el-button @click="resetDocumentPoints" :disabled="!documentPoints.length">
                    清空选区
                  </el-button>

                  <el-button type="primary" :loading="loading" :disabled="!canDocumentScan" @click="handleDocumentScan">
                    生成扫描件
                  </el-button>
                </div>
              </el-form>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="8">
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
              <div class="scan-overlay" ref="overlayRef">
                <img :src="originalPreview" alt="原始图片预览" ref="scanImageRef" @click.stop="handleScanAreaClick" />
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

        <el-col :xs="24" :md="8">
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
              <img :src="processedPreview" alt="扫描件结果" @click="openImageViewer(processedPreview)" />
            </div>
            <p v-else class="preview-placeholder">完成扫描后将在此展示结果</p>
          </el-card>
        </el-col>
      </el-row>
    </section>

    <section v-else-if="activeFeature === 'watermark'" class="feature-panel">
      <el-row :gutter="20">
        <el-col :xs="24" :md="8">
          <el-card shadow="hover" class="tool-card compact-card">
            <template #header>
              <div class="card-header">
                <div>
                  <p class="eyebrow">Step 01</p>
                  <h2 class="title">水印添加</h2>
                </div>
                <p class="subtitle">
                  &#36873;&#25321;&#22909;&#20004;&#24352;&#22270;&#29255;&#21518;&#65292;&#20877;&#22312;&#21407;&#22270;&#19978;&#28857;&#20987;&#27700;&#21360;&#20301;&#32622;&#21363;&#21487;&#12290;
                </p>
              </div>
            </template>

            <el-form label-position="top" class="tool-form compact-form">
              <el-form-item label="&#19978;&#20256;&#24453;&#22788;&#29702;&#22270;&#29255;">
                <el-upload ref="uploadRef" drag accept="image/*" :auto-upload="false" :limit="1" :show-file-list="false"
                  :on-change="handleFileChange" :on-remove="handleRemove" :on-exceed="handleExceed">
                  <div class="upload-placeholder-icon">☁️</div>
                  <div class="el-upload__text">&#25463;&#25289;&#22270;&#29255;&#21040;&#27492;&#22788;&#25110;
                    <em>&#28857;&#20987;&#19978;&#20256;</em>
                  </div>
                  <template #tip>
                    <div class="el-upload__tip">&#25903;&#25345; png / jpg /
                      webp&#65292;&#24314;&#35758;&#36873;&#25321;&#39640;&#28165;&#21407;&#22270;&#12290;</div>
                  </template>
                </el-upload>
              </el-form-item>

              <el-form-item label="&#19978;&#20256;&#27700;&#21360;&#22270;">
                <el-upload ref="watermarkUploadRef" drag accept="image/*" :auto-upload="false" :limit="1"
                  :show-file-list="false" :on-change="handleWatermarkChange" :on-remove="handleWatermarkRemove"
                  :on-exceed="handleWatermarkExceed">
                  <div class="upload-placeholder-icon">WM</div>
                  <div class="el-upload__text">&#25463;&#25289;&#25110; <em>&#28857;&#20987;&#19978;&#20256;</em>
                    &#27700;&#21360;&#22270;</div>
                  <template #tip>
                    <div class="el-upload__tip">
                      &#24314;&#35758;&#20351;&#29992;&#24102;&#36879;&#26126;&#36890;&#36947;&#30340;
                      PNG&#65292;&#31995;&#32479;&#20250;&#33258;&#21160;&#38480;&#21046;&#23610;&#23544;&#12290;</div>
                  </template>
                </el-upload>
              </el-form-item>

              <div v-if="watermarkPreview" class="watermark-thumb">
                <p>&#27700;&#21360;&#39044;&#35272;</p>
                <img :src="watermarkPreview" alt="&#27700;&#21360;&#39044;&#35272;" />
              </div>

              <div class="form-actions column">
                <el-button @click="handleRemove"
                  :disabled="!uploadFile">&#37325;&#26032;&#36873;&#25321;&#21407;&#22270;</el-button>
                <el-button @click="handleWatermarkRemove"
                  :disabled="!watermarkFile">&#37325;&#26032;&#36873;&#25321;&#27700;&#21360;</el-button>
                <el-button @click="resetWatermarkPoint"
                  :disabled="!watermarkPoint">&#28165;&#38500;&#33853;&#28857;</el-button>
                <el-button type="primary" :loading="loading" :disabled="!canApplyWatermark"
                  @click="handleWatermarkApply">
                  &#29983;&#25104;&#27700;&#21360;&#22270;
                </el-button>
              </div>
            </el-form>
          </el-card>
        </el-col>

        <el-col :xs="24" :md="8">
          <el-card shadow="never" class="preview-card tall-preview">
            <div class="preview-header">
              <div>
                <p class="eyebrow">Step 02</p>
                <h3>&#28857;&#20987;&#36873;&#25321;&#33853;&#28857;</h3>
              </div>
              <el-switch v-model="saveOriginal" :disabled="!uploadFile" active-text="&#20445;&#23384;&#21407;&#22270;"
                @change="(val) => handleToggleGallery('original', Boolean(val))" />
            </div>
            <div class="preview-body scan-body" v-if="originalPreview">
              <div class="scan-overlay" ref="watermarkOverlayRef">
                <img :src="originalPreview" alt="&#21407;&#22987;&#22270;&#29255;&#39044;&#35272;"
                  ref="watermarkImageRef" @click.stop="handleWatermarkClick" />
                <span v-if="watermarkPointPercent" class="scan-point watermark-point" :style="watermarkPointPercent">
                  W
                </span>
              </div>
              <p class="scan-instruction">
                &#25552;&#31034;&#65306;&#28857;&#20987;&#21407;&#22270;&#21363;&#21487;&#35774;&#32622;&#27700;&#21360;&#33853;&#28857;&#65292;&#21487;&#22810;&#27425;&#20462;&#25913;&#12290;
              </p>
            </div>
            <p v-else class="preview-placeholder">
              &#19978;&#20256;&#21407;&#22270;&#21518;&#21487;&#22312;&#27492;&#36873;&#25321;&#27700;&#21360;&#33853;&#28857;
            </p>
          </el-card>
        </el-col>


        <el-col :xs="24" :md="8">
          <el-card shadow="never" class="preview-card tall-preview">
            <div class="preview-header">
              <div>
                <p class="eyebrow">Step 03</p>
                <h3>&#27700;&#21360;&#32467;&#26524;</h3>
              </div>
              <el-switch v-model="saveProcessed" :disabled="!hasProcessedResult"
                active-text="&#20445;&#23384;&#32467;&#26524;"
                @change="(val) => handleToggleGallery('processed', Boolean(val))" />
            </div>
            <div class="preview-body" v-if="processedPreview">
              <img :src="processedPreview" alt="&#27700;&#21360;&#32467;&#26524;"
                @click="openImageViewer(processedPreview)" />
            </div>
            <p v-else class="preview-placeholder">
              &#25191;&#34892;&#29983;&#25104;&#21518;&#23558;&#22312;&#27492;&#26174;&#31034;&#24102;&#27700;&#21360;&#30340;&#22270;&#29255;
            </p>
          </el-card>
        </el-col>
      </el-row>
    </section>


    <section v-else-if="activeFeature === 'brightness'" class="feature-panel">
      <el-row :gutter="20">
        <el-col :xs="24" :md="8">
          <el-card shadow="hover" class="tool-card compact-card">
            <template #header>
              <div class="card-header">
                <div>
                  <p class="eyebrow">Step 01</p>
                  <h2 class="title">上传图片并调节亮度</h2>
                </div>
                <p class="subtitle">通过滑杆快速提亮或压暗画面，修复曝光问题。</p>
              </div>
            </template>

            <el-form label-position="top" class="tool-form compact-form">
              <el-form-item label="上传需要处理的图片">
                <el-upload ref="uploadRef" drag accept="image/*" :auto-upload="false" :limit="1" :show-file-list="false"
                  :on-change="handleFileChange" :on-remove="handleRemove" :on-exceed="handleExceed">
                  <div class="upload-placeholder-icon">+</div>
                  <div class="el-upload__text">拖拽图片到此处，或 <em>点击上传</em></div>
                  <template #tip>
                    <div class="el-upload__tip">支持常见格式 png/jpg/webp，单次处理一张图片。</div>
                  </template>
                </el-upload>
              </el-form-item>

              <el-form-item label="亮度偏移（-100 ~ 100）">
                <el-slider v-model="brightnessLevel" :min="-100" :max="100" :step="1" show-input
                  :format-tooltip="(val) => `${val > 0 ? '+' : ''}${val}`" />
              </el-form-item>

              <div class="form-actions column">
                <el-button @click="handleRemove" :disabled="!uploadFile">重新选择</el-button>
                <el-button type="primary" :loading="loading" :disabled="!canAdjustBrightness"
                  @click="handleBrightnessAdjust">
                  执行调整
                </el-button>
              </div>
            </el-form>
          </el-card>
        </el-col>

        <el-col :xs="24" :md="8">
          <el-card shadow="never" class="preview-card tall-preview">
            <div class="preview-header">
              <div>
                <p class="eyebrow">Step 02</p>
                <h3>原始图片</h3>
              </div>
              <el-switch v-model="saveOriginal" :disabled="!uploadFile" active-text="保存原图"
                @change="(val) => handleToggleGallery('original', Boolean(val))" />
            </div>
            <div class="preview-body" v-if="originalPreview">
              <img :src="originalPreview" alt="原图预览" />
            </div>
            <p v-else class="preview-placeholder">上传后可在此查看原图预览</p>
          </el-card>
        </el-col>


        <el-col :xs="24" :md="8">
          <el-card shadow="never" class="preview-card tall-preview">
            <div class="preview-header">
              <div>
                <p class="eyebrow">Step 03</p>
                <h3>亮度调整结果</h3>
              </div>
              <el-switch v-model="saveProcessed" :disabled="!hasProcessedResult" active-text="保存结果"
                @change="(val) => handleToggleGallery('processed', Boolean(val))" />
            </div>
            <div class="preview-body" v-if="processedPreview">
              <img :src="processedPreview" alt="亮度调整结果" @click="openImageViewer(processedPreview)" />
            </div>
            <p v-else class="preview-placeholder">执行调整后将在此展示亮度优化后的图片</p>
          </el-card>
        </el-col>
      </el-row>
    </section>


    <section v-else-if="activeFeature === 'contrast'" class="feature-panel">
      <el-row :gutter="20">
        <el-col :xs="24" :md="8">
          <el-card shadow="hover" class="tool-card compact-card">
            <template #header>
              <div class="card-header">
                <div>
                  <p class="eyebrow">Step 01</p>
                  <h2 class="title">上传图片并设置对比度</h2>
                </div>
                <p class="subtitle">增强对比度可突出文字与细节，降低则可柔化画面。</p>
              </div>
            </template>

            <el-form label-position="top" class="tool-form compact-form">
              <el-form-item label="上传待处理图片">
                <el-upload ref="uploadRef" drag accept="image/*" :auto-upload="false" :limit="1" :show-file-list="false"
                  :on-change="handleFileChange" :on-remove="handleRemove" :on-exceed="handleExceed">
                  <div class="upload-placeholder-icon">☁️</div>
                  <div class="el-upload__text">拖拽图片到此处或 <em>点击上传</em></div>
                  <template #tip>
                    <div class="el-upload__tip">建议选择曝光正常的图片，以便对比度调整更直观。</div>
                  </template>
                </el-upload>
              </el-form-item>

              <el-form-item label="对比度调节 (%)">
                <el-slider v-model="contrastLevel" :min="-100" :max="100" :step="1" show-input
                  :format-tooltip="(val) => `${val > 0 ? '+' : ''}${val}%`" />
              </el-form-item>

              <div class="form-actions column">
                <el-button @click="handleRemove" :disabled="!uploadFile">重新选择</el-button>
                <el-button type="primary" :loading="loading" :disabled="!canAdjustContrast"
                  @click="handleContrastAdjust">
                  执行调节
                </el-button>
              </div>
            </el-form>
          </el-card>
        </el-col>

        <el-col :xs="24" :md="8">
          <el-card shadow="never" class="preview-card tall-preview">
            <div class="preview-header">
              <div>
                <p class="eyebrow">Step 02</p>
                <h3>原始图片</h3>
              </div>
              <el-switch v-model="saveOriginal" :disabled="!uploadFile" active-text="保存原图"
                @change="(val) => handleToggleGallery('original', Boolean(val))" />
            </div>
            <div class="preview-body" v-if="originalPreview">
              <img :src="originalPreview" alt="原始图片预览" />
            </div>
            <p v-else class="preview-placeholder">上传后展示原始图像预览</p>
          </el-card>
        </el-col>


        <el-col :xs="24" :md="8">
          <el-card shadow="never" class="preview-card tall-preview">
            <div class="preview-header">
              <div>
                <p class="eyebrow">Step 03</p>
                <h3>对比度结果</h3>
              </div>
              <el-switch v-model="saveProcessed" :disabled="!hasProcessedResult" active-text="保存结果"
                @change="(val) => handleToggleGallery('processed', Boolean(val))" />
            </div>
            <div class="preview-body" v-if="processedPreview">
              <img :src="processedPreview" alt="对比度调整结果" @click="openImageViewer(processedPreview)" />
            </div>
            <p v-else class="preview-placeholder">执行调节后将在此展示结果</p>
          </el-card>
        </el-col>
      </el-row>
    </section>

    <section v-else-if="activeFeature === 'rotate'" class="feature-panel">
      <el-row :gutter="20">
        <el-col :xs="24" :md="8">
          <el-card shadow="hover" class="tool-card compact-card">
            <template #header>
              <div class="card-header">
                <div>
                  <p class="eyebrow">Step 01</p>
                  <h2 class="title">上传图片并设置角度</h2>
                </div>
                <p class="subtitle">❗❗❗逆时针为正方向❗❗❗</p>
              </div>
            </template>

            <el-form label-position="top" class="tool-form compact-form">
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

              <el-form-item label="旋转角度 (°)">
                <el-slider v-model="rotationOnly" :min="-180" :max="180" :step="1" show-input />
              </el-form-item>

              <div class="form-actions column">
                <el-button @click="handleRemove" :disabled="!uploadFile">重新选择</el-button>
                <el-button type="primary" :loading="loading" :disabled="!uploadFile" @click="handleImageRotate">
                  执行旋转
                </el-button>
              </div>
            </el-form>
          </el-card>
        </el-col>

        <el-col :xs="24" :md="8">
          <el-card shadow="never" class="preview-card tall-preview">
            <div class="preview-header">
              <div>
                <p class="eyebrow">Step 02</p>
                <h3>原始图片</h3>
              </div>
              <el-switch v-model="saveOriginal" :disabled="!uploadFile" active-text="保存原图"
                @change="(val) => handleToggleGallery('original', Boolean(val))" />
            </div>
            <div class="preview-body" v-if="originalPreview">
              <img :src="originalPreview" alt="原始图片预览" />
            </div>
            <p v-else class="preview-placeholder">上传后展示原始图像预览</p>
          </el-card>
        </el-col>


        <el-col :xs="24" :md="8">
          <el-card shadow="never" class="preview-card tall-preview">
            <div class="preview-header">
              <div>
                <p class="eyebrow">Step 03</p>
                <h3>旋转结果</h3>
              </div>
              <el-switch v-model="saveProcessed" :disabled="!hasProcessedResult" active-text="保存旋转图"
                @change="(val) => handleToggleGallery('processed', Boolean(val))" />
            </div>
            <div class="preview-body" v-if="processedPreview">
              <img :src="processedPreview" alt="旋转结果" @click="openImageViewer(processedPreview)" />
            </div>
            <p v-else class="preview-placeholder">执行旋转后将在此展示结果</p>
          </el-card>
        </el-col>
      </el-row>
    </section>

    <teleport to="body">
      <el-image-viewer v-if="viewerVisible" :url-list="viewerUrls" :initial-index="viewerIndex"
        @close="closeImageViewer" />
    </teleport>
  </section>
</template>


<style scoped>
/* 让整个卡片内部更紧凑，视觉更现代 */
.tool-card {
  padding: 12px 16px;
}

/* 调整 header 区域 */
.card-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.eyebrow {
  font-size: 12px;
  font-weight: 600;
  color: #409eff;
  margin: 0;
  letter-spacing: 0.5px;
}

.title {
  font-size: 20px;
  margin: 0;
}

.subtitle {
  font-size: 12px;
  color: #888;
  margin-top: 2px;
}

/* 内容区域宽度居中并限制最大宽度 */
.form-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}

.tool-form {
  width: 100%;
  max-width: 440px;
  /* 控制整体大小，视觉更紧凑 */
}

/* 上传区域更居中、美观 */
.upload-box {
  width: 100%;
  padding: 12px 0;
}

.upload-placeholder-icon {
  font-size: 32px;
  opacity: 0.75;
  margin-bottom: 6px;
}

/* 按钮区域居中 + 自动换行 + 更好间距 */
.form-actions {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 6px;
}

.form-container {
  display: flex;
  justify-content: center;
  width: 100%;
}

.tool-form {
  max-width: 480px;
  /* 控制整体宽度 */
  width: 100%;
  margin: 0 auto;
  padding: 4px 0;
}

/* 上传区宽度优化 */
.upload-box {
  width: 100%;
}

/* Radio 组更好看 */
.mode-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 统一按钮布局 */
.form-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 12px;
}

/* 上传区的图标更小、更精致 */
.upload-placeholder-icon {
  font-size: 32px;
  opacity: 0.7;
  margin-bottom: 8px;
}

.center-form {
  max-width: 480px;
  /* 控制宽度 */
  margin: 0 auto;
  /* 居中对齐 */
}

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

:deep(.feature-panel .el-row) {
  align-items: stretch;
}

:deep(.feature-panel .el-col) {
  display: flex;
  flex-direction: column;
}

:deep(.feature-panel .el-col > .el-card) {
  flex: 1;
  display: flex;
  flex-direction: column;
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
  display: inline-block;
  cursor: crosshair;
  max-width: 100%;
}

.scan-overlay img {
  display: block;
  max-width: 100%;
  max-height: 360px;
  border-radius: 10px;
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

.watermark-point {
  background: #f97316;
}

.watermark-thumb {
  margin-bottom: 12px;
  text-align: center;
  background: #f8fafc;
  border: 1px dashed #cbd5f5;
  border-radius: 12px;
  padding: 8px;
}

.watermark-thumb img {
  max-width: 100%;
  max-height: 120px;
  object-fit: contain;
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
