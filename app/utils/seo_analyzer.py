"""
🔍 SEO 分析工具
提供全面的SEO分析功能，包括关键词分析、内容质量评估、技术SEO检查
"""
import re
import json
from datetime import datetime
from urllib.parse import urlparse
from collections import Counter
import jieba
import requests
from bs4 import BeautifulSoup


class SEOAnalyzer:
    """SEO分析器"""
    
    def __init__(self):
        self.stop_words = set([
            '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说',
            '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '这个', '那个', '什么', '怎么',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'
        ])
    
    def analyze_content(self, content, title="", meta_description="", url=""):
        """
        全面分析内容的SEO质量
        返回详细的分析报告
        """
        analysis = {
            'score': 0,
            'max_score': 100,
            'issues': [],
            'recommendations': [],
            'keywords': {},
            'readability': {},
            'technical': {},
            'content_analysis': {},
            'meta_analysis': {}
        }
        
        # 1. 标题分析 (20分)
        title_score = self._analyze_title(title, analysis)
        
        # 2. 元描述分析 (15分)
        meta_score = self._analyze_meta_description(meta_description, analysis)
        
        # 3. 内容分析 (25分)
        content_score = self._analyze_content_body(content, analysis)
        
        # 4. 关键词分析 (20分)
        keyword_score = self._analyze_keywords(content, title, analysis)
        
        # 5. 可读性分析 (10分)
        readability_score = self._analyze_readability(content, analysis)
        
        # 6. 技术SEO分析 (10分)
        technical_score = self._analyze_technical_seo(url, analysis)
        
        # 计算总分
        analysis['score'] = title_score + meta_score + content_score + keyword_score + readability_score + technical_score
        
        # 生成整体建议
        self._generate_overall_recommendations(analysis)
        
        return analysis
    
    def _analyze_title(self, title, analysis):
        """分析标题质量"""
        score = 0
        
        if not title:
            analysis['issues'].append('缺少页面标题')
            analysis['recommendations'].append('添加具有描述性的页面标题')
            return score
        
        title_len = len(title)
        
        # 标题长度分析
        if 10 <= title_len <= 60:
            score += 15
            analysis['meta_analysis']['title_length'] = 'optimal'
        elif 60 < title_len <= 70:
            score += 12
            analysis['issues'].append('标题稍长，可能在搜索结果中被截断')
            analysis['meta_analysis']['title_length'] = 'good'
        elif title_len < 10:
            score += 5
            analysis['issues'].append('标题过短，缺乏描述性')
            analysis['meta_analysis']['title_length'] = 'too_short'
        else:
            score += 8
            analysis['issues'].append('标题过长，将在搜索结果中被截断')
            analysis['meta_analysis']['title_length'] = 'too_long'
        
        # 标题关键词分析
        if self._has_meaningful_keywords(title):
            score += 5
            analysis['meta_analysis']['title_keywords'] = 'good'
        else:
            analysis['recommendations'].append('在标题中包含更多相关关键词')
            analysis['meta_analysis']['title_keywords'] = 'needs_improvement'
        
        analysis['meta_analysis']['title'] = title
        analysis['meta_analysis']['title_character_count'] = title_len
        
        return score
    
    def _analyze_meta_description(self, meta_description, analysis):
        """分析元描述质量"""
        score = 0
        
        if not meta_description:
            analysis['issues'].append('缺少元描述')
            analysis['recommendations'].append('添加120-160字符的元描述')
            return score
        
        desc_len = len(meta_description)
        
        # 元描述长度分析
        if 120 <= desc_len <= 160:
            score += 15
            analysis['meta_analysis']['description_length'] = 'optimal'
        elif 160 < desc_len <= 200:
            score += 12
            analysis['issues'].append('元描述稍长，可能在搜索结果中被截断')
            analysis['meta_analysis']['description_length'] = 'good'
        elif desc_len < 120:
            score += 8
            analysis['issues'].append('元描述过短，建议扩充到120-160字符')
            analysis['meta_analysis']['description_length'] = 'too_short'
        else:
            score += 5
            analysis['issues'].append('元描述过长，将在搜索结果中被截断')
            analysis['meta_analysis']['description_length'] = 'too_long'
        
        analysis['meta_analysis']['description'] = meta_description
        analysis['meta_analysis']['description_character_count'] = desc_len
        
        return score
    
    def _analyze_content_body(self, content, analysis):
        """分析内容主体质量"""
        score = 0
        
        if not content:
            analysis['issues'].append('内容为空')
            return score
        
        # 内容长度分析
        word_count = len(self._extract_words(content))
        char_count = len(content.replace(' ', '').replace('\n', ''))
        
        if char_count >= 500:
            score += 10
            analysis['content_analysis']['length'] = 'good'
        elif char_count >= 300:
            score += 8
            analysis['content_analysis']['length'] = 'adequate'
        else:
            score += 5
            analysis['issues'].append('内容长度不足，建议增加到300字符以上')
            analysis['content_analysis']['length'] = 'too_short'
        
        # 内容结构分析
        structure_score = self._analyze_content_structure(content, analysis)
        score += structure_score
        
        # 图片分析
        image_score = self._analyze_images(content, analysis)
        score += image_score
        
        analysis['content_analysis']['word_count'] = word_count
        analysis['content_analysis']['character_count'] = char_count
        
        return score
    
    def _analyze_content_structure(self, content, analysis):
        """分析内容结构"""
        score = 0
        
        # 检查标题标签
        h1_count = len(re.findall(r'#\s+.*', content))
        h2_count = len(re.findall(r'##\s+.*', content))
        h3_count = len(re.findall(r'###\s+.*', content))
        
        if h1_count > 0:
            score += 3
            analysis['content_analysis']['has_h1'] = True
        else:
            analysis['issues'].append('缺少H1标题，建议添加主标题')
            analysis['content_analysis']['has_h1'] = False
        
        if h2_count > 0:
            score += 2
            analysis['content_analysis']['has_h2'] = True
        else:
            analysis['recommendations'].append('添加H2副标题来改善内容结构')
            analysis['content_analysis']['has_h2'] = False
        
        # 检查列表
        list_count = len(re.findall(r'^\s*[-*+]\s+.*', content, re.MULTILINE))
        if list_count > 0:
            score += 2
            analysis['content_analysis']['has_lists'] = True
        else:
            analysis['recommendations'].append('使用列表来提高内容可读性')
            analysis['content_analysis']['has_lists'] = False
        
        # 检查链接
        link_count = len(re.findall(r'\[.*?\]\(.*?\)', content))
        if link_count > 0:
            score += 2
            analysis['content_analysis']['has_links'] = True
            if link_count > 10:
                analysis['issues'].append('链接过多，可能影响用户体验')
        else:
            analysis['recommendations'].append('添加相关的内部或外部链接')
            analysis['content_analysis']['has_links'] = False
        
        analysis['content_analysis']['heading_structure'] = {
            'h1_count': h1_count,
            'h2_count': h2_count,
            'h3_count': h3_count
        }
        
        return score
    
    def _analyze_images(self, content, analysis):
        """分析图片使用"""
        score = 0
        
        # 检查Markdown图片
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        images = re.findall(image_pattern, content)
        
        if images:
            score += 3
            analysis['content_analysis']['has_images'] = True
            
            # 检查Alt文本
            images_with_alt = [img for img in images if img[0].strip()]
            if len(images_with_alt) == len(images):
                score += 2
                analysis['content_analysis']['images_have_alt'] = True
            else:
                analysis['issues'].append(f'{len(images) - len(images_with_alt)} 个图片缺少Alt文本')
                analysis['content_analysis']['images_have_alt'] = False
        else:
            analysis['recommendations'].append('添加相关图片来提高内容丰富度')
            analysis['content_analysis']['has_images'] = False
        
        analysis['content_analysis']['image_count'] = len(images)
        
        return score
    
    def _analyze_keywords(self, content, title, analysis):
        """关键词密度分析"""
        score = 0
        
        # 提取所有文本
        full_text = f"{title} {content}"
        words = self._extract_words(full_text.lower())
        
        if not words:
            return score
        
        # 计算词频
        word_freq = Counter(words)
        total_words = len(words)
        
        # 提取关键词
        keywords = {}
        for word, count in word_freq.most_common(20):
            if len(word) > 2 and word not in self.stop_words:
                density = (count / total_words) * 100
                keywords[word] = {
                    'count': count,
                    'density': round(density, 2)
                }
        
        analysis['keywords'] = keywords
        
        # 关键词密度评估
        if keywords:
            score += 10
            max_density = max(kw['density'] for kw in keywords.values())
            
            if max_density > 5:
                analysis['issues'].append(f'关键词密度过高 ({max_density}%)，可能被认为是关键词填充')
            elif max_density < 0.5:
                analysis['recommendations'].append('适当增加主要关键词的使用频率')
            else:
                score += 10
                analysis['content_analysis']['keyword_density'] = 'optimal'
        else:
            analysis['issues'].append('未检测到明显的关键词模式')
        
        return score
    
    def _analyze_readability(self, content, analysis):
        """可读性分析"""
        score = 0
        
        if not content:
            return score
        
        # 句子分析
        sentences = re.split(r'[。！？.!?]', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return score
        
        # 平均句子长度
        avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
        
        if avg_sentence_length <= 20:
            score += 5
            analysis['readability']['sentence_length'] = 'good'
        elif avg_sentence_length <= 30:
            score += 3
            analysis['readability']['sentence_length'] = 'adequate'
        else:
            analysis['issues'].append('句子平均长度过长，建议使用更短的句子')
            analysis['readability']['sentence_length'] = 'too_long'
        
        # 段落分析
        paragraphs = content.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        if len(paragraphs) >= 3:
            score += 3
            analysis['readability']['paragraph_structure'] = 'good'
        else:
            analysis['recommendations'].append('将内容分为更多段落以提高可读性')
            analysis['readability']['paragraph_structure'] = 'needs_improvement'
        
        # 复杂词汇分析（简化版）
        complex_words = len(re.findall(r'[\u4e00-\u9fff]{4,}', content))  # 4字以上的中文词汇
        total_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        
        if total_chars > 0:
            complex_ratio = complex_words / total_chars
            if complex_ratio < 0.1:
                score += 2
                analysis['readability']['complexity'] = 'simple'
            else:
                analysis['recommendations'].append('考虑使用更简单的词汇')
                analysis['readability']['complexity'] = 'complex'
        
        analysis['readability']['avg_sentence_length'] = round(avg_sentence_length, 1)
        analysis['readability']['paragraph_count'] = len(paragraphs)
        analysis['readability']['sentence_count'] = len(sentences)
        
        return score
    
    def _analyze_technical_seo(self, url, analysis):
        """技术SEO分析"""
        score = 10  # 基础分数，因为这里主要分析URL结构
        
        if url:
            # URL长度分析
            if len(url) <= 100:
                score += 0  # 基础分数已给
                analysis['technical']['url_length'] = 'good'
            else:
                analysis['issues'].append('URL过长，建议缩短')
                analysis['technical']['url_length'] = 'too_long'
            
            # URL结构分析
            if re.search(r'[a-zA-Z0-9\-_/]', url):
                analysis['technical']['url_structure'] = 'clean'
            else:
                analysis['recommendations'].append('使用更清晰的URL结构')
                analysis['technical']['url_structure'] = 'complex'
        else:
            analysis['technical']['url_analysis'] = 'not_available'
        
        return score
    
    def _generate_overall_recommendations(self, analysis):
        """生成整体建议"""
        score = analysis['score']
        
        if score >= 80:
            analysis['grade'] = 'A'
            analysis['overall_status'] = 'excellent'
        elif score >= 70:
            analysis['grade'] = 'B'
            analysis['overall_status'] = 'good'
        elif score >= 60:
            analysis['grade'] = 'C'  
            analysis['overall_status'] = 'needs_improvement'
        else:
            analysis['grade'] = 'D'
            analysis['overall_status'] = 'poor'
        
        # 优先级建议
        priority_recommendations = []
        
        if analysis['score'] < 70:
            if not analysis['meta_analysis'].get('title'):
                priority_recommendations.append('添加吸引人的页面标题')
            if not analysis['meta_analysis'].get('description'):
                priority_recommendations.append('编写引人注目的元描述')
            if analysis['content_analysis'].get('length') == 'too_short':
                priority_recommendations.append('增加内容长度和深度')
        
        analysis['priority_recommendations'] = priority_recommendations
    
    def _extract_words(self, text):
        """提取文本中的词汇"""
        # 中文分词
        chinese_words = jieba.lcut(text)
        chinese_words = [word for word in chinese_words if len(word) > 1 and word not in self.stop_words]
        
        # 英文分词
        english_words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        english_words = [word for word in english_words if word not in self.stop_words]
        
        return chinese_words + english_words
    
    def _has_meaningful_keywords(self, text):
        """检查文本是否包含有意义的关键词"""
        words = self._extract_words(text.lower())
        meaningful_words = [w for w in words if len(w) > 2 and w not in self.stop_words]
        return len(meaningful_words) >= 2
    
    def generate_sitemap_entry(self, url, lastmod=None, changefreq='monthly', priority=0.5):
        """生成站点地图条目"""
        if not lastmod:
            lastmod = datetime.now().strftime('%Y-%m-%d')
        
        return {
            'url': url,
            'lastmod': lastmod,
            'changefreq': changefreq,
            'priority': priority
        }
    
    def analyze_competitor(self, competitor_url):
        """竞争对手分析（简化版）"""
        try:
            response = requests.get(competitor_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            analysis = {
                'title': soup.find('title').get_text() if soup.find('title') else '',
                'meta_description': '',
                'h1_count': len(soup.find_all('h1')),
                'h2_count': len(soup.find_all('h2')),
                'image_count': len(soup.find_all('img')),
                'link_count': len(soup.find_all('a')),
                'word_count': len(soup.get_text().split())
            }
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                analysis['meta_description'] = meta_desc.get('content', '')
            
            return analysis
            
        except Exception as e:
            return {'error': f'分析失败: {str(e)}'}


class SEOReportGenerator:
    """SEO报告生成器"""
    
    @staticmethod
    def generate_html_report(analysis_data):
        """生成HTML格式的SEO报告"""
        score = analysis_data['score']
        max_score = analysis_data['max_score']
        grade = analysis_data.get('grade', 'N/A')
        
        # 评分颜色
        if score >= 80:
            score_color = 'success'
        elif score >= 60:
            score_color = 'warning'
        else:
            score_color = 'danger'
        
        html_report = f"""
        <div class="seo-report">
            <div class="seo-score-card">
                <h3>SEO总评分</h3>
                <div class="score-circle">
                    <span class="score text-{score_color}">{score}</span>
                    <span class="max-score">/{max_score}</span>
                    <div class="grade badge bg-{score_color}">{grade}</div>
                </div>
            </div>
            
            <div class="seo-sections">
                <div class="meta-analysis">
                    <h4>元数据分析</h4>
                    <div class="analysis-item">
                        <strong>标题:</strong> {analysis_data['meta_analysis'].get('title', '未设置')}
                        <span class="badge bg-secondary">{analysis_data['meta_analysis'].get('title_character_count', 0)} 字符</span>
                    </div>
                    <div class="analysis-item">
                        <strong>描述:</strong> {analysis_data['meta_analysis'].get('description', '未设置')[:100]}...
                        <span class="badge bg-secondary">{analysis_data['meta_analysis'].get('description_character_count', 0)} 字符</span>
                    </div>
                </div>
                
                <div class="content-analysis">
                    <h4>内容分析</h4>
                    <div class="stats-grid">
                        <div>字数统计: {analysis_data['content_analysis'].get('word_count', 0)}</div>
                        <div>字符数: {analysis_data['content_analysis'].get('character_count', 0)}</div>
                        <div>图片数量: {analysis_data['content_analysis'].get('image_count', 0)}</div>
                        <div>段落数: {analysis_data['readability'].get('paragraph_count', 0)}</div>
                    </div>
                </div>
                
                <div class="issues-recommendations">
                    <div class="issues">
                        <h4>发现的问题</h4>
                        <ul>
                            {''.join([f'<li>{issue}</li>' for issue in analysis_data['issues']])}
                        </ul>
                    </div>
                    
                    <div class="recommendations">
                        <h4>优化建议</h4>
                        <ul>
                            {''.join([f'<li>{rec}</li>' for rec in analysis_data['recommendations']])}
                        </ul>
                    </div>
                </div>
                
                <div class="keywords-analysis">
                    <h4>关键词分析</h4>
                    <div class="keywords-list">
                        {''.join([f'<span class="keyword-badge">{kw} ({data["density"]}%)</span>' for kw, data in list(analysis_data['keywords'].items())[:10]])}
                    </div>
                </div>
            </div>
        </div>
        """
        
        return html_report
    
    @staticmethod
    def generate_json_report(analysis_data):
        """生成JSON格式的SEO报告"""
        return json.dumps(analysis_data, ensure_ascii=False, indent=2)