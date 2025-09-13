"""
🔗 URL友好链接生成器
生成SEO友好的URL slug，支持中文转拼音和多语言处理
"""
import re
import unicodedata
from datetime import datetime
from pypinyin import lazy_pinyin, Style


class SlugGenerator:
    """URL Slug 生成器"""
    
    def __init__(self):
        # 常用词汇映射表
        self.common_mappings = {
            # 技术术语
            'javascript': 'js',
            'typescript': 'ts', 
            'python': 'py',
            'artificial-intelligence': 'ai',
            'machine-learning': 'ml',
            'deep-learning': 'dl',
            'application-programming-interface': 'api',
            'user-interface': 'ui',
            'user-experience': 'ux',
            'database': 'db',
            'development': 'dev',
            'production': 'prod',
            
            # 中文常用词
            '人工智能': 'ai',
            '机器学习': 'ml', 
            '深度学习': 'dl',
            '数据库': 'database',
            '应用程序': 'app',
            '编程接口': 'api',
            '用户界面': 'ui',
            '用户体验': 'ux',
            '开发': 'dev',
            '生产': 'prod',
            '测试': 'test',
            '项目': 'project',
            '系统': 'system',
            '网站': 'website',
            '博客': 'blog',
            '文章': 'article',
            '教程': 'tutorial',
            '指南': 'guide',
        }
        
        # 停用词列表（URL中应避免的词）
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were',
            '的', '了', '是', '在', '我', '有', '和', '就', '不', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着'
        }
    
    def generate_slug(self, title, max_length=60, use_pinyin=True, include_date=False):
        """
        生成URL友好的slug
        
        Args:
            title: 标题文本
            max_length: 最大长度限制
            use_pinyin: 是否将中文转换为拼音
            include_date: 是否包含日期
        
        Returns:
            生成的slug字符串
        """
        if not title:
            return self._generate_fallback_slug()
        
        # 1. 基础清理
        slug = title.lower().strip()
        
        # 2. 应用常用词映射
        slug = self._apply_mappings(slug)
        
        # 3. 中文处理
        if use_pinyin:
            slug = self._chinese_to_pinyin(slug)
        
        # 4. 英文和特殊字符处理
        slug = self._clean_english_text(slug)
        
        # 5. 移除停用词
        slug = self._remove_stop_words(slug)
        
        # 6. 规范化处理
        slug = self._normalize_slug(slug)
        
        # 7. 长度限制
        slug = self._truncate_slug(slug, max_length)
        
        # 8. 添加日期前缀（可选）
        if include_date:
            date_prefix = datetime.now().strftime('%Y%m%d')
            slug = f"{date_prefix}-{slug}"
        
        # 9. 最终验证
        slug = self._validate_slug(slug)
        
        return slug
    
    def _apply_mappings(self, text):
        """应用常用词汇映射"""
        for original, mapped in self.common_mappings.items():
            text = text.replace(original, mapped)
        return text
    
    def _chinese_to_pinyin(self, text):
        """中文转拼音"""
        # 提取中文字符
        chinese_pattern = r'[\u4e00-\u9fff]+'
        chinese_matches = re.findall(chinese_pattern, text)
        
        for match in chinese_matches:
            # 转换为拼音
            pinyin_list = lazy_pinyin(match, style=Style.NORMAL)
            pinyin_text = '-'.join(pinyin_list)
            text = text.replace(match, pinyin_text)
        
        return text
    
    def _clean_english_text(self, text):
        """清理英文文本和特殊字符"""
        # Unicode标准化
        text = unicodedata.normalize('NFKD', text)
        
        # 移除重音符号
        text = ''.join(c for c in text if not unicodedata.combining(c))
        
        # 替换特殊字符
        replacements = {
            '&': 'and',
            '+': 'plus',
            '@': 'at',
            '#': 'hash',
            '%': 'percent',
            '=': 'equals',
            '<': 'lt',
            '>': 'gt',
            '|': 'or',
            '\\': 'backslash',
            '/': 'slash',
            '?': 'question',
            '!': 'exclamation',
            '*': 'star',
            '"': 'quote',
            "'": 'quote',
            '(': '',
            ')': '',
            '[': '',
            ']': '',
            '{': '',
            '}': '',
            '：': 'colon',
            '；': 'semicolon',
            '，': 'comma',
            '。': 'period',
            '！': 'exclamation',
            '？': 'question',
            '（': '',
            '）': '',
            '【': '',
            '】': '',
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, f'-{replacement}-' if replacement else '-')
        
        return text
    
    def _remove_stop_words(self, text):
        """移除停用词"""
        words = text.split('-')
        filtered_words = [word for word in words if word and word not in self.stop_words and len(word) > 1]
        return '-'.join(filtered_words)
    
    def _normalize_slug(self, slug):
        """规范化slug"""
        # 只保留字母、数字和连字符
        slug = re.sub(r'[^a-zA-Z0-9\-]', '-', slug)
        
        # 将多个连续的连字符替换为单个
        slug = re.sub(r'-+', '-', slug)
        
        # 移除开头和结尾的连字符
        slug = slug.strip('-')
        
        return slug
    
    def _truncate_slug(self, slug, max_length):
        """截断slug到指定长度"""
        if len(slug) <= max_length:
            return slug
        
        # 在单词边界截断
        truncated = slug[:max_length]
        last_dash = truncated.rfind('-')
        
        if last_dash > max_length * 0.7:  # 如果截断点在合理范围内
            truncated = truncated[:last_dash]
        
        return truncated.rstrip('-')
    
    def _validate_slug(self, slug):
        """验证和修复slug"""
        if not slug:
            return self._generate_fallback_slug()
        
        # 确保slug不以数字开头（某些系统要求）
        if slug[0].isdigit():
            slug = f"post-{slug}"
        
        # 确保最小长度
        if len(slug) < 3:
            slug = f"{slug}-post"
        
        return slug
    
    def _generate_fallback_slug(self):
        """生成后备slug"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"post-{timestamp}"
    
    def batch_generate_slugs(self, titles, **kwargs):
        """批量生成slug"""
        slugs = {}
        used_slugs = set()
        
        for title in titles:
            base_slug = self.generate_slug(title, **kwargs)
            unique_slug = self._ensure_unique_slug(base_slug, used_slugs)
            slugs[title] = unique_slug
            used_slugs.add(unique_slug)
        
        return slugs
    
    def _ensure_unique_slug(self, slug, used_slugs):
        """确保slug唯一性"""
        if slug not in used_slugs:
            return slug
        
        counter = 1
        while f"{slug}-{counter}" in used_slugs:
            counter += 1
        
        return f"{slug}-{counter}"
    
    def suggest_slug_variations(self, title, count=5):
        """生成slug变体建议"""
        variations = []
        
        # 基础版本
        base_slug = self.generate_slug(title)
        variations.append(('标准版', base_slug))
        
        # 短版本
        short_slug = self.generate_slug(title, max_length=30)
        if short_slug != base_slug:
            variations.append(('简短版', short_slug))
        
        # 包含日期版本
        date_slug = self.generate_slug(title, include_date=True)
        variations.append(('日期版', date_slug))
        
        # 不使用拼音版本
        no_pinyin_slug = self.generate_slug(title, use_pinyin=False)
        if no_pinyin_slug != base_slug:
            variations.append(('英文版', no_pinyin_slug))
        
        # 紧凑版本（移除更多停用词）
        compact_slug = self._generate_compact_slug(title)
        if compact_slug != base_slug:
            variations.append(('紧凑版', compact_slug))
        
        return variations[:count]
    
    def _generate_compact_slug(self, title):
        """生成紧凑版slug（更激进的词汇移除）"""
        # 扩展停用词列表
        extended_stop_words = self.stop_words.union({
            'how', 'what', 'when', 'where', 'why', 'which', 'who',
            '如何', '什么', '怎么', '哪里', '为什么', '哪个', '谁',
            'tutorial', 'guide', 'introduction', 'basic', 'advanced',
            '教程', '指南', '介绍', '基础', '高级', '入门'
        })
        
        # 暂时替换停用词列表
        original_stop_words = self.stop_words
        self.stop_words = extended_stop_words
        
        compact_slug = self.generate_slug(title, max_length=40)
        
        # 恢复原始停用词列表
        self.stop_words = original_stop_words
        
        return compact_slug
    
    def analyze_slug_seo(self, slug):
        """分析slug的SEO质量"""
        analysis = {
            'score': 0,
            'max_score': 100,
            'issues': [],
            'recommendations': []
        }
        
        # 长度分析
        length = len(slug)
        if 3 <= length <= 60:
            analysis['score'] += 25
        elif length > 60:
            analysis['issues'].append(f'URL过长 ({length} 字符)，建议控制在60字符以内')
            analysis['score'] += 15
        else:
            analysis['issues'].append('URL过短，缺乏描述性')
            analysis['score'] += 10
        
        # 字符分析
        if re.match(r'^[a-z0-9-]+$', slug):
            analysis['score'] += 20
        else:
            analysis['issues'].append('URL包含不推荐的字符，建议只使用小写字母、数字和连字符')
        
        # 连字符分析
        dash_count = slug.count('-')
        if dash_count <= 5:
            analysis['score'] += 20
        else:
            analysis['issues'].append(f'连字符过多 ({dash_count} 个)，建议减少到5个以内')
            analysis['score'] += 10
        
        # 可读性分析
        words = slug.split('-')
        if len(words) >= 2:
            analysis['score'] += 20
            if all(len(word) >= 3 for word in words):
                analysis['score'] += 15
            else:
                analysis['recommendations'].append('避免过短的单词以提高可读性')
                analysis['score'] += 10
        else:
            analysis['recommendations'].append('使用多个单词来提高URL的描述性')
            analysis['score'] += 10
        
        # SEO友好性检查
        if not slug.startswith('-') and not slug.endswith('-'):
            analysis['score'] += 0  # 基础要求
        else:
            analysis['issues'].append('URL不应以连字符开始或结束')
        
        if '--' not in slug:
            analysis['score'] += 0  # 基础要求
        else:
            analysis['issues'].append('避免连续的连字符')
        
        # 评级
        if analysis['score'] >= 90:
            analysis['grade'] = 'A'
        elif analysis['score'] >= 80:
            analysis['grade'] = 'B'
        elif analysis['score'] >= 70:
            analysis['grade'] = 'C'
        else:
            analysis['grade'] = 'D'
        
        return analysis