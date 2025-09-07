"""
👤 用户模型 - 管理员认证系统
📊 data-scientist 设计的简化用户管理
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class User(UserMixin, db.Model):
    """
    👤 用户模型 - 管理员用户系统
    
    简化设计，主要用于：
    - 管理员登录认证
    - 内容管理权限控制
    - 后台操作日志记录
    """
    __tablename__ = 'user'
    
    # 🆔 基础字段
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    
    # 🔒 认证字段
    password_hash = db.Column(db.String(255), nullable=False)
    
    # 👤 个人信息
    full_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(500))
    
    # 🔑 权限字段
    is_admin = db.Column(db.Boolean, default=False, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # ⏰ 时间字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime)
    
    # 📊 统计字段
    login_count = db.Column(db.Integer, default=0)
    
    # 🔍 联系方式 (可选)
    website = db.Column(db.String(200))
    github = db.Column(db.String(100))
    twitter = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_seen(self):
        """更新最后活动时间"""
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()
    
    def record_login(self):
        """记录登录"""
        self.last_login_at = datetime.utcnow()
        self.login_count = (self.login_count or 0) + 1
        self.update_last_seen()
    
    def get_avatar_url(self, size=80):
        """获取头像URL"""
        if self.avatar_url:
            return self.avatar_url
        
        # 使用Gravatar作为默认头像
        import hashlib
        email_hash = hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon'
    
    def get_social_links(self):
        """获取社交媒体链接"""
        links = []
        
        if self.website:
            links.append({
                'name': '网站',
                'url': self.website,
                'icon': 'globe'
            })
        
        if self.github:
            github_url = f"https://github.com/{self.github}" if not self.github.startswith('http') else self.github
            links.append({
                'name': 'GitHub',
                'url': github_url,
                'icon': 'github'
            })
        
        if self.twitter:
            twitter_url = f"https://twitter.com/{self.twitter}" if not self.twitter.startswith('http') else self.twitter
            links.append({
                'name': 'Twitter',
                'url': twitter_url,
                'icon': 'twitter'
            })
        
        return links
    
    def can_edit_content(self):
        """检查是否可以编辑内容"""
        return self.is_admin and self.is_active
    
    def can_manage_inquiries(self):
        """检查是否可以管理咨询"""
        return self.is_admin and self.is_active
    
    @staticmethod
    def get_admin_users():
        """获取所有管理员用户"""
        return User.query.filter_by(is_admin=True, is_active=True).all()
    
    @staticmethod
    def create_admin_user(username, email, password, full_name=None):
        """创建管理员用户"""
        # 检查用户是否已存在
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            raise ValueError("用户名或邮箱已存在")
        
        # 创建新用户
        user = User(
            username=username,
            email=email,
            full_name=full_name or username,
            is_admin=True,
            is_active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @classmethod
    def get_user_stats(cls):
        """获取用户统计"""
        from sqlalchemy import func
        
        total_users = cls.query.count()
        admin_users = cls.query.filter_by(is_admin=True).count()
        active_users = cls.query.filter_by(is_active=True).count()
        
        # 最近活跃用户 (30天内)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_active = cls.query.filter(
            cls.last_seen >= thirty_days_ago
        ).count()
        
        return {
            'total': total_users,
            'admins': admin_users,
            'active': active_users,
            'recent_active': recent_active
        }


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login用户加载器"""
    return User.query.get(int(user_id))