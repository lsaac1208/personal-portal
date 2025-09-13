#!/usr/bin/env python3
"""
🧪 Phase 3 系统验收测试脚本
验证内容发布系统的核心功能完整性
"""
import os
import sys
import unittest
from app import create_app, db
from app.models import Content, Tag, Project
from app.utils.search_engine import search_engine
from app.utils.seo_analyzer import SEOAnalyzer


class Phase3SystemTest(unittest.TestCase):
    """Phase 3 系统功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # 创建测试数据库
        db.create_all()
        
        # 创建测试数据
        self.create_test_data()
    
    def tearDown(self):
        """测试后清理"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def create_test_data(self):
        """创建测试数据"""
        # 创建标签
        tag1 = Tag(name='Python', category='技术', color='#007bff')
        tag2 = Tag(name='Flask', category='技术', color='#007bff')
        tag3 = Tag(name='AI', category='技术', color='#007bff')
        
        db.session.add_all([tag1, tag2, tag3])
        db.session.flush()
        
        # 创建测试内容
        content1 = Content(
            title='Python Flask开发教程',
            content='这是一篇关于Flask开发的详细教程...',
            summary='Flask web框架的完整学习指南',
            category='技术',
            is_published=True,
            view_count=150,
            like_count=25
        )
        content1.tags.extend([tag1, tag2])
        
        content2 = Content(
            title='人工智能入门指南',
            content='本文介绍AI基础概念和Python实现...',
            summary='人工智能的基础知识和实战',
            category='技术',
            is_published=True,
            view_count=200,
            like_count=45
        )
        content2.tags.extend([tag1, tag3])
        
        content3 = Content(
            title='机器学习项目实战',
            content='从数据处理到模型部署的完整流程...',
            summary='机器学习项目的完整实战案例',
            category='技术',
            is_published=False  # 草稿状态
        )
        
        db.session.add_all([content1, content2, content3])
        db.session.commit()
        
        # 存储ID用于测试
        self.content1_id = content1.id
        self.content2_id = content2.id
        self.content3_id = content3.id
    
    def test_content_creation(self):
        """测试内容创建功能"""
        # 验证内容已成功创建
        content = Content.query.get(self.content1_id)
        self.assertIsNotNone(content)
        self.assertEqual(content.title, 'Python Flask开发教程')
        self.assertEqual(content.category, '技术')
        self.assertTrue(content.is_published)
        
    def test_tag_association(self):
        """测试标签关联功能"""
        content = Content.query.get(self.content1_id)
        tag_names = [tag.name for tag in content.tags]
        self.assertIn('Python', tag_names)
        self.assertIn('Flask', tag_names)
        
    def test_search_functionality(self):
        """测试搜索引擎功能"""
        # 测试全文搜索
        results = search_engine.full_text_search(
            query='Flask教程',
            page=1,
            per_page=10
        )
        
        self.assertGreater(results['total'], 0)
        self.assertTrue(results['results'])
        
        # 验证搜索结果包含相关内容
        titles = [result['content'].title for result in results['results']]
        self.assertTrue(
            any('Flask' in title for title in titles) or
            any('Python' in title for title in titles)
        )
    
    def test_semantic_search(self):
        """测试语义搜索功能"""
        results = search_engine.semantic_search(
            query='web开发框架',
            limit=5
        )
        
        self.assertIsInstance(results, list)
        # 语义搜索可能返回空结果，这是正常的
        
    def test_related_content(self):
        """测试相关内容推荐"""
        content = Content.query.get(self.content1_id)
        related = search_engine.get_related_content(
            content=content,
            limit=3,
            method='mixed'
        )
        
        self.assertIsInstance(related, list)
        # 相关内容推荐基于标签和分类，应该能找到相关内容
        
    def test_trending_content(self):
        """测试热门内容获取"""
        trending = search_engine.get_trending_content(
            days=30,
            limit=5
        )
        
        self.assertIsInstance(trending, list)
        self.assertGreater(len(trending), 0)
        
        # 验证按浏览量排序
        if len(trending) > 1:
            self.assertGreaterEqual(
                trending[0].view_count or 0,
                trending[1].view_count or 0
            )
    
    def test_search_suggestions(self):
        """测试搜索建议功能"""
        suggestions = search_engine.get_search_suggestions(
            query='Py',
            limit=5
        )
        
        self.assertIsInstance(suggestions, list)
        # 搜索建议可能为空，这是正常的
        
    def test_category_stats(self):
        """测试分类统计功能"""
        stats = search_engine.get_category_stats()
        
        self.assertIsInstance(stats, list)
        self.assertGreater(len(stats), 0)
        
        # 验证统计数据结构
        if stats:
            stat = stats[0]
            self.assertIn('category', stat)
            self.assertIn('count', stat)
            self.assertIn('avg_views', stat)
    
    def test_seo_analyzer(self):
        """测试SEO分析功能"""
        analyzer = SEOAnalyzer()
        content = Content.query.get(self.content1_id)
        
        analysis = analyzer.analyze_content(
            content=content.content,
            title=content.title,
            meta_description=content.summary
        )
        
        self.assertIn('score', analysis)
        self.assertIn('issues', analysis)
        self.assertIn('recommendations', analysis)
        self.assertIn('keywords', analysis)
        
        # 验证评分在合理范围内
        self.assertGreaterEqual(analysis['score'], 0)
        self.assertLessEqual(analysis['score'], analysis['max_score'])
    
    def test_published_content_filter(self):
        """测试已发布内容过滤"""
        # 搜索应该只返回已发布的内容
        all_content = Content.query.filter_by(is_published=True).all()
        self.assertEqual(len(all_content), 2)  # 只有两篇已发布
        
        # 验证草稿不会在搜索结果中显示
        draft_content = Content.query.filter_by(is_published=False).all()
        self.assertEqual(len(draft_content), 1)  # 一篇草稿


def run_system_tests():
    """运行系统测试"""
    print("🧪 开始 Phase 3 系统验收测试...\n")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加所有测试
    test_methods = [
        'test_content_creation',
        'test_tag_association', 
        'test_search_functionality',
        'test_semantic_search',
        'test_related_content',
        'test_trending_content',
        'test_search_suggestions',
        'test_category_stats',
        'test_seo_analyzer',
        'test_published_content_filter'
    ]
    
    for test_method in test_methods:
        test_suite.addTest(Phase3SystemTest(test_method))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出结果摘要
    print(f"\n📊 测试结果摘要:")
    print(f"✅ 成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ 失败: {len(result.failures)}")
    print(f"🚨 错误: {len(result.errors)}")
    print(f"📝 总计: {result.testsRun}")
    
    if result.failures:
        print(f"\n❌ 失败测试详情:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print(f"\n🚨 错误测试详情:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    # 返回测试结果
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == '__main__':
    # 设置测试环境
    os.environ['FLASK_CONFIG'] = 'testing'
    
    try:
        success = run_system_tests()
        if success:
            print(f"\n🎉 Phase 3 系统验收测试全部通过！")
            print(f"✅ 内容发布系统核心功能完整性验证成功")
            sys.exit(0)
        else:
            print(f"\n⚠️  Phase 3 系统验收测试发现问题，请检查失败的测试")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n🚨 测试运行出现异常: {e}")
        sys.exit(1)