"""
🔧 工具类包初始化
统一导入所有工具模块
"""
from .content_utils import (
    render_markdown, extract_summary, generate_slug,
    get_featured_content, get_recent_content, get_mixed_recent_content,
    get_category_emoji, validate_image_file, process_uploaded_image,
    count_words, estimate_reading_time, generate_toc
)

from .email_utils import (
    EmailSender, EmailTemplates,
    send_inquiry_notification, send_inquiry_confirmation, 
    send_inquiry_response, send_newsletter
)

__all__ = [
    # 内容工具
    'render_markdown', 'extract_summary', 'generate_slug',
    'get_featured_content', 'get_recent_content', 'get_mixed_recent_content',
    'get_category_emoji', 'validate_image_file', 'process_uploaded_image',
    'count_words', 'estimate_reading_time', 'generate_toc',
    
    # 邮件工具
    'EmailSender', 'EmailTemplates',
    'send_inquiry_notification', 'send_inquiry_confirmation',
    'send_inquiry_response', 'send_newsletter'
]