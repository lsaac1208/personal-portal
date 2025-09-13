#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个人门户网站演示数据创建脚本
自动为网站创建内容、项目和咨询等演示数据
"""
import os
import sys
from datetime import datetime, timedelta
from app import create_app, db
from app.models import Content, Project, ProjectInquiry, Tag
from app.models.customer import Customer, CustomerInteraction, BusinessOpportunity

def create_demo_data():
    """创建演示数据"""
    print("🚀 开始创建演示数据...")
    
    # 1. 创建技术文章内容
    articles = [
        {
            'title': 'Flask Web开发最佳实践',
            'content': '''# Flask Web开发最佳实践

Flask是一个轻量级的Python Web框架，以其简洁和灵活性而闻名。本文将分享一些Flask开发的最佳实践。

## 1. 项目结构设计

```python
app/
├── __init__.py          # 应用工厂
├── models.py           # 数据模型
├── routes.py           # 路由处理
├── forms.py            # 表单类
└── templates/          # 模板文件
```

## 2. 配置管理

使用配置类来管理不同环境的配置：

```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
```

## 3. 蓝图组织

使用蓝图来组织大型应用：

```python
from flask import Blueprint
main = Blueprint('main', __name__)
```

Flask的生态系统丰富，社区活跃，是Web开发的优秀选择。''',
            'category': '技术',
            'is_featured': True,
            'tags': 'Flask,Python,Web开发,最佳实践',
            'summary': '分享Flask Web框架的开发最佳实践，包括项目结构、配置管理、蓝图组织等关键技术要点。',
            'reading_time': 8,
            'published': True
        },
        {
            'title': 'Python异步编程深度解析',
            'content': '''# Python异步编程深度解析

异步编程是现代Python开发中的重要技术，能显著提升程序性能。

## async/await语法

```python
import asyncio

async def fetch_data():
    await asyncio.sleep(1)
    return "数据获取完成"

async def main():
    result = await fetch_data()
    print(result)

asyncio.run(main())
```

## 并发处理

使用asyncio.gather()实现并发：

```python
async def concurrent_tasks():
    results = await asyncio.gather(
        fetch_data(),
        fetch_data(),
        fetch_data()
    )
    return results
```

异步编程虽然强大，但需要注意避免常见陷阱。''',
            'category': '技术',
            'is_featured': True,
            'tags': 'Python,异步编程,asyncio,并发',
            'summary': '深入探讨Python异步编程技术，包括async/await语法、并发处理等核心概念。',
            'reading_time': 12,
            'published': True
        },
        {
            'title': '现代前端开发趋势观察',
            'content': '''# 现代前端开发趋势观察

前端技术发展日新月异，让我们来看看当前的发展趋势。

## 主流框架发展

- **React**: Hook生态成熟，并发特性强化
- **Vue**: Composition API推广，生态完善
- **Angular**: 版本迭代稳定，企业级应用首选

## 新兴技术

### 1. 边缘计算
CDN + SSR的结合，提升用户体验。

### 2. Web3集成
区块链技术与前端的结合越来越紧密。

### 3. 低代码平台
可视化开发工具的兴起。

## 开发工具链

构建工具从Webpack演进到Vite，开发体验持续改善。

前端技术的发展速度令人兴奋，但学习成本也在增加。''',
            'category': '观察',
            'is_featured': True,
            'tags': '前端开发,技术趋势,React,Vue,Angular',
            'summary': '观察和分析现代前端开发的最新趋势，包括主流框架发展、新兴技术和开发工具链的演进。',
            'reading_time': 6,
            'published': True
        },
        {
            'title': '程序员的工作与生活平衡',
            'content': '''# 程序员的工作与生活平衡

作为程序员，如何在高强度的工作中保持生活质量？

## 时间管理策略

### 番茄工作法
- 25分钟专注工作
- 5分钟短暂休息
- 每4个番茄后长休息

### 时间块安排
- 深度工作时间：上午9-12点
- 轻松工作时间：下午2-5点
- 学习时间：晚上7-9点

## 健康管理

### 体力管理
- 定期运动：每周3次有氧运动
- 正确坐姿：注意颈椎和腰椎保护
- 眼部保护：20-20-20法则

### 心理健康
- 适当的社交活动
- 培养技术外的兴趣爱好
- 学会说"不"

## 持续学习

在保持工作效率的同时，不忘记持续充电。

平衡不是一蹴而就的，需要不断调整和优化。''',
            'category': '生活',
            'is_featured': False,
            'tags': '工作生活平衡,时间管理,健康管理,程序员',
            'summary': '探讨程序员如何在繁忙的工作中维持良好的生活品质，包括时间管理、健康管理等实用建议。',
            'reading_time': 5,
            'published': True
        }
    ]
    
    print("📝 创建文章内容...")
    for article_data in articles:
        article = Content(
            title=article_data['title'],
            content=article_data['content'],
            category=article_data['category'],
            is_featured=article_data['is_featured'],
            summary=article_data['summary'],
            reading_time=article_data['reading_time'],
            is_published=article_data['published'],
            created_at=datetime.utcnow() - timedelta(days=len(articles) - articles.index(article_data))
        )
        db.session.add(article)
        
        # 处理标签 - 在文章保存后添加
        if 'tags' in article_data:
            tag_names = [tag.strip() for tag in article_data['tags'].split(',')]
            article.update_tags(tag_names)
    
    # 2. 创建项目作品
    projects = [
        {
            'title': '个人门户网站系统',
            'subtitle': '现代化个人展示平台',
            'description': '''这是一个功能完整的个人门户网站系统，基于Flask框架开发。

## 主要特性

- **内容管理**: 支持多种类型内容发布
- **项目展示**: 专业的作品集展示
- **CRM系统**: 客户关系管理功能
- **响应式设计**: 完美适配各种设备
- **SEO优化**: 搜索引擎友好

## 技术栈

- 后端：Flask + SQLAlchemy
- 前端：Bootstrap 5 + JavaScript
- 数据库：SQLite/PostgreSQL
- 部署：Docker + Nginx

这个项目展示了现代Web开发的最佳实践。''',
            'tech_stack': 'Flask,Python,SQLAlchemy,Bootstrap,JavaScript,HTML5,CSS3',
            'status': '已完成',
            'demo_url': 'https://demo.example.com',
            'github_url': 'https://github.com/user/personal-portal',
            'start_date': datetime.utcnow() - timedelta(days=90),
            'completion_date': datetime.utcnow() - timedelta(days=30),
            'is_featured': True
        },
        {
            'title': 'AI驱动的内容推荐系统',
            'subtitle': '智能化内容发现平台',
            'description': '''基于机器学习算法的个性化内容推荐系统。

## 核心功能

- **智能推荐**: 基于用户行为的个性化推荐
- **内容分析**: NLP技术分析内容质量
- **实时更新**: 推荐模型实时学习优化
- **多元数据**: 整合多维度用户数据

## 算法特色

- 协同过滤算法
- 深度学习模型
- 实时特征工程
- A/B测试框架

该系统显著提升了用户参与度和内容消费量。''',
            'tech_stack': 'Python,TensorFlow,Pandas,Redis,FastAPI,PostgreSQL',
            'status': '开发中',
            'demo_url': None,
            'github_url': 'https://github.com/user/ai-recommender',
            'start_date': datetime.utcnow() - timedelta(days=60),
            'completion_date': None,
            'is_featured': True
        },
        {
            'title': '微服务架构电商平台',
            'subtitle': '云原生电商解决方案',
            'description': '''采用微服务架构的现代化电商平台。

## 架构特点

- **微服务拆分**: 按业务领域拆分服务
- **容器化部署**: Docker + Kubernetes
- **API网关**: 统一入口和路由管理
- **服务发现**: Consul服务注册发现
- **监控告警**: Prometheus + Grafana

## 业务模块

- 用户服务
- 商品服务  
- 订单服务
- 支付服务
- 物流服务

这个项目体现了企业级应用的复杂性和扩展性。''',
            'tech_stack': 'Java,Spring Cloud,Docker,Kubernetes,Redis,MySQL,RabbitMQ',
            'status': '规划中',
            'demo_url': None,
            'github_url': None,
            'start_date': datetime.utcnow() + timedelta(days=30),
            'completion_date': None,
            'is_featured': False
        }
    ]
    
    print("💼 创建项目数据...")
    for project_data in projects:
        project = Project(
            name=project_data['title'],
            summary=project_data.get('subtitle', ''),
            description=project_data['description'],
            tech_stack=project_data['tech_stack'].split(',') if isinstance(project_data['tech_stack'], str) else project_data['tech_stack'],
            project_status=project_data['status'],
            demo_url=project_data['demo_url'],
            github_url=project_data['github_url'],
            start_date=project_data['start_date'],
            completion_date=project_data['completion_date'],
            is_featured=project_data['is_featured'],
            created_at=datetime.utcnow() - timedelta(days=len(projects) - projects.index(project_data))
        )
        db.session.add(project)
    
    # 3. 创建示例咨询
    inquiries = [
        {
            'name': '张先生',
            'email': 'zhang@example.com',
            'phone': '138****8888',
            'company': '科技创新公司',
            'position': '技术总监',
            'inquiry_type': '项目合作',
            'subject': '企业级Web应用开发咨询',
            'description': '''您好！我们公司正在寻找经验丰富的全栈开发工程师合作开发一个企业级的项目管理系统。

项目需求：
1. 用户权限管理系统
2. 项目进度跟踪功能
3. 团队协作工具集成
4. 数据可视化报表
5. 移动端适配

技术要求：
- 后端：Python/Java
- 前端：React/Vue
- 数据库：PostgreSQL
- 部署：云服务器

希望能够深入沟通项目细节，期待您的回复。''',
            'budget_range': '3万-10万',
            'timeline': '3个月内',
            'preferred_tech': 'Python,Flask,React,PostgreSQL',
            'contact_preference': '邮件',
            'contact_time': '工作日下午',
            'status': '新咨询',
            'priority': '高'
        },
        {
            'name': 'Lisa Wang',
            'email': 'lisa.wang@startup.com',
            'phone': '159****6666',
            'company': '创业科技',
            'position': '产品经理',
            'inquiry_type': '技术咨询',
            'subject': 'AI算法集成技术咨询',
            'description': '''Hello! 我们团队正在开发一个智能推荐产品，希望咨询以下技术问题：

1. 推荐算法的选择和实现
2. 大数据处理架构设计  
3. 机器学习模型的部署策略
4. 实时计算的性能优化

我们目前的技术栈：
- 数据：Spark + Kafka
- 算法：Python + TensorFlow
- 服务：微服务架构

希望能获得专业的技术指导，谢谢！''',
            'budget_range': '1万-3万',
            'timeline': '1个月内',
            'preferred_tech': 'Python,TensorFlow,Spark,Kafka',
            'contact_preference': '微信',
            'contact_time': '任何时间',
            'status': '处理中',
            'priority': '中'
        }
    ]
    
    print("📨 创建咨询数据...")
    for inquiry_data in inquiries:
        inquiry = ProjectInquiry(
            client_name=inquiry_data['name'],
            client_email=inquiry_data['email'],
            client_phone=inquiry_data['phone'],
            client_company=inquiry_data['company'],
            client_title=inquiry_data['position'],
            project_type=inquiry_data['inquiry_type'],
            title=inquiry_data['subject'],
            description=inquiry_data['description'],
            budget_range=inquiry_data['budget_range'],
            timeline=inquiry_data['timeline'],
            status=inquiry_data['status'],
            priority=inquiry_data['priority'],
            created_at=datetime.utcnow() - timedelta(days=len(inquiries) - inquiries.index(inquiry_data))
        )
        db.session.add(inquiry)
    
    # 4. 创建CRM客户数据
    customers = [
        {
            'name': '北京科技有限公司',
            'email': 'contact@bjtech.com',
            'phone': '010-12345678',
            'company_size': '中型企业',
            'industry': '软件开发',
            'lead_score': 85,
            'status': '潜在客户',
            'source': '官网咨询',
            'notes': '对企业级Web开发服务有强烈需求，预算充足，决策周期约1个月。'
        },
        {
            'name': '上海创新科技',
            'email': 'info@shcx.com', 
            'phone': '021-87654321',
            'company_size': '初创公司',
            'industry': '人工智能',
            'lead_score': 75,
            'status': '跟进中',
            'source': 'GitHub',
            'notes': 'AI技术团队，寻求算法优化和系统架构咨询，技术实力强。'
        }
    ]
    
    print("🏢 创建CRM客户数据...")
    for customer_data in customers:
        customer = Customer(
            name=customer_data['name'],
            email=customer_data['email'],
            phone=customer_data['phone'],
            company_size=customer_data['company_size'],
            industry=customer_data['industry'],
            lead_score=customer_data['lead_score'],
            customer_type=customer_data['status'],
            lead_source=customer_data['source'],
            notes=customer_data['notes'],
            created_at=datetime.utcnow() - timedelta(days=len(customers) - customers.index(customer_data))
        )
        db.session.add(customer)
    
    # 提交所有数据
    try:
        db.session.commit()
        print("✅ 演示数据创建成功！")
        
        # 统计信息
        content_count = Content.query.count()
        project_count = Project.query.count() 
        inquiry_count = ProjectInquiry.query.count()
        customer_count = Customer.query.count()
        
        print(f"""
📊 数据统计:
  📝 技术文章: {content_count} 篇
  💼 项目作品: {project_count} 个
  📨 客户咨询: {inquiry_count} 条
  🏢 CRM客户: {customer_count} 个
        """)
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 数据创建失败: {str(e)}")
        return False
        
    return True

if __name__ == '__main__':
    # 设置环境变量
    os.environ.setdefault('SECRET_KEY', 'demo-data-creation-key')
    os.environ.setdefault('DATABASE_URL', 'sqlite:///personal_portal.db')
    
    # 创建应用和数据库
    app = create_app()
    with app.app_context():
        # 创建数据表
        db.create_all()
        print("🗄️ 数据库表创建完成")
        
        # 创建演示数据
        success = create_demo_data()
        
        if success:
            print("🎉 演示数据初始化完成！现在可以访问网站查看内容。")
        else:
            print("💥 演示数据初始化失败！")
            sys.exit(1)