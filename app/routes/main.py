"""
🏠 主要页面路由蓝图
🔶 frontend-developer 设计的用户访问路径
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from app.models import Content, Project, Tag
from app.utils.content_utils import get_featured_content, get_recent_content

bp = Blueprint('main', __name__)


@bp.route('/')
@bp.route('/index')
def index():
    """
    🌟 首页 - 多元内容中心型设计
    展示精选推荐、最新动态、热门标签
    """
    # 获取精选内容 (PRD原型B设计)
    featured_content = get_featured_content(limit=3)
    
    # 获取最新动态 (所有类型混合)
    recent_content = get_recent_content(limit=5)
    
    # 获取热门标签
    popular_tags = Tag.get_popular_tags(limit=12)
    
    # 获取统计数据
    stats = {
        'tech_count': Content.query.filter_by(category='技术').count(),
        'project_count': Project.query.count(),
        'creative_count': Content.query.filter_by(category='创作').count(),
        'total_content': Content.query.filter_by(is_published=True).count()
    }
    
    return render_template('index.html',
                         featured_content=featured_content,
                         recent_content=recent_content,
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
    """🔍 搜索功能"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    if query:
        # 简单的全文搜索 (MVP版本)
        search_results = Content.search_content(query)
        
        # 分页处理
        per_page = current_app.config.get('POSTS_PER_PAGE', 10)
        total = len(search_results)
        start = (page - 1) * per_page
        end = start + per_page
        items = search_results[start:end]
        
        # 手动构建分页信息
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'has_prev': page > 1,
            'has_next': page * per_page < total,
            'prev_num': page - 1 if page > 1 else None,
            'next_num': page + 1 if page * per_page < total else None
        }
    else:
        items = []
        pagination = None
    
    return render_template('search.html',
                         query=query,
                         results=items,
                         pagination=pagination)


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