"""
👥 客户管理模型 - CRM客户关系管理
📊 data-scientist 设计的客户生命周期管理
"""
from datetime import datetime, timedelta
from app import db


class Customer(db.Model):
    """
    👥 客户模型 - CRM客户关系管理
    
    统一管理：
    - 客户基础信息
    - 接触历史记录
    - 商机跟踪
    - 标签分类
    - 价值评估
    """
    __tablename__ = 'customer'
    
    # 🆔 基础字段
    id = db.Column(db.Integer, primary_key=True)
    customer_code = db.Column(db.String(20), unique=True, index=True)  # 客户编号
    
    # 👤 基础信息
    name = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(100), nullable=False, index=True)
    phone = db.Column(db.String(50))
    company = db.Column(db.String(200))
    title = db.Column(db.String(100))  # 职位
    industry = db.Column(db.String(100))  # 行业
    
    # 🏢 公司信息
    company_size = db.Column(db.String(50))  # '小型(1-50)', '中型(51-200)', '大型(201+)'
    company_website = db.Column(db.String(200))
    company_address = db.Column(db.Text)
    
    # 📊 客户价值
    customer_type = db.Column(db.String(50), default='潜在客户')  # '潜在客户', '意向客户', '签约客户', '流失客户'
    value_level = db.Column(db.String(20), default='中')  # '高', '中', '低'
    lifetime_value = db.Column(db.Float, default=0.0)  # 客户终身价值
    
    # 📈 商机信息
    lead_source = db.Column(db.String(100))  # '网站咨询', '推荐', '社交媒体', '广告'
    lead_score = db.Column(db.Integer, default=0)  # 线索评分 0-100
    conversion_probability = db.Column(db.Float, default=0.0)  # 转化概率 0.0-1.0
    
    # 📞 沟通偏好
    preferred_contact = db.Column(db.String(50), default='邮件')  # '邮件', '电话', '微信', '会议'
    contact_frequency = db.Column(db.String(50), default='按需')  # '每周', '每月', '按需'
    timezone = db.Column(db.String(50), default='Asia/Shanghai')
    
    # 📅 重要时间
    first_contact = db.Column(db.DateTime)  # 首次接触时间
    last_contact = db.Column(db.DateTime)  # 最后接触时间
    next_followup = db.Column(db.DateTime)  # 下次跟进时间
    
    # 📝 备注和标签
    notes = db.Column(db.Text)  # 客户备注
    tags = db.Column(db.JSON)  # 标签 ["VIP", "技术型", "决策者"]
    custom_fields = db.Column(db.JSON)  # 自定义字段
    
    # 🔄 状态管理
    status = db.Column(db.String(50), default='活跃')  # '活跃', '暂停', '流失'
    stage = db.Column(db.String(100), default='初次接触')  # 销售阶段
    
    # 📅 时间字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 🔗 关系
    inquiries = db.relationship('ProjectInquiry', backref='customer', lazy='dynamic')
    interactions = db.relationship('CustomerInteraction', backref='customer', lazy='dynamic')
    
    def __repr__(self):
        return f'<Customer {self.customer_code}: {self.name}>'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.customer_code:
            self.customer_code = self.generate_customer_code()
        if not self.first_contact:
            self.first_contact = datetime.utcnow()
    
    def generate_customer_code(self):
        """生成客户编号"""
        from datetime import date
        today = date.today()
        prefix = f"CUS{today.strftime('%Y%m')}"
        
        # 查找本月最后一个编号
        last_customer = Customer.query\
            .filter(Customer.customer_code.startswith(prefix))\
            .order_by(Customer.customer_code.desc())\
            .first()
        
        if last_customer:
            try:
                last_num = int(last_customer.customer_code[-4:])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1
        
        return f"{prefix}{new_num:04d}"
    
    def update_lead_score(self):
        """更新线索评分"""
        score = 0
        
        # 基础信息完整度 (0-30分)
        if self.email: score += 10
        if self.phone: score += 10
        if self.company: score += 10
        
        # 互动频率 (0-30分)
        inquiry_count = self.inquiries.count()
        if inquiry_count >= 5: score += 30
        elif inquiry_count >= 3: score += 20
        elif inquiry_count >= 1: score += 10
        
        # 最近活跃度 (0-20分)
        if self.last_contact:
            days_ago = (datetime.utcnow() - self.last_contact).days
            if days_ago <= 7: score += 20
            elif days_ago <= 30: score += 15
            elif days_ago <= 90: score += 10
        
        # 客户类型 (0-20分)
        type_scores = {
            '签约客户': 20,
            '意向客户': 15,
            '潜在客户': 10,
            '流失客户': 0
        }
        score += type_scores.get(self.customer_type, 0)
        
        self.lead_score = min(score, 100)
        self.updated_at = datetime.utcnow()
    
    def calculate_conversion_probability(self):
        """计算转化概率"""
        # 基于线索评分和历史数据预测转化概率
        if self.lead_score >= 80:
            probability = 0.8
        elif self.lead_score >= 60:
            probability = 0.6
        elif self.lead_score >= 40:
            probability = 0.4
        elif self.lead_score >= 20:
            probability = 0.2
        else:
            probability = 0.1
        
        # 根据客户类型调整
        if self.customer_type == '意向客户':
            probability += 0.2
        elif self.customer_type == '签约客户':
            probability = 1.0
        
        self.conversion_probability = min(probability, 1.0)
    
    def add_tag(self, tag):
        """添加标签"""
        if not self.tags:
            self.tags = []
        
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag):
        """移除标签"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()
    
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
    
    def schedule_followup(self, days_ahead=7, note=""):
        """安排跟进"""
        self.next_followup = datetime.utcnow() + timedelta(days=days_ahead)
        if note:
            self.add_interaction('跟进提醒', f'安排{days_ahead}天后跟进: {note}')
    
    def add_interaction(self, interaction_type, content, outcome=""):
        """添加互动记录"""
        interaction = CustomerInteraction(
            customer_id=self.id,
            interaction_type=interaction_type,
            content=content,
            outcome=outcome
        )
        db.session.add(interaction)
        
        # 更新最后接触时间
        self.last_contact = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def get_interaction_history(self, limit=10):
        """获取互动历史"""
        return self.interactions.order_by(CustomerInteraction.created_at.desc()).limit(limit).all()
    
    def needs_followup(self):
        """检查是否需要跟进"""
        if not self.next_followup:
            return False
        return datetime.utcnow() >= self.next_followup
    
    def days_since_last_contact(self):
        """距离上次接触天数"""
        if not self.last_contact:
            return None
        
        delta = datetime.utcnow() - self.last_contact
        return delta.days
    
    @classmethod
    def get_pending_followups(cls, limit=None):
        """获取需要跟进的客户"""
        query = cls.query.filter(
            cls.next_followup <= datetime.utcnow(),
            cls.status == '活跃'
        ).order_by(cls.next_followup.asc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def search_customers(cls, query_text, limit=20):
        """搜索客户"""
        from sqlalchemy import or_
        
        search_terms = query_text.split()
        conditions = []
        
        for term in search_terms:
            conditions.append(
                or_(
                    cls.name.contains(term),
                    cls.company.contains(term),
                    cls.email.contains(term),
                    cls.phone.contains(term),
                    cls.customer_code.contains(term)
                )
            )
        
        if conditions:
            return cls.query.filter(or_(*conditions))\
                          .order_by(cls.updated_at.desc())\
                          .limit(limit).all()
        
        return []
    
    @classmethod
    def get_stats(cls):
        """获取客户统计"""
        from sqlalchemy import func
        
        # 客户类型统计
        type_stats = db.session.query(
            cls.customer_type,
            func.count(cls.id).label('count')
        ).group_by(cls.customer_type).all()
        
        # 价值等级统计
        value_stats = db.session.query(
            cls.value_level,
            func.count(cls.id).label('count')
        ).group_by(cls.value_level).all()
        
        # 需要跟进的客户数
        pending_followups = cls.query.filter(
            cls.next_followup <= datetime.utcnow(),
            cls.status == '活跃'
        ).count()
        
        return {
            'total_customers': cls.query.count(),
            'active_customers': cls.query.filter_by(status='活跃').count(),
            'potential_customers': cls.query.filter_by(customer_type='潜在客户').count(),
            'signed_customers': cls.query.filter_by(customer_type='签约客户').count(),
            'pending_followups': pending_followups,
            'type_distribution': {stat.customer_type: stat.count for stat in type_stats},
            'value_distribution': {stat.value_level: stat.count for stat in value_stats}
        }


class CustomerInteraction(db.Model):
    """
    📞 客户互动记录模型 - 记录所有客户接触历史
    """
    __tablename__ = 'customer_interaction'
    
    # 🆔 基础字段
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    
    # 📞 互动信息
    interaction_type = db.Column(db.String(50), nullable=False)  # '电话', '邮件', '会议', '访问'
    content = db.Column(db.Text, nullable=False)  # 互动内容
    outcome = db.Column(db.String(200))  # 互动结果
    
    # 📅 时间和持续时长
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    duration_minutes = db.Column(db.Integer)  # 持续时长(分钟)
    
    # 👤 操作人员
    staff_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    staff_name = db.Column(db.String(100), default='系统')
    
    # 📊 评价
    satisfaction_score = db.Column(db.Integer)  # 客户满意度 1-5
    follow_up_needed = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<CustomerInteraction {self.id}: {self.interaction_type}>'
    
    def get_duration_text(self):
        """获取持续时长文本"""
        if not self.duration_minutes:
            return ""
        
        if self.duration_minutes < 60:
            return f"{self.duration_minutes}分钟"
        else:
            hours = self.duration_minutes // 60
            minutes = self.duration_minutes % 60
            return f"{hours}小时{minutes}分钟" if minutes else f"{hours}小时"


class BusinessOpportunity(db.Model):
    """
    💼 商机管理模型 - 跟踪潜在业务机会
    """
    __tablename__ = 'business_opportunity'
    
    # 🆔 基础字段
    id = db.Column(db.Integer, primary_key=True)
    opportunity_code = db.Column(db.String(20), unique=True, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    
    # 💼 商机信息
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    value = db.Column(db.Float)  # 商机价值
    currency = db.Column(db.String(10), default='CNY')
    
    # 📊 状态管理
    stage = db.Column(db.String(100), default='识别需求')  # 销售阶段
    # 阶段: '识别需求', '方案设计', '商务谈判', '合同签署', '项目实施', '项目完成', '已流失'
    
    probability = db.Column(db.Float, default=0.1)  # 成功概率 0.0-1.0
    status = db.Column(db.String(50), default='进行中')  # '进行中', '已成交', '已流失'
    
    # 📅 时间管理
    expected_close_date = db.Column(db.Date)  # 预期成交时间
    actual_close_date = db.Column(db.Date)  # 实际成交时间
    
    # 📝 跟进信息
    next_action = db.Column(db.String(200))  # 下一步行动
    next_action_date = db.Column(db.DateTime)  # 下一步行动时间
    
    # 📅 时间字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 🔗 关系
    customer = db.relationship('Customer', backref='opportunities')
    
    def __repr__(self):
        return f'<BusinessOpportunity {self.opportunity_code}: {self.title}>'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.opportunity_code:
            self.opportunity_code = self.generate_opportunity_code()
    
    def generate_opportunity_code(self):
        """生成商机编号"""
        from datetime import date
        today = date.today()
        prefix = f"OPP{today.strftime('%Y%m')}"
        
        # 查找本月最后一个编号
        last_opp = BusinessOpportunity.query\
            .filter(BusinessOpportunity.opportunity_code.startswith(prefix))\
            .order_by(BusinessOpportunity.opportunity_code.desc())\
            .first()
        
        if last_opp:
            try:
                last_num = int(last_opp.opportunity_code[-4:])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1
        
        return f"{prefix}{new_num:04d}"
    
    def update_stage(self, new_stage):
        """更新销售阶段"""
        # 阶段对应的成功概率
        stage_probabilities = {
            '识别需求': 0.1,
            '方案设计': 0.25,
            '商务谈判': 0.5,
            '合同签署': 0.8,
            '项目实施': 0.9,
            '项目完成': 1.0,
            '已流失': 0.0
        }
        
        self.stage = new_stage
        self.probability = stage_probabilities.get(new_stage, self.probability)
        self.updated_at = datetime.utcnow()
        
        # 更新状态
        if new_stage == '项目完成':
            self.status = '已成交'
            if not self.actual_close_date:
                self.actual_close_date = datetime.utcnow().date()
        elif new_stage == '已流失':
            self.status = '已流失'
    
    def get_stage_color(self):
        """获取阶段对应的颜色"""
        color_mapping = {
            '识别需求': '#ffc107',    # 黄色
            '方案设计': '#17a2b8',    # 青色
            '商务谈判': '#fd7e14',    # 橙色
            '合同签署': '#007bff',    # 蓝色
            '项目实施': '#28a745',    # 绿色
            '项目完成': '#198754',    # 深绿色
            '已流失': '#dc3545'       # 红色
        }
        return color_mapping.get(self.stage, '#6c757d')
    
    def days_to_close(self):
        """距离预期成交天数"""
        if not self.expected_close_date:
            return None
        
        from datetime import date
        delta = self.expected_close_date - date.today()
        return delta.days
    
    def is_overdue(self):
        """是否已过期"""
        days = self.days_to_close()
        return days is not None and days < 0
    
    @classmethod
    def get_active_opportunities(cls, limit=None):
        """获取进行中的商机"""
        query = cls.query.filter_by(status='进行中')\
                        .order_by(cls.expected_close_date.asc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_stats(cls):
        """获取商机统计"""
        from sqlalchemy import func
        
        # 阶段统计
        stage_stats = db.session.query(
            cls.stage,
            func.count(cls.id).label('count'),
            func.sum(cls.value).label('total_value')
        ).group_by(cls.stage).all()
        
        # 状态统计
        status_stats = db.session.query(
            cls.status,
            func.count(cls.id).label('count'),
            func.sum(cls.value).label('total_value')
        ).group_by(cls.status).all()
        
        return {
            'total_opportunities': cls.query.count(),
            'active_opportunities': cls.query.filter_by(status='进行中').count(),
            'closed_won': cls.query.filter_by(status='已成交').count(),
            'closed_lost': cls.query.filter_by(status='已流失').count(),
            'total_value': db.session.query(func.sum(cls.value)).scalar() or 0,
            'stage_distribution': [
                {
                    'stage': stat.stage,
                    'count': stat.count,
                    'value': float(stat.total_value or 0)
                } for stat in stage_stats
            ],
            'status_distribution': [
                {
                    'status': stat.status,
                    'count': stat.count,
                    'value': float(stat.total_value or 0)
                } for stat in status_stats
            ]
        }