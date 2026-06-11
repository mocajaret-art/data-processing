# FBS — 分布式任务调度与数据处理平台

模拟企业内部数据处理平台。上传 CSV/Excel/JSON 文件，自动执行数据分析（缺失值、数值统计、高频值），实时查看结果。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + Vite + Ant Design 5 |
| 后端 | Python + FastAPI + SQLAlchemy |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） |
| 异步任务 | Celery + Redis（生产环境） |
| 数据处理 | Pandas |

## 快速开始

**前置条件**：Python 3.10+、Node.js 18+

```bash
# 1. 安装后端依赖
pip install -r backend/requirements.txt

# 2. 安装前端依赖
cd frontend
npm install --registry=https://registry.npmmirror.com
cd ..

# 3. 一键启动
双击 start_all.bat
```

启动后控制台显示进度，后端端口 8002，前端端口 3000。按任意键停止所有服务。

浏览器访问 `http://localhost:3000`。

## 项目结构

```
fbs/
├── .gitignore
├── README.md
├── start_all.bat           # 一键启动（Windows）
├── start_all.ps1           # 启动脚本本体
├── 测试.json               # 测试用 JSON 数据
├── 测试.csv                # 测试用 CSV 数据
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # FastAPI 入口
│       ├── config.py           # 配置
│       ├── database.py         # 异步引擎（PG→SQLite 自动降级）
│       ├── models/             # User / File / Task
│       ├── schemas/            # Pydantic 请求/响应
│       ├── api/                # auth / files / tasks
│       ├── auth/               # JWT + 认证依赖
│       └── celery_app/         # Celery 实例 + 数据分析
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── App.jsx             # 路由 + 鉴权守卫
        ├── api/client.js       # axios 封装
        ├── pages/              # 登录/注册/仪表盘/上传/详情
        └── components/         # Navbar
```

## 页面说明

### 登录页 `/login`
输入用户名和密码登录。没有账号点下方"立即注册"。

### 注册页 `/register`
填写用户名、邮箱、密码（至少 3 位），注册成功自动登录。

### 仪表盘 `/`
顶部 4 张统计卡片（总数/已完成/失败/运行中），下方最近任务列表，每 5 秒自动刷新。点击任务行进入详情。

### 上传页 `/upload`
拖拽或点击选择 CSV / Excel / JSON 文件，点"上传并开始分析"。自动创建任务并跳转详情。

### 任务详情 `/tasks/{id}`
状态标签实时更新（等待中→运行中→已完成/失败）。成功后展示：缺失值统计、数值列均值/标准差、文本列 Top-N 频次。底部按钮可下载 JSON 结果。

## API 接口

除注册/登录外，均需 `Authorization: Bearer {token}`。

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| GET | `/api/auth/me` | 当前用户 |
| POST | `/api/files/upload` | 上传文件 |
| GET | `/api/files/` | 文件列表 |
| GET | `/api/files/{id}` | 文件详情 |
| POST | `/api/tasks/` | 创建分析任务 |
| GET | `/api/tasks/` | 任务列表 |
| GET | `/api/tasks/{id}` | 任务详情（含结果） |
| GET | `/api/tasks/{id}/result` | 下载结果 JSON |

### 分析结果格式

```json
{
  "row_count": 15,
  "column_count": 9,
  "columns": ["id", "name", "age", ...],
  "missing_values": {"age": 3},
  "numeric_stats": {"age": {"mean": 32.5, "std": 8.3, "min": 18, "max": 65}},
  "top_values": {"city": [{"value": "Beijing", "count": 300}]}
}
```

## 任务状态

```
PENDING  →  等待处理
RUNNING  →  正在处理
SUCCESS  →  处理完成
FAILED   →  处理失败
```

## 使用流程

1. 双击 `start_all.bat` 启动
2. 浏览器访问 `http://localhost:3000`，注册账号并登录
3. 点击"上传文件"，拖入 CSV/Excel/JSON 文件
4. 点"上传并开始分析"，自动跳转任务详情
5. 等待片刻，查看数值统计和高频值分析结果
6. 下载 JSON 结果，或返回仪表盘查看任务列表
7. 关闭启动窗口即停止所有服务


