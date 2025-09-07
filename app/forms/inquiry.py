"""
📨 咨询表单类
🔷 backend-architect 设计的项目咨询和联系表单
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, HiddenField, DateTimeField
from wtforms.validators import DataRequired, Length, Email, Optional, ValidationError
from datetime import datetime
import re


class ProjectInquiryForm(FlaskForm):
    """
    💼 项目咨询表单
    供访客提交项目合作咨询
    """
    
    # 联系人信息
    name = StringField('姓名/公司名称',
                      validators=[DataRequired(message='请填写您的姓名或公司名称'),
                                Length(min=2, max=100, message='姓名长度应在2-100字符之间')],
                      render_kw={'placeholder': '请输入您的姓名或公司名称'})
    
    email = StringField('邮箱地址',
                       validators=[DataRequired(message='请填写有效的邮箱地址'),
                                 Email(message='请输入正确的邮箱格式')],
                       render_kw={
                           'placeholder': 'your@email.com',
                           'type': 'email'
                       })
    
    phone = StringField('联系电话',
                       validators=[Optional(), Length(max=20, message='电话号码不能超过20位')],
                       render_kw={'placeholder': '可选：您的联系电话'})
    
    company = StringField('公司/机构',
                         validators=[Optional(), Length(max=200, message='公司名称不能超过200字符')],
                         render_kw={'placeholder': '可选：您的公司或机构名称'})
    
    position = StringField('职位',
                          validators=[Optional(), Length(max=100, message='职位不能超过100字符')],
                          render_kw={'placeholder': '可选：您的职位'})
    
    # 项目信息
    project_id = HiddenField('关联项目ID')  # 如果是从具体项目页面发起的咨询
    
    inquiry_type = SelectField('咨询类型',
                              choices=[
                                  ('项目合作', '项目合作 🤝'),
                                  ('技术咨询', '技术咨询 💡'),
                                  ('定制开发', '定制开发 🔧'),
                                  ('技术支持', '技术支持 🛠️'),
                                  ('商业合作', '商业合作 💼'),
                                  ('其他', '其他咨询 📋')
                              ],
                              validators=[DataRequired(message='请选择咨询类型')])
    
    subject = StringField('咨询主题',
                         validators=[DataRequired(message='请填写咨询主题'),
                                   Length(min=5, max=200, message='主题长度应在5-200字符之间')],
                         render_kw={'placeholder': '请简要描述您的咨询主题'})
    
    # 项目需求详情
    description = TextAreaField('详细描述',
                               validators=[DataRequired(message='请详细描述您的需求'),
                                         Length(min=20, max=2000, message='描述长度应在20-2000字符之间')],
                               render_kw={
                                   'placeholder': '请详细描述您的项目需求、预期目标、技术要求等...\n'
                                               '信息越详细，我们能提供越准确的解决方案。',
                                   'rows': 8
                               })
    
    # 项目预算和时间
    budget_range = SelectField('预算范围',
                              choices=[
                                  ('', '请选择预算范围'),
                                  ('5千以下', '5千以下 💰'),
                                  ('5千-1万', '5千-1万 💰💰'),
                                  ('1万-3万', '1万-3万 💰💰💰'),
                                  ('3万-10万', '3万-10万 💰💰💰💰'),
                                  ('10万以上', '10万以上 💰💰💰💰💰'),
                                  ('面议', '预算面议 💬')
                              ],
                              validators=[Optional()])
    
    timeline = SelectField('期望时间',
                          choices=[
                              ('', '请选择期望完成时间'),
                              ('1周内', '1周内 ⚡'),
                              ('1个月内', '1个月内 📅'),
                              ('3个月内', '3个月内 📆'),
                              ('半年内', '半年内 🗓️'),
                              ('1年内', '1年内 📋'),
                              ('时间灵活', '时间灵活 ⏰')
                          ],
                          validators=[Optional()])
    
    # 技术偏好
    preferred_tech = StringField('技术偏好',
                                validators=[Optional(), Length(max=500)],
                                render_kw={
                                    'placeholder': '可选：您希望使用的技术栈，如：Python, React, MySQL'
                                })
    
    # 附加信息
    additional_info = TextAreaField('补充信息',
                                   validators=[Optional(), Length(max=1000)],
                                   render_kw={
                                       'placeholder': '可选：任何其他您认为有助于了解需求的信息',
                                       'rows': 4
                                   })
    
    # 联系偏好
    contact_preference = SelectField('联系方式偏好',
                                    choices=[
                                        ('邮件', '邮件联系 📧'),
                                        ('电话', '电话联系 📞'),
                                        ('微信', '微信联系 💬'),
                                        ('任何方式', '任何方式都可以 📱')
                                    ],
                                    default='邮件')
    
    contact_time = SelectField('方便联系时间',
                              choices=[
                                  ('工作日上午', '工作日上午 (9-12点)'),
                                  ('工作日下午', '工作日下午 (14-18点)'),
                                  ('工作日晚上', '工作日晚上 (19-21点)'),
                                  ('周末', '周末时间'),
                                  ('任何时间', '任何时间都可以')
                              ],
                              default='任何时间')
    
    # 数据保护和同意
    privacy_agreement = BooleanField('隐私协议',
                                    validators=[DataRequired(message='请同意隐私协议')],
                                    label='我同意个人信息处理和使用条款')
    
    marketing_emails = BooleanField('营销邮件',
                                   default=False,
                                   label='我愿意接收技术分享和项目案例邮件（可选）')

    def validate_phone(self, field):
        """验证电话号码格式"""
        if field.data:
            # 简单的电话号码验证
            phone_pattern = r'^[\d\-\+\(\)\s]+$'
            if not re.match(phone_pattern, field.data):
                raise ValidationError('请输入有效的电话号码')


class InquiryResponseForm(FlaskForm):
    """
    💬 咨询回复表单
    管理员用于回复项目咨询
    """
    
    # 回复内容
    response = TextAreaField('回复内容',
                            validators=[DataRequired(message='请填写回复内容'),
                                      Length(min=10, max=2000, message='回复内容应在10-2000字符之间')],
                            render_kw={
                                'placeholder': '请填写对客户咨询的详细回复...',
                                'rows': 8
                            })
    
    # 状态更新
    status = SelectField('咨询状态',
                        choices=[
                            ('新咨询', '新咨询 🆕'),
                            ('处理中', '处理中 🔄'),
                            ('等待客户', '等待客户回复 ⏳'),
                            ('已报价', '已发送报价 💰'),
                            ('已成交', '项目成交 ✅'),
                            ('已拒绝', '项目拒绝 ❌'),
                            ('已关闭', '咨询关闭 🔒')
                        ])
    
    # 优先级
    priority = SelectField('优先级',
                          choices=[
                              ('低', '低优先级'),
                              ('中', '中优先级'),
                              ('高', '高优先级'),
                              ('紧急', '紧急处理')
                          ])
    
    # 预估信息
    estimated_budget = StringField('预估费用',
                                  validators=[Optional(), Length(max=100)],
                                  render_kw={'placeholder': '如：3-5万元'})
    
    estimated_timeline = StringField('预估周期',
                                    validators=[Optional(), Length(max=100)],
                                    render_kw={'placeholder': '如：2-3个月'})
    
    # 跟进信息
    next_contact_date = DateTimeField('下次联系时间',
                                     validators=[Optional()],
                                     format='%Y-%m-%d %H:%M')
    
    internal_notes = TextAreaField('内部备注',
                                  validators=[Optional(), Length(max=1000)],
                                  render_kw={
                                      'placeholder': '内部备注信息（客户不可见）',
                                      'rows': 4
                                  })
    
    # 发送邮件通知
    send_email = BooleanField('发送邮件通知', 
                             default=True,
                             label='向客户发送邮件通知')


class ContactForm(FlaskForm):
    """
    📞 通用联系表单
    用于一般的联系和反馈
    """
    
    name = StringField('姓名',
                      validators=[DataRequired(message='请填写您的姓名'),
                                Length(min=2, max=50, message='姓名长度应在2-50字符之间')],
                      render_kw={'placeholder': '请输入您的姓名'})
    
    email = StringField('邮箱地址',
                       validators=[DataRequired(message='请填写有效的邮箱地址'),
                                 Email(message='请输入正确的邮箱格式')],
                       render_kw={
                           'placeholder': 'your@email.com',
                           'type': 'email'
                       })
    
    subject = StringField('主题',
                         validators=[DataRequired(message='请填写主题'),
                                   Length(min=5, max=200, message='主题长度应在5-200字符之间')],
                         render_kw={'placeholder': '请输入联系主题'})
    
    message = TextAreaField('消息内容',
                           validators=[DataRequired(message='请填写消息内容'),
                                     Length(min=10, max=1000, message='消息长度应在10-1000字符之间')],
                           render_kw={
                               'placeholder': '请详细描述您的问题或建议...',
                               'rows': 6
                           })
    
    contact_type = SelectField('联系类型',
                              choices=[
                                  ('一般咨询', '一般咨询'),
                                  ('技术问题', '技术问题'),
                                  ('合作建议', '合作建议'),
                                  ('bug反馈', 'Bug反馈'),
                                  ('功能建议', '功能建议'),
                                  ('其他', '其他')
                              ],
                              default='一般咨询')


class NewsletterForm(FlaskForm):
    """
    📧 邮件订阅表单
    用于技术博客和项目更新订阅
    """
    
    email = StringField('邮箱地址',
                       validators=[DataRequired(message='请填写有效的邮箱地址'),
                                 Email(message='请输入正确的邮箱格式')],
                       render_kw={
                           'placeholder': 'your@email.com',
                           'type': 'email',
                           'class': 'form-control-lg'
                       })
    
    interests = SelectField('感兴趣的内容',
                           choices=[
                               ('技术文章', '技术文章和教程'),
                               ('项目更新', '项目进展和案例'),
                               ('行业观察', '行业观察和趋势'),
                               ('全部内容', '全部内容更新')
                           ],
                           default='全部内容')
    
    frequency = SelectField('邮件频率',
                           choices=[
                               ('即时', '有新内容立即通知'),
                               ('每周', '每周汇总'),
                               ('每月', '每月精选'),
                           ],
                           default='每周')