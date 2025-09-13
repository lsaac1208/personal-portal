"""
🏠 主要页面路由蓝图
🔶 frontend-developer 设计的用户访问路径
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from sqlalchemy import or_
from app.models import Content, Project, Tag
from app.utils.content_utils import get_featured_content, get_recent_content
from app.utils.search_engine import search_engine

bp = Blueprint('main', __name__)


@bp.route('/')
@bp.route('/index')
def index():
    """
    🌟 首页 - 多元内容中心型设计
    展示精选推荐、最新动态、项目作品
    """
    # 获取精选内容 (PRD原型B设计)
    featured_content = get_featured_content(limit=3)
    
    # 获取最新动态 (所有类型混合)
    recent_content = get_recent_content(limit=5)
    
    # 获取最新项目作品
    recent_projects = Project.get_recent_projects(limit=3)
    
    # 获取热门标签
    popular_tags = Tag.get_popular_tags(limit=12)
    
    # 获取统计数据
    stats = {
        'total_content': Content.query.filter_by(is_published=True).count(),
        'total_projects': Project.query.filter_by(is_published=True).count(),
        'total_code_snippets': Content.query.filter_by(category='代码', is_published=True).count(),
        'total_inquiries': 0  # 这个需要从ProjectInquiry模型获取
    }
    
    return render_template('index.html',
                         featured_content=featured_content,
                         recent_content=recent_content,
                         recent_projects=recent_projects,
                         popular_tags=popular_tags,
                         stats=stats)


@bp.route('/about')
def about():
    """👤 关于我页面 - 个人品牌展示"""
    return render_template('about.html')


@bp.route('/contact')
def contact():
    """📞 联系页面"""
    return render_template('contact.html')


@bp.route('/inquiry')
def inquiry_form():
    """📞 在线咨询表单页面"""
    from app.forms.inquiry import ProjectInquiryForm
    form = ProjectInquiryForm()
    return render_template('api/inquiry_form.html', form=form)


@bp.route('/category/<category>')
def category(category):
    """
    📂 分类页面路由
    支持：技术💻、观察📰、生活🌊、创作🎨、项目💼
    """
    page = request.args.get('page', 1, type=int)
    tag = request.args.get('tag', None)
    
    # 构建查询
    query = Content.query.filter_by(category=category, is_published=True)
    
    if tag:
        query = query.filter(Content.tags.any(Tag.name == tag))
    
    # 分页
    per_page = current_app.config.get('POSTS_PER_PAGE', 10)
    content_pagination = query.order_by(Content.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取该分类的标签
    category_tags = Tag.get_tags_by_category(category)
    
    return render_template('category.html',
                         category=category,
                         content_items=content_pagination.items,
                         pagination=content_pagination,
                         category_tags=category_tags,
                         current_tag=tag)


@bp.route('/search')
def search():
    """🔍 智能搜索功能"""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    tag = request.args.get('tag', '')
    sort_by = request.args.get('sort', 'relevance')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 10)
    
    # 搜索结果初始化
    search_results = {
        'results': [],
        'total': 0,
        'page': page,
        'per_page': per_page,
        'total_pages': 0,
        'query': query,
        'keywords': [],
        'category': category,
        'sort_by': sort_by
    }
    
    suggestions = []
    related_tags = []
    trending_content = []
    
    if query:
        # 使用智能搜索引擎
        search_results = search_engine.full_text_search(
            query=query,
            category=category if category else None,
            page=page,
            per_page=per_page,
            sort_by=sort_by
        )
        
        # 获取搜索建议（如果结果较少）
        if search_results['total'] < 5:
            suggestions = search_engine.get_search_suggestions(query, limit=5)
    
    elif tag:
        # 标签搜索
        tag_results = search_engine.search_by_tags([tag], limit=per_page * 5)
        
        # 手动分页
        total = len(tag_results)
        start = (page - 1) * per_page
        end = start + per_page
        items = tag_results[start:end]
        
        search_results.update({
            'results': [{'content': item, 'score': 0, 'highlight': {'title': item.title}} for item in items],
            'total': total,
            'total_pages': (total + per_page - 1) // per_page,
            'query': f'标签: {tag}'
        })
    
    # 获取相关标签（基于当前搜索）
    if query or category:
        all_tags = Tag.get_popular_tags(limit=20)
        related_tags = all_tags[:10]  # 暂时显示热门标签
    
    # 获取热门内容（当没有搜索或结果较少时显示）
    if not query or search_results['total'] < 3:
        trending_content = search_engine.get_trending_content(days=7, limit=5)
    
    # 获取分类统计
    category_stats = search_engine.get_category_stats()
    
    return render_template('search.html',
                         search_results=search_results,
                         suggestions=suggestions,
                         related_tags=related_tags,
                         trending_content=trending_content,
                         category_stats=category_stats,
                         current_category=category,
                         current_sort=sort_by)


@bp.route('/tag/<tag_name>')
def tag_view(tag_name):
    """🏷️ 标签页面 - 显示特定标签的所有内容"""
    page = request.args.get('page', 1, type=int)
    
    tag = Tag.query.filter_by(name=tag_name).first_or_404()
    
    # 获取该标签下的所有内容
    per_page = current_app.config.get('POSTS_PER_PAGE', 10)
    content_pagination = Content.query.join(Content.tags).filter(
        Tag.name == tag_name,
        Content.is_published == True
    ).order_by(Content.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('tag.html',
                         tag=tag,
                         content_items=content_pagination.items,
                         pagination=content_pagination)


# 🔧 API端点 (用于AJAX请求)
@bp.route('/api/tags/autocomplete')
def tags_autocomplete():
    """标签自动完成API"""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    tags = Tag.query.filter(Tag.name.contains(query)).limit(10).all()
    return jsonify([tag.name for tag in tags])


@bp.route('/api/content/stats')
def content_stats():
    """内容统计API"""
    stats = {
        'total_content': Content.query.filter_by(is_published=True).count(),
        'tech_posts': Content.query.filter_by(category='技术', is_published=True).count(),
        'projects': Project.query.count(),
        'creative_works': Content.query.filter_by(category='创作', is_published=True).count(),
        'life_posts': Content.query.filter_by(category='生活', is_published=True).count()
    }
    return jsonify(stats)


# 🔍 搜索相关API端点
@bp.route('/api/search/suggestions')
def search_suggestions():
    """搜索建议API - 用于搜索框自动完成"""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    if len(query) < 2:
        return jsonify({'suggestions': []})
    
    # 使用搜索引擎获取建议
    suggestions = search_engine.get_search_suggestions(query, limit=limit)
    
    return jsonify({
        'success': True,
        'suggestions': suggestions,
        'query': query
    })


@bp.route('/api/search/related/<int:content_id>')
def search_related_content(content_id):
    """获取相关内容API"""
    method = request.args.get('method', 'mixed')
    limit = request.args.get('limit', 5, type=int)
    
    content = Content.query.get_or_404(content_id)
    related_content = search_engine.get_related_content(content, limit=limit, method=method)
    
    # 构建返回数据
    related_data = []
    for item in related_content:
        related_data.append({
            'id': item.id,
            'title': item.title,
            'summary': item.summary,
            'category': item.category,
            'url': f'/content/{item.id}',
            'created_at': item.created_at.strftime('%Y-%m-%d'),
            'tags': [tag.name for tag in item.tags] if item.tags else []
        })
    
    return jsonify({
        'success': True,
        'related_content': related_data,
        'method': method,
        'count': len(related_data)
    })


@bp.route('/api/search/semantic')
def semantic_search():
    """语义搜索API"""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    if not query:
        return jsonify({'success': False, 'error': '搜索查询不能为空'})
    
    # 使用语义搜索
    results = search_engine.semantic_search(query, limit=limit)
    
    # 构建返回数据
    search_data = []
    for result in results:
        content = result['content']
        search_data.append({
            'id': content.id,
            'title': content.title,
            'summary': content.summary,
            'category': content.category,
            'url': f'/content/{content.id}',
            'created_at': content.created_at.strftime('%Y-%m-%d'),
            'semantic_score': result['semantic_score'],
            'tags': [tag.name for tag in content.tags] if content.tags else []
        })
    
    return jsonify({
        'success': True,
        'results': search_data,
        'query': query,
        'count': len(search_data),
        'search_type': 'semantic'
    })


@bp.route('/api/search/trending')
def trending_content():
    """热门内容API"""
    days = request.args.get('days', 7, type=int)
    limit = request.args.get('limit', 10, type=int)
    category = request.args.get('category', None)
    
    # 获取热门内容
    trending = search_engine.get_trending_content(days=days, limit=limit)
    
    # 如果指定分类，过滤结果
    if category:
        trending = [content for content in trending if content.category == category]
    
    # 构建返回数据
    trending_data = []
    for content in trending:
        trending_data.append({
            'id': content.id,
            'title': content.title,
            'summary': content.summary,
            'category': content.category,
            'url': f'/content/{content.id}',
            'created_at': content.created_at.strftime('%Y-%m-%d'),
            'view_count': content.view_count or 0,
            'like_count': content.like_count or 0,
            'tags': [tag.name for tag in content.tags] if content.tags else []
        })
    
    return jsonify({
        'success': True,
        'trending_content': trending_data,
        'days': days,
        'category': category,
        'count': len(trending_data)
    })


@bp.route('/api/categories/stats')
def category_statistics():
    """分类统计API"""
    # 获取分类统计
    category_stats = search_engine.get_category_stats()
    
    return jsonify({
        'success': True,
        'category_stats': category_stats,
        'total_categories': len(category_stats)
    })


@bp.route('/api/search/advanced')
def advanced_search():
    """高级搜索API"""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    tags = request.args.get('tags', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    sort_by = request.args.get('sort', 'relevance')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 构建查询
    search_query = Content.query.filter_by(is_published=True)
    
    # 全文搜索
    if query:
        keywords = search_engine._extract_keywords(query)
        search_conditions = []
        for keyword in keywords:
            keyword_conditions = [
                Content.title.contains(keyword),
                Content.summary.contains(keyword),
                Content.content.contains(keyword)
            ]
            search_conditions.append(or_(*keyword_conditions))
        
        if search_conditions:
            search_query = search_query.filter(or_(*search_conditions))
    
    # 分类过滤
    if category:
        search_query = search_query.filter(Content.category == category)
    
    # 标签过滤
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        for tag_name in tag_list:
            search_query = search_query.filter(Content.tags.any(Tag.name == tag_name))
    
    # 日期范围过滤
    if date_from:
        from datetime import datetime
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        search_query = search_query.filter(Content.created_at >= date_from_obj)
    
    if date_to:
        from datetime import datetime
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        search_query = search_query.filter(Content.created_at <= date_to_obj)
    
    # 排序
    if sort_by == 'date':
        search_query = search_query.order_by(Content.created_at.desc())
    elif sort_by == 'views':
        search_query = search_query.order_by(Content.view_count.desc())
    elif sort_by == 'likes':
        search_query = search_query.order_by(Content.like_count.desc())
    elif sort_by == 'title':
        search_query = search_query.order_by(Content.title.asc())
    else:  # relevance - 默认按创建时间
        search_query = search_query.order_by(Content.created_at.desc())
    
    # 分页
    pagination = search_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 构建返回数据
    results = []
    for content in pagination.items:
        results.append({
            'id': content.id,
            'title': content.title,
            'summary': content.summary,
            'category': content.category,
            'url': f'/content/{content.id}',
            'created_at': content.created_at.strftime('%Y-%m-%d'),
            'view_count': content.view_count or 0,
            'like_count': content.like_count or 0,
            'tags': [tag.name for tag in content.tags] if content.tags else []
        })
    
    return jsonify({
        'success': True,
        'results': results,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next
        },
        'query': query,
        'filters': {
            'category': category,
            'tags': tags,
            'date_from': date_from,
            'date_to': date_to,
            'sort_by': sort_by
        }
    })