# 文章处理系统

## 启动命令
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8007
```

## 项目结构
```
backend/
├── app/                    # 核心应用代码
│   ├── adapters/          # 平台适配器
│   ├── api/               # API接口
│   ├── core/              # 核心功能
│   ├── services/          # 业务服务
│   └── utils/             # 工具函数
├── static/                # 前端静态资源
├── templates/             # 模板文件
├── data/                  # 数据库文件
├── logs/                  # 日志文件
├── requirements.txt       # 依赖配置
└── run.py                # 启动脚本

docs/                      # 项目文档
```

## 功能特性
- 文章内容提取和处理
- AI内容检测和优化
- 多平台内容发布
- 主题创作功能
- 提示词管理
- API配置管理

## 访问地址
- 主界面: http://localhost:8007
- API文档: http://localhost:8007/docs

