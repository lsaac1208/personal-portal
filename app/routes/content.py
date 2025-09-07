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
def projects():
    """
    💼 项目作品集页面
    展示所有项目的网格视图
    """
    page = request.args.get('page', 1, type=int)
    tech_filter = request.args.get('tech', None)
    
    # 构建查询
    query = Project.query.filter_by(is_published=True)
    
    if tech_filter:
        # 按技术栈筛选
        query = query.filter(Project.tech_stack.contains(tech_filter))
    
    # 分页
    from flask import current_app
    per_page = current_app.config.get('POSTS_PER_PAGE', 12)  # 项目展示用12个一页
    projects_pagination = query.order_by(Project.completion_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取所有技术栈用于筛选
    all_tech_stacks = Project.get_all_tech_stacks()
    
    return render_template('content/projects.html',
                         projects=projects_pagination.items,
                         pagination=projects_pagination,
                         tech_stacks=all_tech_stacks,
                         current_tech=tech_filter)


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