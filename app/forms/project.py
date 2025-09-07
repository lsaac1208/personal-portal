"""
💼 项目表单类
🔷 backend-architect 设计的项目管理表单
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, BooleanField, DateField, IntegerField, FieldList, FormField
from wtforms.validators import DataRequired, Length, Optional, URL, NumberRange
from datetime import datetime


class TechStackField(FlaskForm):
    """
    🔧 技术栈字段（子表单）
    用于动态添加项目使用的技术
    """
    name = StringField('技术名称', 
                      validators=[DataRequired(), Length(max=50)],
                      render_kw={'placeholder': '如：Python, React, MySQL'})
    
    category = SelectField('技术类别',
                          choices=[
                              ('语言', '编程语言'),
                              ('框架', '框架/库'),
                              ('数据库', '数据库'),
                              ('工具', '开发工具'),
                              ('平台', '部署平台')
                          ])


class ProjectForm(FlaskForm):
    """
    💼 项目创建/编辑表单
    支持作品集项目的完整管理
    """
    
    # 基础项目信息
    title = StringField('项目标题', 
                       validators=[DataRequired(message='项目标题不能为空'), 
                                 Length(max=200, message='标题长度不能超过200字符')],
                       render_kw={'placeholder': '输入项目标题...'})
    
    subtitle = StringField('项目副标题',
                          validators=[Optional(), Length(max=300, message='副标题不能超过300字符')],
                          render_kw={'placeholder': '简短的项目描述（可选）'})
    
    # 项目分类
    category = SelectField('项目类型',
                          choices=[
                              ('Web应用', 'Web应用 🌐'),
                              ('移动应用', '移动应用 📱'),
                              ('桌面应用', '桌面应用 💻'),
                              ('数据分析', '数据分析 📊'),
                              ('机器学习', '机器学习 🤖'),
                              ('游戏开发', '游戏开发 🎮'),
                              ('工具/库', '工具/库 🔧'),
                              ('其他', '其他 📦')
                          ],
                          validators=[DataRequired(message='请选择项目类型')])
    
    # 项目内容
    description = TextAreaField('项目描述',
                               validators=[DataRequired(message='项目描述不能为空')],
                               render_kw={
                                   'placeholder': '详细描述项目功能、特色和技术亮点（支持Markdown）',
                                   'rows': 10,
                                   'class': 'markdown-editor'
                               })
    
    features = TextAreaField('主要功能',
                            validators=[Optional(), Length(max=2000)],
                            render_kw={
                                'placeholder': '列出项目的主要功能和特色（每行一个，支持Markdown）',
                                'rows': 6
                            })
    
    challenges = TextAreaField('技术挑战',
                              validators=[Optional(), Length(max=1500)],
                              render_kw={
                                  'placeholder': '描述开发过程中遇到的技术挑战和解决方案',
                                  'rows': 5
                              })
    
    # 项目链接
    demo_url = StringField('演示链接',
                          validators=[Optional(), URL(message='请输入有效的URL')],
                          render_kw={'placeholder': 'https://demo.example.com'})
    
    github_url = StringField('GitHub链接',
                            validators=[Optional(), URL(message='请输入有效的GitHub URL')],
                            render_kw={'placeholder': 'https://github.com/username/project'})
    
    documentation_url = StringField('文档链接',
                                   validators=[Optional(), URL(message='请输入有效的URL')],
                                   render_kw={'placeholder': 'https://docs.example.com'})
    
    # 项目时间线
    start_date = DateField('开始日期',
                          validators=[DataRequired(message='请选择开始日期')],
                          default=datetime.utcnow)
    
    completion_date = DateField('完成日期',
                               validators=[Optional()],
                               render_kw={'placeholder': '如果项目已完成'})
    
    # 项目规模
    team_size = IntegerField('团队人数',
                            validators=[Optional(), NumberRange(min=1, max=100, message='团队人数必须在1-100之间')],
                            default=1,
                            render_kw={'placeholder': '1'})
    
    duration_months = IntegerField('项目周期（月）',
                                  validators=[Optional(), NumberRange(min=1, max=60, message='项目周期必须在1-60个月之间')],
                                  render_kw={'placeholder': '1'})
    
    # 技术栈（使用JSON字段存储）
    tech_stack = TextAreaField('技术栈',
                              validators=[Optional()],
                              render_kw={
                                  'placeholder': '使用的技术和工具，用逗号分隔\n如：Python, Flask, PostgreSQL, Redis, Docker',
                                  'rows': 3
                              })
    
    # 媒体文件
    featured_image = FileField('项目展示图',
                              validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 
                                                                 message='请上传图片文件 (jpg, png, gif, webp)')],
                              render_kw={'accept': 'image/*'})
    
    # 项目状态
    status = SelectField('项目状态',
                        choices=[
                            ('规划中', '规划中 📋'),
                            ('开发中', '开发中 🔨'),
                            ('测试中', '测试中 🧪'),
                            ('已完成', '已完成 ✅'),
                            ('已暂停', '已暂停 ⏸️'),
                            ('已取消', '已取消 ❌')
                        ],
                        default='开发中')
    
    priority = SelectField('优先级',
                          choices=[
                              ('低', '低优先级'),
                              ('中', '中优先级'),
                              ('高', '高优先级'),
                              ('紧急', '紧急')
                          ],
                          default='中')
    
    # 项目设置
    is_public = BooleanField('公开展示', default=True)
    is_featured = BooleanField('加入精选项目', default=False)
    allow_inquiries = BooleanField('允许项目咨询', default=True)
    
    # 项目标签
    tags = StringField('项目标签',
                      validators=[Optional()],
                      render_kw={'placeholder': '用逗号分隔，如：Web开发, Python, 全栈, 开源'})
    
    # 项目成果指标
    metrics = TextAreaField('项目成果',
                           validators=[Optional(), Length(max=1000)],
                           render_kw={
                               'placeholder': '项目的量化成果和影响力\n如：用户数量、性能提升、问题解决等',
                               'rows': 4
                           })


class ProjectFilterForm(FlaskForm):
    """
    📂 项目筛选表单 (作品集展示用)
    """
    
    category = SelectField('项目类型',
                          choices=[
                              ('', '全部类型'),
                              ('Web应用', 'Web应用'),
                              ('移动应用', '移动应用'),
                              ('桌面应用', '桌面应用'),
                              ('数据分析', '数据分析'),
                              ('机器学习', '机器学习'),
                              ('游戏开发', '游戏开发'),
                              ('工具/库', '工具/库'),
                              ('其他', '其他')
                          ],
                          default='')
    
    status = SelectField('项目状态',
                        choices=[
                            ('', '全部状态'),
                            ('规划中', '规划中'),
                            ('开发中', '开发中'),
                            ('测试中', '测试中'),
                            ('已完成', '已完成'),
                            ('已暂停', '已暂停')
                        ],
                        default='')
    
    tech_stack = StringField('技术栈筛选',
                            validators=[Optional()],
                            render_kw={'placeholder': '输入技术名称，如：Python, React'})
    
    featured = SelectField('精选项目',
                          choices=[
                              ('', '全部项目'),
                              ('yes', '精选项目'),
                              ('no', '普通项目')
                          ],
                          default='')
    
    sort_by = SelectField('排序方式',
                         choices=[
                             ('created_desc', '创建时间↓'),
                             ('created_asc', '创建时间↑'),
                             ('completion_desc', '完成时间↓'),
                             ('completion_asc', '完成时间↑'),
                             ('priority_desc', '优先级↓'),
                             ('title_asc', '标题A-Z')
                         ],
                         default='created_desc')


class ProjectSearchForm(FlaskForm):
    """
    🔍 项目搜索表单
    """
    
    query = StringField('搜索项目',
                       validators=[DataRequired(message='请输入搜索关键词')],
                       render_kw={
                           'placeholder': '搜索项目标题、描述、技术栈...',
                           'class': 'form-control-lg'
                       })
    
    search_type = SelectField('搜索范围',
                             choices=[
                                 ('all', '全部内容'),
                                 ('title', '仅标题'),
                                 ('description', '仅描述'),
                                 ('tech_stack', '仅技术栈'),
                                 ('tags', '仅标签')
                             ],
                             default='all')