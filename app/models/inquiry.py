"""
📞 项目咨询模型 - 合作咨询管理
📊 data-scientist 设计的客户关系管理模型
"""
from datetime import datetime
from app import db


class ProjectInquiry(db.Model):
    """
    📞 项目咨询模型 - 管理客户项目咨询
    
    用于记录和跟踪：
    - 项目合作咨询
    - 技术服务询价
    - 创意设计需求
    - 客户沟通记录
    """
    __tablename__ = 'project_inquiry'
    
    # 🆔 基础字段
    id = db.Column(db.Integer, primary_key=True)
    inquiry_number = db.Column(db.String(20), unique=True, index=True)  # 咨询编号
    
    # 👤 客户信息
    client_name = db.Column(db.String(100), nullable=False)
    client_email = db.Column(db.String(100), nullable=False, index=True)
    client_phone = db.Column(db.String(50))
    client_company = db.Column(db.String(200))  # 客户公司
    client_title = db.Column(db.String(100))    # 客户职位
    
    # 📋 项目信息
    project_type = db.Column(db.String(100), nullable=False)
    # 项目类型: 'Web开发', '移动应用', '数据分析', '平面设计', '3D建模', '其他'
    
    title = db.Column(db.String(200), nullable=False)  # 咨询标题
    description = db.Column(db.Text, nullable=False)   # 需求描述
    requirements = db.Column(db.JSON)  # 具体需求 ["功能1", "功能2"]
    
    # 💰 预算和时间
    budget_range = db.Column(db.String(50))  # '5K-1W', '1W-5W', '5W+', '面议'
    budget_currency = db.Column(db.String(10), default='CNY')
    timeline = db.Column(db.String(100))     # 期望时间 '1个月内', '2-3个月', '不急'
    urgency_level = db.Column(db.String(20), default='一般')  # '紧急', '一般', '不急'
    
    # 📈 状态管理
    status = db.Column(db.String(50), default='待处理', index=True)
    # 状态: '待处理', '已回复', '讨论中', '报价中', '进行中', '已完成', '已取消'
    
    priority = db.Column(db.String(20), default='中')  # '高', '中', '低'
    
    # 📝 沟通记录
    initial_response = db.Column(db.Text)    # 初次回复内容
    notes = db.Column(db.Text)               # 内部备注
    communication_log = db.Column(db.JSON)   # 沟通记录
    
    # 💼 项目关联
    estimated_hours = db.Column(db.Integer)  # 预估工时
    estimated_cost = db.Column(db.Decimal(10, 2))  # 预估成本
    actual_cost = db.Column(db.Decimal(10, 2))      # 实际成本
    
    # 📅 时间字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    first_response_at = db.Column(db.DateTime)  # 首次回复时间
    completed_at = db.Column(db.DateTime)       # 完成时间
    
    # 🔗 来源信息
    source = db.Column(db.String(50), default='网站表单')  # '网站表单', '邮件', '推荐', '社交媒体'
    referrer = db.Column(db.String(200))  # 推荐人或来源链接
    
    # 📊 评价字段 (项目完成后)
    client_rating = db.Column(db.Integer)     # 客户评分 1-5
    client_feedback = db.Column(db.Text)      # 客户反馈
    project_success = db.Column(db.Boolean)   # 项目是否成功
    
    # 🏷️ 标签分类
    tags = db.Column(db.JSON)  # 自定义标签 ["紧急", "大客户", "技术挑战"]
    
    def __repr__(self):
        return f'<ProjectInquiry {self.inquiry_number}: {self.client_name}>'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.inquiry_number:
            self.inquiry_number = self.generate_inquiry_number()
    
    def generate_inquiry_number(self):
        """生成咨询编号"""
        from datetime import date
        today = date.today()
        prefix = f"INQ{today.strftime('%Y%m%d')}"
        
        # 查找今日最后一个编号
        last_inquiry = ProjectInquiry.query\
            .filter(ProjectInquiry.inquiry_number.startswith(prefix))\
            .order_by(ProjectInquiry.inquiry_number.desc())\
            .first()
        
        if last_inquiry:
            try:
                last_num = int(last_inquiry.inquiry_number[-3:])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1
        
        return f"{prefix}{new_num:03d}"
    
    def get_status_color(self):
        """获取状态对应的颜色"""
        color_mapping = {
            '待处理': '#dc3545',      # 红色
            '已回复': '#ffc107',      # 黄色
            '讨论中': '#17a2b8',      # 青色
            '报价中': '#fd7e14',      # 橙色
            '进行中': '#007bff',      # 蓝色
            '已完成': '#198754',      # 绿色
            '已取消': '#6c757d'       # 灰色
        }
        return color_mapping.get(self.status, '#6c757d')
    
    def get_priority_color(self):
        """获取优先级对应的颜色"""
        color_mapping = {
            '高': '#dc3545',
            '中': '#ffc107', 
            '低': '#198754'
        }
        return color_mapping.get(self.priority, '#ffc107')
    
    def get_response_time(self):
        """获取响应时间 (小时)"""
        if not self.first_response_at:
            return None
        
        delta = self.first_response_at - self.created_at
        return round(delta.total_seconds() / 3600, 1)
    
    def get_processing_time(self):
        """获取处理时长 (天)"""
        end_time = self.completed_at or datetime.utcnow()
        delta = end_time - self.created_at
        return delta.days
    
    def add_communication_log(self, message, sender='system', message_type='note'):
        """添加沟通记录"""
        if not self.communication_log:
            self.communication_log = []
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'sender': sender,  # 'system', 'client', 'admin'
            'type': message_type,  # 'note', 'email', 'call', 'meeting'
            'message': message
        }
        
        self.communication_log.append(log_entry)
        self.updated_at = datetime.utcnow()
    
    def update_status(self, new_status, note=None):
        """更新状态"""
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # 记录状态变更
        message = f"状态从 '{old_status}' 更改为 '{new_status}'"
        if note:
            message += f" - {note}"
        
        self.add_communication_log(message, sender='system', message_type='status_change')
        
        # 特殊状态的时间记录
        if new_status == '已回复' and not self.first_response_at:
            self.first_response_at = datetime.utcnow()
        elif new_status == '已完成' and not self.completed_at:
            self.completed_at = datetime.utcnow()
    
    def get_requirements_list(self):
        """获取需求列表"""
        if not self.requirements:
            return []
        
        if isinstance(self.requirements, list):
            return self.requirements
        
        try:
            import json
            return json.loads(self.requirements)
        except:
            return []
    
    def get_tags_list(self):
        """获取标签列表"""
        if not self.tags:
            return []
        
        if isinstance(self.tags, list):
            return self.tags
        
        try:
            import json
            return json.loads(self.tags)
        except:
            return []
    
    def get_communication_log_list(self):
        """获取沟通记录列表"""
        if not self.communication_log:
            return []
        
        if isinstance(self.communication_log, list):
            return self.communication_log
        
        try:
            import json
            return json.loads(self.communication_log)
        except:
            return []
    
    @staticmethod
    def get_pending_inquiries(limit=None):
        """获取待处理咨询"""
        query = ProjectInquiry.query.filter_by(status='待处理')\
                                  .order_by(ProjectInquiry.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_recent_inquiries(limit=10):
        """获取最新咨询"""
        return ProjectInquiry.query.order_by(ProjectInquiry.created_at.desc())\
                                 .limit(limit).all()
    
    @staticmethod
    def get_inquiries_by_status(status, limit=None):
        """按状态获取咨询"""
        query = ProjectInquiry.query.filter_by(status=status)\
                                  .order_by(ProjectInquiry.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_stats():
        """获取咨询统计"""
        from sqlalchemy import func
        
        # 状态统计
        status_stats = db.session.query(
            ProjectInquiry.status,
            func.count(ProjectInquiry.id).label('count')
        ).group_by(ProjectInquiry.status).all()
        
        # 项目类型统计
        type_stats = db.session.query(
            ProjectInquiry.project_type,
            func.count(ProjectInquiry.id).label('count')
        ).group_by(ProjectInquiry.project_type).all()
        
        # 月度统计 (最近12个月)
        from sqlalchemy import extract
        monthly_stats = db.session.query(
            extract('year', ProjectInquiry.created_at).label('year'),
            extract('month', ProjectInquiry.created_at).label('month'),
            func.count(ProjectInquiry.id).label('count')
        ).filter(
            ProjectInquiry.created_at >= datetime.utcnow().replace(month=1, day=1) # 今年开始
        ).group_by('year', 'month').all()
        
        return {
            'status_distribution': {stat.status: stat.count for stat in status_stats},
            'type_distribution': {stat.project_type: stat.count for stat in type_stats},
            'monthly_trend': [
                {
                    'year': int(stat.year),
                    'month': int(stat.month),
                    'count': stat.count
                }
                for stat in monthly_stats
            ],
            'total_inquiries': ProjectInquiry.query.count(),
            'pending_count': ProjectInquiry.query.filter_by(status='待处理').count(),
            'completed_count': ProjectInquiry.query.filter_by(status='已完成').count()
        }
    
    @classmethod
    def search_inquiries(cls, query_text, limit=20):
        """搜索咨询"""
        from sqlalchemy import or_
        
        search_terms = query_text.split()
        conditions = []
        
        for term in search_terms:
            conditions.append(
                or_(
                    cls.client_name.contains(term),
                    cls.client_company.contains(term),
                    cls.title.contains(term),
                    cls.description.contains(term),
                    cls.project_type.contains(term),
                    cls.inquiry_number.contains(term)
                )
            )
        
        if conditions:
            return cls.query.filter(or_(*conditions))\
                          .order_by(cls.created_at.desc())\
                          .limit(limit).all()
        
        return []