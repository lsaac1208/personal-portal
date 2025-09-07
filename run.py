"""
🚀 Flask应用启动文件
🔷 backend-architect 设计的生产级启动配置
"""
import os
from app import create_app, db
from app.models import Content, Project, Tag, ProjectInquiry

# 🌍 确定运行环境
config_name = os.environ.get('FLASK_CONFIG', 'development')
app = create_app(config_name)


@app.cli.command()
def init_db():
    """🔧 初始化数据库命令"""
    print("正在创建数据库表...")
    db.create_all()
    print("数据库表创建完成！")


@app.cli.command() 
def create_admin():
    """👤 创建管理员用户命令"""
    from app.models import User
    from werkzeug.security import generate_password_hash
    
    username = input("管理员用户名: ")
    email = input("管理员邮箱: ")
    password = input("管理员密码: ")
    
    admin = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        is_admin=True
    )
    
    db.session.add(admin)
    db.session.commit()
    print(f"管理员用户 {username} 创建成功！")


@app.cli.command()
def seed_data():
    """🌱 填充示例数据"""
    from datetime import datetime
    
    print("正在创建示例数据...")
    
    # 创建标签
    tech_tags = ['Python', 'Flask', 'JavaScript', 'React', 'HTML', 'CSS', 'SQL']
    creative_tags = ['3D打印', '建模', '平面设计', '钩织', '手工艺']
    life_tags = ['钓鱼', '生活感悟', '旅行', '摄影', '思考']
    
    for tag_name in tech_tags:
        tag = Tag(name=tag_name, category='技术', color='#007bff')
        db.session.add(tag)
    
    for tag_name in creative_tags:
        tag = Tag(name=tag_name, category='创意', color='#28a745')
        db.session.add(tag)
    
    for tag_name in life_tags:
        tag = Tag(name=tag_name, category='生活', color='#ffc107')
        db.session.add(tag)
    
    # 创建示例内容
    sample_contents = [
        {
            'title': 'Flask Web开发实战指南',
            'category': '技术',
            'content': '''# Flask开发最佳实践

这篇文章分享我在Flask开发中总结的经验和最佳实践...

## 项目结构设计
使用应用工厂模式可以更好地组织代码...

## 数据库设计
SQLAlchemy ORM的使用技巧...''',
            'tags': ['Python', 'Flask'],
            'is_published': True,
            'is_featured': True
        },
        {
            'title': '我的3D打印创作之路',
            'category': '创作',
            'content': '''# 从零开始学3D打印

分享我的3D打印学习经历和创作作品...

## 建模软件选择
推荐几款适合初学者的3D建模软件...''',
            'tags': ['3D打印', '建模'],
            'is_published': True,
            'is_featured': True
        },
        {
            'title': '周末湖边钓鱼的思考',
            'category': '生活', 
            'content': '''# 钓鱼与人生感悟

在宁静的湖边，我找到了内心的平静...

钓鱼教会我耐心和专注...''',
            'tags': ['钓鱼', '生活感悟'],
            'is_published': True
        }
    ]
    
    for content_data in sample_contents:
        content = Content(
            title=content_data['title'],
            category=content_data['category'],
            content=content_data['content'],
            is_published=content_data['is_published'],
            is_featured=content_data.get('is_featured', False),
            created_at=datetime.utcnow()
        )
        
        # 添加标签
        for tag_name in content_data['tags']:
            tag = Tag.query.filter_by(name=tag_name).first()
            if tag:
                content.tags.append(tag)
        
        # 渲染HTML
        content.render_html()
        db.session.add(content)
    
    # 创建示例项目
    sample_project = Project(
        name='个人博客系统',
        description='基于Flask开发的个人博客平台，支持Markdown编辑、标签分类、响应式设计',
        tech_stack='["Python", "Flask", "SQLAlchemy", "Bootstrap", "JavaScript"]',
        demo_url='#',
        github_url='#',
        is_published=True,
        is_featured=True,
        completion_date=datetime.utcnow().date()
    )
    db.session.add(sample_project)
    
    db.session.commit()
    print("示例数据创建完成！")


@app.cli.command()
def test():
    """🧪 运行测试"""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    # 🔧 开发环境配置
    app.run(debug=True, host='0.0.0.0', port=5000)