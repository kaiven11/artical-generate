# 今日头条AI赛道文章搬运工具

一款专业的AI赛道文章自动化搬运工具，集成文章获取、翻译优化、检测验证、自动发布于一体。

## 功能特性

- 🔍 **多平台文章获取**: 支持Medium、Dev.to、Hashnode等平台
- 🤖 **AI智能翻译**: 集成OpenAI、Claude、Gemini等AI服务
- 🛡️ **原创性检测**: 朱雀检测等多平台检测服务
- 📤 **自动发布**: 支持今日头条、微信公众号等平台
- 🎯 **插件化架构**: 可扩展的平台适配器系统
- 🔒 **反检测机制**: Fingerprint Chromium + 指纹随机化

## 技术架构

- **后端**: Python 3.9+ + FastAPI
- **前端**: HTML5 + CSS3 + JavaScript + Bootstrap 5
- **数据库**: SQLite
- **浏览器自动化**: DrissionPage + Fingerprint Chromium
- **AI服务**: OpenAI、Claude、Gemini等

## 快速开始

### 1. 环境要求

- Python 3.9+
- pip 或 conda
- Fingerprint Chromium (可选，用于反检测)

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置环境

创建 `.env` 文件（可选）：

```env
# 应用配置
APP_NAME="Article Migration Tool"
DEBUG=true
HOST=127.0.0.1
PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///./data/articles.db

# 日志配置
LOG_LEVEL=INFO
LOG_DIRECTORY=./data/logs

# 浏览器配置
BROWSER_CHROME_PATH=/path/to/fingerprint-chromium
BROWSER_HEADLESS_MODE=false

# 检测配置
DETECTION_ORIGINALITY_THRESHOLD=80.0
DETECTION_AI_DETECTION_THRESHOLD=70.0
```

### 4. 启动应用

```bash
# 方式1: 使用启动脚本 (推荐)
python run.py

# 方式2: 直接使用uvicorn
uvicorn app.main:app --host 127.0.0.1 --port 8007 --reload
```

### 5. 访问应用

- **主界面**: http://127.0.0.1:8007
- **API文档**: http://127.0.0.1:8007/docs
- **健康检查**: http://127.0.0.1:8007/health

### 6. 当前功能状态 (2025-06-27更新)

#### 已完成功能 ✅
- **前端界面**: 左右布局，响应式设计，实时进度显示
- **文章搜索**: Medium平台关键词/分类搜索
- **文章管理**: 创建、查询、状态更新完整流程
- **内容提取**: Freedium.cfd + Chrome浏览器自动化
- **任务系统**: 异步处理任务和实时状态监控
- **API集成**: 完整的RESTful API接口

#### 开发中功能 🔄
- **AI翻译**: Claude-4-Sonnet API集成
- **内容优化**: 智能重写和结构优化
- **AI检测**: 朱雀检测循环优化流程
- **发布系统**: 今日头条平台发布

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── core/                   # 核心配置
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库配置
│   │   └── security.py        # 安全工具
│   ├── models/                 # 数据模型
│   │   ├── article.py         # 文章模型
│   │   ├── prompt.py          # 提示词模型
│   │   ├── detection.py       # 检测结果模型
│   │   ├── task.py            # 任务模型
│   │   └── config.py          # 配置模型
│   ├── api/                    # API路由
│   ├── services/               # 业务服务
│   │   ├── platform_manager.py # 平台管理器
│   │   ├── browser_manager.py  # 浏览器管理器
│   │   └── ...
│   ├── adapters/               # 平台适配器
│   │   ├── base.py            # 基础适配器
│   │   ├── source/            # 来源平台适配器
│   │   ├── ai/                # AI服务适配器
│   │   ├── detection/         # 检测服务适配器
│   │   └── publish/           # 发布平台适配器
│   ├── schemas/                # Pydantic模式
│   └── utils/                  # 工具函数
├── data/                       # 数据目录
├── browser_data/              # 浏览器数据
├── templates/                 # HTML模板
├── static/                    # 静态文件
├── requirements.txt           # Python依赖
└── run.py                     # 启动脚本
```

## 开发状态

### ✅ 已完成

- [x] 项目基础架构搭建
- [x] 数据库模型设计
- [x] 平台管理模块
- [x] 浏览器管理模块
- [x] 基础Web界面
- [x] 配置管理系统

### 🚧 开发中

- [ ] 文章获取模块
- [ ] AI翻译服务模块
- [ ] 检测服务模块
- [ ] 发布服务模块
- [ ] 任务调度系统
- [ ] 完整前端界面

### 📋 计划中

- [ ] 插件市场
- [ ] 性能优化
- [ ] 单元测试
- [ ] 部署文档
- [ ] 用户手册

## 配置说明

### API服务配置

系统支持多个AI服务提供商，需要在界面中配置相应的API密钥：

1. **OpenAI**: 需要API Key
2. **Anthropic Claude**: 需要API Key
3. **Google Gemini**: 需要API Key
4. **朱雀检测**: 需要账号登录

### 浏览器配置

为了实现反检测功能，建议使用Fingerprint Chromium：

1. 下载Fingerprint Chromium
2. 在配置中设置浏览器路径
3. 启用指纹随机化功能

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 支持

如果您遇到问题或有建议，请：

1. 查看 [Issues](../../issues) 页面
2. 创建新的 Issue
3. 联系开发团队

## 更新日志

### v1.0.0 (开发中)

- 初始版本发布
- 基础功能实现
- 插件化架构
- Web界面
