"""
📝 内容处理工具类
🔷 backend-architect 设计的内容管理工具函数
"""
import re
from datetime import datetime
from app.models import Content, Project


def render_markdown(text):
    """
    渲染Markdown文本为HTML
    
    Args:
        text (str): Markdown文本
        
    Returns:
        str: 渲染后的HTML
    """
    if not text:
        return ''
    
    import markdown
    from markdown.extensions import codehilite, toc, tables
    
    # Markdown扩展配置
    extensions = [
        'codehilite',  # 代码高亮
        'toc',         # 目录生成
        'tables',      # 表格支持
        'fenced_code', # 围栏代码块
        'nl2br',       # 换行转换
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
    return md.convert(text)


def extract_summary(content, length=150):
    """
    从内容中提取摘要
    
    Args:
        content (str): 原始内容
        length (int): 摘要长度
        
    Returns:
        str: 内容摘要
    """
    if not content:
        return ""
    
    # 移除Markdown标记
    text = re.sub(r'[#*`\[\]()_~]', '', content)
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


def generate_slug(title):
    """
    生成URL友好的slug
    
    Args:
        title (str): 标题
        
    Returns:
        str: URL slug
    """
    try:
        from unidecode import unidecode
        slug = unidecode(title).lower()
    except ImportError:
        # 如果没有unidecode，使用简单转换
        slug = title.lower()
    
    slug = re.sub(r'[^a-z0-9\u4e00-\u9fff]+', '-', slug)
    slug = slug.strip('-')
    
    return slug


def get_featured_content(limit=3):
    """
    获取精选内容
    
    Args:
        limit (int): 返回数量限制
        
    Returns:
        list: 精选内容列表
    """
    return Content.query.filter_by(is_published=True, is_featured=True)\
                        .order_by(Content.created_at.desc())\
                        .limit(limit).all()


def get_recent_content(limit=5, category=None):
    """
    获取最新内容
    
    Args:
        limit (int): 返回数量限制
        category (str): 内容分类过滤
        
    Returns:
        list: 最新内容列表
    """
    query = Content.query.filter_by(is_published=True)
    
    if category:
        query = query.filter_by(category=category)
    
    return query.order_by(Content.created_at.desc()).limit(limit).all()


def get_mixed_recent_content(limit=10):
    """
    获取混合类型的最新内容 (所有分类)
    
    Args:
        limit (int): 返回数量限制
        
    Returns:
        list: 混合内容列表，包含类型标识
    """
    # 获取内容
    contents = Content.query.filter_by(is_published=True)\
                           .order_by(Content.created_at.desc())\
                           .limit(limit//2).all()
    
    # 获取项目
    projects = Project.query.filter_by(is_published=True)\
                           .order_by(Project.completion_date.desc().nullslast())\
                           .limit(limit//2).all()
    
    # 混合和排序
    mixed_items = []
    
    for content in contents:
        mixed_items.append({
            'type': 'content',
            'item': content,
            'date': content.created_at,
            'category': content.category,
            'emoji': get_category_emoji(content.category)
        })
    
    for project in projects:
        mixed_items.append({
            'type': 'project',
            'item': project,
            'date': project.completion_date or project.created_at,
            'category': '项目',
            'emoji': '💼'
        })
    
    # 按日期排序
    mixed_items.sort(key=lambda x: x['date'], reverse=True)
    
    return mixed_items[:limit]


def get_category_emoji(category):
    """
    获取分类对应的emoji
    
    Args:
        category (str): 内容分类
        
    Returns:
        str: 对应的emoji
    """
    emoji_mapping = {
        '技术': '💻',
        '观察': '📰',
        '生活': '🌊',
        '创作': '🎨',
        '代码': '🔧',
        '项目': '💼'
    }
    return emoji_mapping.get(category, '📄')


def validate_image_file(file):
    """
    验证上传的图片文件
    
    Args:
        file: Flask文件对象
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not file:
        return False, "没有选择文件"
    
    if file.filename == '':
        return False, "文件名为空"
    
    # 检查文件扩展名
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    if '.' not in file.filename:
        return False, "文件没有扩展名"
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        return False, f"不支持的文件格式，请使用: {', '.join(allowed_extensions)}"
    
    # 检查文件大小 (这里需要读取文件内容)
    # 注意：这会移动文件指针，使用后需要seek(0)
    file.seek(0, 2)  # 移动到文件末尾
    size = file.tell()
    file.seek(0)     # 重置文件指针
    
    max_size = 5 * 1024 * 1024  # 5MB
    if size > max_size:
        return False, f"文件太大，请选择小于{max_size//1024//1024}MB的文件"
    
    return True, ""


def process_uploaded_image(file, upload_folder, max_width=1200):
    """
    处理上传的图片 (压缩、重命名等)
    
    Args:
        file: Flask文件对象
        upload_folder: 上传目录
        max_width: 最大宽度
        
    Returns:
        str: 保存后的文件名
    """
    import os
    from PIL import Image
    import uuid
    
    # 生成唯一文件名
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_folder, filename)
    
    # 确保上传目录存在
    os.makedirs(upload_folder, exist_ok=True)
    
    try:
        # 打开图片
        image = Image.open(file)
        
        # 转换为RGB (如果是RGBA)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # 调整大小 (保持纵横比)
        if image.width > max_width:
            ratio = max_width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # 保存 (优化质量)
        if ext.lower() in ['jpg', 'jpeg']:
            image.save(filepath, 'JPEG', quality=85, optimize=True)
        else:
            image.save(filepath, optimize=True)
        
        return filename
        
    except Exception as e:
        # 如果图片处理失败，直接保存原文件
        file.seek(0)
        file.save(filepath)
        return filename


def count_words(text):
    """
    统计文本字数 (中英文混合)
    
    Args:
        text (str): 文本内容
        
    Returns:
        int: 字数统计
    """
    if not text:
        return 0
    
    # 移除Markdown标记
    clean_text = re.sub(r'[#*`\[\]()_~]', '', text)
    clean_text = re.sub(r'\n+', ' ', clean_text)
    
    # 分别统计中文字符和英文单词
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', clean_text)
    english_words = re.findall(r'[a-zA-Z]+', clean_text)
    
    return len(chinese_chars) + len(english_words)


def estimate_reading_time(text):
    """
    估算阅读时间 (分钟)
    
    Args:
        text (str): 文本内容
        
    Returns:
        int: 预估阅读时间 (分钟)
    """
    word_count = count_words(text)
    
    # 假设中文200字/分钟，英文250词/分钟，取平均值
    reading_speed = 225  # 字/分钟
    
    minutes = max(1, round(word_count / reading_speed))
    return minutes


def generate_toc(content):
    """
    生成文章目录 (Table of Contents)
    
    Args:
        content (str): Markdown内容
        
    Returns:
        list: 目录项列表 [{'level': 1, 'title': 'xxx', 'anchor': 'xxx'}]
    """
    if not content:
        return []
    
    toc_items = []
    
    # 提取标题
    headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
    
    for heading_match in headings:
        level = len(heading_match[0])  # #的数量
        title = heading_match[1].strip()
        
        # 生成锚点
        anchor = generate_slug(title)
        
        toc_items.append({
            'level': level,
            'title': title,
            'anchor': anchor
        })
    
    return toc_items