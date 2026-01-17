# GPT 账号自动注册系统 - 后端

基于 FastAPI + Playwright 的 GPT 账号自动注册系统。

## 功能特性

- ✅ 批量自动注册 GPT 账号
- ✅ 支持微软账号登录
- ✅ 自动识别和解决验证码
- ✅ 代理池管理,避免 IP 封禁
- ✅ WebSocket 实时进度推送
- ✅ Excel 账号导入导出
- ✅ 密码加密存储
- ✅ 详细日志记录
- ✅ 失败自动重试

## 技术栈

- **Web 框架**: FastAPI 0.104.1
- **浏览器自动化**: Playwright 1.40.0
- **数据存储**: Excel (openpyxl) + SQLite
- **加密**: cryptography (Fernet)
- **日志**: loguru
- **异步**: asyncio + httpx

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 安装 Playwright 浏览器

```bash
playwright install chromium
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置:

```bash
cp .env.example .env
```

**必须配置的项:**

```env
# 加密密钥(必须修改!)
ENCRYPTION_KEY=your-secret-key-here-change-this-in-production

# 验证码服务 API Key
CAPTCHA_SERVICE=2captcha
CAPTCHA_API_KEY=your-captcha-api-key-here
```

### 4. 创建数据目录

```bash
mkdir -p data logs screenshots
```

### 5. 准备账号文件

创建 `data/accounts.xlsx` 文件,包含以下列:

| 邮箱 | 密码 | 备用邮箱 | 代理地址 | 代理端口 | 状态 |
|------|------|----------|----------|----------|------|
| user1@outlook.com | password123 | | | | pending |
| user2@outlook.com | password456 | | | | pending |

### 6. 启动服务

```bash
# 开发模式(支持热重载)
python -m app.main

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后访问:
- API 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc

## API 端点

### 账号管理

- `GET /api/accounts/` - 获取账号列表
- `GET /api/accounts/stats` - 获取统计信息
- `POST /api/accounts/import` - 导入账号
- `POST /api/accounts/export` - 导出账号
- `PUT /api/accounts/{id}` - 更新账号
- `DELETE /api/accounts/{id}` - 删除账���
- `POST /api/accounts/add` - 添加单个账号

### 注册任务

- `POST /api/registration/start` - 开始批量注册
- `GET /api/registration/status/{task_id}` - 获取任务状态
- `POST /api/registration/pause/{task_id}` - 暂停任务
- `POST /api/registration/resume/{task_id}` - 恢复任务
- `POST /api/registration/cancel/{task_id}` - 取消任务

### WebSocket

- `WS /ws/{task_id}` - 实时进度推送

## 使用示例

### 1. 添加账号

```bash
curl -X POST "http://localhost:8000/api/accounts/add" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user1@outlook.com",
    "password": "YourPassword123",
    "status": "pending"
  }'
```

### 2. 开始批量注册

```bash
curl -X POST "http://localhost:8000/api/registration/start?max_concurrent=3"
```

### 3. 查看任务状态

```bash
curl "http://localhost:8000/api/registration/status/task_20240116123456_1"
```

### 4. WebSocket 连接(JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/task_20240116123456_1');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('类型:', data.type);
  console.log('数据:', data.data);
};

// 发送心跳
setInterval(() => {
  ws.send('ping');
}, 30000);
```

## 项目结构

```
backend/
├── app/
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置管理
│   │
│   ├── api/routes/            # API 路由
│   │   ├── accounts.py        # 账号管理 API
│   │   ├── registration.py    # 注册任务 API
│   │   └── websocket.py       # WebSocket 连接
│   │
│   ├── core/                  # 核心业务逻辑
│   │   ├── browser.py         # 浏览器自动化
│   │   ├── registration.py    # 注册流程状态机
│   │   ├── captcha_solver.py  # 验证码识别
│   │   └── proxy_manager.py   # 代理池管理
│   │
│   ├── models/                # 数据模型
│   │   ├── schemas.py         # Pydantic 模型
│   │   └── enums.py           # 枚举定义
│   │
│   ├── services/              # 服务层
│   │   ├── excel_service.py   # Excel 读写
│   │   └── crypto_service.py  # 加密服务
│   │
│   └── utils/                 # 工具函数
│       └── logger.py          # 日志工具
│
├── data/
│   └── accounts.xlsx          # Excel 账号文件
├── logs/                      # 日志目录
├── screenshots/               # 截图目录
├── requirements.txt           # Python 依赖
├── .env.example              # 环境变量示例
└── README.md                 # 本文件
```

## 安全说明

1. **密码加密**: 所有密码使用 Fernet 对称加密存储
2. **环境变量**: 敏感信息通过环境变量配置
3. **CORS**: 生产环境需配置正确的 CORS 源
4. **代理**: 使用代理池避免 IP 封禁
5. **验证码**: 支持 2Captcha/YesCaptcha 等服务

## 注意事项

1. 本项目仅供学习交流使用
2. 请遵守相关服务条款
3. 注意控制注册频率,避免账号被封
4. 使用高质量代理提高成功率
5. 定期备份 Excel 账号文件

## 故障排除

### Playwright 浏览器未安装

```bash
playwright install chromium
```

### 导入错误

确保已安装所有依赖:
```bash
pip install -r requirements.txt
```

### 验证码识别失败

1. 检查 API Key 是否正确
2. 确保账户有足够余额
3. 尝试切换验证码服务商

### 代理连接失败

1. 检查代理地址和端口是否正确
2. 确保代理服务可用
3. 尝试使用不同的代理

## 开发

```bash
# 运行测试
pytest

# 代码格式化
black app/
isort app/

# 类型检查
mypy app/
```

## 许可证

MIT License

## 联系方式

如有问题或建议,请提交 Issue。
