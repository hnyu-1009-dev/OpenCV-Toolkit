# OpenCV-Toolkit FastAPI Backend

> 后端工程骨架：基于 FastAPI + Tortoise ORM 构建，目录结构清晰，并配有中文注释便于扩展。

## 目录结构

```
OpenCV-Toolkit/
├─ app/                  # FastAPI 源码目录
│  ├─ main.py            # 应用入口，创建 FastAPI 实例并注册事件
│  ├─ api/               # 路由模块，按版本拆分
│  ├─ core/              # 配置、常量等核心模块
│  ├─ db/                # 数据库连接、Tortoise ORM 管理
│  ├─ deps/              # 依赖注入函数（预留）
│  ├─ models/            # ORM 模型定义
│  ├─ schemas/           # Pydantic 数据模型
│  └─ services/          # 业务服务层
└─ pyproject.toml        # Python 项目配置
```

## 本地运行

```bash
cd backend-fastapi/OpenCV-Toolkit
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell
pip install -e .
uvicorn app.main:app --reload
```

启动后访问 <http://localhost:8000/api/v1/health> 验证服务状态。

## 数据库

- 默认使用 **Tortoise ORM + SQLite**（`sqlite://app.db`），开箱即用；
- 若需切换 PostgreSQL，只需在 `.env` 中设置 `DATABASE_URL=postgres://user:pass@host:5432/dbname`；
- 所有模型位于 `app/models/`，在 `app/db/session.py` 中统一初始化 / 释放连接。
