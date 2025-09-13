"""
🔍 智能搜索引擎
全文搜索、语义搜索、相关推荐和分类筛选
"""
import re
import jieba
import jieba.analyse
from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy import or_, and_, func, desc
from app.models.content import Content, content_tags
from app.models.tag import Tag


class SearchEngine:
    """智能搜索引擎"""
    
    def __init__(self):
        # 初始化jieba分词
        jieba.initialize()
        
        # 停用词
        self.stop_words = {
            '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说',
            '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '这个', '那个', '什么', '怎么',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are'
        }
        
        # 权重配置
        self.weights = {
            'title': 0.4,      # 标题权重最高
            'summary': 0.3,    # 摘要权重中等
            'content': 0.2,    # 内容权重较低
            'tags': 0.1        # 标签权重最低
        }
    
    def full_text_search(self, query, category=None, page=1, per_page=20, sort_by='relevance'):
        """
        全文搜索
        
        Args:
            query: 搜索关键词
            category: 分类筛选
            page: 页码
            per_page: 每页数量
            sort_by: 排序方式 ('relevance', 'date', 'views', 'likes')
        
        Returns:
            dict: 搜索结果和统计信息
        """
        if not query.strip():
            return self._empty_result()
        
        # 分词处理
        keywords = self._extract_keywords(query)
        if not keywords:
            return self._empty_result()
        
        # 构建基础查询
        base_query = Content.query.filter(Content.is_published == True)
        
        if category:
            base_query = base_query.filter(Content.category == category)
        
        # 构建搜索条件
        search_conditions = []
        
        for keyword in keywords:
            # 为每个关键词创建搜索条件
            keyword_conditions = [
                Content.title.contains(keyword),
                Content.summary.contains(keyword), 
                Content.content.contains(keyword)
            ]
            search_conditions.append(or_(*keyword_conditions))
        
        # 组合所有搜索条件
        if search_conditions:
            search_query = base_query.filter(or_(*search_conditions))
        else:
            return self._empty_result()
        
        # 获取结果用于相关性计算
        all_results = search_query.all()
        
        # 计算相关性评分
        scored_results = []
        for content in all_results:
            score = self._calculate_relevance_score(content, keywords, query)
            scored_results.append((content, score))
        
        # 排序
        if sort_by == 'relevance':
            scored_results.sort(key=lambda x: x[1], reverse=True)
        elif sort_by == 'date':
            scored_results.sort(key=lambda x: x[0].created_at, reverse=True)
        elif sort_by == 'views':
            scored_results.sort(key=lambda x: x[0].view_count or 0, reverse=True)
        elif sort_by == 'likes':
            scored_results.sort(key=lambda x: x[0].like_count or 0, reverse=True)
        
        # 分页
        total = len(scored_results)
        start = (page - 1) * per_page
        end = start + per_page
        paged_results = scored_results[start:end]
        
        # 构建返回结果
        results = []
        for content, score in paged_results:
            result = {
                'content': content,
                'score': score,
                'highlight': self._generate_highlight(content, keywords)
            }
            results.append(result)
        
        return {
            'results': results,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'query': query,
            'keywords': keywords,
            'category': category,
            'sort_by': sort_by
        }
    
    def semantic_search(self, query, limit=10):
        """
        语义搜索（基于关键词提取和标签匹配）
        """
        # 提取查询的关键词和主题
        keywords = jieba.analyse.extract_tags(query, topK=10, withWeight=True)
        if not keywords:
            return []
        
        # 基于关键词权重搜索
        results = []
        
        # 搜索标题和内容
        for keyword, weight in keywords:
            if keyword in self.stop_words:
                continue
                
            # 搜索内容
            contents = Content.query.filter(
                Content.is_published == True,
                or_(
                    Content.title.contains(keyword),
                    Content.content.contains(keyword),
                    Content.summary.contains(keyword)
                )
            ).all()
            
            for content in contents:
                # 计算语义相关度
                semantic_score = self._calculate_semantic_score(content, keywords)
                results.append((content, semantic_score))
        
        # 去重并按相关度排序
        unique_results = {}
        for content, score in results:
            if content.id in unique_results:
                unique_results[content.id] = max(unique_results[content.id], score)
            else:
                unique_results[content.id] = score
        
        # 获取排序后的内容
        sorted_content_ids = sorted(unique_results.items(), key=lambda x: x[1], reverse=True)
        
        final_results = []
        for content_id, score in sorted_content_ids[:limit]:
            content = Content.query.get(content_id)
            if content:
                final_results.append({
                    'content': content,
                    'semantic_score': score
                })
        
        return final_results
    
    def search_by_tags(self, tag_names, limit=20):
        """标签搜索"""
        if not tag_names:
            return []
        
        # 获取标签对象
        tags = Tag.query.filter(Tag.name.in_(tag_names)).all()
        if not tags:
            return []
        
        tag_ids = [tag.id for tag in tags]
        
        # 查询包含这些标签的内容
        from app import db
        
        results = db.session.query(Content)\
                    .join(content_tags)\
                    .filter(content_tags.c.tag_id.in_(tag_ids))\
                    .filter(Content.is_published == True)\
                    .group_by(Content.id)\
                    .order_by(db.func.count(content_tags.c.tag_id).desc(), Content.created_at.desc())\
                    .limit(limit).all()
        
        return results
    
    def get_related_content(self, content, limit=5, method='mixed'):
        """
        获取相关内容
        
        Args:
            content: 当前内容对象
            limit: 返回数量
            method: 推荐方法 ('tags', 'category', 'keywords', 'mixed')
        
        Returns:
            list: 相关内容列表
        """
        if method == 'tags':
            return self._get_related_by_tags(content, limit)
        elif method == 'category':
            return self._get_related_by_category(content, limit)
        elif method == 'keywords':
            return self._get_related_by_keywords(content, limit)
        else:  # mixed
            return self._get_related_mixed(content, limit)
    
    def get_trending_content(self, days=7, limit=10):
        """获取热门内容（基于浏览量和时间）"""
        since_date = datetime.now() - timedelta(days=days)
        
        results = Content.query\
                  .filter(Content.is_published == True)\
                  .filter(Content.created_at >= since_date)\
                  .order_by(desc(Content.view_count), desc(Content.created_at))\
                  .limit(limit).all()
        
        return results
    
    def get_search_suggestions(self, query, limit=5):
        """搜索建议（自动完成）"""
        if len(query) < 2:
            return []
        
        suggestions = []
        
        # 基于标题的建议
        title_matches = Content.query\
                       .filter(Content.is_published == True)\
                       .filter(Content.title.contains(query))\
                       .order_by(desc(Content.view_count))\
                       .limit(limit).all()
        
        for content in title_matches:
            suggestions.append({
                'text': content.title,
                'type': 'title',
                'url': content.get_url() if hasattr(content, 'get_url') else f'/content/{content.id}'
            })
        
        # 基于标签的建议
        if len(suggestions) < limit:
            tag_matches = Tag.query\
                         .filter(Tag.name.contains(query))\
                         .order_by(desc(Tag.usage_count))\
                         .limit(limit - len(suggestions)).all()
            
            for tag in tag_matches:
                suggestions.append({
                    'text': tag.name,
                    'type': 'tag',
                    'url': f'/search?tag={tag.name}'
                })
        
        return suggestions
    
    def get_category_stats(self):
        """获取分类统计"""
        from app import db
        
        stats = db.session.query(
            Content.category,
            func.count(Content.id).label('count'),
            func.avg(Content.view_count).label('avg_views')
        ).filter(Content.is_published == True)\
         .group_by(Content.category)\
         .order_by(desc('count')).all()
        
        return [
            {
                'category': stat.category,
                'count': stat.count,
                'avg_views': round(stat.avg_views or 0, 1)
            }
            for stat in stats
        ]
    
    def _extract_keywords(self, query):
        """提取关键词"""
        # 中文分词
        words = jieba.lcut(query.lower())
        
        # 英文分词（简单空格分割）
        english_words = re.findall(r'[a-zA-Z]+', query.lower())
        
        # 合并并过滤
        all_words = words + english_words
        keywords = [word for word in all_words if len(word) > 1 and word not in self.stop_words]
        
        return list(set(keywords))  # 去重
    
    def _calculate_relevance_score(self, content, keywords, original_query):
        """计算相关性评分"""
        score = 0
        
        # 标题匹配
        title_matches = sum(1 for keyword in keywords if keyword in content.title.lower())
        score += title_matches * self.weights['title'] * 10
        
        # 摘要匹配
        if content.summary:
            summary_matches = sum(1 for keyword in keywords if keyword in content.summary.lower())
            score += summary_matches * self.weights['summary'] * 10
        
        # 内容匹配
        if content.content:
            content_matches = sum(1 for keyword in keywords if keyword in content.content.lower())
            score += content_matches * self.weights['content'] * 10
        
        # 标签匹配
        if content.tags:
            tag_names = [tag.name.lower() for tag in content.tags]
            tag_matches = sum(1 for keyword in keywords if any(keyword in tag_name for tag_name in tag_names))
            score += tag_matches * self.weights['tags'] * 10
        
        # 完整查询匹配（加分）
        if original_query.lower() in content.title.lower():
            score += 20
        elif content.summary and original_query.lower() in content.summary.lower():
            score += 15
        elif content.content and original_query.lower() in content.content.lower():
            score += 10
        
        # 内容质量加分
        if content.is_featured:
            score += 5
        
        if content.view_count and content.view_count > 100:
            score += min(content.view_count / 100, 10)  # 最多加10分
        
        return round(score, 2)
    
    def _calculate_semantic_score(self, content, keywords):
        """计算语义相关度"""
        score = 0
        
        for keyword, weight in keywords:
            # 标题权重更高
            if keyword in content.title.lower():
                score += weight * 0.5
            
            # 摘要权重中等
            if content.summary and keyword in content.summary.lower():
                score += weight * 0.3
            
            # 内容权重较低
            if content.content and keyword in content.content.lower():
                score += weight * 0.2
        
        return round(score, 3)
    
    def _generate_highlight(self, content, keywords):
        """生成搜索结果高亮"""
        highlights = {}
        
        # 高亮标题
        highlighted_title = content.title
        for keyword in keywords:
            highlighted_title = re.sub(
                f'({re.escape(keyword)})', 
                r'<mark>\1</mark>', 
                highlighted_title, 
                flags=re.IGNORECASE
            )
        highlights['title'] = highlighted_title
        
        # 高亮摘要
        if content.summary:
            highlighted_summary = content.summary
            for keyword in keywords:
                highlighted_summary = re.sub(
                    f'({re.escape(keyword)})', 
                    r'<mark>\1</mark>', 
                    highlighted_summary, 
                    flags=re.IGNORECASE
                )
            highlights['summary'] = highlighted_summary
        
        # 生成内容片段（带高亮）
        if content.content:
            snippet = self._generate_content_snippet(content.content, keywords)
            highlights['snippet'] = snippet
        
        return highlights
    
    def _generate_content_snippet(self, content_text, keywords, max_length=200):
        """生成内容摘要片段"""
        # 寻找包含关键词的句子
        sentences = re.split(r'[。！？.!?]', content_text)
        
        best_sentence = ""
        max_keyword_count = 0
        
        for sentence in sentences:
            keyword_count = sum(1 for keyword in keywords if keyword in sentence.lower())
            if keyword_count > max_keyword_count:
                max_keyword_count = keyword_count
                best_sentence = sentence
        
        if not best_sentence and sentences:
            best_sentence = sentences[0]
        
        # 截断到指定长度
        if len(best_sentence) > max_length:
            best_sentence = best_sentence[:max_length] + "..."
        
        # 添加高亮
        highlighted_snippet = best_sentence
        for keyword in keywords:
            highlighted_snippet = re.sub(
                f'({re.escape(keyword)})', 
                r'<mark>\1</mark>', 
                highlighted_snippet, 
                flags=re.IGNORECASE
            )
        
        return highlighted_snippet
    
    def _get_related_by_tags(self, content, limit):
        """基于标签的相关内容"""
        if not content.tags:
            return []
        
        tag_ids = [tag.id for tag in content.tags]
        
        from app import db
        
        related = db.session.query(Content)\
                   .join(content_tags)\
                   .filter(content_tags.c.tag_id.in_(tag_ids))\
                   .filter(Content.id != content.id)\
                   .filter(Content.is_published == True)\
                   .group_by(Content.id)\
                   .order_by(db.func.count(content_tags.c.tag_id).desc(), Content.created_at.desc())\
                   .limit(limit).all()
        
        return related
    
    def _get_related_by_category(self, content, limit):
        """基于分类的相关内容"""
        return Content.query\
               .filter(Content.category == content.category)\
               .filter(Content.id != content.id)\
               .filter(Content.is_published == True)\
               .order_by(desc(Content.view_count), desc(Content.created_at))\
               .limit(limit).all()
    
    def _get_related_by_keywords(self, content, limit):
        """基于关键词的相关内容"""
        if not content.content:
            return []
        
        # 从当前内容提取关键词
        keywords = jieba.analyse.extract_tags(content.title + " " + content.content, topK=5)
        
        if not keywords:
            return []
        
        # 搜索包含这些关键词的其他内容
        search_conditions = []
        for keyword in keywords:
            search_conditions.append(
                or_(
                    Content.title.contains(keyword),
                    Content.content.contains(keyword)
                )
            )
        
        if search_conditions:
            related = Content.query\
                     .filter(Content.id != content.id)\
                     .filter(Content.is_published == True)\
                     .filter(or_(*search_conditions))\
                     .order_by(desc(Content.view_count), desc(Content.created_at))\
                     .limit(limit).all()
            return related
        
        return []
    
    def _get_related_mixed(self, content, limit):
        """混合推荐算法"""
        related_contents = {}
        
        # 基于标签的相关内容（权重最高）
        tag_related = self._get_related_by_tags(content, limit * 2)
        for item in tag_related:
            related_contents[item.id] = {
                'content': item,
                'score': 10,  # 标签匹配权重最高
                'reason': 'tags'
            }
        
        # 基于分类的相关内容
        category_related = self._get_related_by_category(content, limit)
        for item in category_related:
            if item.id in related_contents:
                related_contents[item.id]['score'] += 5
            else:
                related_contents[item.id] = {
                    'content': item,
                    'score': 5,
                    'reason': 'category'
                }
        
        # 基于关键词的相关内容
        keyword_related = self._get_related_by_keywords(content, limit)
        for item in keyword_related:
            if item.id in related_contents:
                related_contents[item.id]['score'] += 3
            else:
                related_contents[item.id] = {
                    'content': item,
                    'score': 3,
                    'reason': 'keywords'
                }
        
        # 按评分排序并返回
        sorted_related = sorted(related_contents.values(), key=lambda x: x['score'], reverse=True)
        
        return [item['content'] for item in sorted_related[:limit]]
    
    def _empty_result(self):
        """空搜索结果"""
        return {
            'results': [],
            'total': 0,
            'page': 1,
            'per_page': 20,
            'total_pages': 0,
            'query': '',
            'keywords': [],
            'category': None,
            'sort_by': 'relevance'
        }


class SearchIndexer:
    """搜索索引管理器"""
    
    def __init__(self):
        self.engine = SearchEngine()
    
    def build_search_index(self):
        """构建搜索索引（为将来全文搜索优化准备）"""
        contents = Content.query.filter_by(is_published=True).all()
        
        index_data = []
        for content in contents:
            # 提取所有文本内容
            full_text = f"{content.title} {content.summary or ''} {content.content or ''}"
            
            # 分词
            keywords = jieba.analyse.extract_tags(full_text, topK=20, withWeight=True)
            
            # 构建索引条目
            index_entry = {
                'content_id': content.id,
                'title': content.title,
                'category': content.category,
                'keywords': keywords,
                'created_at': content.created_at,
                'updated_at': content.updated_at,
                'view_count': content.view_count or 0,
                'is_featured': content.is_featured
            }
            
            index_data.append(index_entry)
        
        return index_data
    
    def update_content_index(self, content_id):
        """更新单个内容的索引"""
        # 这里可以实现增量索引更新
        # 为将来的性能优化准备
        pass


# 全局搜索引擎实例
search_engine = SearchEngine()
search_indexer = SearchIndexer()