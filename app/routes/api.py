"""
🔌 API路由蓝图
RESTful API接口和AJAX端点
"""
from flask import Blueprint, request, jsonify, current_app
from app.models import Content, Project, ProjectInquiry, Tag
from app.forms import ProjectInquiryForm
from app.utils.email_utils import send_inquiry_notification

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
            client_name=form.client_name.data,
            client_email=form.client_email.data,
            client_phone=form.client_phone.data,
            project_type=form.project_type.data,
            description=form.description.data,
            budget_range=form.budget_range.data,
            timeline=form.timeline.data,
            status='待处理'
        )
        
        try:
            from app import db
            db.session.add(inquiry)
            db.session.commit()
            
            # 发送邮件通知 (异步)
            try:
                send_inquiry_notification(inquiry)
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