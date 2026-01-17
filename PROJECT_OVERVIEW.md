# GPT 账号自动注册系统 - 项目总览

## 项目简介

这是一个完整的 GPT 账号自动注册系统,支持使用已有的微软账号批量注册 GPT 账号。

### 核心功能

- ✅ **批量注册**: 支持批量导入微软账号并自动注册 GPT
- ✅ **验证码识别**: 集成 2Captcha/YesCaptcha 自动解决验证码
- ✅ **代理池管理**: 支持 HTTP/SOCKS5 代理,自动轮换避免 IP 封禁
- ✅ **实时进度**: WebSocket 实时推送注册进度和日志
- ✅ **Excel 管理**: 方便的 Excel 账号导入导出功能
- ✅ **密码加密**: Fernet 对称加密保护敏感信息
- ✅ **失败重试**: 智能重试机制,提高成功率
- ✅ **详细日志**: 完整的操作日志和错误截图

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                       前端 (Vue 3)                           │
│  Element Plus UI + WebSocket 客户端 + REST API               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    后端 (FastAPI)                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  API 路由层 (accounts, registration, websocket)     │    │
│  └─────────────────────────────────────────────────────┘    │
│                              ↓                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  核心业务层                                           │    │
│  │  ├─ BrowserService (Playwright)                     │    │
│  │  ├─ RegistrationStateMachine (状态机)               │    │
│  │  ├─ CaptchaSolver (验证码识别)                      │    │
│  │  └─ ProxyManager (代理池)                           │    │
│  └─────────────────────────────────────────────────────┘    │
│                              ↓                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  服务层                                               │    │
│  │  ├─ ExcelService (Excel 读写)                       │    │
│  │  └─ CryptoService (加密服务)                         │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    数据存储层                                │
│  Excel (accounts.xlsx) + SQLite (database.db)               │
└─────────────────────────────────────────────────────────────┘
```

## 已完成模块

### 后端 (Python + FastAPI)

#### 1. 数据模型 (`app/models/`)
- ✅ `enums.py` - 枚举定义(注册状态、日志级别等)
- ✅ `schemas.py` - Pydantic 数据模型

#### 2. 核心业务逻辑 (`app/core/`)
- ✅ `browser.py` - Playwright 浏览器自动化服务
- ✅ `registration.py` - 注册流程状态机
- ✅ `captcha_solver.py` - 验证码识别服务(2Captcha/YesCaptcha)
- ✅ `proxy_manager.py` - 代理池管理器

#### 3. 服务层 (`app/services/`)
- ✅ `crypto_service.py` - Fernet 加密服务
- ✅ `excel_service.py` - Excel 读写服务

#### 4. API 路由 (`app/api/routes/`)
- ✅ `accounts.py` - 账号管理 API
- ✅ `registration.py` - 注册任务 API
- ✅ `websocket.py` - WebSocket 实时通信

#### 5. 工具和配置
- ✅ `config.py` - 配置管理(Pydantic Settings)
- ✅ `logger.py` - 日志系统(loguru)
- ✅ `main.py` - FastAPI 应用入口

#### 6. 配置文件
- ✅ `requirements.txt` - Python 依赖清单
- ✅ `.env.example` - 环境变量示例
- ✅ `README.md` - 详细使用文档

## 项目目录结构

```
d:\工作\忙\python_code\自动注册gpt账号\
│
├── backend/                          # 后端项目 ✅
│   ├── app/
│   │   ├── main.py                  # FastAPI 入口
│   │   ├── config.py                # 配置管理
│   │   │
│   │   ├── api/routes/              # API 路由
│   │   │   ├── accounts.py          # 账号管理 API ✅
│   │   │   ├── registration.py      # 注册任务 API ✅
│   │   │   └── websocket.py         # WebSocket ✅
│   │   │
│   │   ├── core/                    # 核心业务
│   │   │   ├── browser.py           # 浏览器服务 ✅
│   │   │   ├── registration.py      # 注册状态机 ✅
│   │   │   ├── captcha_solver.py    # 验证码识别 ✅
│   │   │   └── proxy_manager.py     # 代理管理 ✅
│   │   │
│   │   ├── models/                  # 数据模型
│   │   │   ├── schemas.py           # Pydantic 模型 ✅
│   │   │   └── enums.py             # 枚举定义 ✅
│   │   │
│   │   ├── services/                # 服务层
│   │   │   ├── excel_service.py     # Excel 读写 ✅
│   │   │   └── crypto_service.py    # 加密服务 ✅
│   │   │
│   │   └── utils/                   # 工具
│   │       └── logger.py            # 日志工具 ✅
│   │
│   ├── data/
│   │   └── accounts.xlsx            # Excel 账号文件
│   ├── logs/                        # 日志目录
│   ├── screenshots/                 # 截图目录
│   ├── requirements.txt             # Python 依赖 ✅
│   ├── .env.example                 # 环境变量示例 ✅
│   └── README.md                    # 后端文档 ✅
│
├── frontend/                        # 前端项目 (Vue 3) ⏳
│   └── (待开发)
│
└── PROJECT_OVERVIEW.md              # 本文件 ✅
```

## 快速开始

### 1. 安装依赖

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 安装 Playwright 浏览器

```bash
playwright install chromium
```

### 3. 配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env 文件,修改以下配置:
# ENCRYPTION_KEY=your-secret-key-here
# CAPTCHA_API_KEY=your-captcha-api-key
```

### 4. 准备账号文件

创建 `data/accounts.xlsx` 文件,格式如下:

| 邮箱 | 密码 | 状态 |
|------|------|------|
| user1@outlook.com | password123 | pending |
| user2@outlook.com | password456 | pending |

### 5. 启动服务

```bash
python -m app.main
```

访问 http://localhost:8000/docs 查看 API 文档

## API 使用示例

### 添加账号

```bash
curl -X POST "http://localhost:8000/api/accounts/add" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user1@outlook.com",
    "password": "YourPassword123"
  }'
```

### 开始批量注册

```bash
curl -X POST "http://localhost:8000/api/registration/start?max_concurrent=3"
```

### 查看任务状态

```bash
curl "http://localhost:8000/api/registration/status/task_xxx"
```

### WebSocket 连接

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/task_xxx');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

## 核心设计原则

### SOLID 原则

1. **单一职责**: 每个模块职责明确
   - `BrowserService` 只负责浏览器操作
   - `ExcelService` 只负责 Excel 读写
   - `CryptoService` 只负责加密解密

2. **开闭原则**: 通过抽象类扩展功能
   - `CaptchaSolver` 抽象类支持多种验证码服务
   - 可轻松添加新的验证码服务商

3. **依赖倒置**: 依赖抽象而非具体实现
   - 使用 `RegistrationContext` 传递依赖
   - 便于测试和替换组件

### DRY (Don't Repeat Yourself)

- 统一的日志系统
- 统一的错误处理
- 统一的配置管理

### KISS (Keep It Simple, Stupid)

- 清晰的代码结构
- 简单的 API 设计
- 直观的状态机流程

## 安全特性

1. **密码加密**: 所有密码使用 Fernet 加密存储
2. **环境变量**: 敏感配置通过环境变量管理
3. **CORS 保护**: 可配置的 CORS 源
4. **代理支持**: 隐藏真实 IP 地址
5. **失败重试**: 智能的错误处理和恢复

## 下一步开发

### 前端开发 (Vue 3)

- [ ] 搭建 Vue 3 + Vite 项目
- [ ] 实现账号管理页面
- [ ] 实现批量注册页面
- [ ] 实现进度监控页面
- [ ] WebSocket 集成

### 功能增强

- [ ] 邮箱自动验证
- [ ] 更多验证码服务支持
- [ ] 任务暂停/恢复功能
- [ ] 分布式任务队列
- [ ] Web 界面

## 技术栈版本

| 组件 | 版本 |
|------|------|
| Python | 3.10+ |
| FastAPI | 0.104.1 |
| Playwright | 1.40.0 |
| openpyxl | 3.1.2 |
| cryptography | 41.0.7 |
| loguru | 0.7.2 |

## 注意事项

⚠️ **重要提示:**

1. 本项目仅供学习交流使用
2. 请遵守相关服务条款
3. 注意控制注册频率
4. 使用高质量代理提高成功率
5. 生产环境必须修改加密密钥

## 许可证

MIT License

---

**当前状态**: 后端核心功能已完成 ✅

**下一步**: 安装依赖并测试 API
