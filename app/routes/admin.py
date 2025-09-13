"""
🔧 管理后台路由蓝图
管理员内容管理和项目咨询处理
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os, json, uuid
from PIL import Image
from app.models import Content, Project, Tag, ProjectInquiry
from app.forms import ContentForm, ProjectForm, InquiryResponseForm
from app.utils.file_handler import allowed_file, save_upload_file, optimize_image, ImageProcessor, validate_image_file
from app.utils.media_manager import MediaManager

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
        'pending': ProjectInquiry.query.filter_by(status='新咨询').count(),
        'in_progress': ProjectInquiry.query.filter_by(status='处理中').count(),
        'completed': ProjectInquiry.query.filter_by(status='已成交').count()
    }
    
    # 最新咨询 (新咨询)
    recent_inquiries = ProjectInquiry.query.filter_by(status='新咨询')\
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
    
    return render_template('admin/content_manage.html',
                         contents=content_pagination.items,
                         pagination=content_pagination,
                         current_category=category,
                         current_status=status)


@bp.route('/content/create', methods=['GET', 'POST'])
@login_required
@admin_required
def content_create():
    """创建新内容"""
    form = ContentForm()
    
    if form.validate_on_submit():
        action = request.form.get('action', 'draft')
        
        # 创建新内容
        content = Content(
            title=form.title.data,
            content=form.content.data,
            summary=form.summary.data,
            category=form.category.data,
            author=current_user.name or '管理员',
            meta_title=form.meta_title.data,
            meta_description=form.meta_description.data,
            slug=form.slug.data,
            reading_time=form.reading_time.data,
            difficulty=form.difficulty.data,
            is_featured=form.is_featured.data,
            indexable=form.indexable.data,
            sitemap=form.sitemap.data,
            status='已发布' if action == 'publish' else '草稿'
        )
        
        # 处理发布时间
        if form.publish_date.data:
            content.published_at = form.publish_date.data
        elif action == 'publish':
            from datetime import datetime
            content.published_at = datetime.utcnow()
        
        # 处理标签
        if form.tags.data:
            tag_names = [name.strip() for name in form.tags.data.split(',') if name.strip()]
            content.update_tags(tag_names)
        
        # 自动生成 slug
        if not content.slug:
            content.generate_slug()
        
        # 计算阅读时间
        if not content.reading_time:
            content.calculate_reading_time()
        
        # 渲染Markdown为HTML
        content.render_html()
        
        try:
            from app import db
            db.session.add(content)
            db.session.commit()
            
            action_msg = '发布' if action == 'publish' else '保存'
            flash(f'内容{action_msg}成功！', 'success')
            
            if action == 'preview':
                return redirect(url_for('content.detail', id=content.id, preview=1))
            else:
                return redirect(url_for('admin.content_list'))
                
        except Exception as e:
            db.session.rollback()
            flash(f'保存失败：{str(e)}', 'error')
    
    return render_template('admin/content_create.html', form=form)


@bp.route('/content/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def content_edit(id):
    """编辑内容"""
    content = Content.query.get_or_404(id)
    form = ContentForm(obj=content)
    
    # 预填充标签
    if content.tags:
        form.tags.data = ', '.join([tag.name for tag in content.tags])
    
    if form.validate_on_submit():
        action = request.form.get('action', 'draft')
        
        # 保存原始数据用于版本对比
        original_content = {
            'title': content.title,
            'content': content.content,
            'summary': content.summary
        }
        
        # 更新内容
        content.title = form.title.data
        content.content = form.content.data
        content.summary = form.summary.data
        content.category = form.category.data
        content.meta_title = form.meta_title.data
        content.meta_description = form.meta_description.data
        content.slug = form.slug.data
        content.reading_time = form.reading_time.data
        content.difficulty = form.difficulty.data
        content.is_featured = form.is_featured.data
        content.indexable = form.indexable.data
        content.sitemap = form.sitemap.data
        
        # 处理状态更新
        if action == 'publish':
            content.status = '已发布'
            if not content.published_at:
                from datetime import datetime
                content.published_at = datetime.utcnow()
        elif action == 'update' and content.status == '已发布':
            from datetime import datetime
            content.updated_at = datetime.utcnow()
        else:
            content.status = '草稿'
        
        # 处理发布时间
        if form.publish_date.data:
            content.published_at = form.publish_date.data
        
        # 处理标签
        if form.tags.data:
            tag_names = [name.strip() for name in form.tags.data.split(',') if name.strip()]
            content.update_tags(tag_names)
        
        # 自动生成 slug
        if not content.slug:
            content.generate_slug()
        
        # 计算阅读时间
        if not content.reading_time:
            content.calculate_reading_time()
        
        # 创建版本历史记录
        if any(content.__dict__[k] != original_content[k] for k in original_content):
            content.create_version_history(original_content)
        
        # 渲染Markdown为HTML
        content.render_html()
        
        try:
            from app import db
            db.session.commit()
            
            action_msg = '发布' if action == 'publish' else '更新' if action == 'update' else '保存'
            flash(f'内容{action_msg}成功！', 'success')
            
            if action == 'preview':
                return redirect(url_for('content.detail', id=content.id, preview=1))
            else:
                return redirect(url_for('admin.content_list'))
                
        except Exception as e:
            db.session.rollback()
            flash(f'保存失败：{str(e)}', 'error')
    
    return render_template('admin/content_edit.html', form=form, content=content)


@bp.route('/content/manage')
@login_required
@admin_required
def content_manage():
    """内容管理列表"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    sort = request.args.get('sort', 'created_desc')
    
    # 构建查询
    query = Content.query
    
    # 搜索
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            Content.title.like(search_filter) |
            Content.summary.like(search_filter) |
            Content.content.like(search_filter)
        )
    
    # 分类筛选
    if category:
        query = query.filter_by(category=category)
    
    # 状态筛选
    if status:
        query = query.filter_by(status=status)
    
    # 排序
    if sort == 'created_desc':
        query = query.order_by(Content.created_at.desc())
    elif sort == 'created_asc':
        query = query.order_by(Content.created_at.asc())
    elif sort == 'updated_desc':
        query = query.order_by(Content.updated_at.desc())
    elif sort == 'views_desc':
        query = query.order_by(Content.views.desc())
    elif sort == 'title_asc':
        query = query.order_by(Content.title.asc())
    
    # 分页
    from flask import current_app
    per_page = current_app.config.get('POSTS_PER_PAGE', 15)
    pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 内容统计
    stats = {
        'total': Content.query.count(),
        'published': Content.query.filter_by(status='已发布').count(),
        'draft': Content.query.filter_by(status='草稿').count(),
        'views': Content.query.with_entities(Content.views).filter(Content.views.isnot(None)).all(),
        'this_month': Content.query.filter(
            Content.created_at >= datetime.now().replace(day=1, hour=0, minute=0, second=0)
        ).count(),
        'featured': Content.query.filter_by(is_featured=True).count()
    }
    
    # 计算总浏览量
    stats['views'] = sum(v[0] or 0 for v in stats['views'])
    
    return render_template('admin/content_manage.html',
                         contents=pagination.items,
                         pagination=pagination,
                         stats=stats)


# 💼 项目管理
@bp.route('/projects')
@login_required
@admin_required
def project_list():
    """项目列表管理"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'updated_desc')
    
    # 构建查询
    query = Project.query
    
    # 搜索
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            Project.title.like(search_filter) |
            Project.description.like(search_filter) |
            Project.tech_stack.like(search_filter)
        )
    
    # 状态筛选
    if status:
        query = query.filter_by(status=status)
    
    # 分类筛选  
    if category:
        query = query.filter_by(category=category)
    
    # 排序
    if sort == 'created_desc':
        query = query.order_by(Project.created_at.desc())
    elif sort == 'created_asc':
        query = query.order_by(Project.created_at.asc())
    elif sort == 'updated_desc':
        query = query.order_by(Project.updated_at.desc())
    elif sort == 'title_asc':
        query = query.order_by(Project.title.asc())
    elif sort == 'status':
        query = query.order_by(Project.status, Project.updated_at.desc())
    else:
        query = query.order_by(Project.updated_at.desc())
    
    # 分页
    from flask import current_app
    per_page = current_app.config.get('POSTS_PER_PAGE', 15)
    projects_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/project_list.html',
                         projects=projects_pagination.items,
                         pagination=projects_pagination,
                         current_search=search,
                         current_status=status,
                         current_category=category,
                         current_sort=sort)


@bp.route('/project/new', methods=['GET', 'POST'])
@bp.route('/project/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def project_edit(id=None):
    """创建或编辑项目"""
    if id:
        project = Project.query.get_or_404(id)
        form = ProjectForm(obj=project)
        
        # 预填充标签
        if project.tags:
            form.tags.data = ', '.join([tag.name for tag in project.tags])
    else:
        project = None
        form = ProjectForm()
    
    if form.validate_on_submit():
        action = request.form.get('action', 'save')
        
        if project is None:
            # 创建新项目
            project = Project(
                title=form.title.data,
                subtitle=form.subtitle.data,
                description=form.description.data,
                category=form.category.data,
                features=form.features.data,
                challenges=form.challenges.data,
                metrics=form.metrics.data,
                tech_stack=form.tech_stack.data,
                demo_url=form.demo_url.data,
                github_url=form.github_url.data,
                documentation_url=form.documentation_url.data,
                start_date=form.start_date.data,
                completion_date=form.completion_date.data,
                duration_months=form.duration_months.data,
                team_size=form.team_size.data,
                status=form.status.data,
                priority=form.priority.data,
                is_public=form.is_public.data,
                is_featured=form.is_featured.data,
                allow_inquiries=form.allow_inquiries.data
            )
            from app import db
            db.session.add(project)
            
            # 设置默认值
            project.is_published = True if action == 'save' else False
        else:
            # 更新现有项目
            form.populate_obj(project)
            
            # 处理发布状态
            if action == 'save':
                project.is_published = True
                
        # 处理标签
        if form.tags.data:
            tag_names = [name.strip() for name in form.tags.data.split(',') if name.strip()]
            project.update_tags(tag_names)
        
        # 处理图片上传
        if form.featured_image.data:
            from app.utils.media_manager import MediaManager
            media_manager = MediaManager()
            
            try:
                result = media_manager.save_image(
                    form.featured_image.data,
                    subfolder='projects',
                    max_size=(1200, 800)
                )
                if result['success']:
                    # 删除旧图片
                    if project.featured_image:
                        media_manager.delete_image(project.featured_image)
                    project.featured_image = result['filename']
                else:
                    flash(f'图片上传失败：{result["message"]}', 'warning')
            except Exception as e:
                flash(f'图片处理失败：{str(e)}', 'warning')
        
        # 处理图片删除
        if request.form.get('remove_featured_image') == 'true':
            if project.featured_image:
                from app.utils.media_manager import MediaManager
                media_manager = MediaManager()
                try:
                    media_manager.delete_image(project.featured_image)
                except:
                    pass  # 忽略删除错误
                project.featured_image = None
        
        # 自动生成slug
        if not project.slug:
            project.generate_slug()
        
        try:
            from app import db
            db.session.commit()
            
            action_msg = '发布' if action == 'save' else '保存'
            flash(f'项目{action_msg}成功！', 'success')
            
            if action == 'save_and_preview' and project:
                return redirect(url_for('content.project_detail', id=project.id))
            else:
                return redirect(url_for('admin.project_list'))
                
        except Exception as e:
            db.session.rollback()
            flash(f'保存失败：{str(e)}', 'error')
    
    return render_template('admin/project_edit.html',
                         form=form,
                         project=project)


# 👤 管理员认证
@bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录页面"""
    from flask import redirect, url_for, flash, session
    from flask_login import login_user
    from flask_wtf import FlaskForm
    from wtforms import StringField, PasswordField, SubmitField, BooleanField
    from wtforms.validators import DataRequired
    
    # 简单的登录表单
    class LoginForm(FlaskForm):
        username = StringField('用户名', validators=[DataRequired()])
        password = PasswordField('密码', validators=[DataRequired()])
        remember_me = BooleanField('记住我')
        submit = SubmitField('登录')
    
    form = LoginForm()
    
    # 简化的登录逻辑 (开发阶段)
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # TODO: 实现真实的用户认证
        if username == 'admin' and password == 'admin':
            # 检查是否已存在管理员用户，如果不存在则创建
            from app.models import User
            from app import db
            
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                # 创建管理员用户并保存到数据库
                admin_user = User(
                    username='admin',
                    email='admin@localhost',
                    full_name='系统管理员',
                    is_admin=True,
                    is_active=True
                )
                admin_user.set_password('admin')
                db.session.add(admin_user)
                db.session.commit()
            
            # 建立Flask-Login会话
            login_user(admin_user, remember=False)
            flash('登录成功！', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('admin/login.html', form=form)


@bp.route('/logout')
def logout():
    """管理员登出"""
    from flask_login import logout_user
    logout_user()
    flash('已成功登出', 'info')
    return redirect(url_for('main.index'))


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
            if form.send_email.data and form.response.data:
                try:
                    from app.utils.email_utils import send_inquiry_response
                    # 创建回复记录
                    from app.models.inquiry import InquiryResponse
                    response = InquiryResponse(
                        inquiry_id=inquiry.id,
                        response=form.response.data,
                        estimated_budget=form.estimated_budget.data,
                        estimated_timeline=form.estimated_timeline.data,
                        next_contact_date=form.next_contact_date.data
                    )
                    db.session.add(response)
                    db.session.commit()
                    
                    # 发送回复邮件
                    success, message = send_inquiry_response(inquiry, response)
                    if success:
                        flash('回复邮件发送成功！', 'success')
                    else:
                        flash(f'邮件发送失败：{message}', 'warning')
                except Exception as e:
                    current_app.logger.error(f'发送回复邮件失败: {str(e)}')
                    flash('邮件发送失败，但状态更新成功。', 'warning')
                
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


# 📊 内容管理 API接口
@bp.route('/content/auto-save', methods=['POST'])
@login_required
@admin_required
def content_auto_save():
    """内容自动保存"""
    try:
        data = {
            'title': request.form.get('title', ''),
            'content': request.form.get('content', ''),
            'summary': request.form.get('summary', ''),
            'category': request.form.get('category', ''),
            'tags': request.form.get('tags', ''),
            'user_id': current_user.id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # 保存到会话或临时存储
        session_key = f'auto_save_content_{current_user.id}'
        current_app.extensions['redis'].setex(
            session_key, 
            timedelta(hours=24),
            json.dumps(data, ensure_ascii=False)
        ) if hasattr(current_app.extensions, 'redis') else None
        
        return jsonify({
            'success': True, 
            'message': '自动保存成功',
            'timestamp': data['timestamp']
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'自动保存失败：{str(e)}'
        }), 500


@bp.route('/content/upload-image', methods=['POST'])
@login_required
@admin_required
def upload_image():
    """上传图片接口 - 使用ImageProcessor"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    try:
        # 使用ImageProcessor处理图片上传
        processor = ImageProcessor()
        result = processor.process_upload(file, subfolder='content', create_thumbnail=True)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '图片上传成功',
                'url': result['image_url'],
                'thumbnail_url': result['thumbnail_url'],
                'filename': result['filename'],
                'info': result['info']
            })
        else:
            return jsonify({
                'success': False,
                'errors': result['errors']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'上传失败：{str(e)}'
        }), 500


@bp.route('/content/upload-featured-image', methods=['POST'])
@login_required
@admin_required
def upload_featured_image():
    """上传特色图片接口"""
    if 'featured_image' not in request.files:
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    file = request.files['featured_image']
    content_id = request.form.get('content_id')
    
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    try:
        # 验证图片
        validation = validate_image_file(file)
        if not validation['valid']:
            return jsonify({
                'success': False,
                'errors': validation['errors']
            }), 400
        
        # 使用ImageProcessor处理特色图片
        processor = ImageProcessor()
        result = processor.process_upload(
            file, 
            subfolder='featured', 
            create_thumbnail=True
        )
        
        if result['success']:
            # 如果有content_id，更新内容的特色图片
            if content_id:
                content = Content.query.get(content_id)
                if content:
                    # 删除旧图片
                    if content.featured_image:
                        old_image_path = os.path.join(
                            current_app.static_folder, 
                            content.featured_image.lstrip('/static/')
                        )
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    
                    # 更新特色图片
                    content.featured_image = result['image_url']
                    content.og_image = result['image_url']  # 同时用作社交分享图片
                    
                    from app import db
                    db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '特色图片上传成功',
                'url': result['image_url'],
                'thumbnail_url': result['thumbnail_url'],
                'info': result['info']
            })
        else:
            return jsonify({
                'success': False,
                'errors': result['errors']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'上传失败：{str(e)}'
        }), 500


@bp.route('/content/batch-upload', methods=['POST'])
@login_required
@admin_required
def batch_upload_images():
    """批量上传图片接口"""
    files = request.files.getlist('images')
    if not files:
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    results = []
    processor = ImageProcessor()
    
    for file in files:
        if file.filename == '':
            continue
            
        try:
            result = processor.process_upload(file, subfolder='batch', create_thumbnail=True)
            if result['success']:
                results.append({
                    'filename': file.filename,
                    'success': True,
                    'url': result['image_url'],
                    'thumbnail_url': result['thumbnail_url'],
                    'info': result['info']
                })
            else:
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'errors': result['errors']
                })
        except Exception as e:
            results.append({
                'filename': file.filename,
                'success': False,
                'errors': [f'处理失败：{str(e)}']
            })
    
    success_count = sum(1 for r in results if r['success'])
    
    return jsonify({
        'success': True,
        'message': f'批量上传完成，成功 {success_count}/{len(results)} 个文件',
        'results': results
    })


@bp.route('/content/<int:id>/revisions')
@login_required
@admin_required
def content_revisions(id):
    """获取内容版本历史"""
    content = Content.query.get_or_404(id)
    
    # 模拟版本历史数据（实际应从数据库获取）
    revisions = [
        {
            'version': content.version or 1,
            'created_at': content.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'author': content.author or '管理员',
            'summary': f'版本 {content.version or 1} - 最新修改',
            'changes': '更新了内容和元数据'
        }
    ]
    
    return jsonify({
        'success': True,
        'revisions': revisions
    })


@bp.route('/content/<int:id>/remove-image', methods=['POST'])
@login_required
@admin_required
def remove_featured_image(id):
    """删除特色图片"""
    content = Content.query.get_or_404(id)
    
    try:
        if content.featured_image:
            # 删除文件（如果存在）
            old_image_path = os.path.join(
                current_app.static_folder, 
                content.featured_image.lstrip('/static/')
            )
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
            
            content.featured_image = None
            
        from app import db
        db.session.commit()
        
        return jsonify({'success': True, 'message': '特色图片删除成功'})
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败：{str(e)}'}), 500


@bp.route('/content/<int:id>/duplicate')
@login_required
@admin_required
def duplicate_content(id):
    """复制内容"""
    original = Content.query.get_or_404(id)
    
    try:
        # 创建副本
        duplicate = Content(
            title=f"{original.title} - 副本",
            content=original.content,
            summary=original.summary,
            category=original.category,
            author=current_user.name or '管理员',
            meta_title=original.meta_title,
            meta_description=original.meta_description,
            reading_time=original.reading_time,
            difficulty=original.difficulty,
            status='草稿',
            is_featured=False
        )
        
        # 复制标签
        if original.tags:
            duplicate.tags = original.tags.copy()
        
        duplicate.generate_slug()
        duplicate.render_html()
        
        from app import db
        db.session.add(duplicate)
        db.session.commit()
        
        flash('内容复制成功！', 'success')
        return redirect(url_for('admin.content_edit', id=duplicate.id))
        
    except Exception as e:
        from app import db
        db.session.rollback()
        flash(f'复制失败：{str(e)}', 'error')
        return redirect(url_for('admin.content_list'))


@bp.route('/content/<int:id>/unpublish', methods=['POST'])
@login_required
@admin_required
def unpublish_content(id):
    """取消发布内容"""
    content = Content.query.get_or_404(id)
    
    try:
        content.status = '草稿'
        content.published_at = None
        
        from app import db
        db.session.commit()
        
        return jsonify({'success': True, 'message': '内容已取消发布'})
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'success': False, 'message': f'取消发布失败：{str(e)}'}), 500


@bp.route('/content/bulk-<action>', methods=['POST'])
@login_required
@admin_required
def bulk_content_action(action):
    """批量操作内容"""
    content_ids = request.form.getlist('content_ids')
    if not content_ids:
        return jsonify({'success': False, 'message': '没有选择内容'}), 400
    
    try:
        contents = Content.query.filter(Content.id.in_(content_ids)).all()
        count = 0
        
        for content in contents:
            if action == 'publish':
                content.status = '已发布'
                if not content.published_at:
                    content.published_at = datetime.utcnow()
                count += 1
            elif action == 'draft':
                content.status = '草稿'
                content.published_at = None
                count += 1
            elif action == 'feature':
                content.is_featured = True
                count += 1
            elif action == 'delete':
                from app import db
                db.session.delete(content)
                count += 1
        
        from app import db
        db.session.commit()
        
        action_names = {
            'publish': '发布',
            'draft': '设为草稿',
            'feature': '设为精选',
            'delete': '删除'
        }
        
        return jsonify({
            'success': True,
            'message': f'成功{action_names.get(action, "处理")}了 {count} 项内容'
        })
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'success': False, 'message': f'批量操作失败：{str(e)}'}), 500


@bp.route('/api/content/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_content(id):
    """删除内容"""
    content = Content.query.get_or_404(id)
    
    try:
        # 删除关联的图片文件
        if content.featured_image:
            image_path = os.path.join(
                current_app.static_folder,
                content.featured_image.lstrip('/static/')
            )
            if os.path.exists(image_path):
                os.remove(image_path)
        
        from app import db
        db.session.delete(content)
        db.session.commit()
        return jsonify({'success': True, 'message': '内容删除成功'})
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败：{str(e)}'}), 500


@bp.route('/project/<int:id>/duplicate')
@login_required
@admin_required
def duplicate_project(id):
    """复制项目"""
    original = Project.query.get_or_404(id)
    
    try:
        # 创建副本
        duplicate = Project(
            title=f"{original.title} - 副本",
            subtitle=original.subtitle,
            description=original.description,
            category=original.category,
            features=original.features,
            challenges=original.challenges,
            metrics=original.metrics,
            tech_stack=original.tech_stack,
            demo_url=None,  # 清空链接避免冲突
            github_url=None,
            documentation_url=None,
            start_date=original.start_date,
            completion_date=None,  # 新项目未完成
            duration_months=original.duration_months,
            team_size=original.team_size,
            status='规划中',  # 重置状态
            priority=original.priority,
            is_public=False,  # 默认私密
            is_published=False,  # 默认未发布
            is_featured=False,  # 不复制精选状态
            allow_inquiries=original.allow_inquiries
        )
        
        # 复制标签
        if original.tags:
            tag_names = [tag.name for tag in original.tags]
            duplicate.update_tags(tag_names)
        
        # 自动生成新的slug
        duplicate.generate_slug()
        
        from app import db
        db.session.add(duplicate)
        db.session.commit()
        
        flash('项目复制成功！', 'success')
        return redirect(url_for('admin.project_edit', id=duplicate.id))
        
    except Exception as e:
        from app import db
        db.session.rollback()
        flash(f'复制失败：{str(e)}', 'error')
        return redirect(url_for('admin.project_list'))


@bp.route('/api/project/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_project(id):
    """删除项目"""
    project = Project.query.get_or_404(id)
    
    try:
        # 删除关联的图片文件
        if project.featured_image:
            from app.utils.media_manager import MediaManager
            media_manager = MediaManager()
            try:
                media_manager.delete_image(project.featured_image)
            except:
                pass  # 忽略删除错误
        
        from app import db
        db.session.delete(project)
        db.session.commit()
        return jsonify({'success': True, 'message': '项目删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败：{str(e)}'}), 500


@bp.route('/project/bulk-<action>', methods=['POST'])
@login_required
@admin_required
def bulk_project_action(action):
    """批量操作项目"""
    project_ids = request.form.getlist('project_ids')
    if not project_ids:
        return jsonify({'success': False, 'message': '没有选择项目'}), 400
    
    try:
        projects = Project.query.filter(Project.id.in_(project_ids)).all()
        count = 0
        
        for project in projects:
            if action == 'publish':
                project.is_published = True
                project.status = '已完成' if project.status == '规划中' else project.status
                count += 1
            elif action == 'unpublish':
                project.is_published = False
                count += 1
            elif action == 'feature':
                project.is_featured = True
                count += 1
            elif action == 'unfeature':
                project.is_featured = False
                count += 1
            elif action == 'archive':
                project.status = '已暂停'
                project.is_published = False
                count += 1
            elif action == 'delete':
                # 删除关联图片
                if project.featured_image:
                    from app.utils.media_manager import MediaManager
                    media_manager = MediaManager()
                    try:
                        media_manager.delete_image(project.featured_image)
                    except:
                        pass
                from app import db
                db.session.delete(project)
                count += 1
        
        from app import db
        db.session.commit()
        
        action_names = {
            'publish': '发布',
            'unpublish': '取消发布',
            'feature': '设为精选',
            'unfeature': '取消精选',
            'archive': '归档',
            'delete': '删除'
        }
        
        return jsonify({
            'success': True,
            'message': f'成功{action_names.get(action, "处理")}了 {count} 个项目'
        })
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'success': False, 'message': f'批量操作失败：{str(e)}'}), 500


# 📂 媒体管理
@bp.route('/media')
@login_required
@admin_required
def media_manager():
    """媒体文件管理器"""
    media_manager = MediaManager()
    
    # 获取存储统计
    stats = media_manager.get_storage_stats()
    
    # 获取文件夹结构
    folder_structure = media_manager.get_folder_structure()
    
    return render_template('admin/media_manager.html',
                         stats=stats,
                         folder_structure=folder_structure)


@bp.route('/media/stats')
@login_required
@admin_required
def media_stats():
    """获取媒体存储统计"""
    media_manager = MediaManager()
    stats = media_manager.get_storage_stats()
    
    return jsonify({
        'success': True,
        'stats': stats
    })


@bp.route('/media/organize', methods=['POST'])
@login_required
@admin_required
def organize_media():
    """整理媒体文件"""
    media_manager = MediaManager()
    result = media_manager.organize_files()
    
    if result['success']:
        flash(f'文件整理完成！{result["message"]}', 'success')
    else:
        flash(f'文件整理失败：{result["message"]}', 'error')
    
    return jsonify(result)


@bp.route('/media/cleanup', methods=['POST'])
@login_required
@admin_required
def cleanup_media():
    """清理旧文件"""
    days = request.form.get('days', 30, type=int)
    dry_run = request.form.get('dry_run', False, type=bool)
    
    media_manager = MediaManager()
    result = media_manager.cleanup_old_files(days=days, dry_run=dry_run)
    
    if result['success']:
        if dry_run:
            message = f'预览清理结果：将清理 {result["cleaned_count"]} 个文件，节省 {result["size_saved_mb"]} MB'
        else:
            message = f'清理完成！清理了 {result["cleaned_count"]} 个文件，节省了 {result["size_saved_mb"]} MB'
        flash(message, 'success')
    else:
        flash(f'清理失败：{result["message"]}', 'error')
    
    return jsonify(result)


@bp.route('/media/optimize', methods=['POST'])
@login_required
@admin_required
def optimize_media():
    """批量优化图片"""
    media_manager = MediaManager()
    result = media_manager.optimize_all_images()
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f'优化失败：{result["message"]}', 'error')
    
    return jsonify(result)


@bp.route('/media/search')
@login_required
@admin_required
def search_media():
    """搜索媒体文件"""
    query = request.args.get('query', '')
    file_type = request.args.get('type', None)
    
    if not query:
        return jsonify({'success': False, 'message': '搜索关键词不能为空'}), 400
    
    media_manager = MediaManager()
    result = media_manager.search_files(query, file_type)
    
    return jsonify(result)


# 🔍 SEO优化管理
@bp.route('/content/<int:id>/seo-analysis')
@login_required
@admin_required
def content_seo_analysis(id):
    """内容SEO分析"""
    content = Content.query.get_or_404(id)
    
    # 获取完整的SEO分析
    seo_analysis = content.get_full_seo_analysis()
    
    # 获取slug变体建议
    slug_variations = content.get_slug_variations()
    
    # 分析slug质量
    slug_quality = content.analyze_slug_quality()
    
    return render_template('admin/seo_analysis.html',
                         content=content,
                         seo_analysis=seo_analysis,
                         slug_variations=slug_variations,
                         slug_quality=slug_quality)


@bp.route('/api/content/<int:id>/auto-seo', methods=['POST'])
@login_required
@admin_required
def auto_optimize_seo(id):
    """自动SEO优化"""
    content = Content.query.get_or_404(id)
    
    try:
        # 执行自动SEO优化
        optimizations = content.auto_optimize_seo()
        
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'SEO自动优化完成',
            'optimizations': optimizations,
            'new_score': content.seo_score
        })
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'SEO优化失败：{str(e)}'
        }), 500


@bp.route('/api/content/<int:id>/generate-slug', methods=['POST'])
@login_required
@admin_required
def regenerate_slug(id):
    """重新生成URL标识"""
    content = Content.query.get_or_404(id)
    
    try:
        force_regenerate = request.form.get('force', False, type=bool)
        
        # 重新生成slug
        content.generate_slug(force_regenerate=force_regenerate)
        
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'URL标识生成成功',
            'new_slug': content.slug
        })
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'URL标识生成失败：{str(e)}'
        }), 500


@bp.route('/api/content/<int:id>/generate-summary', methods=['POST'])
@login_required
@admin_required
def regenerate_summary(id):
    """重新生成内容摘要"""
    content = Content.query.get_or_404(id)
    
    try:
        length = request.form.get('length', 150, type=int)
        force_regenerate = request.form.get('force', False, type=bool)
        
        # 重新生成摘要
        new_summary = content.generate_auto_summary(length=length, force_regenerate=force_regenerate)
        
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '摘要生成成功',
            'new_summary': new_summary
        })
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'摘要生成失败：{str(e)}'
        }), 500


@bp.route('/api/content/<int:id>/generate-keywords', methods=['POST'])
@login_required
@admin_required
def generate_keywords(id):
    """生成SEO关键词"""
    content = Content.query.get_or_404(id)
    
    try:
        max_keywords = request.form.get('max_keywords', 10, type=int)
        
        # 生成关键词
        keywords = content.generate_seo_keywords(max_keywords=max_keywords)
        
        # 更新到content
        if keywords and not content.seo_keywords:
            content.seo_keywords = keywords
        
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'SEO关键词生成成功',
            'keywords': keywords
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'关键词生成失败：{str(e)}'
        }), 500


@bp.route('/seo/sitemap')
@login_required
@admin_required
def seo_sitemap_manager():
    """站点地图管理"""
    # 获取所有已发布的内容
    published_content = Content.query.filter_by(is_published=True, sitemap=True).all()
    
    # 生成站点地图条目
    sitemap_entries = []
    for content in published_content:
        entry = content.get_sitemap_entry()
        entry['content_id'] = content.id
        entry['title'] = content.title
        sitemap_entries.append(entry)
    
    # 统计信息
    stats = {
        'total_entries': len(sitemap_entries),
        'last_updated': max([content.updated_at for content in published_content]) if published_content else None,
        'categories': {}
    }
    
    # 按分类统计
    for content in published_content:
        category = content.category
        if category not in stats['categories']:
            stats['categories'][category] = 0
        stats['categories'][category] += 1
    
    return render_template('admin/sitemap_manager.html',
                         sitemap_entries=sitemap_entries,
                         stats=stats)


@bp.route('/api/seo/generate-sitemap', methods=['POST'])
@login_required
@admin_required
def generate_sitemap():
    """生成XML站点地图"""
    try:
        from xml.etree.ElementTree import Element, SubElement, tostring
        from datetime import datetime
        
        # 创建XML根元素
        urlset = Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        # 获取所有需要包含在站点地图中的内容
        published_content = Content.query.filter_by(is_published=True, sitemap=True).all()
        
        for content in published_content:
            url_element = SubElement(urlset, 'url')
            
            # URL
            loc = SubElement(url_element, 'loc')
            loc.text = content.get_url()
            
            # 最后修改时间
            if content.updated_at:
                lastmod = SubElement(url_element, 'lastmod')
                lastmod.text = content.updated_at.strftime('%Y-%m-%d')
            
            # 获取站点地图条目信息
            entry = content.get_sitemap_entry()
            
            # 更新频率
            changefreq = SubElement(url_element, 'changefreq')
            changefreq.text = entry['changefreq']
            
            # 优先级
            priority = SubElement(url_element, 'priority')
            priority.text = str(entry['priority'])
        
        # 转换为字符串
        xml_string = tostring(urlset, encoding='unicode')
        
        # 添加XML声明
        sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_string
        
        # 保存到文件
        sitemap_path = os.path.join(current_app.static_folder, 'sitemap.xml')
        with open(sitemap_path, 'w', encoding='utf-8') as f:
            f.write(sitemap_xml)
        
        return jsonify({
            'success': True,
            'message': '站点地图生成成功',
            'entries_count': len(published_content),
            'sitemap_url': '/static/sitemap.xml'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'站点地图生成失败：{str(e)}'
        }), 500


@bp.route('/seo/bulk-optimize', methods=['GET', 'POST'])
@login_required
@admin_required
def bulk_seo_optimize():
    """批量SEO优化"""
    if request.method == 'GET':
        # 获取需要优化的内容统计
        contents = Content.query.all()
        stats = {
            'total': len(contents),
            'no_slug': len([c for c in contents if not c.slug]),
            'no_summary': len([c for c in contents if not c.summary]),
            'no_meta_title': len([c for c in contents if not c.meta_title]),
            'no_meta_description': len([c for c in contents if not c.meta_description]),
            'low_seo_score': len([c for c in contents if (c.seo_score or 0) < 70])
        }
        
        return render_template('admin/bulk_seo_optimize.html', stats=stats)
    
    # POST 请求 - 执行批量优化
    try:
        optimization_types = request.form.getlist('optimizations')
        target_content = request.form.get('target', 'all')  # all, published, drafts
        
        # 构建查询
        query = Content.query
        if target_content == 'published':
            query = query.filter_by(is_published=True)
        elif target_content == 'drafts':
            query = query.filter_by(is_published=False)
        
        contents = query.all()
        
        results = {
            'processed': 0,
            'optimizations': {},
            'errors': []
        }
        
        for content in contents:
            try:
                content_optimizations = []
                
                # 生成slug
                if 'generate_slug' in optimization_types and not content.slug:
                    content.generate_slug()
                    content_optimizations.append('生成URL标识')
                
                # 生成摘要
                if 'generate_summary' in optimization_types and not content.summary:
                    content.generate_auto_summary()
                    content_optimizations.append('生成摘要')
                
                # 生成meta标题
                if 'generate_meta_title' in optimization_types and not content.meta_title:
                    content.meta_title = content.title[:60]
                    content_optimizations.append('生成页面标题')
                
                # 生成meta描述
                if 'generate_meta_description' in optimization_types and not content.meta_description:
                    if content.summary:
                        content.meta_description = content.summary[:160]
                        content_optimizations.append('生成页面描述')
                
                # 计算SEO评分
                if 'calculate_seo_score' in optimization_types:
                    content.calculate_seo_score()
                    content_optimizations.append('更新SEO评分')
                
                # 生成关键词
                if 'generate_keywords' in optimization_types and not content.seo_keywords:
                    keywords = content.generate_seo_keywords()
                    if keywords:
                        content.seo_keywords = keywords
                        content_optimizations.append('生成SEO关键词')
                
                if content_optimizations:
                    results['optimizations'][content.id] = {
                        'title': content.title,
                        'optimizations': content_optimizations
                    }
                    results['processed'] += 1
                    
            except Exception as e:
                results['errors'].append({
                    'content_id': content.id,
                    'title': content.title,
                    'error': str(e)
                })
        
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'批量优化完成，处理了 {results["processed"]} 项内容',
            'results': results
        })
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'批量优化失败：{str(e)}'
        }), 500