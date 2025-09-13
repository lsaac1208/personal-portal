#!/usr/bin/env python3
"""
🔍 Phase 3 快速完整性检查
无需外部依赖的基础验证
"""
import os
import sys

def check_file_exists(file_path, description):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        print(f"✅ {description}: 文件存在")
        return True
    else:
        print(f"❌ {description}: 文件不存在 ({file_path})")
        return False

def check_directory_exists(dir_path, description):
    """检查目录是否存在"""
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        print(f"✅ {description}: 目录存在")
        return True
    else:
        print(f"❌ {description}: 目录不存在 ({dir_path})")
        return False

def check_phase3_structure():
    """检查 Phase 3 项目结构完整性"""
    print("🔍 检查 Phase 3 项目结构...")
    
    structure_checks = [
        # 核心配置文件
        ("config.py", "配置管理"),
        ("run.py", "应用启动文件"),
        ("requirements.txt", "依赖配置"),
        
        # 应用目录结构
        ("app", "主应用目录"),
        ("app/__init__.py", "应用初始化"),
        ("app/models", "数据模型目录"),
        ("app/routes", "路由目录"),
        ("app/utils", "工具模块目录"),
        ("app/forms", "表单目录"),
        ("app/templates", "模板目录"),
        ("app/static", "静态文件目录"),
        
        # 核心模型文件
        ("app/models/__init__.py", "模型包初始化"),
        ("app/models/content.py", "内容模型"),
        ("app/models/tag.py", "标签模型"),
        ("app/models/project.py", "项目模型"),
        ("app/models/user.py", "用户模型"),
        ("app/models/inquiry.py", "咨询模型"),
        
        # 核心路由文件
        ("app/routes/__init__.py", "路由包初始化"),
        ("app/routes/main.py", "主路由"),
        ("app/routes/admin.py", "管理路由"),
        ("app/routes/content.py", "内容路由"),
        ("app/routes/api.py", "API路由"),
        
        # 核心工具模块
        ("app/utils/__init__.py", "工具包初始化"),
        ("app/utils/search_engine.py", "搜索引擎"),
        ("app/utils/seo_analyzer.py", "SEO分析器"),
        ("app/utils/slug_generator.py", "URL生成器"),
        ("app/utils/content_utils.py", "内容工具"),
        ("app/utils/file_handler.py", "文件处理"),
        ("app/utils/media_manager.py", "媒体管理器"),
        ("app/utils/email_utils.py", "邮件工具"),
        
        # 表单模块
        ("app/forms/__init__.py", "表单包初始化"),
        ("app/forms/content.py", "内容表单"),
        ("app/forms/project.py", "项目表单"),
        ("app/forms/inquiry.py", "咨询表单")
    ]
    
    success_count = 0
    total_count = len(structure_checks)
    
    for path, description in structure_checks:
        if os.path.isdir(path):
            if check_directory_exists(path, description):
                success_count += 1
        else:
            if check_file_exists(path, description):
                success_count += 1
    
    print(f"\n📊 项目结构检查结果: {success_count}/{total_count} 通过")
    print(f"🎯 完整性: {success_count/total_count*100:.1f}%")
    
    return success_count, total_count

def check_phase3_features():
    """检查 Phase 3 功能特性"""
    print("\n🔍 检查 Phase 3 功能特性...")
    
    feature_checks = []
    
    # 检查搜索引擎功能
    try:
        with open("app/utils/search_engine.py", 'r', encoding='utf-8') as f:
            content = f.read()
            if "full_text_search" in content:
                feature_checks.append(("全文搜索功能", True))
            if "semantic_search" in content:
                feature_checks.append(("语义搜索功能", True))
            if "get_related_content" in content:
                feature_checks.append(("相关内容推荐", True))
            if "get_trending_content" in content:
                feature_checks.append(("热门内容功能", True))
    except:
        feature_checks.append(("搜索引擎模块", False))
    
    # 检查SEO分析器功能
    try:
        with open("app/utils/seo_analyzer.py", 'r', encoding='utf-8') as f:
            content = f.read()
            if "analyze_content" in content:
                feature_checks.append(("SEO内容分析", True))
            if "_analyze_title" in content:
                feature_checks.append(("标题分析功能", True))
            if "_analyze_meta_description" in content:
                feature_checks.append(("元描述分析", True))
            if "generate_html_report" in content:
                feature_checks.append(("SEO报告生成", True))
    except:
        feature_checks.append(("SEO分析器模块", False))
    
    # 检查管理路由的SEO功能
    try:
        with open("app/routes/admin.py", 'r', encoding='utf-8') as f:
            content = f.read()
            if "content_seo_analysis" in content:
                feature_checks.append(("SEO分析路由", True))
            if "auto_optimize_seo" in content:
                feature_checks.append(("SEO自动优化", True))
            if "generate_sitemap" in content:
                feature_checks.append(("站点地图生成", True))
            if "bulk_seo_optimize" in content:
                feature_checks.append(("批量SEO优化", True))
    except:
        feature_checks.append(("管理路由SEO功能", False))
    
    # 检查主路由的搜索API
    try:
        with open("app/routes/main.py", 'r', encoding='utf-8') as f:
            content = f.read()
            if "/api/search/suggestions" in content:
                feature_checks.append(("搜索建议API", True))
            if "/api/search/related" in content:
                feature_checks.append(("相关内容API", True))
            if "/api/search/semantic" in content:
                feature_checks.append(("语义搜索API", True))
            if "/api/search/trending" in content:
                feature_checks.append(("热门内容API", True))
            if "/api/search/advanced" in content:
                feature_checks.append(("高级搜索API", True))
    except:
        feature_checks.append(("主路由搜索API", False))
    
    # 统计结果
    success_count = sum(1 for _, success in feature_checks if success)
    total_count = len(feature_checks)
    
    for feature, success in feature_checks:
        status = "✅" if success else "❌"
        print(f"  {status} {feature}")
    
    print(f"\n📊 功能特性检查结果: {success_count}/{total_count} 通过")
    print(f"🎯 功能完整性: {success_count/total_count*100:.1f}%")
    
    return success_count, total_count

def generate_phase3_report():
    """生成 Phase 3 完整性报告"""
    print("=" * 60)
    print("🎯 Phase 3 内容发布系统完整性报告")
    print("=" * 60)
    
    # 检查项目结构
    structure_success, structure_total = check_phase3_structure()
    
    # 检查功能特性
    feature_success, feature_total = check_phase3_features()
    
    # 计算总体评分
    total_success = structure_success + feature_success
    total_count = structure_total + feature_total
    overall_score = total_success / total_count * 100
    
    print(f"\n📋 Phase 3 完整性摘要:")
    print(f"  📁 项目结构: {structure_success}/{structure_total} ({structure_success/structure_total*100:.1f}%)")
    print(f"  ⚙️  功能特性: {feature_success}/{feature_total} ({feature_success/feature_total*100:.1f}%)")
    print(f"  🎯 总体完整性: {total_success}/{total_count} ({overall_score:.1f}%)")
    
    # 评估结果
    if overall_score >= 95:
        print(f"\n🏆 优秀！Phase 3 开发质量极高")
        status = "EXCELLENT"
    elif overall_score >= 85:
        print(f"\n✨ 良好！Phase 3 开发基本完成")
        status = "GOOD"
    elif overall_score >= 70:
        print(f"\n⚠️  及格，但还有改进空间")
        status = "ACCEPTABLE"
    else:
        print(f"\n❌ 需要进一步开发和完善")
        status = "NEEDS_WORK"
    
    print(f"\n🚀 Phase 3 状态: {status}")
    
    if overall_score >= 85:
        print("✅ 系统已准备好进入下一个开发阶段 (Phase 4)")
        return True
    else:
        print("⚠️  建议完善当前阶段后再继续")
        return False

if __name__ == '__main__':
    try:
        ready_for_next = generate_phase3_report()
        sys.exit(0 if ready_for_next else 1)
    except Exception as e:
        print(f"\n🚨 检查过程发生异常: {e}")
        sys.exit(1)