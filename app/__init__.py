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
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请登录以访问此页面。'
    login_manager.login_message_category = 'info'
    
    # 📱 注册蓝图
    register_blueprints(app)
    
    # 🎨 注册模板上下文处理器
    register_template_context(app)
    
    # 🔧 注册错误处理器
    register_error_handlers(app)
    
    # ⚡ 注册Shell上下文处理器 (开发环境)
    register_shell_context(app)
    
    return app


def register_blueprints(app):
    """📱 注册所有蓝图"""
    from app.routes import main, content, admin, api
    
    # 主要路由蓝图
    app.register_blueprint(main.bp)
    app.register_blueprint(content.bp, url_prefix='/content')
    app.register_blueprint(admin.bp, url_prefix='/admin')
    app.register_blueprint(api.bp, url_prefix='/api')


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