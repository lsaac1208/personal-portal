"""
📝 内容模型 - 多元化内容管理核心
📊 data-scientist 设计的统一内容模型
支持：技术博客、行业观察、生活分享、创意作品、代码片段
"""
from datetime import datetime
from flask import url_for, current_app
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
    meta_title = db.Column(db.String(200))  # 页面标题
    meta_description = db.Column(db.String(300))  # 页面描述
    
    # 📊 内容元数据
    reading_time = db.Column(db.Integer)  # 预计阅读时间(分钟)
    difficulty = db.Column(db.String(20), default='初级')  # 难度等级: 初级/中级/高级
    word_count = db.Column(db.Integer, default=0)  # 字数统计
    views = db.Column(db.Integer, default=0)  # 浏览量
    
    # 🔄 版本控制
    version = db.Column(db.Integer, default=1)  # 版本号
    revision_notes = db.Column(db.Text)  # 修订说明
    
    # 🗂️ 内容状态管理
    status = db.Column(db.String(20), default='草稿', index=True)  # '草稿', '已发布', '计划', '归档'
    priority = db.Column(db.String(20), default='普通')  # '低', '普通', '高', '紧急'
    
    # 🔒 访问控制
    indexable = db.Column(db.Boolean, default=True)  # 是否允许搜索引擎索引
    sitemap = db.Column(db.Boolean, default=True)  # 是否包含在站点地图中
    comments_enabled = db.Column(db.Boolean, default=True)  # 是否允许评论
    
    # 📱 社交媒体优化
    og_title = db.Column(db.String(200))  # Open Graph标题
    og_description = db.Column(db.String(300))  # Open Graph描述
    og_image = db.Column(db.String(500))  # Open Graph图片
    twitter_card = db.Column(db.String(20), default='summary')  # Twitter卡片类型
    
    # 📈 分析数据
    last_analyzed_at = db.Column(db.DateTime)  # 最后分析时间
    seo_score = db.Column(db.Integer, default=0)  # SEO评分 (0-100)
    readability_score = db.Column(db.Float)  # 可读性评分
    
    # 🏷️ 关系字段
    tags = db.relationship('Tag', secondary=content_tags, lazy='subquery',
                          backref=db.backref('contents', lazy=True))
    
    def __repr__(self):
        return f'<Content {self.title}>'
    
    def generate_slug(self, force_regenerate=False):
        """生成URL友好的slug"""
        if not self.slug or force_regenerate:
            try:
                from app.utils.slug_generator import SlugGenerator
                generator = SlugGenerator()
                
                # 生成基础slug
                base_slug = generator.generate_slug(
                    title=self.title,
                    max_length=60,
                    use_pinyin=True,
                    include_date=False
                )
                
                # 确保唯一性
                slug = self._ensure_unique_slug(base_slug)
                self.slug = slug
                
            except ImportError:
                # 降级处理：使用简单方法
                self._generate_simple_slug()
    
    def _ensure_unique_slug(self, base_slug):
        """确保slug唯一性"""
        if not Content.query.filter(Content.slug == base_slug, Content.id != self.id).first():
            return base_slug
        
        counter = 1
        while True:
            candidate_slug = f"{base_slug}-{counter}"
            if not Content.query.filter(Content.slug == candidate_slug, Content.id != self.id).first():
                return candidate_slug
            counter += 1
    
    def _generate_simple_slug(self):
        """简单的slug生成方法（降级处理）"""
        import re
        try:
            from unidecode import unidecode
            slug = unidecode(self.title).lower()
        except ImportError:
            slug = self.title.lower()
        
        slug = re.sub(r'[^a-z0-9\u4e00-\u9fff]+', '-', slug)
        slug = slug.strip('-')
        
        if not slug:
            slug = f"post-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        self.slug = self._ensure_unique_slug(slug)
    
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
                'pygments_style': 'default'
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
    
    def calculate_reading_time(self):
        """计算阅读时间 (假设每分钟200字)"""
        if not self.content:
            self.reading_time = 0
            return 0
        
        import re
        # 计算中文字符和英文单词
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', self.content))
        english_words = len(re.findall(r'[a-zA-Z]+', self.content))
        
        # 中文按字符计算，英文按单词计算
        total_chars = chinese_chars + english_words
        self.word_count = total_chars
        
        # 每分钟阅读200字符
        reading_time = max(1, round(total_chars / 200))
        self.reading_time = reading_time
        return reading_time
    
    def calculate_seo_score(self):
        """计算SEO评分"""
        try:
            from app.utils.seo_analyzer import SEOAnalyzer
            analyzer = SEOAnalyzer()
            
            # 构建内容URL
            content_url = self.get_url() if hasattr(self, 'get_url') else ''
            
            # 进行全面SEO分析
            analysis = analyzer.analyze_content(
                content=self.content or '',
                title=self.title or '',
                meta_description=self.meta_description or '',
                url=content_url
            )
            
            # 更新SEO评分
            self.seo_score = analysis['score']
            
            # 缓存分析结果到字段（如果有的话）
            if hasattr(self, 'seo_analysis'):
                import json
                self.seo_analysis = json.dumps(analysis, ensure_ascii=False)
            
            return self.seo_score
            
        except ImportError:
            # 降级处理：使用简单评分方法
            return self._calculate_simple_seo_score()
    
    def _calculate_simple_seo_score(self):
        """简单的SEO评分方法（降级处理）"""
        score = 0
        
        # 标题评分 (25分)
        if self.title:
            if 10 <= len(self.title) <= 60:
                score += 25
            elif 5 <= len(self.title) <= 80:
                score += 15
            else:
                score += 5
        
        # 描述评分 (20分)
        if self.meta_description:
            if 120 <= len(self.meta_description) <= 160:
                score += 20
            elif 80 <= len(self.meta_description) <= 200:
                score += 15
            else:
                score += 5
        
        # 内容长度评分 (15分)
        if self.word_count:
            if self.word_count >= 300:
                score += 15
            elif self.word_count >= 150:
                score += 10
            else:
                score += 5
        
        # 图片优化评分 (15分)
        if self.featured_image:
            score += 10
        if self.og_image:
            score += 5
        
        # 结构化数据评分 (10分)
        if self.tags:
            score += 5
        if self.category:
            score += 3
        
        # URL优化评分 (10分)
        if self.slug:
            if len(self.slug) <= 60 and '-' in self.slug:
                score += 10
            else:
                score += 5
        
        # 索引设置评分 (5分)
        if self.indexable and self.sitemap:
            score += 5
        
        self.seo_score = min(100, score)
        return self.seo_score
    
    def create_version_history(self, original_content):
        """创建版本历史记录"""
        # 这里可以扩展为独立的ContentVersion模型
        # 暂时使用简单的版本记录
        self.version = (self.version or 0) + 1
        
        # 记录主要变更
        changes = []
        if original_content.get('title') != self.title:
            changes.append('修改标题')
        if original_content.get('content') != self.content:
            changes.append('更新内容')
        if original_content.get('summary') != self.summary:
            changes.append('修改摘要')
        
        self.revision_notes = f"版本 {self.version}: {', '.join(changes)}" if changes else f"版本 {self.version}: 常规更新"
    
    def get_seo_analysis(self):
        """获取SEO分析结果"""
        analysis = {
            'score': self.seo_score or 0,
            'issues': [],
            'recommendations': []
        }
        
        # 标题分析
        if not self.title or len(self.title) < 10:
            analysis['issues'].append('标题过短，建议10-60字符')
            analysis['recommendations'].append('添加更具描述性的标题')
        elif len(self.title) > 60:
            analysis['issues'].append('标题过长，可能影响搜索显示')
            analysis['recommendations'].append('缩短标题至60字符以内')
        
        # 描述分析
        if not self.meta_description:
            analysis['issues'].append('缺少页面描述')
            analysis['recommendations'].append('添加120-160字符的页面描述')
        elif len(self.meta_description) < 120:
            analysis['issues'].append('页面描述过短')
            analysis['recommendations'].append('扩展描述至120-160字符')
        elif len(self.meta_description) > 160:
            analysis['issues'].append('页面描述过长')
            analysis['recommendations'].append('缩短描述至160字符以内')
        
        # 内容分析
        if not self.word_count or self.word_count < 300:
            analysis['issues'].append('内容长度不足')
            analysis['recommendations'].append('增加内容至300字符以上')
        
        # 图片分析
        if not self.featured_image:
            analysis['issues'].append('缺少特色图片')
            analysis['recommendations'].append('添加吸引人的特色图片')
        
        # 标签分析
        if not self.tags:
            analysis['issues'].append('缺少标签分类')
            analysis['recommendations'].append('添加相关标签以提高可发现性')
        
        return analysis
    
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
    
    def get_full_seo_analysis(self):
        """获取完整SEO分析"""
        try:
            from app.utils.seo_analyzer import SEOAnalyzer
            analyzer = SEOAnalyzer()
            
            content_url = self.get_url() if hasattr(self, 'get_url') else ''
            
            analysis = analyzer.analyze_content(
                content=self.content or '',
                title=self.title or '',
                meta_description=self.meta_description or '',
                url=content_url
            )
            
            return analysis
            
        except ImportError:
            return {
                'score': self.seo_score or 0,
                'issues': ['SEO分析器未可用'],
                'recommendations': ['安装SEO分析依赖包']
            }
    
    def generate_auto_summary(self, length=150, force_regenerate=False):
        """自动生成摘要"""
        if self.summary and not force_regenerate:
            return self.summary
        
        if not self.content:
            return ""
        
        try:
            from app.utils.seo_analyzer import SEOAnalyzer
            analyzer = SEOAnalyzer()
            
            # 使用SEO分析器的摘要生成功能
            summary = analyzer._extract_words(self.content)
            if summary:
                # 重新构建句子
                import re
                sentences = re.split(r'[。！？.!?]', self.content)
                sentences = [s.strip() for s in sentences if s.strip()]
                
                if sentences:
                    # 取前几句作为摘要
                    auto_summary = ''
                    for sentence in sentences:
                        if len(auto_summary + sentence) <= length:
                            auto_summary += sentence + '。'
                        else:
                            break
                    
                    if auto_summary:
                        if not self.summary or force_regenerate:
                            self.summary = auto_summary.rstrip('。')
                        return auto_summary.rstrip('。')
        
        except ImportError:
            pass
        
        # 降级处理
        return self.generate_summary(length)
    
    def generate_seo_keywords(self, max_keywords=10):
        """生成SEO关键词"""
        try:
            from app.utils.seo_analyzer import SEOAnalyzer
            analyzer = SEOAnalyzer()
            
            # 分析关键词
            full_text = f"{self.title} {self.content}"
            words = analyzer._extract_words(full_text.lower())
            
            if words:
                from collections import Counter
                word_freq = Counter(words)
                
                # 提取高频词作为关键词
                keywords = []
                for word, count in word_freq.most_common(max_keywords * 2):
                    if len(word) > 2 and word not in analyzer.stop_words:
                        keywords.append(word)
                        if len(keywords) >= max_keywords:
                            break
                
                return ', '.join(keywords)
            
        except ImportError:
            pass
        
        # 降级处理：从标签生成关键词
        if self.tags:
            tag_names = [tag.name for tag in self.tags[:max_keywords]]
            return ', '.join(tag_names)
        
        return ""
    
    def get_slug_variations(self):
        """获取slug变体建议"""
        try:
            from app.utils.slug_generator import SlugGenerator
            generator = SlugGenerator()
            
            return generator.suggest_slug_variations(self.title)
            
        except ImportError:
            return [('当前', self.slug or '')]
    
    def analyze_slug_quality(self):
        """分析slug质量"""
        try:
            from app.utils.slug_generator import SlugGenerator
            generator = SlugGenerator()
            
            if self.slug:
                return generator.analyze_slug_seo(self.slug)
            else:
                return {
                    'score': 0,
                    'issues': ['缺少URL标识'],
                    'recommendations': ['生成URL友好的标识']
                }
                
        except ImportError:
            return {
                'score': 50 if self.slug else 0,
                'issues': ['Slug分析器未可用'],
                'recommendations': ['安装相关依赖包']
            }
    
    def get_sitemap_entry(self):
        """生成站点地图条目"""
        try:
            from app.utils.seo_analyzer import SEOAnalyzer
            analyzer = SEOAnalyzer()
            
            # 根据内容类型设置更新频率和优先级
            changefreq_mapping = {
                '技术': 'weekly',
                '代码': 'weekly',
                '观察': 'monthly',
                '生活': 'monthly',
                '创作': 'monthly'
            }
            
            priority_mapping = {
                '技术': 0.8,
                '代码': 0.8,
                '观察': 0.6,
                '生活': 0.5,
                '创作': 0.6
            }
            
            changefreq = changefreq_mapping.get(self.category, 'monthly')
            priority = priority_mapping.get(self.category, 0.5)
            
            # 如果是精选内容，提高优先级
            if self.is_featured:
                priority = min(1.0, priority + 0.2)
            
            return analyzer.generate_sitemap_entry(
                url=self.get_url() if hasattr(self, 'get_url') else '',
                lastmod=self.updated_at.strftime('%Y-%m-%d') if self.updated_at else None,
                changefreq=changefreq,
                priority=priority
            )
            
        except ImportError:
            return {
                'url': self.get_url() if hasattr(self, 'get_url') else '',
                'lastmod': self.updated_at.strftime('%Y-%m-%d') if self.updated_at else '',
                'changefreq': 'monthly',
                'priority': 0.5
            }
    
    def auto_optimize_seo(self):
        """自动优化SEO"""
        optimizations = []
        
        # 1. 生成slug（如果没有）
        if not self.slug:
            self.generate_slug()
            optimizations.append('生成URL标识')
        
        # 2. 生成摘要（如果没有）
        if not self.summary and self.content:
            self.generate_auto_summary()
            optimizations.append('生成内容摘要')
        
        # 3. 计算阅读时间
        if not self.reading_time:
            self.calculate_reading_time()
            optimizations.append('计算阅读时间')
        
        # 4. 生成meta_title（如果没有）
        if not self.meta_title and self.title:
            self.meta_title = self.title[:60]
            optimizations.append('设置页面标题')
        
        # 5. 生成meta_description（如果没有）
        if not self.meta_description and self.summary:
            self.meta_description = self.summary[:160]
            optimizations.append('设置页面描述')
        
        # 6. 设置og_image（如果有特色图片）
        if not self.og_image and self.featured_image:
            self.og_image = self.featured_image
            optimizations.append('设置社交分享图片')
        
        # 7. 更新SEO分数
        self.calculate_seo_score()
        optimizations.append('更新SEO评分')
        
        return optimizations
    
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