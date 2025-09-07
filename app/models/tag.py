"""
🏷️ 标签模型 - 智能标签系统
📊 data-scientist 设计的多维度标签管理
"""
from datetime import datetime
from app import db
from sqlalchemy import func


class Tag(db.Model):
    """
    🏷️ 标签模型 - 统一标签管理系统
    
    支持多种标签类型：
    - 技术标签: Python, Flask, React, JavaScript
    - 创意标签: 3D打印, 平面设计, 钩织, 建模
    - 生活标签: 钓鱼, 旅行, 摄影, 思考
    - 行业标签: AI, 前端, 后端, 设计
    """
    __tablename__ = 'tag'
    
    # 🆔 基础字段
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    slug = db.Column(db.String(100), unique=True, index=True)
    
    # 📂 分类字段
    category = db.Column(db.String(50), nullable=False, index=True)
    # 分类: '技术', '创意', '生活', '行业', '通用'
    
    # 🎨 显示字段
    color = db.Column(db.String(20), default='#6c757d')  # 标签颜色
    icon = db.Column(db.String(50))  # 图标类名 (可选)
    description = db.Column(db.String(200))  # 标签描述
    
    # 📊 统计字段
    usage_count = db.Column(db.Integer, default=0, index=True)  # 使用次数
    
    # ⏰ 时间字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 🔍 SEO字段
    seo_description = db.Column(db.String(300))  # 标签页面SEO描述
    
    def __repr__(self):
        return f'<Tag {self.name}>'
    
    def generate_slug(self):
        """生成URL友好的slug"""
        if not self.slug:
            import re
            from unidecode import unidecode
            
            slug = unidecode(self.name).lower()
            slug = re.sub(r'[^a-z0-9]+', '-', slug)
            slug = slug.strip('-')
            
            # 确保唯一性
            original_slug = slug
            counter = 1
            while Tag.query.filter_by(slug=slug).first():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            self.slug = slug
    
    def get_url(self):
        """获取标签页面URL"""
        from flask import url_for
        return url_for('main.tag_view', tag_name=self.name)
    
    def increment_usage(self):
        """增加使用次数"""
        self.usage_count = (self.usage_count or 0) + 1
        self.updated_at = datetime.utcnow()
    
    def get_related_tags(self, limit=5):
        """获取相关标签 (基于共同出现的内容)"""
        from app.models.content import content_tags, Content
        
        # 查找与当前标签一起出现的其他标签
        related_query = db.session.query(Tag, func.count(content_tags.c.content_id).label('co_occurrence'))\
                                 .join(content_tags, Tag.id == content_tags.c.tag_id)\
                                 .join(content_tags.alias(), content_tags.c.content_id == content_tags.alias().c.content_id)\
                                 .join(Tag.alias(), content_tags.alias().c.tag_id == Tag.alias().id)\
                                 .filter(Tag.alias().id == self.id, Tag.id != self.id)\
                                 .group_by(Tag.id)\
                                 .order_by(func.count(content_tags.c.content_id).desc())\
                                 .limit(limit)
        
        return [result[0] for result in related_query.all()]
    
    @staticmethod
    def get_popular_tags(limit=20, category=None):
        """获取热门标签"""
        query = Tag.query.filter(Tag.usage_count > 0)
        
        if category:
            query = query.filter_by(category=category)
        
        return query.order_by(Tag.usage_count.desc()).limit(limit).all()
    
    @staticmethod
    def get_tags_by_category(category, limit=None):
        """按分类获取标签"""
        query = Tag.query.filter_by(category=category)\
                        .order_by(Tag.usage_count.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_programming_languages():
        """获取编程语言标签"""
        programming_langs = [
            'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 
            'PHP', 'Ruby', 'Go', 'Rust', 'Swift', 'Kotlin', 'Scala',
            'HTML', 'CSS', 'SQL', 'Shell', 'PowerShell'
        ]
        
        return Tag.query.filter(Tag.name.in_(programming_langs))\
                       .order_by(Tag.usage_count.desc()).all()
    
    @staticmethod
    def get_tech_tags(limit=None):
        """获取技术类标签"""
        query = Tag.query.filter_by(category='技术')\
                        .order_by(Tag.usage_count.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_creative_tags(limit=None):
        """获取创意类标签"""
        query = Tag.query.filter_by(category='创意')\
                        .order_by(Tag.usage_count.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def search_tags(query_text, limit=10):
        """搜索标签"""
        return Tag.query.filter(Tag.name.contains(query_text))\
                        .order_by(Tag.usage_count.desc())\
                        .limit(limit).all()
    
    @staticmethod
    def create_or_get_tag(name, category='通用', color=None):
        """创建或获取标签"""
        tag = Tag.query.filter_by(name=name).first()
        
        if not tag:
            # 根据分类设置默认颜色
            if not color:
                color_mapping = {
                    '技术': '#007bff',
                    '创意': '#198754', 
                    '生活': '#fd7e14',
                    '行业': '#6c757d',
                    '通用': '#6c757d'
                }
                color = color_mapping.get(category, '#6c757d')
            
            tag = Tag(name=name, category=category, color=color)
            tag.generate_slug()
            db.session.add(tag)
            db.session.flush()  # 确保获得ID
        
        return tag
    
    @staticmethod
    def get_tag_cloud_data(limit=50):
        """获取标签云数据"""
        tags = Tag.get_popular_tags(limit=limit)
        
        if not tags:
            return []
        
        # 计算权重 (基于使用次数)
        max_count = max(tag.usage_count for tag in tags)
        min_count = min(tag.usage_count for tag in tags)
        count_range = max_count - min_count if max_count > min_count else 1
        
        tag_cloud = []
        for tag in tags:
            # 计算相对权重 (1-5)
            if count_range > 0:
                weight = 1 + 4 * (tag.usage_count - min_count) / count_range
            else:
                weight = 3
            
            tag_cloud.append({
                'name': tag.name,
                'count': tag.usage_count,
                'weight': round(weight, 1),
                'color': tag.color,
                'url': tag.get_url(),
                'category': tag.category
            })
        
        return tag_cloud
    
    @classmethod
    def get_category_stats(cls):
        """获取标签分类统计"""
        stats = db.session.query(
            cls.category,
            func.count(cls.id).label('tag_count'),
            func.sum(cls.usage_count).label('total_usage')
        ).group_by(cls.category).all()
        
        return [
            {
                'category': stat.category,
                'tag_count': stat.tag_count,
                'total_usage': stat.total_usage or 0
            }
            for stat in stats
        ]
    
    @classmethod
    def cleanup_unused_tags(cls):
        """清理未使用的标签"""
        unused_tags = cls.query.filter_by(usage_count=0).all()
        
        for tag in unused_tags:
            db.session.delete(tag)
        
        db.session.commit()
        return len(unused_tags)
    
    @classmethod
    def update_usage_counts(cls):
        """更新所有标签的使用次数 (维护任务)"""
        from app.models.content import content_tags
        
        # 重新计算所有标签的使用次数
        usage_stats = db.session.query(
            content_tags.c.tag_id,
            func.count(content_tags.c.content_id).label('count')
        ).group_by(content_tags.c.tag_id).all()
        
        # 重置所有标签使用次数
        db.session.query(cls).update({'usage_count': 0})
        
        # 更新计算出的使用次数
        for stat in usage_stats:
            tag = cls.query.get(stat.tag_id)
            if tag:
                tag.usage_count = stat.count
        
        db.session.commit()