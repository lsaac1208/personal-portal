"""
📝 内容相关路由蓝图
处理内容详情、项目展示等功能
"""
from flask import Blueprint, render_template, request, abort
from app.models import Content, Project

bp = Blueprint('content', __name__)


@bp.route('/<int:id>')
@bp.route('/<int:id>/<slug>')
def detail(id, slug=None):
    """
    📄 内容详情页面
    支持所有内容类型：技术、观察、生活、创作
    """
    content = Content.query.get_or_404(id)
    
    # 检查内容是否发布
    if not content.is_published:
        abort(404)
    
    # 增加浏览次数
    content.view_count = (content.view_count or 0) + 1
    try:
        from app import db
        db.session.commit()
    except:
        db.session.rollback()
    
    # 获取相关内容 (同类别或相同标签)
    related_content = Content.get_related_content(content, limit=3)
    
    # 获取上一篇和下一篇
    prev_content = Content.query.filter(
        Content.id < content.id,
        Content.category == content.category,
        Content.is_published == True
    ).order_by(Content.id.desc()).first()
    
    next_content = Content.query.filter(
        Content.id > content.id,
        Content.category == content.category,
        Content.is_published == True
    ).order_by(Content.id.asc()).first()
    
    return render_template('content/detail.html',
                         content=content,
                         related_content=related_content,
                         prev_content=prev_content,
                         next_content=next_content)


@bp.route('/project/<int:id>')
@bp.route('/project/<int:id>/<slug>')
def project_detail(id, slug=None):
    """
    💼 项目详情页面
    展示项目的详细信息、技术栈、效果图等
    """
    project = Project.query.get_or_404(id)
    
    # 增加浏览次数
    project.view_count = (project.view_count or 0) + 1
    try:
        from app import db
        db.session.commit()
    except:
        db.session.rollback()
    
    # 获取相关项目
    related_projects = Project.get_related_projects(project, limit=3)
    
    return render_template('content/project_detail.html',
                         project=project,
                         related_projects=related_projects)


@bp.route('/projects')
@bp.route('/portfolio')
def portfolio():
    """
    💼 项目作品集页面
    展示所有项目的网格视图
    
    🆕 Enhanced with GitHub API integration
    """
    page = request.args.get('page', 1, type=int)
    project_type = request.args.get('project_type', None)
    tech_filter = request.args.get('tech', None)
    sort_order = request.args.get('sort', 'latest')
    with_github = request.args.get('github', 'true').lower() == 'true'  # 是否加载GitHub数据
    
    # 构建查询
    query = Project.query.filter_by(is_published=True)
    
    if project_type:
        # 按项目类型筛选
        query = query.filter(Project.project_type == project_type)
    
    if tech_filter:
        # 按技术栈筛选
        query = query.filter(Project.tech_stack.contains(tech_filter))
    
    # 排序
    if sort_order == 'featured':
        query = query.order_by(Project.is_featured.desc(), Project.completion_date.desc().nullslast())
    elif sort_order == 'status':
        query = query.order_by(Project.project_status, Project.completion_date.desc().nullslast())
    elif sort_order == 'stars':  # 🆕 新增按GitHub stars排序
        query = query.order_by(Project.completion_date.desc().nullslast(), Project.created_at.desc())  # 先按常规排序，GitHub数据在模板中排序
    else:  # latest
        query = query.order_by(Project.completion_date.desc().nullslast(), Project.created_at.desc())
    
    # 分页
    from flask import current_app
    per_page = current_app.config.get('POSTS_PER_PAGE', 12)  # 项目展示用12个一页
    projects_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 🆕 GitHub数据集成
    github_stats = {}
    github_rate_limit = None
    
    if with_github:
        try:
            from app.utils.github_service import get_github_stats, batch_get_github_stats, GitHubService, format_github_stats_for_display
            
            # 获取速率限制信息
            github_service = GitHubService()
            github_rate_limit = github_service.get_rate_limit_info()
            
            # 收集所有项目的GitHub URL
            github_urls = []
            for project in projects_pagination.items:
                if project.github_url:
                    github_urls.append(project.github_url)
            
            # 批量获取GitHub数据 (避免在模板中发起API请求)
            if github_urls:
                raw_github_data = batch_get_github_stats(github_urls)
                
                # 格式化数据供前端使用
                for url, raw_stats in raw_github_data.items():
                    github_stats[url] = format_github_stats_for_display(raw_stats)
            
        except Exception as e:
            # GitHub API调用失败时优雅降级
            import logging
            logging.getLogger(__name__).warning(f"GitHub API integration failed: {e}")
            github_stats = {}
            github_rate_limit = None
    
    # 获取统计数据
    project_stats = {
        'total_projects': Project.query.filter_by(is_published=True).count(),
        'completed_projects': Project.query.filter_by(is_published=True, project_status='已完成').count(),
        'in_progress_projects': Project.query.filter_by(is_published=True, project_status='进行中').count(),
        'featured_projects': Project.query.filter_by(is_published=True, is_featured=True).count()
    }
    
    # 🆕 增强统计数据包含GitHub指标
    if github_stats:
        total_stars = sum(stats.get('stars', 0) for stats in github_stats.values() if stats.get('available'))
        total_forks = sum(stats.get('forks', 0) for stats in github_stats.values() if stats.get('available'))
        github_projects_count = len([stats for stats in github_stats.values() if stats.get('available')])
        
        project_stats.update({
            'github_projects': github_projects_count,
            'total_stars': total_stars,
            'total_forks': total_forks,
            'github_enabled': True
        })
    else:
        project_stats['github_enabled'] = False
    
    # 获取技术栈统计
    tech_stats = Project.get_tech_stack_stats()[:15]  # 只显示前15个
    
    # 获取精选项目
    featured_projects = Project.get_featured_projects(limit=4)
    
    return render_template('content/portfolio.html',
                         projects=projects_pagination,
                         project_type=project_type,
                         tech_filter=tech_filter,
                         sort_order=sort_order,
                         stats=project_stats,
                         tech_stats=tech_stats,
                         featured_projects=featured_projects,
                         github_stats=github_stats,  # 🆕 GitHub统计数据
                         github_rate_limit=github_rate_limit,  # 🆕 API速率限制信息
                         with_github=with_github)  # 🆕 是否启用GitHub集成


@bp.route('/code-snippets')
def code_snippets():
    """
    💻 代码片段页面
    展示所有代码片段，支持按语言筛选
    """
    page = request.args.get('page', 1, type=int)
    language = request.args.get('lang', None)
    
    # 查询代码片段 (使用特殊分类)
    query = Content.query.filter_by(category='代码', is_published=True)
    
    if language:
        # 按编程语言筛选 (假设语言信息存储在tags中)
        from app.models import Tag
        query = query.filter(Content.tags.any(Tag.name == language))
    
    # 分页
    from flask import current_app
    per_page = current_app.config.get('POSTS_PER_PAGE', 15)
    snippets_pagination = query.order_by(Content.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取编程语言标签
    programming_languages = Tag.get_programming_languages()
    
    return render_template('content/code_snippets.html',
                         snippets=snippets_pagination.items,
                         pagination=snippets_pagination,
                         languages=programming_languages,
                         current_language=language)


@bp.route('/timeline')
def project_timeline():
    """
    📅 项目时间线页面
    展示所有项目的时间线视图
    """
    timeline_data = Project.get_project_timeline()
    
    # 按年份分组
    timeline_by_year = {}
    for item in timeline_data:
        year = item['start_date'].year if item['start_date'] else 'unknown'
        if year not in timeline_by_year:
            timeline_by_year[year] = []
        timeline_by_year[year].append(item)
    
    return render_template('content/timeline.html',
                         timeline_data=timeline_data,
                         timeline_by_year=timeline_by_year)


@bp.route('/all')
def all_content():
    """
    📚 所有内容列表页面
    展示所有已发布的内容
    """
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', None)
    
    # 构建查询
    query = Content.query.filter_by(is_published=True)
    
    if category:
        query = query.filter_by(category=category)
    
    # 分页
    from flask import current_app
    per_page = current_app.config.get('POSTS_PER_PAGE', 12)
    content_pagination = query.order_by(Content.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取统计数据
    category_stats = Content.get_category_stats()
    
    # 获取热门标签 (简化版)
    from app.models import Tag
    popular_tags = []
    
    # 获取最新内容
    recent_content = Content.query.filter_by(is_published=True).order_by(Content.created_at.desc()).limit(5).all()
    
    # 内容统计
    total_content = Content.query.filter_by(is_published=True).count()
    stats = {
        'total_content': total_content,
        'total_words': total_content * 500  # 简化估算
    }
    
    return render_template('content/list.html',
                         content_list=content_pagination,
                         category=category,
                         popular_tags=popular_tags,
                         recent_content=recent_content,
                         stats=stats)


@bp.route('/category/<category>')
def category_list(category):
    """
    🏷️ 分类内容列表页面
    按分类展示内容
    """
    valid_categories = ['技术', '观察', '生活', '创作', '代码']
    if category not in valid_categories:
        abort(404)
    
    page = request.args.get('page', 1, type=int)
    
    # 查询该分类的内容
    query = Content.query.filter_by(category=category, is_published=True)
    
    # 分页
    from flask import current_app
    per_page = current_app.config.get('POSTS_PER_PAGE', 12)
    content_pagination = query.order_by(Content.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取分类统计
    category_stats = Content.get_category_stats()
    
    # 获取热门标签 (简化版)
    from app.models import Tag
    popular_tags = []
    
    # 获取最新内容
    recent_content = Content.query.filter_by(is_published=True).order_by(Content.created_at.desc()).limit(5).all()
    
    # 内容统计
    total_content = Content.query.filter_by(category=category, is_published=True).count()
    stats = {
        'total_content': total_content,
        'total_words': total_content * 500  # 简化估算
    }
    
    return render_template('content/list.html',
                         content_list=content_pagination,
                         category=category,
                         popular_tags=popular_tags,
                         recent_content=recent_content,
                         stats=stats)


@bp.route('/rss')
@bp.route('/feed')
def rss_feed():
    """
    📡 RSS订阅源
    生成最新内容的RSS feed
    """
    from flask import Response, url_for
    from datetime import datetime
    
    # 获取最新内容 (所有类型)
    recent_content = Content.query.filter_by(is_published=True)\
                                  .order_by(Content.created_at.desc())\
                                  .limit(20).all()
    
    # 生成RSS XML (简化版)
    rss_items = []
    for content in recent_content:
        item = f"""
        <item>
            <title><![CDATA[{content.title}]]></title>
            <link>{url_for('content.detail', id=content.id, _external=True)}</link>
            <description><![CDATA[{content.get_summary(150)}]]></description>
            <pubDate>{content.created_at.strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
            <guid>{url_for('content.detail', id=content.id, _external=True)}</guid>
        </item>"""
        rss_items.append(item)
    
    from flask import current_app
    rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>{current_app.config.get('SITE_NAME', '个人门户')}</title>
        <link>{url_for('main.index', _external=True)}</link>
        <description>{current_app.config.get('SITE_DESCRIPTION', '')}</description>
        <language>zh-CN</language>
        <lastBuildDate>{datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>
        {''.join(rss_items)}
    </channel>
</rss>"""
    
    return Response(rss_xml, mimetype='application/rss+xml')


@bp.route('/tag/<tag>')
def tag_content(tag):
    """
    🏷️ 标签内容页面
    显示包含特定标签的所有内容
    """
    page = request.args.get('page', 1, type=int)
    
    # 查询包含该标签的内容
    from app.models import Tag
    tag_obj = Tag.query.filter_by(name=tag).first()
    
    if not tag_obj:
        abort(404)
    
    # 获取包含该标签的内容
    query = Content.query.filter(
        Content.is_published == True,
        Content.tags.contains(tag_obj)
    )
    
    # 分页
    from flask import current_app
    per_page = current_app.config.get('POSTS_PER_PAGE', 12)
    content_pagination = query.order_by(Content.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取热门标签
    popular_tags = []
    
    # 获取最新内容
    recent_content = Content.query.filter_by(is_published=True).order_by(Content.created_at.desc()).limit(5).all()
    
    # 内容统计
    total_content = query.count()
    stats = {
        'total_content': total_content,
        'total_words': total_content * 500  # 简化估算
    }
    
    return render_template('content/list.html',
                         content_list=content_pagination,
                         category=f'标签：{tag}',
                         popular_tags=popular_tags,
                         recent_content=recent_content,
                         stats=stats)


@bp.route('/search')
def search():
    """🔍 内容搜索页面 支持全文搜索和标签筛选"""
    query = request.args.get('q', '').strip()
    content_type = request.args.get('type', '').strip()
    page = request.args.get('page', 1, type=int)
    
    results = []
    total_results = 0
    search_time = 0
    pagination = None
    
    if query:
        import time
        start_time = time.time()
        
        # 构建基础查询
        base_query = Content.query.filter(Content.is_published == True)
        
        # 按类型筛选
        if content_type:
            base_query = base_query.filter(Content.category == content_type)
        
        # 全文搜索 (简化版 - 搜索标题和内容)
        search_filter = Content.title.contains(query) | Content.content.contains(query)
        
        # 也搜索标签
        if hasattr(Content, 'tags'):
            search_filter = search_filter | Content.tags.contains(query)
        
        base_query = base_query.filter(search_filter)
        
        # 分页
        pagination = base_query.order_by(Content.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
        
        results = pagination.items
        total_results = pagination.total
        search_time = time.time() - start_time
    
    # 计算各类型的结果数量
    results_count = {
        'total': total_results,
        'content': total_results,  # 简化版
        'project': 0  # TODO: 项目搜索
    }
    
    return render_template('content/search_results.html', 
                         query=query, 
                         content_type=content_type,
                         results=results,
                         total_results=total_results,
                         search_time=search_time,
                         results_count=results_count,
                         pagination=pagination)