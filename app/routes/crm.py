"""
👥 CRM客户关系管理路由蓝图
客户管理、商机跟踪、互动记录
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
import json

from app.models import Customer, CustomerInteraction, BusinessOpportunity, ProjectInquiry
from app.routes.admin import admin_required

bp = Blueprint('crm', __name__)


# 👥 客户管理
@bp.route('/customers')
@login_required
@admin_required
def customer_list():
    """客户列表管理"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    customer_type = request.args.get('type', '')
    value_level = request.args.get('value', '')
    sort = request.args.get('sort', 'updated_desc')
    
    # 构建查询
    query = Customer.query
    
    # 搜索
    if search:
        customers = Customer.search_customers(search, limit=100)
        # 转换为查询对象
        if customers:
            customer_ids = [c.id for c in customers]
            query = Customer.query.filter(Customer.id.in_(customer_ids))
        else:
            query = Customer.query.filter(Customer.id == -1)  # 空结果
    
    # 类型筛选
    if customer_type:
        query = query.filter_by(customer_type=customer_type)
    
    # 价值等级筛选
    if value_level:
        query = query.filter_by(value_level=value_level)
    
    # 排序
    if sort == 'name_asc':
        query = query.order_by(Customer.name.asc())
    elif sort == 'created_desc':
        query = query.order_by(Customer.created_at.desc())
    elif sort == 'lead_score_desc':
        query = query.order_by(Customer.lead_score.desc())
    elif sort == 'last_contact_desc':
        query = query.order_by(Customer.last_contact.desc())
    else:  # updated_desc
        query = query.order_by(Customer.updated_at.desc())
    
    # 分页
    per_page = current_app.config.get('POSTS_PER_PAGE', 20)
    customers_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取统计数据
    stats = Customer.get_stats()
    
    return render_template('crm/customer_list.html',
                         customers=customers_pagination.items,
                         pagination=customers_pagination,
                         stats=stats,
                         current_search=search,
                         current_type=customer_type,
                         current_value=value_level,
                         current_sort=sort)


@bp.route('/customer/<int:id>')
@login_required
@admin_required
def customer_detail(id):
    """客户详情页面"""
    customer = Customer.query.get_or_404(id)
    
    # 获取客户的所有咨询
    inquiries = customer.inquiries.order_by(ProjectInquiry.created_at.desc()).limit(10).all()
    
    # 获取最近的互动记录
    interactions = customer.get_interaction_history(limit=20)
    
    # 获取商机
    opportunities = customer.opportunities.order_by(BusinessOpportunity.updated_at.desc()).all()
    
    # 更新线索评分
    customer.update_lead_score()
    customer.calculate_conversion_probability()
    
    from app import db
    db.session.commit()
    
    return render_template('crm/customer_detail.html',
                         customer=customer,
                         inquiries=inquiries,
                         interactions=interactions,
                         opportunities=opportunities)


@bp.route('/customer/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def customer_edit(id):
    """编辑客户信息"""
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # 更新基础信息
            customer.name = request.form.get('name', '').strip()
            customer.email = request.form.get('email', '').strip()
            customer.phone = request.form.get('phone', '').strip()
            customer.company = request.form.get('company', '').strip()
            customer.title = request.form.get('title', '').strip()
            customer.industry = request.form.get('industry', '').strip()
            
            # 更新公司信息
            customer.company_size = request.form.get('company_size', '')
            customer.company_website = request.form.get('company_website', '').strip()
            customer.company_address = request.form.get('company_address', '').strip()
            
            # 更新客户价值
            customer.customer_type = request.form.get('customer_type', '潜在客户')
            customer.value_level = request.form.get('value_level', '中')
            
            # 更新沟通偏好
            customer.preferred_contact = request.form.get('preferred_contact', '邮件')
            customer.contact_frequency = request.form.get('contact_frequency', '按需')
            
            # 更新备注
            customer.notes = request.form.get('notes', '').strip()
            
            # 处理标签
            tags_str = request.form.get('tags', '').strip()
            if tags_str:
                customer.tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            else:
                customer.tags = []
            
            # 更新线索评分
            customer.update_lead_score()
            customer.calculate_conversion_probability()
            
            from app import db
            db.session.commit()
            
            flash('客户信息更新成功！', 'success')
            return redirect(url_for('crm.customer_detail', id=customer.id))
            
        except Exception as e:
            from app import db
            db.session.rollback()
            flash(f'更新失败：{str(e)}', 'error')
    
    return render_template('crm/customer_edit.html', customer=customer)


@bp.route('/customer/<int:id>/interaction', methods=['POST'])
@login_required
@admin_required
def add_interaction(id):
    """添加客户互动记录"""
    customer = Customer.query.get_or_404(id)
    
    try:
        interaction_type = request.form.get('interaction_type', '').strip()
        content = request.form.get('content', '').strip()
        outcome = request.form.get('outcome', '').strip()
        duration = request.form.get('duration', type=int)
        
        if not interaction_type or not content:
            flash('互动类型和内容不能为空', 'error')
            return redirect(url_for('crm.customer_detail', id=id))
        
        # 创建互动记录
        interaction = CustomerInteraction(
            customer_id=customer.id,
            interaction_type=interaction_type,
            content=content,
            outcome=outcome,
            duration_minutes=duration,
            staff_name=current_user.name or '管理员'
        )
        
        from app import db
        db.session.add(interaction)
        
        # 更新客户最后接触时间
        customer.last_contact = datetime.utcnow()
        customer.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('互动记录添加成功！', 'success')
        
    except Exception as e:
        from app import db
        db.session.rollback()
        flash(f'添加失败：{str(e)}', 'error')
    
    return redirect(url_for('crm.customer_detail', id=id))


@bp.route('/customer/<int:id>/followup', methods=['POST'])
@login_required
@admin_required
def schedule_followup(id):
    """安排客户跟进"""
    customer = Customer.query.get_or_404(id)
    
    try:
        days_ahead = request.form.get('days_ahead', 7, type=int)
        note = request.form.get('note', '').strip()
        
        # 安排跟进
        customer.schedule_followup(days_ahead, note)
        
        from app import db
        db.session.commit()
        
        flash(f'已安排 {days_ahead} 天后跟进！', 'success')
        
    except Exception as e:
        from app import db
        db.session.rollback()
        flash(f'安排失败：{str(e)}', 'error')
    
    return redirect(url_for('crm.customer_detail', id=id))


# 💼 商机管理
@bp.route('/opportunities')
@login_required
@admin_required
def opportunity_list():
    """商机列表管理"""
    page = request.args.get('page', 1, type=int)
    stage = request.args.get('stage', '')
    status = request.args.get('status', '')
    sort = request.args.get('sort', 'updated_desc')
    
    # 构建查询
    query = BusinessOpportunity.query
    
    # 阶段筛选
    if stage:
        query = query.filter_by(stage=stage)
    
    # 状态筛选
    if status:
        query = query.filter_by(status=status)
    
    # 排序
    if sort == 'value_desc':
        query = query.order_by(BusinessOpportunity.value.desc())
    elif sort == 'close_date_asc':
        query = query.order_by(BusinessOpportunity.expected_close_date.asc())
    elif sort == 'probability_desc':
        query = query.order_by(BusinessOpportunity.probability.desc())
    else:  # updated_desc
        query = query.order_by(BusinessOpportunity.updated_at.desc())
    
    # 分页
    per_page = current_app.config.get('POSTS_PER_PAGE', 20)
    opportunities_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取统计数据
    stats = BusinessOpportunity.get_stats()
    
    return render_template('crm/opportunity_list.html',
                         opportunities=opportunities_pagination.items,
                         pagination=opportunities_pagination,
                         stats=stats,
                         current_stage=stage,
                         current_status=status,
                         current_sort=sort)


@bp.route('/opportunity/<int:id>')
@login_required
@admin_required
def opportunity_detail(id):
    """商机详情页面"""
    opportunity = BusinessOpportunity.query.get_or_404(id)
    return render_template('crm/opportunity_detail.html', opportunity=opportunity)


@bp.route('/opportunity/create', methods=['GET', 'POST'])
@bp.route('/opportunity/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def opportunity_edit(id=None):
    """创建或编辑商机"""
    if id:
        opportunity = BusinessOpportunity.query.get_or_404(id)
    else:
        opportunity = None
    
    if request.method == 'POST':
        try:
            if opportunity is None:
                # 创建新商机
                opportunity = BusinessOpportunity()
                from app import db
                db.session.add(opportunity)
            
            # 更新字段
            opportunity.customer_id = request.form.get('customer_id', type=int)
            opportunity.title = request.form.get('title', '').strip()
            opportunity.description = request.form.get('description', '').strip()
            opportunity.value = request.form.get('value', type=float)
            opportunity.stage = request.form.get('stage', '识别需求')
            
            # 处理预期成交时间
            expected_close_str = request.form.get('expected_close_date', '').strip()
            if expected_close_str:
                opportunity.expected_close_date = datetime.strptime(expected_close_str, '%Y-%m-%d').date()
            
            opportunity.next_action = request.form.get('next_action', '').strip()
            
            # 处理下一步行动时间
            next_action_str = request.form.get('next_action_date', '').strip()
            if next_action_str:
                opportunity.next_action_date = datetime.strptime(next_action_str, '%Y-%m-%dT%H:%M')
            
            # 更新阶段和概率
            opportunity.update_stage(opportunity.stage)
            
            from app import db
            db.session.commit()
            
            action = '创建' if id is None else '更新'
            flash(f'商机{action}成功！', 'success')
            return redirect(url_for('crm.opportunity_detail', id=opportunity.id))
            
        except Exception as e:
            from app import db
            db.session.rollback()
            flash(f'操作失败：{str(e)}', 'error')
    
    # 获取客户列表
    customers = Customer.query.order_by(Customer.name.asc()).all()
    
    return render_template('crm/opportunity_edit.html', 
                         opportunity=opportunity, 
                         customers=customers)


# 📊 CRM仪表盘
@bp.route('/dashboard')
@login_required
@admin_required
def crm_dashboard():
    """CRM总览仪表盘"""
    # 获取客户统计
    customer_stats = Customer.get_stats()
    
    # 获取商机统计
    opportunity_stats = BusinessOpportunity.get_stats()
    
    # 需要跟进的客户
    pending_followups = Customer.get_pending_followups(limit=10)
    
    # 进行中的商机
    active_opportunities = BusinessOpportunity.get_active_opportunities(limit=10)
    
    # 最近的互动记录
    recent_interactions = CustomerInteraction.query\
        .order_by(CustomerInteraction.created_at.desc())\
        .limit(10).all()
    
    return render_template('crm/dashboard.html',
                         customer_stats=customer_stats,
                         opportunity_stats=opportunity_stats,
                         pending_followups=pending_followups,
                         active_opportunities=active_opportunities,
                         recent_interactions=recent_interactions)


# 📞 跟进提醒
@bp.route('/followups')
@login_required
@admin_required
def followup_list():
    """跟进提醒列表"""
    # 需要跟进的客户
    pending_customers = Customer.get_pending_followups()
    
    # 今日需要跟进
    today_followups = [c for c in pending_customers if c.next_followup.date() == date.today()]
    
    # 过期未跟进
    overdue_followups = [c for c in pending_customers if c.next_followup.date() < date.today()]
    
    # 本周需要跟进
    week_end = date.today() + timedelta(days=7)
    week_followups = [c for c in pending_customers 
                     if date.today() < c.next_followup.date() <= week_end]
    
    return render_template('crm/followup_list.html',
                         today_followups=today_followups,
                         overdue_followups=overdue_followups,
                         week_followups=week_followups)


# 🔍 搜索和筛选
@bp.route('/api/customers/search')
@login_required
@admin_required
def search_customers_api():
    """客户搜索API"""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({'customers': []})
    
    customers = Customer.search_customers(query, limit=limit)
    
    result = []
    for customer in customers:
        result.append({
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'company': customer.company,
            'customer_type': customer.customer_type,
            'lead_score': customer.lead_score
        })
    
    return jsonify({'customers': result})


@bp.route('/api/customer/<int:id>/lead_score', methods=['POST'])
@login_required
@admin_required
def update_lead_score_api(id):
    """更新客户线索评分API"""
    customer = Customer.query.get_or_404(id)
    
    try:
        customer.update_lead_score()
        customer.calculate_conversion_probability()
        
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'lead_score': customer.lead_score,
            'conversion_probability': customer.conversion_probability
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# 📈 CRM数据同步
@bp.route('/sync/inquiries-to-customers', methods=['POST'])
@login_required
@admin_required
def sync_inquiries_to_customers():
    """将咨询记录同步为客户记录"""
    try:
        # 获取所有没有对应客户记录的咨询
        inquiries = ProjectInquiry.query.filter(
            ~ProjectInquiry.client_email.in_(
                Customer.query.with_entities(Customer.email).subquery()
            )
        ).all()
        
        created_count = 0
        
        for inquiry in inquiries:
            # 创建客户记录
            customer = Customer(
                name=inquiry.client_name,
                email=inquiry.client_email,
                phone=inquiry.client_phone or '',
                company=inquiry.client_company or '',
                title=inquiry.client_position or '',
                customer_type='潜在客户',
                lead_source='网站咨询',
                first_contact=inquiry.created_at,
                last_contact=inquiry.updated_at
            )
            
            from app import db
            db.session.add(customer)
            db.session.flush()  # 获取customer.id
            
            # 关联咨询记录
            inquiry.customer_id = customer.id
            
            # 更新线索评分
            customer.update_lead_score()
            customer.calculate_conversion_probability()
            
            created_count += 1
        
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'成功同步创建了 {created_count} 个客户记录',
            'created_count': created_count
        })
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'同步失败：{str(e)}'
        }), 500