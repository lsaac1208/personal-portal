"""
📋 内容表单类
🔶 frontend-developer 设计的内容管理表单
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, BooleanField, DateField
from wtforms.validators import DataRequired, Length, Optional, URL
from wtforms.widgets import TextArea


class ContentForm(FlaskForm):
    """
    📝 内容创建/编辑表单
    支持所有内容类型的统一管理
    """
    
    # 基础信息
    title = StringField('标题', 
                       validators=[DataRequired(message='标题不能为空'), 
                                 Length(max=200, message='标题长度不能超过200字符')],
                       render_kw={'placeholder': '输入文章标题...'})
    
    category = SelectField('分类',
                          choices=[
                              ('技术', '技术💻'),
                              ('观察', '观察📰'),
                              ('生活', '生活🌊'),
                              ('创作', '创作🎨'),
                              ('代码', '代码🔧')
                          ],
                          validators=[DataRequired(message='请选择内容分类')])
    
    # 内容字段
    content = TextAreaField('内容',
                           validators=[DataRequired(message='内容不能为空')],
                           render_kw={
                               'placeholder': '支持Markdown格式...',
                               'rows': 20,
                               'class': 'markdown-editor'
                           })
    
    summary = TextAreaField('摘要',
                           validators=[Optional(), Length(max=500, message='摘要不能超过500字符')],
                           render_kw={
                               'placeholder': '简要描述文章内容（可选，系统会自动生成）',
                               'rows': 3
                           })
    
    # 分类和标签
    tags = StringField('标签',
                      validators=[Optional()],
                      render_kw={'placeholder': '用逗号分隔，如：Python, Flask, Web开发'})
    
    # 媒体文件
    featured_image = FileField('特色图片',
                              validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 
                                                                 message='请上传图片文件 (jpg, png, gif, webp)')],
                              render_kw={'accept': 'image/*'})
    
    # 外部来源 (转载文章用)
    source_type = SelectField('来源类型',
                             choices=[
                                 ('原创', '原创'),
                                 ('转载', '转载')
                             ],
                             default='原创')
    
    source_url = StringField('来源链接',
                            validators=[Optional(), URL(message='请输入有效的URL')],
                            render_kw={'placeholder': 'https://...'})
    
    source_author = StringField('原作者',
                               validators=[Optional(), Length(max=100, message='作者名不能超过100字符')],
                               render_kw={'placeholder': '原作者姓名（转载时填写）'})
    
    # 状态设置
    is_published = BooleanField('立即发布', default=True)
    is_featured = BooleanField('加入精选推荐')
    
    # SEO设置
    seo_title = StringField('SEO标题',
                           validators=[Optional(), Length(max=200, message='SEO标题不能超过200字符')],
                           render_kw={'placeholder': '搜索引擎显示标题（可选）'})
    
    seo_description = TextAreaField('SEO描述',
                                   validators=[Optional(), Length(max=300, message='SEO描述不能超过300字符')],
                                   render_kw={
                                       'placeholder': '搜索引擎显示描述（可选）',
                                       'rows': 2
                                   })
    
    seo_keywords = StringField('SEO关键词',
                              validators=[Optional(), Length(max=500, message='关键词不能超过500字符')],
                              render_kw={'placeholder': '用逗号分隔关键词（可选）'})


class CodeSnippetForm(FlaskForm):
    """
    🔧 代码片段专用表单
    """
    
    title = StringField('代码片段标题', 
                       validators=[DataRequired(), Length(max=200)],
                       render_kw={'placeholder': '如：Python快速排序算法'})
    
    language = SelectField('编程语言',
                          choices=[
                              ('python', 'Python'),
                              ('javascript', 'JavaScript'),
                              ('typescript', 'TypeScript'),
                              ('html', 'HTML'),
                              ('css', 'CSS'),
                              ('sql', 'SQL'),
                              ('bash', 'Bash'),
                              ('java', 'Java'),
                              ('cpp', 'C++'),
                              ('go', 'Go'),
                              ('rust', 'Rust'),
                              ('php', 'PHP'),
                              ('other', '其他')
                          ],
                          validators=[DataRequired()])
    
    code = TextAreaField('代码内容',
                        validators=[DataRequired()],
                        render_kw={
                            'placeholder': '粘贴或输入代码...',
                            'rows': 15,
                            'class': 'code-editor',
                            'spellcheck': 'false'
                        })
    
    description = TextAreaField('代码说明',
                               validators=[Optional(), Length(max=1000)],
                               render_kw={
                                   'placeholder': '解释代码功能、用法等（支持Markdown）',
                                   'rows': 5
                               })
    
    difficulty = SelectField('难度级别',
                            choices=[
                                ('初级', '初级'),
                                ('中级', '中级'),
                                ('高级', '高级')
                            ],
                            default='中级')
    
    tags = StringField('技术标签',
                      render_kw={'placeholder': '算法, 排序, 数据结构'})
    
    is_published = BooleanField('立即发布', default=True)


class ContentSearchForm(FlaskForm):
    """
    🔍 内容搜索表单
    """
    
    query = StringField('搜索关键词',
                       validators=[DataRequired(message='请输入搜索关键词')],
                       render_kw={
                           'placeholder': '搜索文章、项目、代码片段...',
                           'class': 'form-control-lg'
                       })
    
    category = SelectField('分类筛选',
                          choices=[
                              ('', '全部分类'),
                              ('技术', '技术💻'),
                              ('观察', '观察📰'),
                              ('生活', '生活🌊'),
                              ('创作', '创作🎨'),
                              ('代码', '代码🔧'),
                              ('项目', '项目💼')
                          ],
                          default='')


class ContentFilterForm(FlaskForm):
    """
    📂 内容筛选表单 (后台管理用)
    """
    
    category = SelectField('分类',
                          choices=[
                              ('', '全部分类'),
                              ('技术', '技术'),
                              ('观察', '观察'),
                              ('生活', '生活'),
                              ('创作', '创作'),
                              ('代码', '代码')
                          ],
                          default='')
    
    status = SelectField('状态',
                        choices=[
                            ('', '全部状态'),
                            ('published', '已发布'),
                            ('draft', '草稿')
                        ],
                        default='')
    
    featured = SelectField('推荐',
                          choices=[
                              ('', '全部'),
                              ('yes', '精选推荐'),
                              ('no', '普通内容')
                          ],
                          default='')
    
    date_from = DateField('开始日期', validators=[Optional()])
    date_to = DateField('结束日期', validators=[Optional()])