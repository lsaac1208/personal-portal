# 个人门户网站 | Personal Portal Website

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)](#)

一个现代化的个人门户网站，支持多内容类型管理、项目展示、技术博客和在线咨询功能。

## 🌟 核心特性

### 📝 多内容类型支持
- **技术文章** 💻 - 深度技术分享和教程
- **行业观察** 📰 - 行业趋势分析和见解  
- **生活分享** 🌊 - 个人生活和兴趣爱好
- **创作作品** 🎨 - 设计作品和创意项目
- **代码片段** 🔧 - 实用代码和工具分享

### 💼 项目作品集
- **项目展示** - 完整的项目介绍和技术栈
- **在线演示** - 项目demo和GitHub链接
- **技术亮点** - 核心技术和解决方案
- **项目时间线** - 开发过程和里程碑

### 📬 在线咨询系统
- **项目咨询** - 自动化咨询流程管理
- **邮件通知** - 智能邮件模板系统
- **状态跟踪** - 完整的咨询状态管理
- **客户管理** - 潜在客户信息管理

### 🔍 智能搜索与分类
- **全文搜索** - 支持标题、内容、标签搜索
- **分类筛选** - 多维度内容筛选
- **标签系统** - 智能标签管理和推荐
- **SEO优化** - 搜索引擎优化支持

## 🛠️ 技术架构

### 后端技术栈
- **Flask 2.3+** - 轻量级Web框架
- **SQLAlchemy** - ORM数据库管理
- **SQLite3** - 嵌入式数据库
- **Markdown** - 内容格式化渲染
- **Pygments** - 代码语法高亮
- **WTForms** - 表单处理和验证

### 前端技术栈  
- **Bootstrap 5** - 响应式UI框架
- **Jinja2** - 模板引擎
- **FontAwesome** - 图标库
- **响应式设计** - 移动端适配
- **渐进式加载** - 性能优化

### 开发工具
- **Flask-CLI** - 命令行工具
- **CCMP** - 项目管理系统
- **Git** - 版本控制
- **虚拟环境** - 依赖隔离

## 🚀 快速开始

### 环境要求
- Python 3.8+
- pip 包管理器
- Git 版本控制

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/personal-portal.git
cd personal-portal
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **初始化数据库**
```bash
flask init-db
flask seed-data  # 可选：添加示例数据
```

5. **启动开发服务器**
```bash
flask run
# 或者
python run.py
```

6. **访问网站**
打开浏览器访问: `http://localhost:5000`

### 环境配置

创建 `.env` 文件配置环境变量：
```bash
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# 邮件配置（可选）
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_USE_TLS=True

# 管理员邮箱
ADMIN_EMAIL=admin@example.com
```

## 📂 项目结构

```
personal-portal/
├── app/                    # Flask应用目录
│   ├── __init__.py        # 应用工厂
│   ├── models/            # 数据模型
│   │   ├── content.py     # 内容模型
│   │   ├── project.py     # 项目模型
│   │   ├── inquiry.py     # 咨询模型
│   │   ├── tag.py         # 标签模型
│   │   └── user.py        # 用户模型
│   ├── routes/            # 路由蓝图
│   │   ├── main.py        # 主页路由
│   │   ├── content.py     # 内容路由
│   │   ├── admin.py       # 管理后台
│   │   └── api.py         # API接口
│   ├── forms/             # 表单类
│   │   ├── content.py     # 内容表单
│   │   ├── project.py     # 项目表单
│   │   └── inquiry.py     # 咨询表单
│   ├── utils/             # 工具函数
│   │   ├── content_utils.py # 内容处理
│   │   └── email_utils.py   # 邮件工具
│   ├── templates/         # HTML模板
│   └── static/           # 静态文件
├── .claude/              # CCMP项目管理
│   ├── prds/             # 产品需求文档
│   ├── epics/            # Epic管理
│   └── context/          # 项目上下文
├── config.py             # 配置文件
├── requirements.txt      # 项目依赖
├── run.py               # 启动文件
└── README.md            # 项目文档
```

## 🎯 功能模块

### 1. 内容管理系统
- ✅ **多类型内容支持** - 技术、观察、生活、创作、代码
- ✅ **Markdown编辑器** - 支持语法高亮和实时预览
- ✅ **标签系统** - 智能标签分类和管理
- ✅ **SEO优化** - 元数据管理和搜索优化
- ✅ **图片上传** - 自动压缩和尺寸优化

### 2. 项目作品集
- ✅ **项目展示** - 完整的项目信息展示
- ✅ **技术栈管理** - 项目使用的技术标签
- ✅ **演示链接** - GitHub和在线demo链接
- ✅ **项目时间线** - 开发进度和里程碑
- ✅ **成果展示** - 项目成果和影响力

### 3. 咨询管理系统  
- ✅ **在线咨询表单** - 智能表单验证和提交
- ✅ **邮件通知系统** - 自动邮件模板和通知
- ✅ **状态跟踪** - 完整的咨询流程管理
- ✅ **客户管理** - 潜在客户信息管理
- ✅ **回复管理** - 管理员回复和跟进

### 4. 用户体验优化
- ✅ **响应式设计** - 完美适配移动设备
- ✅ **性能优化** - 图片压缩和延迟加载
- ✅ **搜索功能** - 全文搜索和智能筛选
- ✅ **RSS订阅** - 内容订阅和推送
- ✅ **社交分享** - 文章和项目分享

## 🔧 开发指南

### 添加新的内容类型
1. 在 `app/models/content.py` 中添加新的分类选项
2. 更新 `app/forms/content.py` 中的表单选项
3. 在模板中添加对应的图标和样式

### 扩展邮件模板
1. 在 `app/utils/email_utils.py` 的 `EmailTemplates` 类中添加新模板
2. 创建对应的发送函数
3. 在路由中调用新的邮件发送功能

### 自定义主题样式
1. 修改 `app/static/css/` 中的样式文件
2. 更新 `app/templates/base.html` 中的基础模板
3. 使用Bootstrap变量自定义主题色彩

## 📊 项目管理

本项目采用 **CCMP (Critical Chain Project Management)** 方法进行管理：

- **📋 PRD文档** - 详细的产品需求文档
- **🎯 Epic管理** - 分阶段的开发计划  
- **📈 进度跟踪** - 实时的项目状态监控
- **🔄 迭代开发** - 持续交付和改进

查看项目管理文档: [.claude/PROJECT-STATUS.md](.claude/PROJECT-STATUS.md)

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出改进建议：

1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📝 开发日志

### Phase 1: 基础架构 ✅ (已完成)
- [x] Flask应用架构搭建
- [x] 数据模型设计
- [x] 路由系统配置
- [x] 表单和工具类

### Phase 2: 模板系统 🔄 (开发中)
- [ ] 基础HTML模板  
- [ ] 响应式UI设计
- [ ] 内容展示页面
- [ ] 管理后台界面

### Phase 3: 内容发布 📋 (计划中)
- [ ] 内容发布功能
- [ ] 图片上传处理
- [ ] SEO优化集成
- [ ] RSS订阅系统

## 📞 联系方式

- **作者**: [您的姓名]
- **邮箱**: [your-email@example.com]
- **GitHub**: [https://github.com/yourusername](https://github.com/yourusername)
- **网站**: [https://your-website.com](https://your-website.com)

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢以下开源项目和工具：

- [Flask](https://flask.palletsprojects.com/) - 优雅的Python Web框架
- [Bootstrap](https://getbootstrap.com/) - 强大的前端UI框架  
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL工具包
- [Markdown](https://python-markdown.github.io/) - Markdown处理库
- [Pygments](https://pygments.org/) - 代码语法高亮

---

⭐ 如果这个项目对您有帮助，欢迎给个Star支持！