"""
💼 项目模型 - 作品集展示核心
📊 data-scientist 设计的项目作品展示模型
"""
from datetime import datetime, date
from flask import url_for
from app import db
from sqlalchemy import or_


class Project(db.Model):
    """
    💼 项目模型 - 展示技术项目和创意作品
    
    用于展示：
    - 技术项目: Web应用、移动应用、开源项目
    - 创意作品: 3D打印、平面设计、手工艺品
    - 客户项目: 外包项目、合作项目 (保护隐私)
    """
    __tablename__ = 'project'
    
    # 🆔 基础字段
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    slug = db.Column(db.String(200), unique=True, index=True)
    
    # 📝 描述字段
    description = db.Column(db.Text, nullable=False)  # 项目描述
    description_html = db.Column(db.Text)  # 渲染后的HTML
    summary = db.Column(db.String(500))  # 简短摘要
    
    # 🔧 技术字段
    tech_stack = db.Column(db.JSON)  # 技术栈数组 ["Python", "Flask", "React"]
    category = db.Column(db.String(50), default='技术')  # '技术', '创意', '商业'
    project_type = db.Column(db.String(50))  # 'Web应用', '移动应用', '3D打印', '平面设计'
    
    # 🖼️ 媒体字段
    featured_image = db.Column(db.String(500))  # 主要展示图片
    images = db.Column(db.JSON)  # 项目图片数组
    video_url = db.Column(db.String(500))  # 演示视频URL
    
    # 🔗 链接字段
    demo_url = db.Column(db.String(500))  # 在线演示链接
    github_url = db.Column(db.String(500))  # GitHub仓库链接
    download_url = db.Column(db.String(500))  # 下载链接
    
    # 📊 项目信息
    client_name = db.Column(db.String(100))  # 客户名称 (可选)
    collaboration_type = db.Column(db.String(50))  # '个人项目', '团队合作', '客户项目'
    project_status = db.Column(db.String(50), default='已完成')  # '进行中', '已完成', '已暂停'
    
    # 📅 时间字段
    start_date = db.Column(db.Date)  # 项目开始日期
    completion_date = db.Column(db.Date)  # 完成日期
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 📊 状态字段
    is_published = db.Column(db.Boolean, default=True, index=True)
    is_featured = db.Column(db.Boolean, default=False, index=True)  # 精选项目
    view_count = db.Column(db.Integer, default=0)
    difficulty_level = db.Column(db.String(20))  # '初级', '中级', '高级'
    
    # 🔍 SEO字段
    seo_title = db.Column(db.String(200))
    seo_description = db.Column(db.String(300))
    seo_keywords = db.Column(db.String(500))
    
    # 🏆 成果字段
    achievements = db.Column(db.JSON)  # 项目成果 ["获得XX奖项", "用户量达到XX"]
    lessons_learned = db.Column(db.Text)  # 经验总结
    
    def __repr__(self):
        return f'<Project {self.name}>'
    
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
            while Project.query.filter_by(slug=slug).first():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            self.slug = slug
    
    def render_description_html(self):
        """渲染描述为HTML (如果包含Markdown)"""
        if not self.description:
            self.description_html = ''
            return
        
        # 简单的Markdown渲染
        import markdown
        md = markdown.Markdown(extensions=['fenced_code', 'nl2br'])
        self.description_html = md.convert(self.description)
    
    def get_url(self):
        """获取项目URL"""
        if self.slug:
            return url_for('content.project_detail', id=self.id, slug=self.slug)
        return url_for('content.project_detail', id=self.id)
    
    def get_tech_stack_list(self):
        """获取技术栈列表"""
        if not self.tech_stack:
            return []
        
        if isinstance(self.tech_stack, list):
            return self.tech_stack
        
        # 如果是字符串，尝试解析
        try:
            import json
            return json.loads(self.tech_stack)
        except:
            return self.tech_stack.split(',') if isinstance(self.tech_stack, str) else []
    
    def get_images_list(self):
        """获取项目图片列表"""
        if not self.images:
            return []
        
        if isinstance(self.images, list):
            return self.images
        
        try:
            import json
            return json.loads(self.images)
        except:
            return []
    
    def get_achievements_list(self):
        """获取项目成果列表"""
        if not self.achievements:
            return []
        
        if isinstance(self.achievements, list):
            return self.achievements
        
        try:
            import json
            return json.loads(self.achievements)
        except:
            return []
    
    def get_duration_text(self):
        """获取项目持续时间文本"""
        if not self.start_date:
            return "时间未知"
        
        if not self.completion_date:
            if self.project_status == '进行中':
                duration = (date.today() - self.start_date).days
                return f"进行中 ({duration}天)"
            else:
                return "完成时间未知"
        
        duration = (self.completion_date - self.start_date).days
        if duration < 7:
            return f"{duration}天"
        elif duration < 30:
            weeks = duration // 7
            return f"{weeks}周"
        elif duration < 365:
            months = duration // 30
            return f"{months}个月"
        else:
            years = duration // 365
            return f"{years}年"
    
    def get_summary(self, length=150):
        """获取项目摘要"""
        if self.summary:
            if len(self.summary) > length:
                return self.summary[:length] + '...'
            return self.summary
        
        # 从描述中生成摘要
        if not self.description:
            return ""
        
        import re
        text = re.sub(r'[#*`\[\]()_~]', '', self.description)
        text = re.sub(r'\n+', ' ', text)
        text = text.strip()
        
        if len(text) <= length:
            return text
        
        truncated = text[:length]
        last_space = truncated.rfind(' ')
        if last_space > length * 0.8:
            truncated = truncated[:last_space]
        
        return truncated + '...'
    
    @staticmethod
    def get_featured_projects(limit=6):
        """获取精选项目"""
        return Project.query.filter_by(is_published=True, is_featured=True)\
                          .order_by(Project.completion_date.desc().nullslast())\
                          .limit(limit).all()
    
    @staticmethod
    def get_recent_projects(limit=6):
        """获取最新项目"""
        return Project.query.filter_by(is_published=True)\
                          .order_by(Project.completion_date.desc().nullslast())\
                          .limit(limit).all()
    
    @staticmethod
    def get_projects_by_category(category, limit=None):
        """按分类获取项目"""
        query = Project.query.filter_by(category=category, is_published=True)\
                           .order_by(Project.completion_date.desc().nullslast())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_related_projects(project, limit=3):
        """获取相关项目"""
        # 基于技术栈或分类查找相关项目
        related_by_tech = []
        related_by_category = []
        
        if project.tech_stack:
            # 基于技术栈查找
            tech_list = project.get_tech_stack_list()
            if tech_list:
                for tech in tech_list:
                    projects = Project.query.filter(
                        Project.id != project.id,
                        Project.is_published == True,
                        Project.tech_stack.contains(tech)
                    ).limit(2).all()
                    related_by_tech.extend(projects)
        
        # 基于分类查找
        related_by_category = Project.query.filter(
            Project.id != project.id,
            Project.category == project.category,
            Project.is_published == True
        ).order_by(Project.completion_date.desc().nullslast()).limit(3).all()
        
        # 合并并去重
        related = []
        seen_ids = set()
        
        for p in related_by_tech + related_by_category:
            if p.id not in seen_ids:
                related.append(p)
                seen_ids.add(p.id)
                if len(related) >= limit:
                    break
        
        return related[:limit]
    
    @staticmethod
    def get_all_tech_stacks():
        """获取所有技术栈 (用于筛选)"""
        projects = Project.query.filter_by(is_published=True).all()
        tech_stacks = set()
        
        for project in projects:
            tech_list = project.get_tech_stack_list()
            tech_stacks.update(tech_list)
        
        return sorted(list(tech_stacks))
    
    @staticmethod
    def search_projects(query, limit=10):
        """搜索项目"""
        keywords = query.split()
        search_conditions = []
        
        for keyword in keywords:
            search_conditions.append(
                or_(
                    Project.name.contains(keyword),
                    Project.description.contains(keyword),
                    Project.tech_stack.contains(keyword),
                    Project.summary.contains(keyword)
                )
            )
        
        if search_conditions:
            search_query = Project.query.filter(
                Project.is_published == True,
                or_(*search_conditions)
            )
        else:
            search_query = Project.query.filter_by(is_published=True)
        
        return search_query.order_by(
            Project.completion_date.desc().nullslast()
        ).limit(limit).all()
    
    @classmethod 
    def get_category_stats(cls):
        """获取分类统计"""
        from sqlalchemy import func
        
        stats = db.session.query(
            cls.category,
            func.count(cls.id).label('count')
        ).filter_by(is_published=True).group_by(cls.category).all()
        
        return {stat.category: stat.count for stat in stats}
    
    @classmethod
    def get_tech_stack_stats(cls):
        """获取技术栈使用统计"""
        projects = cls.query.filter_by(is_published=True).all()
        tech_count = {}
        
        for project in projects:
            tech_list = project.get_tech_stack_list()
            for tech in tech_list:
                tech_count[tech] = tech_count.get(tech, 0) + 1
        
        # 按使用频率排序
        return sorted(tech_count.items(), key=lambda x: x[1], reverse=True)