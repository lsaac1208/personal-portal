"""
🔷 backend-architect 设计的Flask应用工厂
使用应用工厂模式，支持多环境配置和扩展注册
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_caching import Cache
from config import config

# 🔧 扩展实例化 (延迟初始化模式)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
cache = Cache()


def create_app(config_name='default'):
    """
    🏗️ Flask应用工厂函数
    
    Args:
        config_name: 配置环境名称 ('development', 'production', 'testing')
        
    Returns:
        Flask: 配置好的Flask应用实例
    """
    app = Flask(__name__)
    
    # 📋 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 🔧 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    cache.init_app(app)
    
    # 👤 登录管理器配置
    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'
    login_manager.login_message = '请登录以访问此页面。'
    login_manager.login_message_category = 'info'
    
    # 📱 注册蓝图
    register_blueprints(app)
    
    # 🎨 注册模板上下文处理器
    register_template_context(app)
    
    # 🆕 注册GitHub集成模板过滤器
    register_github_template_filters(app)
    
    # 🔧 注册错误处理器
    register_error_handlers(app)
    
    # ⚡ 注册Shell上下文处理器 (开发环境)
    register_shell_context(app)
    
    return app


def register_blueprints(app):
    """📱 注册所有蓝图"""
    from app.routes import main, content, admin, api, crm
    
    # 主要路由蓝图
    app.register_blueprint(main.bp)
    app.register_blueprint(content.bp, url_prefix='/content')
    app.register_blueprint(admin.bp, url_prefix='/admin')
    app.register_blueprint(api.bp, url_prefix='/api')
    app.register_blueprint(crm.bp, url_prefix='/crm')


def register_template_context(app):
    """🎨 注册模板全局上下文"""
    @app.context_processor
    def inject_site_config():
        """注入网站配置到所有模板"""
        return {
            'site_name': app.config.get('SITE_NAME'),
            'site_description': app.config.get('SITE_DESCRIPTION'),
            'site_author': app.config.get('SITE_AUTHOR')
        }
    
    @app.template_filter('markdown')
    def markdown_filter(text):
        """Markdown模板过滤器"""
        from app.utils.content_utils import render_markdown
        return render_markdown(text)
    
    @app.template_global()
    def render_markdown(text):
        """全局Markdown渲染函数"""
        from app.utils.content_utils import render_markdown as _render_markdown
        return _render_markdown(text)
    
    @app.template_global()
    def moment(datetime_obj):
        """时间处理全局函数"""
        if not datetime_obj:
            return None
        
        class MomentJS:
            def __init__(self, dt):
                self.dt = dt
                
            def format(self, fmt):
                """格式化日期"""
                if not self.dt:
                    return ""
                    
                # 简化的格式映射
                format_map = {
                    'YYYY年MM月DD日': '%Y年%m月%d日',
                    'YYYY年MM月': '%Y年%m月',
                    'MM月DD日': '%m月%d日',
                    'YYYY-MM-DD': '%Y-%m-%d',
                    'YYYY-MM': '%Y-%m',
                    'MM-DD': '%m-%d',
                    'HH:mm': '%H:%M',
                    'MM-DD HH:mm': '%m-%d %H:%M',
                    'YYYY-MM-DD HH:mm': '%Y-%m-%d %H:%M',
                    'YYYY-MM-DD HH:mm:ss': '%Y-%m-%d %H:%M:%S'
                }
                
                python_fmt = format_map.get(fmt, fmt)
                try:
                    return self.dt.strftime(python_fmt)
                except:
                    return str(self.dt)
                    
            def fromNow(self):
                """相对时间"""
                from datetime import datetime
                now = datetime.utcnow()
                diff = now - self.dt
                
                if diff.days > 0:
                    return f"{diff.days}天前"
                elif diff.seconds > 3600:
                    hours = diff.seconds // 3600
                    return f"{hours}小时前"
                elif diff.seconds > 60:
                    minutes = diff.seconds // 60
                    return f"{minutes}分钟前"
                else:
                    return "刚刚"
        
        return MomentJS(datetime_obj)
    
    @app.template_global()
    def get_category_emoji(category):
        """获取分类对应的emoji"""
        emoji_map = {
            '技术': '💻',
            '观察': '👀',
            '生活': '🌊',
            '创作': '🎨',
            '代码': '💻',
            '项目': '💼'
        }
        return emoji_map.get(category, '📝')
    
    @app.template_global()
    def estimate_reading_time(content):
        """估算阅读时间（分钟）"""
        if not content:
            return 1
        
        # 简化的中文阅读速度估算：300字/分钟
        import re
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', content)  # 移除标点符号
        char_count = len(text)
        reading_time = max(1, round(char_count / 300))
        return reading_time
    
    @app.template_global()
    def count_words(content):
        """统计文字数量"""
        from app.utils.content_utils import count_words as _count_words
        return _count_words(content)
    
    @app.template_global()
    def generate_toc(content):
        """生成文章目录"""
        from app.utils.content_utils import generate_toc as _generate_toc
        return _generate_toc(content)


def register_error_handlers(app):
    """🚨 注册错误处理器"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        from flask import render_template, flash
        flash('上传文件过大，请选择小于16MB的文件。', 'error')
        return render_template('errors/413.html'), 413


def register_github_template_filters(app):
    """🐙 注册GitHub集成模板过滤器"""
    from app.utils.template_filters import register_template_filters
    register_template_filters(app)


def register_shell_context(app):
    """⚡ 注册Shell上下文 (方便调试)"""
    @app.shell_context_processor
    def make_shell_context():
        from app.models import Content, Project, Tag, ProjectInquiry
        return {
            'db': db,
            'Content': Content,
            'Project': Project, 
            'Tag': Tag,
            'ProjectInquiry': ProjectInquiry
        }