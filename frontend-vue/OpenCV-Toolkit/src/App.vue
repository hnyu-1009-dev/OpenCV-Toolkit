<script setup lang="ts">
import { RouterView } from 'vue-router' // RouterView 负责渲染匹配到的页面组件
</script>

<template>
  <!-- 应用的通用外壳，提供统一背景与居中布局 -->
  <div class="app-shell">
    <div class="app-shell__content">
      <!-- 渲染当前激活的路由页面，如登录/注册/首页 -->
      <RouterView />
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  /* 让整个页面垂直居中并提供柔和渐变背景 */
  min-height: 100vh;
  background: radial-gradient(circle at top, rgba(14, 165, 233, 0.35), transparent 40%),
    radial-gradient(circle at bottom, rgba(59, 130, 246, 0.4), transparent 40%), #020617;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(24px, 4vw, 56px);
}

.app-shell__content {
  /* 限制内容宽度，避免大屏时内容太散 */
  width: min(1100px, 100%);
  margin: 0 auto;
}
</style>
