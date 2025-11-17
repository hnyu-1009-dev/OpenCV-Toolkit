# 🖼️ OpenCV Toolkit

## 概述（Overview）
**OpenCV Toolkit** 是一个 **中英双语的全栈计算机视觉工作平台**。  
后端采用 **FastAPI + Tortoise ORM** 处理各种 OpenCV / Pillow 图像任务，前端使用 **Vue 3 + Element Plus** 构建单页可视化工作环境，让用户可以上传图片、调参处理、并将结果保存到共享图库中。

---

## 📁 仓库结构（Repository Layout）

```
OpenCV-Toolkit/
├─ backend-fastapi/OpenCV-Toolkit/ # FastAPI 服务、Tortoise ORM 模型、Aerich 迁移
│ ├─ app/ # API 路由、业务逻辑、设置、数据库会话
│ ├─ storage/ # 上传文件的本地目录（通过 /media 暴露）
│ └─ migrations/ # Aerich 自动创建的数据库迁移文件
└─ frontend-vue/OpenCV-Toolkit/ # Vue3 + Element Plus 单页应用
├─ src/api # Auth / Gallery / Vision 的 REST API 客户端
├─ src/views # 页面：工作空间、图库、用户信息、登录注册等
└─ src/stores # Pinia 本地持久化 Auth Store
```
yaml
复制代码

---

## ✨ 核心功能（Key Features）

### 🔧 后端：视觉与图库服务（Vision & Gallery Services）
* 统一的 `/api/v1` 路由结构，包含健康检查、身份认证、用户模块以及工作面板功能接口。
* Dashboard 模块提供丰富的图像操作：  
  - 色盲模拟  
  - 文档透视扫描  
  - 水印叠加  
  - 自由旋转  
  - 对比度调节  
  - 亮度调节  
  - 图像持久化保存到图库  
* 独立控制器提供：  
  - 健康检查  
  - 登录注册  
  - 用户资料获取与修改  

### 🖥️ 前端：可视化工作页面（Frontend Workspace）
* 包含多个视觉工具页签：色盲检测、文档扫描、水印叠加、亮度/对比度调节、旋转工具。
* 各工具具有：拖拽操作、滑块控制、图像预览、上传组件。
* Pinia 管理 Token、自动同步用户资料到 localStorage。
* Axios 注入 Token、统一处理 API 错误，如 Token 过期自动跳转。

---

## 🛠️ 技术栈（Tech Stack）

| 层级 | 技术 |
| --- | --- |
| 后端 | FastAPI, Tortoise ORM, Aerich, Pillow, OpenCV, Uvicorn (Python ≥3.11) |
| 前端 | Vue 3 + TypeScript, Vite, Pinia, Vue Router, Element Plus |
| 存储 | 本地 `storage/` 文件夹，通过 `/media` 静态资源服务暴露 |

---

## 📝 常用命令（Frequently Used Commands）

| 场景 | 命令 | 功能 |
| --- | --- | --- |
| 后端 | `uvicorn app.main:app --reload` | 运行 FastAPI 开发服务器 |
| 后端 | `aerich upgrade` | 应用数据库迁移 |
| 前端 | `pnpm dev` | 启动开发模式 |
| 前端 | `pnpm build` | 构建生产环境代码 |
| 前端 | `pnpm lint` / `pnpm type-check` | 代码质量检查、类型检查 |

---

## 🌐 API 接口总览（API Surface Overview）

| 方法 | 路径 | 描述 |
| --- | --- | --- |
| GET | `/api/v1/health` | 健康检查接口 |
| POST | `/api/v1/auth/login` | 用户登录，返回 Token |
| POST | `/api/v1/auth/register` | 用户注册 |
| GET / PATCH | `/api/v1/users/{user_id}` | 获取或更新个人资料 |
| GET | `/api/v1/dashboard/summary` | 获取工作区首页统计信息 |
| POST | `/api/v1/dashboard/gallery` | 已存在文件的图库元数据入库 |
| POST | `/api/v1/dashboard/gallery/upload` | 上传新图片并创建图库记录 |
| GET | `/api/v1/dashboard/gallery/{user_id}` | 分页查询图库（支持过滤） |
| DELETE | `/api/v1/dashboard/gallery/{item_id}` | 删除图库项 |
| POST | `/api/v1/dashboard/vision/color-blind` | 色盲模拟 |
| POST | `/api/v1/dashboard/vision/document-scan` | 文档扫描（透视校正） |
| POST | `/api/v1/dashboard/vision/rotate` | 自由旋转图像 |
| POST | `/api/v1/dashboard/vision/watermark` | 添加水印 |
| POST | `/api/v1/dashboard/vision/contrast` | 对比度调整 |
| POST | `/api/v1/dashboard/vision/brightness` | 亮度调整 |

---

欢迎发起 Issue 或加入讨论来扩展更多功能（如 OCR、批量处理流水线等）！