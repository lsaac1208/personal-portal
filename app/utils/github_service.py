"""
🐙 GitHub API 集成服务
📊 data-scientist 设计的实时仓库数据获取系统
"""
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from flask import current_app
from app import db
import logging

logger = logging.getLogger(__name__)


class GitHubService:
    """
    GitHub API集成服务类
    
    功能:
    - 获取仓库基本信息 (stars, forks, watchers)
    - 获取仓库语言统计
    - 获取最新提交信息
    - 缓存机制避免API限制
    """
    
    def __init__(self, token: Optional[str] = None):
        """初始化GitHub服务"""
        self.token = token or current_app.config.get('GITHUB_TOKEN')
        self.base_url = 'https://api.github.com'
        self.session = requests.Session()
        
        # 设置认证头
        if self.token:
            self.session.headers.update({
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'PersonalPortal/1.0'
            })
        else:
            # 无token时使用基本头部
            self.session.headers.update({
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'PersonalPortal/1.0'
            })
    
    def parse_github_url(self, github_url: str) -> Optional[Tuple[str, str]]:
        """
        解析GitHub URL获取owner和repo名称
        
        Args:
            github_url: GitHub仓库URL
            
        Returns:
            (owner, repo) tuple或None
        """
        if not github_url:
            return None
            
        # 支持多种URL格式
        # https://github.com/owner/repo
        # https://github.com/owner/repo.git
        # git@github.com:owner/repo.git
        try:
            if 'github.com' in github_url:
                if github_url.startswith('git@'):
                    # SSH格式: git@github.com:owner/repo.git
                    path_part = github_url.split(':')[1]
                else:
                    # HTTPS格式: https://github.com/owner/repo
                    path_part = github_url.split('github.com/')[1]
                
                # 移除.git后缀
                path_part = path_part.rstrip('.git')
                
                # 分割owner和repo
                parts = path_part.split('/')
                if len(parts) >= 2:
                    return parts[0], parts[1]
                    
        except (IndexError, AttributeError) as e:
            logger.warning(f"Failed to parse GitHub URL {github_url}: {e}")
            
        return None
    
    def get_repository_info(self, owner: str, repo: str) -> Optional[Dict]:
        """
        获取仓库基本信息
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            
        Returns:
            仓库信息字典或None
        """
        try:
            url = f'{self.base_url}/repos/{owner}/{repo}'
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'name': data.get('name'),
                    'full_name': data.get('full_name'),
                    'description': data.get('description'),
                    'stars': data.get('stargazers_count', 0),
                    'forks': data.get('forks_count', 0),
                    'watchers': data.get('watchers_count', 0),
                    'open_issues': data.get('open_issues_count', 0),
                    'language': data.get('language'),
                    'created_at': data.get('created_at'),
                    'updated_at': data.get('updated_at'),
                    'pushed_at': data.get('pushed_at'),
                    'size': data.get('size', 0),  # KB
                    'default_branch': data.get('default_branch', 'main'),
                    'license': data.get('license', {}).get('name') if data.get('license') else None,
                    'homepage': data.get('homepage'),
                    'topics': data.get('topics', []),
                    'archived': data.get('archived', False),
                    'disabled': data.get('disabled', False),
                    'private': data.get('private', False)
                }
            elif response.status_code == 404:
                logger.warning(f"Repository {owner}/{repo} not found")
            elif response.status_code == 403:
                logger.warning(f"Rate limited or access denied for {owner}/{repo}")
            else:
                logger.warning(f"Unexpected status {response.status_code} for {owner}/{repo}")
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch repository info for {owner}/{repo}: {e}")
            
        return None
    
    def get_repository_languages(self, owner: str, repo: str) -> Optional[Dict[str, int]]:
        """
        获取仓库语言统计
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            
        Returns:
            语言统计字典 {"Python": 12345, "JavaScript": 6789}
        """
        try:
            url = f'{self.base_url}/repos/{owner}/{repo}/languages'
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get languages for {owner}/{repo}: {response.status_code}")
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch languages for {owner}/{repo}: {e}")
            
        return None
    
    def get_latest_commits(self, owner: str, repo: str, count: int = 5) -> Optional[List[Dict]]:
        """
        获取最新提交信息
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            count: 获取提交数量
            
        Returns:
            提交信息列表
        """
        try:
            url = f'{self.base_url}/repos/{owner}/{repo}/commits'
            params = {'per_page': min(count, 100)}  # GitHub API最大100
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                commits = response.json()
                return [{
                    'sha': commit.get('sha'),
                    'message': commit.get('commit', {}).get('message', '').split('\n')[0],  # 只取第一行
                    'author': commit.get('commit', {}).get('author', {}).get('name'),
                    'date': commit.get('commit', {}).get('author', {}).get('date'),
                    'url': commit.get('html_url')
                } for commit in commits]
            else:
                logger.warning(f"Failed to get commits for {owner}/{repo}: {response.status_code}")
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch commits for {owner}/{repo}: {e}")
            
        return None
    
    def get_repository_stats(self, github_url: str) -> Optional[Dict]:
        """
        获取完整的仓库统计信息
        
        Args:
            github_url: GitHub仓库URL
            
        Returns:
            完整统计信息字典
        """
        parsed = self.parse_github_url(github_url)
        if not parsed:
            return None
            
        owner, repo = parsed
        
        # 获取基本信息
        repo_info = self.get_repository_info(owner, repo)
        if not repo_info:
            return None
        
        # 获取语言统计
        languages = self.get_repository_languages(owner, repo)
        
        # 获取最新提交
        commits = self.get_latest_commits(owner, repo, 3)
        
        # 组合结果
        stats = {
            'basic': repo_info,
            'languages': languages or {},
            'recent_commits': commits or [],
            'fetched_at': datetime.utcnow().isoformat(),
            'owner': owner,
            'repo': repo
        }
        
        return stats
    
    def get_rate_limit_info(self) -> Optional[Dict]:
        """
        获取API速率限制信息
        
        Returns:
            速率限制信息
        """
        try:
            url = f'{self.base_url}/rate_limit'
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                core = data.get('resources', {}).get('core', {})
                return {
                    'limit': core.get('limit', 60),  # 未认证用户60/小时，认证用户5000/小时
                    'remaining': core.get('remaining', 0),
                    'reset': core.get('reset', 0),
                    'reset_time': datetime.fromtimestamp(core.get('reset', 0)).isoformat()
                }
            else:
                logger.warning(f"Failed to get rate limit info: {response.status_code}")
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch rate limit info: {e}")
            
        return None


class GitHubCache:
    """
    GitHub数据缓存管理类
    避免频繁调用API，提高性能
    """
    
    @staticmethod
    def get_cache_key(github_url: str) -> str:
        """生成缓存键"""
        return f"github_stats_{hash(github_url)}"
    
    @staticmethod
    def get_cached_stats(github_url: str) -> Optional[Dict]:
        """
        从缓存获取统计数据
        
        Args:
            github_url: GitHub URL
            
        Returns:
            缓存的统计数据或None
        """
        try:
            # 这里可以集成Redis或简单的文件缓存
            # 暂时使用简单的内存缓存实现
            cache_key = GitHubCache.get_cache_key(github_url)
            
            # 实际项目中应该使用Redis等持久化缓存
            # 这里先返回None，表示缓存未命中
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached stats: {e}")
            return None
    
    @staticmethod
    def cache_stats(github_url: str, stats: Dict, ttl: int = 3600):
        """
        缓存统计数据
        
        Args:
            github_url: GitHub URL
            stats: 统计数据
            ttl: 缓存时间（秒），默认1小时
        """
        try:
            cache_key = GitHubCache.get_cache_key(github_url)
            
            # 实际项目中应该使用Redis等持久化缓存
            # 这里暂时跳过缓存存储
            pass
            
        except Exception as e:
            logger.error(f"Failed to cache stats: {e}")


# 便捷函数
def get_github_stats(github_url: str, use_cache: bool = True) -> Optional[Dict]:
    """
    获取GitHub仓库统计信息（带缓存）
    
    Args:
        github_url: GitHub仓库URL
        use_cache: 是否使用缓存
        
    Returns:
        统计信息字典或None
    """
    if not github_url:
        return None
    
    # 检查缓存
    if use_cache:
        cached = GitHubCache.get_cached_stats(github_url)
        if cached:
            return cached
    
    # 创建服务实例并获取数据
    try:
        github_service = GitHubService()
        stats = github_service.get_repository_stats(github_url)
        
        # 缓存结果
        if stats and use_cache:
            GitHubCache.cache_stats(github_url, stats)
            
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get GitHub stats for {github_url}: {e}")
        return None


def batch_get_github_stats(github_urls: List[str]) -> Dict[str, Optional[Dict]]:
    """
    批量获取GitHub统计信息
    
    Args:
        github_urls: GitHub URL列表
        
    Returns:
        URL到统计信息的映射字典
    """
    results = {}
    github_service = GitHubService()
    
    for url in github_urls:
        if url:
            try:
                stats = github_service.get_repository_stats(url)
                results[url] = stats
            except Exception as e:
                logger.error(f"Failed to get stats for {url}: {e}")
                results[url] = None
        else:
            results[url] = None
    
    return results


def format_github_stats_for_display(stats: Optional[Dict]) -> Dict:
    """
    格式化GitHub统计数据用于前端显示
    
    Args:
        stats: 原始统计数据
        
    Returns:
        格式化后的显示数据
    """
    if not stats or not stats.get('basic'):
        return {
            'available': False,
            'error': 'No data available'
        }
    
    basic = stats['basic']
    languages = stats.get('languages', {})
    
    # 计算语言百分比
    total_bytes = sum(languages.values())
    language_percentages = []
    
    if total_bytes > 0:
        for lang, bytes_count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            percentage = (bytes_count / total_bytes) * 100
            language_percentages.append({
                'name': lang,
                'percentage': round(percentage, 1),
                'bytes': bytes_count
            })
    
    # 格式化时间
    def format_date(date_str):
        if not date_str:
            return None
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except:
            return date_str
    
    return {
        'available': True,
        'name': basic.get('name'),
        'description': basic.get('description'),
        'stars': basic.get('stars', 0),
        'forks': basic.get('forks', 0),
        'watchers': basic.get('watchers', 0),
        'open_issues': basic.get('open_issues', 0),
        'language': basic.get('language'),
        'languages': language_percentages[:5],  # 只显示前5种语言
        'license': basic.get('license'),
        'created_at': format_date(basic.get('created_at')),
        'updated_at': format_date(basic.get('updated_at')),
        'size_kb': basic.get('size', 0),
        'topics': basic.get('topics', [])[:8],  # 限制显示的topics数量
        'recent_commits': stats.get('recent_commits', [])[:3],  # 最近3个提交
        'homepage': basic.get('homepage'),
        'archived': basic.get('archived', False),
        'private': basic.get('private', False)
    }