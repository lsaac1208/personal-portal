"""
🔧 管理后台路由蓝图
管理员内容管理和项目咨询处理
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Content, Project, Tag, ProjectInquiry
from app.forms import ContentForm, ProjectForm, InquiryResponseForm

bp = Blueprint('admin', __name__)


# 🔒 管理员验证装饰器
def admin_required(f):
    """管理员权限验证装饰器"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('需要管理员权限才能访问此页面。', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/')
@login_required
@admin_required
def dashboard():
    """📊 管理后台首页 - 数据统计面板"""
    # 内容统计
    content_stats = {
        'total': Content.query.count(),
        'published': Content.query.filter_by(is_published=True).count(),
        'drafts': Content.query.filter_by(is_published=False).count(),
        'tech': Content.query.filter_by(category='技术').count(),
        'creative': Content.query.filter_by(category='创作').count(),
        'life': Content.query.filter_by(category='生活').count()
    }
    
    # 项目统计
    project_stats = {
        'total': Project.query.count(),
        'published': Project.query.filter_by(is_published=True).count(),
        'featured': Project.query.filter_by(is_featured=True).count()
    }
    
    # 咨询统计
    inquiry_stats = {
        'total': ProjectInquiry.query.count(),
        'pending': ProjectInquiry.query.filter_by(status='待处理').count(),
        'in_progress': ProjectInquiry.query.filter_by(status='进行中').count(),
        'completed': ProjectInquiry.query.filter_by(status='已完成').count()
    }
    
    # 最新咨询 (待处理)
    recent_inquiries = ProjectInquiry.query.filter_by(status='待处理')\
                                          .order_by(ProjectInquiry.created_at.desc())\
                                          .limit(5).all()
    
    # 最近内容
    recent_content = Content.query.order_by(Content.updated_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         content_stats=content_stats,
                         project_stats=project_stats,
                         inquiry_stats=inquiry_stats,
                         recent_inquiries=recent_inquiries,
                         recent_content=recent_content)


# 📝 内容管理
@bp.route('/content')
@login_required
@admin_required
def content_list():
    """内容列表管理"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', None)
    status = request.args.get('status', None)
    
    # 构建查询
    query = Content.query
    
    if category:
        query = query.filter_by(category=category)
    
    if status == 'published':
        query = query.filter_by(is_published=True)
    elif status == 'draft':
        query = query.filter_by(is_published=False)
    
    # 分页
    from flask import current_app
    per_page = current_app.config.get('POSTS_PER_PAGE', 20)
    content_pagination = query.order_by(Content.updated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/content_list.html',
                         content_items=content_pagination.items,
                         pagination=content_pagination,
                         current_category=category,
                         current_status=status)


@bp.route('/content/new', methods=['GET', 'POST'])
@bp.route('/content/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required  
def content_edit(id=None):
    """创建或编辑内容"""
    if id:
        content = Content.query.get_or_404(id)
        form = ContentForm(obj=content)
    else:
        content = None
        form = ContentForm()
    
    if form.validate_on_submit():
        if content is None:
            # 创建新内容
            content = Content()
            from app import db
            db.session.add(content)
        
        # 更新内容
        form.populate_obj(content)
        
        # 处理标签
        if form.tags.data:
            tag_names = [name.strip() for name in form.tags.data.split(',') if name.strip()]
            content.update_tags(tag_names)
        
        # 渲染Markdown为HTML
        content.render_html()
        
        try:
            from app import db
            db.session.commit()
            flash('内容保存成功！', 'success')
            return redirect(url_for('admin.content_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'保存失败：{str(e)}', 'error')
    
    return render_template('admin/content_edit.html',
                         form=form,
                         content=content)


# 💼 项目管理
@bp.route('/projects')
@login_required
@admin_required
def project_list():
    """项目列表管理"""
    page = request.args.get('page', 1, type=int)
    
    # 分页
    from flask import current_app
    per_page = current_app.config.get('POSTS_PER_PAGE', 20)
    projects_pagination = Project.query.order_by(Project.updated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/project_list.html',
                         projects=projects_pagination.items,
                         pagination=projects_pagination)


@bp.route('/project/new', methods=['GET', 'POST'])
@bp.route('/project/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def project_edit(id=None):
    """创建或编辑项目"""
    if id:
        project = Project.query.get_or_404(id)
        form = ProjectForm(obj=project)
    else:
        project = None
        form = ProjectForm()
    
    if form.validate_on_submit():
        if project is None:
            project = Project()
            from app import db
            db.session.add(project)
        
        form.populate_obj(project)
        
        try:
            from app import db
            db.session.commit()
            flash('项目保存成功！', 'success')
            return redirect(url_for('admin.project_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'保存失败：{str(e)}', 'error')
    
    return render_template('admin/project_edit.html',
                         form=form,
                         project=project)


# 📞 项目咨询管理
@bp.route('/inquiries')
@login_required
@admin_required
def inquiry_list():
    """项目咨询列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', None)
    
    query = ProjectInquiry.query
    if status:
        query = query.filter_by(status=status)
    
    from flask import current_app
    per_page = current_app.config.get('POSTS_PER_PAGE', 20)
    inquiries_pagination = query.order_by(ProjectInquiry.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/inquiry_list.html',
                         inquiries=inquiries_pagination.items,
                         pagination=inquiries_pagination,
                         current_status=status)


@bp.route('/inquiry/<int:id>')
@login_required
@admin_required
def inquiry_detail(id):
    """项目咨询详情"""
    inquiry = ProjectInquiry.query.get_or_404(id)
    form = InquiryResponseForm()
    
    return render_template('admin/inquiry_detail.html',
                         inquiry=inquiry,
                         form=form)


@bp.route('/inquiry/<int:id>/update', methods=['POST'])
@login_required
@admin_required
def inquiry_update(id):
    """更新项目咨询状态"""
    inquiry = ProjectInquiry.query.get_or_404(id)
    form = InquiryResponseForm()
    
    if form.validate_on_submit():
        inquiry.status = form.status.data
        if form.notes.data:
            inquiry.notes = form.notes.data
        
        try:
            from app import db
            db.session.commit()
            flash('咨询状态更新成功！', 'success')
            
            # 如果需要，发送邮件通知客户
            if form.send_email.data:
                # TODO: 实现邮件发送功能
                pass
                
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败：{str(e)}', 'error')
    
    return redirect(url_for('admin.inquiry_detail', id=id))


# 🏷️ 标签管理
@bp.route('/tags')
@login_required
@admin_required
def tag_list():
    """标签管理"""
    tags = Tag.query.order_by(Tag.usage_count.desc()).all()
    return render_template('admin/tag_list.html', tags=tags)


# 📊 API接口 (AJAX用)
@bp.route('/api/content/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_content(id):
    """删除内容"""
    content = Content.query.get_or_404(id)
    
    try:
        from app import db
        db.session.delete(content)
        db.session.commit()
        return jsonify({'success': True, 'message': '内容删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败：{str(e)}'}), 500


@bp.route('/api/project/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_project(id):
    """删除项目"""
    project = Project.query.get_or_404(id)
    
    try:
        from app import db
        db.session.delete(project)
        db.session.commit()
        return jsonify({'success': True, 'message': '项目删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败：{str(e)}'}), 500