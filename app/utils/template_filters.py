"""
🎨 模板过滤器工具
📊 data-scientist 设计的模板增强工具集
"""
from flask import current_app


def get_language_color(language_name: str) -> str:
    """
    获取编程语言对应的颜色
    
    Args:
        language_name: 编程语言名称
        
    Returns:
        颜色的十六进制代码
    """
    # GitHub官方语言颜色映射
    language_colors = {
        'Python': '#3776ab',
        'JavaScript': '#f1e05a', 
        'TypeScript': '#2b7489',
        'Java': '#b07219',
        'Go': '#00add8',
        'Rust': '#dea584',
        'C++': '#f34b7d',
        'C': '#555555',
        'CSS': '#563d7c',
        'HTML': '#e34c26',
        'Shell': '#89e051',
        'Vue': '#2c3e50',
        'React': '#61dafb',
        'PHP': '#4f5d95',
        'Ruby': '#701516',
        'Swift': '#ffac45',
        'Kotlin': '#f18e33',
        'Scala': '#c22d40',
        'R': '#198ce7',
        'Dart': '#00b4ab',
        'Elixir': '#6e4a7e',
        'Haskell': '#5e5086',
        'Lua': '#000080',
        'Perl': '#0298c3',
        'PowerShell': '#012456',
        'Objective-C': '#438eff',
        'C#': '#239120',
        'F#': '#b845fc',
        'Clojure': '#db5855',
        'CoffeeScript': '#244776',
        'Erlang': '#b83998',
        'OCaml': '#3be133',
        'Scheme': '#1e4aec',
        'Assembly': '#6e4c13',
        'Makefile': '#427819',
        'Dockerfile': '#384d54',
        'YAML': '#cb171e',
        'JSON': '#292929',
        'XML': '#0060ac',
        'Markdown': '#083fa1',
        'LaTeX': '#3d6117',
    }
    
    # 返回对应颜色，如果没找到则返回默认灰色
    return language_colors.get(language_name, '#6c757d')


def format_number(number: int, threshold: int = 1000) -> str:
    """
    格式化数字显示
    
    Args:
        number: 要格式化的数字
        threshold: 使用K表示的阈值
        
    Returns:
        格式化后的字符串
    """
    if not isinstance(number, (int, float)):
        return str(number)
    
    if number >= 1000000:
        return f"{number / 1000000:.1f}M"
    elif number >= threshold:
        return f"{number / 1000:.1f}K"
    else:
        return str(int(number))


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        格式化的文件大小字符串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def truncate_commit_message(message: str, max_length: int = 50) -> str:
    """
    截断Git提交信息
    
    Args:
        message: 提交信息
        max_length: 最大长度
        
    Returns:
        截断后的提交信息
    """
    if not message:
        return ""
    
    # 只取第一行
    first_line = message.split('\n')[0].strip()
    
    if len(first_line) <= max_length:
        return first_line
    
    return first_line[:max_length - 3] + "..."


def time_ago(date_string: str) -> str:
    """
    计算相对时间
    
    Args:
        date_string: ISO格式的日期字符串
        
    Returns:
        相对时间字符串
    """
    if not date_string:
        return ""
    
    try:
        from datetime import datetime, timezone
        import re
        
        # 处理不同的日期格式
        if date_string.endswith('Z'):
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        elif '+' in date_string[-6:] or '-' in date_string[-6:]:
            dt = datetime.fromisoformat(date_string)
        else:
            # 假设是UTC时间
            dt = datetime.fromisoformat(date_string).replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        diff = now - dt
        
        days = diff.days
        seconds = diff.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if days > 365:
            years = days // 365
            return f"{years}年前"
        elif days > 30:
            months = days // 30
            return f"{months}个月前"
        elif days > 0:
            return f"{days}天前"
        elif hours > 0:
            return f"{hours}小时前"
        elif minutes > 0:
            return f"{minutes}分钟前"
        else:
            return "刚刚"
            
    except Exception:
        return date_string


def github_status_badge(status: dict) -> str:
    """
    生成GitHub状态徽章HTML
    
    Args:
        status: GitHub仓库状态信息
        
    Returns:
        徽章HTML字符串
    """
    if not status or not status.get('available'):
        return ""
    
    badges = []
    
    # 星数徽章
    if status.get('stars', 0) > 0:
        badges.append(f'<span class="badge bg-warning text-dark me-1">'
                     f'<i class="fas fa-star"></i> {format_number(status["stars"])}</span>')
    
    # 派生数徽章
    if status.get('forks', 0) > 0:
        badges.append(f'<span class="badge bg-info text-white me-1">'
                     f'<i class="fas fa-code-branch"></i> {format_number(status["forks"])}</span>')
    
    # 主要语言徽章
    if status.get('language'):
        color = get_language_color(status['language'])
        badges.append(f'<span class="badge me-1" style="background-color: {color}; color: white;">'
                     f'{status["language"]}</span>')
    
    # 许可证徽章
    if status.get('license'):
        badges.append(f'<span class="badge bg-secondary text-white me-1">'
                     f'<i class="fas fa-balance-scale"></i> {status["license"]}</span>')
    
    return ' '.join(badges)


def highlight_search(text: str, search_query: str) -> str:
    """
    在文本中高亮搜索关键词
    
    Args:
        text: 原始文本
        search_query: 搜索关键词
        
    Returns:
        高亮处理后的HTML字符串
    """
    if not text or not search_query:
        return text
    
    # 转义HTML特殊字符
    import html
    import re
    
    # 如果文本已经是HTML，先处理掉标签
    clean_text = re.sub(r'<[^>]+>', '', str(text))
    escaped_text = html.escape(clean_text)
    
    # 转义搜索查询中的特殊正则字符
    escaped_query = re.escape(search_query.strip())
    
    if not escaped_query:
        return escaped_text
    
    # 使用正则表达式进行不区分大小写的搜索和替换
    pattern = re.compile(escaped_query, re.IGNORECASE)
    highlighted = pattern.sub(
        lambda m: f'<mark class="bg-warning text-dark">{m.group()}</mark>',
        escaped_text
    )
    
    return highlighted


def register_template_filters(app):
    """
    注册所有模板过滤器到Flask应用
    
    Args:
        app: Flask应用实例
    """
    app.jinja_env.filters['get_language_color'] = get_language_color
    app.jinja_env.filters['format_number'] = format_number
    app.jinja_env.filters['format_file_size'] = format_file_size
    app.jinja_env.filters['truncate_commit'] = truncate_commit_message
    app.jinja_env.filters['time_ago'] = time_ago
    app.jinja_env.filters['github_status_badge'] = github_status_badge
    app.jinja_env.filters['highlight_search'] = highlight_search