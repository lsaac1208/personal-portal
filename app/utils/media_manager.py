"""
📂 媒体文件管理器
处理所有媒体文件的组织、分类、清理功能
"""
import os
import json
import shutil
from datetime import datetime, timedelta
from flask import current_app
from .file_handler import get_file_size, get_image_info


class MediaManager:
    """媒体文件管理器"""
    
    def __init__(self):
        self.upload_folder = current_app.config.get(
            'UPLOAD_FOLDER',
            os.path.join(current_app.static_folder, 'uploads')
        )
        self.max_storage_mb = current_app.config.get('MAX_STORAGE_MB', 1000)  # 1GB默认限制
    
    def get_folder_structure(self):
        """获取文件夹结构"""
        structure = {}
        if not os.path.exists(self.upload_folder):
            return structure
        
        for root, dirs, files in os.walk(self.upload_folder):
            # 计算相对路径
            rel_path = os.path.relpath(root, self.upload_folder)
            if rel_path == '.':
                rel_path = '/'
            
            structure[rel_path] = {
                'dirs': dirs,
                'files': [],
                'size': 0,
                'count': len(files)
            }
            
            # 收集文件信息
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size = get_file_size(file_path)
                    created = datetime.fromtimestamp(os.path.getctime(file_path))
                    modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    file_info = {
                        'name': file,
                        'size': size,
                        'size_mb': round(size, 2),
                        'created_at': created.strftime('%Y-%m-%d %H:%M:%S'),
                        'modified_at': modified.strftime('%Y-%m-%d %H:%M:%S'),
                        'extension': os.path.splitext(file)[1].lower(),
                        'is_image': file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')),
                        'path': os.path.join(rel_path, file).replace('\\', '/')
                    }
                    
                    # 如果是图片，获取图片信息
                    if file_info['is_image']:
                        img_info = get_image_info(file_path)
                        if img_info:
                            file_info.update(img_info)
                    
                    structure[rel_path]['files'].append(file_info)
                    structure[rel_path]['size'] += size
                    
                except Exception as e:
                    current_app.logger.warning(f"无法获取文件信息 {file_path}: {str(e)}")
        
        return structure
    
    def get_storage_stats(self):
        """获取存储统计信息"""
        stats = {
            'total_size_mb': 0,
            'total_files': 0,
            'folders': {},
            'file_types': {},
            'large_files': [],  # 大于10MB的文件
            'old_files': [],   # 超过30天未使用的文件
            'storage_usage_percent': 0
        }
        
        structure = self.get_folder_structure()
        
        for folder_path, folder_data in structure.items():
            # 文件夹统计
            folder_size_mb = folder_data['size']
            stats['folders'][folder_path] = {
                'size_mb': round(folder_size_mb, 2),
                'files': folder_data['count'],
                'size_percent': 0  # 稍后计算
            }
            
            stats['total_size_mb'] += folder_size_mb
            stats['total_files'] += folder_data['count']
            
            # 文件分析
            for file_info in folder_data['files']:
                # 文件类型统计
                ext = file_info['extension'] or 'no_extension'
                if ext not in stats['file_types']:
                    stats['file_types'][ext] = {'count': 0, 'size_mb': 0}
                
                stats['file_types'][ext]['count'] += 1
                stats['file_types'][ext]['size_mb'] += file_info['size']
                
                # 大文件检测
                if file_info['size'] > 10:  # 大于10MB
                    stats['large_files'].append({
                        'path': file_info['path'],
                        'name': file_info['name'],
                        'size_mb': file_info['size_mb']
                    })
                
                # 旧文件检测
                modified_date = datetime.strptime(file_info['modified_at'], '%Y-%m-%d %H:%M:%S')
                if (datetime.now() - modified_date).days > 30:
                    stats['old_files'].append({
                        'path': file_info['path'],
                        'name': file_info['name'],
                        'modified_at': file_info['modified_at'],
                        'days_old': (datetime.now() - modified_date).days
                    })
        
        # 计算百分比
        if stats['total_size_mb'] > 0:
            for folder_path in stats['folders']:
                stats['folders'][folder_path]['size_percent'] = round(
                    (stats['folders'][folder_path]['size_mb'] / stats['total_size_mb']) * 100, 1
                )
        
        # 存储使用率
        stats['storage_usage_percent'] = round((stats['total_size_mb'] / self.max_storage_mb) * 100, 1)
        
        # 排序
        stats['large_files'] = sorted(stats['large_files'], key=lambda x: x['size_mb'], reverse=True)[:10]
        stats['old_files'] = sorted(stats['old_files'], key=lambda x: x['days_old'], reverse=True)[:20]
        
        return stats
    
    def organize_files(self):
        """文件整理 - 按类型和日期组织文件"""
        organized_count = 0
        
        try:
            # 创建组织结构
            folders_to_create = [
                'images/content',
                'images/featured', 
                'images/thumbnails',
                'documents',
                'archives',
                'temp'
            ]
            
            for folder in folders_to_create:
                folder_path = os.path.join(self.upload_folder, folder)
                os.makedirs(folder_path, exist_ok=True)
            
            # 扫描并移动文件
            structure = self.get_folder_structure()
            
            for folder_path, folder_data in structure.items():
                if folder_path == '/':  # 只处理根目录的散乱文件
                    for file_info in folder_data['files']:
                        file_path = os.path.join(self.upload_folder, file_info['name'])
                        
                        # 确定目标文件夹
                        target_folder = self._get_target_folder(file_info)
                        target_path = os.path.join(self.upload_folder, target_folder, file_info['name'])
                        
                        # 移动文件
                        if target_folder and file_path != target_path:
                            try:
                                # 确保目标文件夹存在
                                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                                shutil.move(file_path, target_path)
                                organized_count += 1
                                current_app.logger.info(f"文件已整理: {file_info['name']} -> {target_folder}")
                            except Exception as e:
                                current_app.logger.error(f"整理文件失败 {file_info['name']}: {str(e)}")
            
            return {
                'success': True,
                'organized_count': organized_count,
                'message': f'成功整理了 {organized_count} 个文件'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'文件整理失败：{str(e)}'
            }
    
    def _get_target_folder(self, file_info):
        """根据文件类型确定目标文件夹"""
        if file_info['is_image']:
            if 'thumb' in file_info['name'].lower():
                return 'images/thumbnails'
            elif 'featured' in file_info['name'].lower():
                return 'images/featured'
            else:
                return 'images/content'
        
        # 文档类型
        doc_extensions = ['.pdf', '.doc', '.docx', '.txt', '.md']
        if file_info['extension'] in doc_extensions:
            return 'documents'
        
        # 压缩文件
        archive_extensions = ['.zip', '.rar', '.7z', '.tar', '.gz']
        if file_info['extension'] in archive_extensions:
            return 'archives'
        
        # 临时文件
        temp_patterns = ['temp', 'tmp', 'cache']
        if any(pattern in file_info['name'].lower() for pattern in temp_patterns):
            return 'temp'
        
        return None  # 不移动
    
    def cleanup_old_files(self, days=30, dry_run=False):
        """清理旧文件"""
        cleaned_files = []
        total_size_saved = 0
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            structure = self.get_folder_structure()
            
            for folder_path, folder_data in structure.items():
                for file_info in folder_data['files']:
                    modified_date = datetime.strptime(file_info['modified_at'], '%Y-%m-%d %H:%M:%S')
                    
                    if modified_date < cutoff_date:
                        file_path = os.path.join(
                            self.upload_folder,
                            file_info['path'].lstrip('/')
                        )
                        
                        cleaned_files.append({
                            'path': file_info['path'],
                            'name': file_info['name'],
                            'size_mb': file_info['size_mb'],
                            'days_old': (datetime.now() - modified_date).days
                        })
                        
                        total_size_saved += file_info['size']
                        
                        # 实际删除文件
                        if not dry_run:
                            try:
                                os.remove(file_path)
                                current_app.logger.info(f"已删除旧文件: {file_info['path']}")
                            except Exception as e:
                                current_app.logger.error(f"删除文件失败 {file_info['path']}: {str(e)}")
            
            return {
                'success': True,
                'cleaned_count': len(cleaned_files),
                'size_saved_mb': round(total_size_saved, 2),
                'files': cleaned_files,
                'dry_run': dry_run
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'清理失败：{str(e)}'
            }
    
    def optimize_all_images(self):
        """批量优化所有图片"""
        from .file_handler import optimize_image
        
        optimized_count = 0
        total_size_saved = 0
        
        try:
            structure = self.get_folder_structure()
            
            for folder_path, folder_data in structure.items():
                for file_info in folder_data['files']:
                    if file_info['is_image']:
                        file_path = os.path.join(
                            self.upload_folder,
                            file_info['path'].lstrip('/')
                        )
                        
                        original_size = file_info['size']
                        
                        # 优化图片
                        optimize_image(file_path)
                        
                        # 计算节省的空间
                        new_size = get_file_size(file_path)
                        if new_size < original_size:
                            total_size_saved += (original_size - new_size)
                            optimized_count += 1
            
            return {
                'success': True,
                'optimized_count': optimized_count,
                'size_saved_mb': round(total_size_saved, 2),
                'message': f'成功优化了 {optimized_count} 张图片，节省 {round(total_size_saved, 2)} MB'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'批量优化失败：{str(e)}'
            }
    
    def search_files(self, query, file_type=None):
        """搜索文件"""
        results = []
        query_lower = query.lower()
        
        try:
            structure = self.get_folder_structure()
            
            for folder_path, folder_data in structure.items():
                for file_info in folder_data['files']:
                    # 文件名匹配
                    if query_lower in file_info['name'].lower():
                        match = True
                    else:
                        match = False
                    
                    # 文件类型筛选
                    if match and file_type:
                        if file_type == 'images' and not file_info['is_image']:
                            match = False
                        elif file_type == 'documents' and file_info['extension'] not in ['.pdf', '.doc', '.docx', '.txt', '.md']:
                            match = False
                    
                    if match:
                        results.append({
                            'name': file_info['name'],
                            'path': file_info['path'],
                            'size_mb': file_info['size_mb'],
                            'modified_at': file_info['modified_at'],
                            'is_image': file_info['is_image'],
                            'folder': folder_path
                        })
            
            return {
                'success': True,
                'results': results,
                'count': len(results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'搜索失败：{str(e)}'
            }