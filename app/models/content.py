"""
📝 内容模型 - 多元化内容管理核心
📊 data-scientist 设计的统一内容模型
支持：技术博客、行业观察、生活分享、创意作品、代码片段
"""
from datetime import datetime
from flask import url_for
from app import db
from sqlalchemy import or_

# 内容-标签多对多关联表
content_tags = db.Table('content_tags',
    db.Column('content_id', db.Integer, db.ForeignKey('content.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)


class Content(db.Model):
    """
    📄 内容模型 - 统一管理所有内容类型
    
    支持的内容类型：
    - 技术💻: 技术博客、教程、经验分享
    - 观察📰: 行业观察、新闻评论、趋势分析
    - 生活🌊: 个人生活、感悟、日常记录
    - 创作🎨: 创意作品、手工艺、设计作品
    - 代码💻: 代码片段、算法示例
    """
    __tablename__ = 'content'
    
    # 🆔 基础字段
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    slug = db.Column(db.String(200), unique=True, index=True)  # URL友好标识
    
    # 📝 内容字段
    content = db.Column(db.Text, nullable=False)  # Markdown原文
    content_html = db.Column(db.Text)  # 渲染后的HTML
    summary = db.Column(db.Text)  # 摘要/简介
    
    # 📂 分类字段
    category = db.Column(db.String(50), nullable=False, index=True)
    # 类别: '技术', '观察', '生活', '创作', '代码'
    
    # 📷 媒体字段
    featured_image = db.Column(db.String(500))  # 特色图片URL
    images = db.Column(db.JSON)  # 图片数组 ["url1", "url2"]
    attachments = db.Column(db.JSON)  # 附件数组 [{"name": "", "url": ""}]
    
    # 🔗 外部链接
    source_type = db.Column(db.String(20), default='原创')  # '原创', '转载'
    source_url = db.Column(db.String(500))  # 转载来源URL
    source_author = db.Column(db.String(100))  # 原作者
    
    # 📊 状态字段
    is_published = db.Column(db.Boolean, default=False, index=True)
    is_featured = db.Column(db.Boolean, default=False, index=True)  # 精选推荐
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)  # 预留点赞功能
    
    # ⏰ 时间字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, index=True)
    
    # 🔍 SEO字段
    seo_title = db.Column(db.String(200))  # SEO标题
    seo_description = db.Column(db.String(300))  # SEO描述
    seo_keywords = db.Column(db.String(500))  # SEO关键词
    
    # 🏷️ 关系字段
    tags = db.relationship('Tag', secondary=content_tags, lazy='subquery',
                          backref=db.backref('contents', lazy=True))
    
    def __repr__(self):
        return f'<Content {self.title}>'
    
    def generate_slug(self):
        """生成URL友好的slug"""
        if not self.slug:
            import re
            from unidecode import unidecode
            
            # 基于标题生成slug
            slug = unidecode(self.title).lower()
            slug = re.sub(r'[^a-z0-9]+', '-', slug)
            slug = slug.strip('-')
            
            # 确保唯一性
            original_slug = slug
            counter = 1
            while Content.query.filter_by(slug=slug).first():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            self.slug = slug
    
    def render_html(self):
        """渲染Markdown为HTML"""
        if not self.content:
            self.content_html = ''
            return
        
        import markdown
        from markdown.extensions import codehilite, toc, tables
        
        # Markdown扩展配置
        extensions = [
            'codehilite',  # 代码高亮
            'toc',  # 目录生成
            'tables',  # 表格支持
            'fenced_code',  # 围栏代码块
            'nl2br',  # 换行转换
        ]
        
        extension_configs = {
            'codehilite': {
                'css_class': 'highlight',
                'use_pygments': True,
                'pygments_style': 'github'
            },
            'toc': {
                'anchorlink': True
            }
        }
        
        md = markdown.Markdown(extensions=extensions, extension_configs=extension_configs)
        self.content_html = md.convert(self.content)
        
        # 生成摘要 (如果没有手动设置)
        if not self.summary:
            self.summary = self.generate_summary()
    
    def generate_summary(self, length=150):
        """生成内容摘要"""
        if not self.content:
            return ""
        
        import re
        # 移除Markdown标记
        text = re.sub(r'[#*`\[\]()_~]', '', self.content)
        text = re.sub(r'\n+', ' ', text)
        text = text.strip()
        
        if len(text) <= length:
            return text
        
        # 在合适的位置截断
        truncated = text[:length]
        last_space = truncated.rfind(' ')
        if last_space > length * 0.8:  # 如果最后一个空格位置合理
            truncated = truncated[:last_space]
        
        return truncated + '...'
    
    def get_url(self):
        """获取内容URL"""
        if self.slug:
            return url_for('content.detail', id=self.id, slug=self.slug)
        return url_for('content.detail', id=self.id)
    
    def get_summary(self, length=None):
        """获取摘要"""
        if self.summary:
            if length and len(self.summary) > length:
                return self.summary[:length] + '...'
            return self.summary
        return self.generate_summary(length or 150)
    
    def update_tags(self, tag_names):
        """更新内容标签"""
        from app.models.tag import Tag
        
        # 清除现有标签
        self.tags.clear()
        
        # 添加新标签
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name.strip()).first()
            if not tag:
                # 创建新标签
                tag = Tag(
                    name=tag_name.strip(),
                    category=self.get_tag_category(),
                    color=self.get_tag_color()
                )
                db.session.add(tag)
            
            # 增加标签使用次数
            tag.usage_count = (tag.usage_count or 0) + 1
            self.tags.append(tag)
    
    def get_tag_category(self):
        """根据内容类型确定标签分类"""
        category_mapping = {
            '技术': '技术',
            '代码': '技术', 
            '观察': '行业',
            '生活': '生活',
            '创作': '创意'
        }
        return category_mapping.get(self.category, '通用')
    
    def get_tag_color(self):
        """根据内容类型确定标签颜色"""
        color_mapping = {
            '技术': '#007bff',
            '代码': '#6610f2',
            '观察': '#6c757d', 
            '生活': '#fd7e14',
            '创作': '#198754'
        }
        return color_mapping.get(self.category, '#6c757d')
    
    @staticmethod
    def get_related_content(content, limit=5):
        """获取相关内容"""
        if not content.tags:
            # 如果没有标签，返回同类别的最新内容
            return Content.query.filter(
                Content.id != content.id,
                Content.category == content.category,
                Content.is_published == True
            ).order_by(Content.created_at.desc()).limit(limit).all()
        
        # 基于标签查找相关内容
        tag_ids = [tag.id for tag in content.tags]
        
        related = Content.query.join(content_tags).filter(
            content_tags.c.tag_id.in_(tag_ids),
            Content.id != content.id,
            Content.is_published == True
        ).group_by(Content.id).order_by(
            db.func.count(content_tags.c.tag_id).desc(),  # 按匹配标签数排序
            Content.created_at.desc()
        ).limit(limit).all()
        
        return related
    
    @staticmethod
    def search_content(query, category=None, limit=20):
        """搜索内容 (简化版全文搜索)"""
        # 构建基础查询
        base_query = Content.query.filter(Content.is_published == True)
        
        if category:
            base_query = base_query.filter(Content.category == category)
        
        # 分割搜索词
        keywords = query.split()
        search_conditions = []
        
        for keyword in keywords:
            # 搜索标题和内容
            search_conditions.append(
                or_(
                    Content.title.contains(keyword),
                    Content.content.contains(keyword),
                    Content.summary.contains(keyword)
                )
            )
        
        # 组合搜索条件
        if search_conditions:
            search_query = base_query.filter(or_(*search_conditions))
        else:
            search_query = base_query
        
        # 按相关性排序 (简化版：按更新时间)
        results = search_query.order_by(Content.updated_at.desc()).limit(limit).all()
        
        return results
    
    @staticmethod
    def get_featured_content(limit=3):
        """获取精选内容"""
        return Content.query.filter_by(is_published=True, is_featured=True)\
                          .order_by(Content.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_recent_content(limit=5, category=None):
        """获取最新内容"""
        query = Content.query.filter_by(is_published=True)
        
        if category:
            query = query.filter_by(category=category)
        
        return query.order_by(Content.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_popular_content(limit=10):
        """获取热门内容 (按浏览量)"""
        return Content.query.filter_by(is_published=True)\
                          .order_by(Content.view_count.desc())\
                          .limit(limit).all()
    
    @classmethod
    def get_category_stats(cls):
        """获取分类统计"""
        from sqlalchemy import func
        
        stats = db.session.query(
            cls.category,
            func.count(cls.id).label('count')
        ).filter_by(is_published=True).group_by(cls.category).all()
        
        return {stat.category: stat.count for stat in stats}