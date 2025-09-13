"""
🔌 API路由蓝图
RESTful API接口和AJAX端点
"""
from flask import Blueprint, request, jsonify, current_app, flash, redirect, url_for
from app.models import Content, Project, ProjectInquiry, Tag
from app.forms import ProjectInquiryForm, NewsletterForm
from app.utils.email_utils import send_inquiry_notification, send_newsletter

bp = Blueprint('api', __name__)


# 📞 项目咨询API
@bp.route('/inquiry', methods=['POST'])
def submit_inquiry():
    """
    📝 提交项目咨询
    用于合作咨询表单的AJAX提交
    """
    form = ProjectInquiryForm()
    
    if form.validate_on_submit():
        # 创建咨询记录
        inquiry = ProjectInquiry(
            client_name=form.name.data,
            client_email=form.email.data,
            client_phone=form.phone.data,
            client_company=form.company.data,
            client_position=form.position.data,
            project_id=form.project_id.data if form.project_id.data else None,
            inquiry_type=form.inquiry_type.data,
            subject=form.subject.data,
            description=form.description.data,
            budget_range=form.budget_range.data,
            timeline=form.timeline.data,
            tech_requirements=form.preferred_tech.data,
            additional_info=form.additional_info.data,
            contact_preference=form.contact_preference.data,
            contact_time=form.contact_time.data,
            privacy_agreed=form.privacy_agreement.data,
            receive_updates=form.marketing_emails.data,
            status='新咨询'
        )
        
        try:
            from app import db
            db.session.add(inquiry)
            db.session.commit()
            
            # 发送邮件通知 (异步)
            try:
                from app.utils.email_utils import send_inquiry_notification, send_inquiry_confirmation
                # 发送管理员通知邮件
                send_inquiry_notification(inquiry)
                # 发送客户确认邮件
                send_inquiry_confirmation(inquiry)
            except Exception as e:
                current_app.logger.error(f'邮件发送失败: {str(e)}')
            
            return jsonify({
                'success': True,
                'message': '咨询提交成功！我会尽快与您联系。',
                'inquiry_id': inquiry.id
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'咨询提交失败: {str(e)}')
            return jsonify({
                'success': False,
                'message': '提交失败，请稍后重试。'
            }), 500
    
    # 表单验证失败
    errors = {}
    for field, field_errors in form.errors.items():
        errors[field] = field_errors
    
    return jsonify({
        'success': False,
        'message': '请检查表单信息',
        'errors': errors
    }), 400


# 🔍 搜索API
@bp.route('/search')
def search_api():
    """
    🔍 内容搜索API
    支持关键词搜索和分类筛选
    """
    query = request.args.get('q', '').strip()
    category = request.args.get('category', None)
    limit = min(request.args.get('limit', 10, type=int), 50)  # 最多50条
    
    if not query:
        return jsonify({
            'success': False,
            'message': '搜索关键词不能为空'
        }), 400
    
    try:
        # 搜索内容
        results = Content.search_content(query, category=category, limit=limit)
        
        # 格式化结果
        formatted_results = []
        for content in results:
            formatted_results.append({
                'id': content.id,
                'title': content.title,
                'category': content.category,
                'summary': content.get_summary(100),
                'url': content.get_url(),
                'created_at': content.created_at.isoformat(),
                'tags': [tag.name for tag in content.tags]
            })
        
        return jsonify({
            'success': True,
            'query': query,
            'results': formatted_results,
            'total': len(formatted_results)
        })
        
    except Exception as e:
        current_app.logger.error(f'搜索API错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': '搜索服务暂时不可用'
        }), 500


# 📊 统计API
@bp.route('/stats')
def stats_api():
    """
    📊 网站统计API
    返回各类内容的统计数据
    """
    try:
        stats = {
            'content': {
                'total': Content.query.filter_by(is_published=True).count(),
                'tech': Content.query.filter_by(category='技术', is_published=True).count(),
                'observation': Content.query.filter_by(category='观察', is_published=True).count(),
                'life': Content.query.filter_by(category='生活', is_published=True).count(),
                'creative': Content.query.filter_by(category='创作', is_published=True).count()
            },
            'projects': {
                'total': Project.query.filter_by(is_published=True).count(),
                'featured': Project.query.filter_by(is_featured=True).count()
            },
            'tags': {
                'total': Tag.query.count()
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        current_app.logger.error(f'统计API错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': '统计数据获取失败'
        }), 500


# 🏷️ 标签API
@bp.route('/tags')
def tags_api():
    """
    🏷️ 标签列表API
    返回标签云数据
    """
    try:
        category = request.args.get('category', None)
        limit = min(request.args.get('limit', 20, type=int), 100)
        
        if category:
            tags = Tag.get_tags_by_category(category, limit=limit)
        else:
            tags = Tag.get_popular_tags(limit=limit)
        
        tag_data = []
        for tag in tags:
            tag_data.append({
                'name': tag.name,
                'category': tag.category,
                'usage_count': tag.usage_count,
                'color': tag.color,
                'url': f"/tag/{tag.name}"
            })
        
        return jsonify({
            'success': True,
            'tags': tag_data
        })
        
    except Exception as e:
        current_app.logger.error(f'标签API错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': '标签数据获取失败'
        }), 500


# 📱 内容推荐API
@bp.route('/recommendations/<int:content_id>')
def recommendations_api(content_id):
    """
    🎯 内容推荐API
    基于当前内容推荐相关内容
    """
    try:
        current_content = Content.query.get_or_404(content_id)
        
        # 获取相关内容
        related_content = Content.get_related_content(current_content, limit=5)
        
        recommendations = []
        for content in related_content:
            recommendations.append({
                'id': content.id,
                'title': content.title,
                'category': content.category,
                'summary': content.get_summary(80),
                'url': content.get_url(),
                'tags': [tag.name for tag in content.tags[:3]]  # 只显示前3个标签
            })
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        current_app.logger.error(f'推荐API错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': '推荐数据获取失败'
        }), 500


# 📈 浏览统计API
@bp.route('/view/<int:content_id>', methods=['POST'])
def track_view(content_id):
    """
    📈 浏览量统计API
    用于统计内容浏览量 (防重复)
    """
    try:
        content = Content.query.get_or_404(content_id)
        
        # 简单防重复机制 (基于IP，实际项目可以用更复杂的方法)
        user_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        
        # 这里可以添加Redis缓存来记录IP访问记录，避免重复计数
        # 暂时简化处理
        content.view_count = (content.view_count or 0) + 1
        
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'view_count': content.view_count
        })
        
    except Exception as e:
        current_app.logger.error(f'浏览统计错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': '统计失败'
        }), 500


# 💬 简单的反馈API
@bp.route('/feedback', methods=['POST'])
def feedback_api():
    """
    💬 用户反馈API
    收集用户对网站的反馈意见
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('message'):
            return jsonify({
                'success': False,
                'message': '反馈内容不能为空'
            }), 400
        
        # 这里可以保存到数据库或发送邮件
        # 暂时记录到日志
        current_app.logger.info(f"用户反馈: {data.get('message')} | 来源: {request.remote_addr}")
        
        return jsonify({
            'success': True,
            'message': '感谢您的反馈！'
        })
        
    except Exception as e:
        current_app.logger.error(f'反馈API错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': '反馈提交失败'
        }), 500


# 📧 邮件订阅API
@bp.route('/newsletter-subscribe', methods=['POST'])
def newsletter_subscribe():
    """
    📧 邮件订阅
    用户订阅技术分享和项目更新
    """
    try:
        email = request.form.get('email')
        if not email:
            flash('请输入邮箱地址', 'error')
            return redirect(request.referrer or url_for('main.index'))
        
        # 简单邮箱格式验证
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('请输入有效的邮箱地址', 'error')
            return redirect(request.referrer or url_for('main.index'))
        
        # 这里应该存储到数据库，暂时只记录日志
        current_app.logger.info(f'新的邮件订阅: {email}')
        
        # 发送欢迎邮件
        try:
            newsletter_data = {
                'title': '欢迎订阅！',
                'content': '<h2>感谢您的订阅！</h2><p>您已成功订阅我们的技术分享和项目更新。我们将定期为您发送最新的技术文章、项目案例和行业洞察。</p><p>如果您有任何问题或建议，请随时联系我们。</p>'
            }
            send_newsletter(email, newsletter_data)
        except Exception as e:
            current_app.logger.error(f'欢迎邮件发送失败: {str(e)}')
        
        flash('订阅成功！欢迎邮件已发送到您的邮箱。', 'success')
        return redirect(request.referrer or url_for('main.index'))
        
    except Exception as e:
        current_app.logger.error(f'邮件订阅错误: {str(e)}')
        flash('订阅失败，请稍后重试。', 'error')
        return redirect(request.referrer or url_for('main.index'))


# 📧 取消订阅API
@bp.route('/unsubscribe', methods=['GET'])
def unsubscribe():
    """
    📧 取消邮件订阅
    用户取消邮件订阅
    """
    try:
        email = request.args.get('email')
        if email:
            # 这里应该从数据库中删除订阅记录
            current_app.logger.info(f'取消订阅: {email}')
            flash('已成功取消订阅。', 'info')
        else:
            flash('无效的取消订阅链接。', 'error')
        
        return redirect(url_for('main.index'))
        
    except Exception as e:
        current_app.logger.error(f'取消订阅错误: {str(e)}')
        flash('操作失败，请稍后重试。', 'error')
        return redirect(url_for('main.index'))