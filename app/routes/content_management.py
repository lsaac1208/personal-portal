"""
📝 内容管理路由蓝图 - Story 2.1 内容发布系统
🎯 backend-architect + content-marketer 设计
支持Markdown编辑器、内容CRUD、草稿管理、SEO优化
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime
import json
from app import db
from app.models import Content, Tag
from app.forms.content import ContentForm, ContentSearchForm

bp = Blueprint('content_management', __name__, url_prefix='/admin/content')


@bp.route('/')
@bp.route('/list')
@login_required
def content_list():
    """
    📋 内容管理列表页面
    支持状态筛选、搜索、批量操作
    """
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'updated_desc')
    
    # 构建查询
    query = Content.query
    
    # 分类筛选
    if category:
        query = query.filter(Content.category == category)
    
    # 状态筛选
    if status:
        if status == 'published':
            query = query.filter(Content.is_published == True)
        elif status == 'draft':
            query = query.filter(Content.is_published == False)
        elif status == 'featured':
            query = query.filter(Content.is_featured == True)
        else:
            query = query.filter(Content.status == status)
    
    # 搜索
    if search:
        query = query.filter(
            db.or_(
                Content.title.contains(search),
                Content.content.contains(search),
                Content.summary.contains(search)
            )
        )
    
    # 排序
    if sort_by == 'title_asc':
        query = query.order_by(Content.title.asc())
    elif sort_by == 'created_desc':
        query = query.order_by(Content.created_at.desc())
    elif sort_by == 'created_asc':
        query = query.order_by(Content.created_at.asc())
    elif sort_by == 'views_desc':
        query = query.order_by(Content.view_count.desc())
    elif sort_by == 'seo_score_desc':
        query = query.order_by(Content.seo_score.desc())
    else:  # updated_desc (default)
        query = query.order_by(Content.updated_at.desc())
    
    # 分页
    per_page = current_app.config.get('ADMIN_POSTS_PER_PAGE', 20)
    contents = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取统计数据
    stats = {
        'total': Content.query.count(),
        'published': Content.query.filter_by(is_published=True).count(),
        'draft': Content.query.filter_by(is_published=False).count(),
        'featured': Content.query.filter_by(is_featured=True).count(),
    }
    
    # 获取分类统计
    category_stats = Content.get_category_stats()
    
    return render_template('admin/content/list.html',
                         contents=contents,
                         stats=stats,
                         category_stats=category_stats,
                         current_category=category,
                         current_status=status,
                         current_search=search,
                         current_sort=sort_by)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_content():
    """
    ✏️ 创建新内容
    支持Markdown编辑、实时预览、SEO优化
    """
    form = ContentForm()
    
    if form.validate_on_submit():
        # 创建新内容
        content = Content(
            title=form.title.data,
            content=form.content.data,
            summary=form.summary.data,
            category=form.category.data,
            featured_image=form.featured_image.data,
            source_type=form.source_type.data,
            source_url=form.source_url.data,
            source_author=form.source_author.data,
            is_published=form.is_published.data,
            is_featured=form.is_featured.data,
            difficulty=form.difficulty.data,
            priority=form.priority.data,
            status=form.status.data,
            indexable=form.indexable.data,
            sitemap=form.sitemap.data,
            comments_enabled=form.comments_enabled.data,
            # SEO字段
            seo_title=form.seo_title.data,
            seo_description=form.seo_description.data,
            seo_keywords=form.seo_keywords.data,
            meta_title=form.meta_title.data,
            meta_description=form.meta_description.data,
            # Open Graph字段
            og_title=form.og_title.data,
            og_description=form.og_description.data,
            og_image=form.og_image.data,
            twitter_card=form.twitter_card.data
        )
        
        # 生成slug
        content.generate_slug()
        
        # 渲染HTML
        content.render_html()
        
        # 计算阅读时间和字数
        content.calculate_reading_time()
        
        # 自动优化SEO
        content.auto_optimize_seo()
        
        # 设置发布时间
        if content.is_published:
            content.published_at = datetime.utcnow()
        
        # 保存到数据库
        try:
            db.session.add(content)
            db.session.commit()
            
            # 处理标签
            if form.tags.data:
                tag_names = [tag.strip() for tag in form.tags.data.split(',') if tag.strip()]
                content.update_tags(tag_names)
                db.session.commit()
            
            flash(f'内容 "{content.title}" 创建成功！', 'success')
            
            # 根据操作决定跳转
            if request.form.get('action') == 'save_and_continue':
                return redirect(url_for('content_management.edit_content', id=content.id))
            elif request.form.get('action') == 'save_and_preview':
                return redirect(url_for('content.detail', id=content.id))
            else:
                return redirect(url_for('content_management.content_list'))
                
        except Exception as e:
            db.session.rollback()
            flash(f'创建失败: {str(e)}', 'error')
            current_app.logger.error(f'Content creation error: {e}')
    
    # 获取标签建议
    popular_tags = Tag.get_popular_tags(limit=20)
    category_tags = {}
    for category in ['技术', '观察', '生活', '创作', '代码']:
        category_tags[category] = Tag.get_category_tags(category, limit=10)
    
    return render_template('admin/content/edit.html',
                         form=form,
                         content=None,
                         popular_tags=popular_tags,
                         category_tags=category_tags,
                         is_edit=False)


@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_content(id):
    """
    ✏️ 编辑内容
    支持版本历史、草稿保存、批量操作
    """
    content = Content.query.get_or_404(id)
    
    # 记录编辑前的状态
    original_data = {
        'title': content.title,
        'content': content.content,
        'summary': content.summary,
        'is_published': content.is_published
    }
    
    form = ContentForm(obj=content)
    
    # 设置标签表单数据
    if content.tags:
        form.tags.data = ', '.join([tag.name for tag in content.tags])
    
    if form.validate_on_submit():
        # 更新内容
        form.populate_obj(content)
        
        # 重新生成slug（如果标题变了）
        if original_data['title'] != content.title:
            content.generate_slug(force_regenerate=True)
        
        # 重新渲染HTML（如果内容变了）
        if original_data['content'] != content.content:
            content.render_html()
            content.calculate_reading_time()
        
        # 自动优化SEO
        content.auto_optimize_seo()
        
        # 更新发布时间
        if content.is_published and not original_data['is_published']:
            content.published_at = datetime.utcnow()
        elif not content.is_published:
            content.published_at = None
        
        # 创建版本历史
        content.create_version_history(original_data)
        
        try:
            db.session.commit()
            
            # 处理标签更新
            if form.tags.data:
                tag_names = [tag.strip() for tag in form.tags.data.split(',') if tag.strip()]
                content.update_tags(tag_names)
            else:
                content.tags.clear()
            
            db.session.commit()
            
            flash(f'内容 "{content.title}" 更新成功！', 'success')
            
            # 根据操作决定跳转
            if request.form.get('action') == 'save_and_continue':
                return redirect(url_for('content_management.edit_content', id=content.id))
            elif request.form.get('action') == 'save_and_preview':
                return redirect(url_for('content.detail', id=content.id))
            else:
                return redirect(url_for('content_management.content_list'))
                
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败: {str(e)}', 'error')
            current_app.logger.error(f'Content update error: {e}')
    
    # 获取标签建议
    popular_tags = Tag.get_popular_tags(limit=20)
    category_tags = {}
    for category in ['技术', '观察', '生活', '创作', '代码']:
        category_tags[category] = Tag.get_category_tags(category, limit=10)
    
    # 获取SEO分析
    seo_analysis = content.get_seo_analysis()
    
    return render_template('admin/content/edit.html',
                         form=form,
                         content=content,
                         popular_tags=popular_tags,
                         category_tags=category_tags,
                         seo_analysis=seo_analysis,
                         is_edit=True)


@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_content(id):
    """
    🗑️ 删除内容
    """
    content = Content.query.get_or_404(id)
    title = content.title
    
    try:
        db.session.delete(content)
        db.session.commit()
        
        flash(f'内容 "{title}" 已删除', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'error')
        current_app.logger.error(f'Content deletion error: {e}')
    
    return redirect(url_for('content_management.content_list'))


@bp.route('/bulk-action', methods=['POST'])
@login_required
def bulk_action():
    """
    📦 批量操作内容
    支持批量发布、删除、更改状态
    """
    action = request.form.get('action')
    content_ids = request.form.getlist('content_ids')
    
    if not content_ids:
        flash('请选择要操作的内容', 'error')
        return redirect(url_for('content_management.content_list'))
    
    content_list = Content.query.filter(Content.id.in_(content_ids)).all()
    success_count = 0
    error_count = 0
    
    try:
        for content in content_list:
            try:
                if action == 'publish':
                    content.is_published = True
                    content.published_at = datetime.utcnow()
                elif action == 'unpublish':
                    content.is_published = False
                    content.published_at = None
                elif action == 'feature':
                    content.is_featured = True
                elif action == 'unfeature':
                    content.is_featured = False
                elif action == 'delete':
                    db.session.delete(content)
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                current_app.logger.error(f'Bulk action error for content {content.id}: {e}')
        
        db.session.commit()
        
        if success_count > 0:
            flash(f'成功处理 {success_count} 个内容', 'success')
        if error_count > 0:
            flash(f'{error_count} 个内容处理失败', 'error')
    
    except Exception as e:
        db.session.rollback()
        flash(f'批量操作失败: {str(e)}', 'error')
        current_app.logger.error(f'Bulk action error: {e}')
    
    return redirect(url_for('content_management.content_list'))


@bp.route('/preview/<int:id>')
@login_required
def preview_content(id):
    """
    👁️ 预览内容
    """
    content = Content.query.get_or_404(id)
    
    # 临时渲染HTML（不保存到数据库）
    if not content.content_html:
        content.render_html()
    
    return render_template('content/detail.html',
                         content=content,
                         is_preview=True)


@bp.route('/api/autosave', methods=['POST'])
@login_required
def autosave_content():
    """
    💾 自动保存草稿
    AJAX接口，定期保存编辑中的内容
    """
    try:
        data = request.get_json()
        content_id = data.get('content_id')
        
        if content_id:
            # 更新现有内容
            content = Content.query.get_or_404(content_id)
        else:
            # 创建新的草稿
            content = Content(
                title='未命名草稿',
                content='',
                category='技术',
                is_published=False,
                status='草稿'
            )
            db.session.add(content)
            db.session.flush()  # 获取ID但不提交
        
        # 更新字段
        if 'title' in data:
            content.title = data['title'] or '未命名草稿'
        if 'content' in data:
            content.content = data['content']
        if 'summary' in data:
            content.summary = data['summary']
        if 'category' in data:
            content.category = data['category']
        
        # 重新渲染HTML
        if 'content' in data:
            content.render_html()
            content.calculate_reading_time()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'content_id': content.id,
            'last_saved': datetime.utcnow().strftime('%H:%M:%S'),
            'word_count': content.word_count,
            'reading_time': content.reading_time
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Autosave error: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/markdown-preview', methods=['POST'])
@login_required
def markdown_preview():
    """
    📝 Markdown预览
    实时将Markdown转换为HTML预览
    """
    try:
        data = request.get_json()
        markdown_content = data.get('content', '')
        
        if not markdown_content:
            return jsonify({'html': ''})
        
        # 使用与Content模型相同的Markdown配置
        import markdown
        
        extensions = [
            'codehilite',
            'toc',
            'tables',
            'fenced_code',
            'nl2br',
        ]
        
        extension_configs = {
            'codehilite': {
                'css_class': 'highlight',
                'use_pygments': True,
                'pygments_style': 'default'
            },
            'toc': {
                'anchorlink': True
            }
        }
        
        md = markdown.Markdown(extensions=extensions, extension_configs=extension_configs)
        html = md.convert(markdown_content)
        
        return jsonify({
            'success': True,
            'html': html
        })
    
    except Exception as e:
        current_app.logger.error(f'Markdown preview error: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/seo-analysis/<int:id>')
@login_required
def seo_analysis(id):
    """
    📊 SEO分析
    返回内容的详细SEO分析结果
    """
    content = Content.query.get_or_404(id)
    
    try:
        # 重新计算SEO分数
        content.calculate_seo_score()
        db.session.commit()
        
        # 获取完整SEO分析
        analysis = content.get_full_seo_analysis()
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'score': content.seo_score,
            'word_count': content.word_count,
            'reading_time': content.reading_time
        })
    
    except Exception as e:
        current_app.logger.error(f'SEO analysis error: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/slug-suggestions/<int:id>')
@login_required
def slug_suggestions(id):
    """
    🔗 Slug建议
    生成URL友好的slug建议
    """
    content = Content.query.get_or_404(id)
    
    try:
        suggestions = content.get_slug_variations()
        analysis = content.analyze_slug_quality()
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'current_slug': content.slug,
            'analysis': analysis
        })
    
    except Exception as e:
        current_app.logger.error(f'Slug suggestions error: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/generate-summary/<int:id>', methods=['POST'])
@login_required
def generate_summary(id):
    """
    📋 生成摘要
    自动生成内容摘要
    """
    content = Content.query.get_or_404(id)
    
    try:
        data = request.get_json()
        length = data.get('length', 150)
        force_regenerate = data.get('force_regenerate', False)
        
        summary = content.generate_auto_summary(length, force_regenerate)
        keywords = content.generate_seo_keywords()
        
        # 如果强制重新生成，保存到数据库
        if force_regenerate:
            content.summary = summary
            content.seo_keywords = keywords
            db.session.commit()
        
        return jsonify({
            'success': True,
            'summary': summary,
            'keywords': keywords,
            'length': len(summary)
        })
    
    except Exception as e:
        current_app.logger.error(f'Generate summary error: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/stats')
@login_required
def content_stats():
    """
    📊 内容统计页面
    展示内容数据分析和趋势
    """
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # 基础统计
    basic_stats = {
        'total': Content.query.count(),
        'published': Content.query.filter_by(is_published=True).count(),
        'draft': Content.query.filter_by(is_published=False).count(),
        'featured': Content.query.filter_by(is_featured=True).count(),
    }
    
    # 分类统计
    category_stats = Content.get_category_stats()
    
    # 月度发布统计
    monthly_stats = db.session.query(
        func.strftime('%Y-%m', Content.created_at).label('month'),
        func.count(Content.id).label('count')
    ).filter_by(is_published=True).group_by('month').order_by('month').all()
    
    # 浏览量TOP10
    popular_content = Content.query.filter_by(is_published=True)\
                                  .order_by(Content.view_count.desc())\
                                  .limit(10).all()
    
    # SEO评分分布
    seo_distribution = db.session.query(
        func.case(
            (Content.seo_score >= 80, '优秀(80+)'),
            (Content.seo_score >= 60, '良好(60-79)'),
            (Content.seo_score >= 40, '一般(40-59)'),
            else_='待优化(<40)'
        ).label('score_range'),
        func.count(Content.id).label('count')
    ).group_by('score_range').all()
    
    # 标签使用统计
    tag_stats = Tag.get_popular_tags(limit=20)
    
    return render_template('admin/content/stats.html',
                         basic_stats=basic_stats,
                         category_stats=category_stats,
                         monthly_stats=monthly_stats,
                         popular_content=popular_content,
                         seo_distribution=seo_distribution,
                         tag_stats=tag_stats)