#!/usr/bin/env python3
"""
✅ Phase 3 功能完整性验证脚本
快速验证所有核心模块和功能的可用性
"""
import sys
import os

def check_import(module_name, description):
    """检查模块导入"""
    try:
        if module_name == 'jieba':
            import jieba
            print(f"✅ {description}: jieba {jieba.__version__}")
        elif module_name == 'pypinyin':
            import pypinyin
            print(f"✅ {description}: pypinyin 已安装")
        elif module_name == 'flask':
            import flask
            print(f"✅ {description}: Flask {flask.__version__}")
        elif module_name == 'flask_sqlalchemy':
            import flask_sqlalchemy
            print(f"✅ {description}: Flask-SQLAlchemy {flask_sqlalchemy.__version__}")
        elif module_name == 'pillow':
            from PIL import Image
            print(f"✅ {description}: Pillow 已安装")
        elif module_name == 'markdown':
            import markdown
            print(f"✅ {description}: Markdown {markdown.__version__}")
        else:
            __import__(module_name)
            print(f"✅ {description}: 模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ {description}: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {description}: {e}")
        return False


def verify_core_dependencies():
    """验证核心依赖包"""
    print("🔍 检查核心依赖包...")
    
    dependencies = [
        ('flask', 'Flask Web框架'),
        ('flask_sqlalchemy', 'SQLAlchemy数据库ORM'),
        ('jieba', '中文分词库'),
        ('pypinyin', '中文转拼音库'),
        ('pillow', 'Python图像处理库'),
        ('markdown', 'Markdown处理库'),
    ]
    
    success_count = 0
    for module, desc in dependencies:
        if check_import(module, desc):
            success_count += 1
    
    print(f"\n📊 依赖包检查结果: {success_count}/{len(dependencies)} 成功\n")
    return success_count == len(dependencies)


def verify_app_modules():
    """验证应用核心模块"""
    print("🔍 检查应用核心模块...")
    
    # 添加项目路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    modules = [
        ('app', '主应用模块'),
        ('app.models', '数据模型'),
        ('app.models.content', '内容模型'),
        ('app.models.tag', '标签模型'),
        ('app.models.project', '项目模型'),
        ('app.routes', '路由蓝图'),
        ('app.routes.main', '主路由'),
        ('app.routes.admin', '管理路由'),
        ('app.utils.search_engine', '搜索引擎'),
        ('app.utils.seo_analyzer', 'SEO分析器'),
        ('app.utils.slug_generator', 'URL生成器'),
        ('config', '配置管理')
    ]
    
    success_count = 0
    for module, desc in modules:
        if check_import(module, desc):
            success_count += 1
    
    print(f"\n📊 应用模块检查结果: {success_count}/{len(modules)} 成功\n")
    return success_count == len(modules)


def verify_functionality():
    """验证核心功能"""
    print("🔍 检查核心功能...")
    
    try:
        # 导入搜索引擎
        from app.utils.search_engine import SearchEngine, search_engine
        print("✅ 搜索引擎: 导入成功")
        
        # 测试关键词提取
        test_keywords = search_engine._extract_keywords("Python Flask 开发教程")
        if test_keywords:
            print(f"✅ 中文分词: 提取关键词 {test_keywords[:3]}...")
        else:
            print("⚠️  中文分词: 未提取到关键词")
        
        # 导入SEO分析器
        from app.utils.seo_analyzer import SEOAnalyzer
        seo = SEOAnalyzer()
        print("✅ SEO分析器: 导入成功")
        
        # 导入slug生成器
        from app.utils.slug_generator import generate_slug
        test_slug = generate_slug("Python Flask 开发教程")
        print(f"✅ URL生成器: 生成slug '{test_slug}'")
        
        return True
        
    except Exception as e:
        print(f"❌ 功能验证失败: {e}")
        return False


def verify_database_models():
    """验证数据库模型"""
    print("🔍 检查数据库模型...")
    
    try:
        from app.models.content import Content
        from app.models.tag import Tag  
        from app.models.project import Project
        from app.models.inquiry import ProjectInquiry
        from app.models.user import User
        
        print("✅ 内容模型: Content 导入成功")
        print("✅ 标签模型: Tag 导入成功")
        print("✅ 项目模型: Project 导入成功")
        print("✅ 咨询模型: ProjectInquiry 导入成功")
        print("✅ 用户模型: User 导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库模型验证失败: {e}")
        return False


def generate_verification_report():
    """生成验证报告"""
    print("=" * 60)
    print("🎯 Phase 3 内容发布系统验证报告")
    print("=" * 60)
    
    results = {
        '核心依赖包': verify_core_dependencies(),
        '应用模块': verify_app_modules(), 
        '数据库模型': verify_database_models(),
        '核心功能': verify_functionality()
    }
    
    print("📋 验证结果摘要:")
    success_count = 0
    for category, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {category}: {status}")
        if success:
            success_count += 1
    
    print(f"\n🎉 总体通过率: {success_count}/{len(results)} ({success_count/len(results)*100:.0f}%)")
    
    if success_count == len(results):
        print("\n✨ Phase 3 内容发布系统验证完全通过！")
        print("🚀 系统已准备好进入下一个开发阶段")
        return True
    else:
        print(f"\n⚠️  发现 {len(results)-success_count} 个问题需要解决")
        return False


if __name__ == '__main__':
    try:
        success = generate_verification_report()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n🚨 验证过程发生异常: {e}")
        sys.exit(1)