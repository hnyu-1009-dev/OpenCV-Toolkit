import './assets/main.css' // 引入全局样式，确保应用基础视觉统一

import { createApp } from 'vue' // 创建 Vue 应用实例
import { createPinia } from 'pinia' // 注册 Pinia，以便后续拓展状态管理
import ElementPlus from 'element-plus' // 引入 Element Plus 组件库
import 'element-plus/dist/index.css' // 引入 Element Plus 的默认样式

import App from './App.vue' // 应用根组件
import router from './router' // 应用路由配置

const app = createApp(App) // 创建 Vue 应用

app.use(createPinia()) // 启用 Pinia，方便后续引入全局状态
app.use(router) // 安装路由，让组件可以进行页面跳转
app.use(ElementPlus) // 全局注册 Element Plus 组件

app.mount('#app') // 将应用挂载到 DOM 节点，正式启动
