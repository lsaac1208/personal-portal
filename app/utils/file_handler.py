"""
🗂️ 文件处理工具模块
处理文件上传、图片优化、文件验证等功能
"""
import os
import uuid
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename
from flask import current_app
import mimetypes


def allowed_file(filename, allowed_extensions=None):
    """
    检查文件是否为允许的格式
    
    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名列表
    
    Returns:
        bool: 是否允许的文件格式
    """
    if not allowed_extensions:
        allowed_extensions = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg']
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_file_size(filepath):
    """获取文件大小（MB）"""
    return os.path.getsize(filepath) / (1024 * 1024)


def validate_file_size(file, max_size_mb=5):
    """
    验证文件大小
    
    Args:
        file: 文件对象
        max_size_mb: 最大大小（MB）
    
    Returns:
        bool: 是否符合大小要求
    """
    file.seek(0, 2)  # 移动到文件末尾
    size = file.tell() / (1024 * 1024)  # 获取大小（MB）
    file.seek(0)  # 重置到开头
    return size <= max_size_mb


def generate_unique_filename(original_filename):
    """
    生成唯一文件名
    
    Args:
        original_filename: 原始文件名
    
    Returns:
        str: 唯一文件名
    """
    filename = secure_filename(original_filename)
    name, ext = os.path.splitext(filename)
    unique_id = uuid.uuid4().hex[:8]
    return f"{name}_{unique_id}{ext}"


def save_upload_file(file, upload_folder, filename=None):
    """
    保存上传的文件
    
    Args:
        file: 文件对象
        upload_folder: 上传目录
        filename: 自定义文件名（可选）
    
    Returns:
        str: 保存的文件路径
    """
    if not filename:
        filename = generate_unique_filename(file.filename)
    
    # 确保上传目录存在
    os.makedirs(upload_folder, exist_ok=True)
    
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    return filepath


def optimize_image(image_path, max_width=1200, max_height=800, quality=85):
    """
    优化图片：调整大小、压缩质量
    
    Args:
        image_path: 图片路径
        max_width: 最大宽度
        max_height: 最大高度
        quality: 质量（1-100）
    
    Returns:
        str: 优化后的图片路径
    """
    try:
        with Image.open(image_path) as img:
            # 转换为RGB模式（如果是RGBA）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 获取原始尺寸
            width, height = img.size
            
            # 计算新尺寸（保持长宽比）
            if width > max_width or height > max_height:
                # 计算缩放比例
                width_ratio = max_width / width
                height_ratio = max_height / height
                ratio = min(width_ratio, height_ratio)
                
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                
                # 使用高质量重采样
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 生成优化后的文件名
            name, ext = os.path.splitext(image_path)
            optimized_path = f"{name}_optimized{ext}"
            
            # 保存优化后的图片
            img.save(optimized_path, 'JPEG', quality=quality, optimize=True)
            
            # 如果优化后的文件更小，删除原文件并重命名
            if os.path.getsize(optimized_path) < os.path.getsize(image_path):
                os.remove(image_path)
                os.rename(optimized_path, image_path)
            else:
                os.remove(optimized_path)
            
            return image_path
            
    except Exception as e:
        current_app.logger.error(f"图片优化失败：{str(e)}")
        return image_path


def create_thumbnail(image_path, size=(300, 200)):
    """
    创建缩略图
    
    Args:
        image_path: 原图路径
        size: 缩略图尺寸 (width, height)
    
    Returns:
        str: 缩略图路径
    """
    try:
        name, ext = os.path.splitext(image_path)
        thumbnail_path = f"{name}_thumb{ext}"
        
        with Image.open(image_path) as img:
            # 转换为RGB模式
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 创建缩略图（保持长宽比）
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # 创建固定尺寸的画布
            thumb = Image.new('RGB', size, (255, 255, 255))
            
            # 计算居中位置
            x = (size[0] - img.size[0]) // 2
            y = (size[1] - img.size[1]) // 2
            
            # 粘贴图片到画布中心
            thumb.paste(img, (x, y))
            
            # 保存缩略图
            thumb.save(thumbnail_path, 'JPEG', quality=80, optimize=True)
            
            return thumbnail_path
            
    except Exception as e:
        current_app.logger.error(f"缩略图生成失败：{str(e)}")
        return image_path


def get_image_info(image_path):
    """
    获取图片信息
    
    Args:
        image_path: 图片路径
    
    Returns:
        dict: 图片信息
    """
    try:
        with Image.open(image_path) as img:
            return {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.size[0],
                'height': img.size[1],
                'file_size': get_file_size(image_path)
            }
    except Exception as e:
        current_app.logger.error(f"获取图片信息失败：{str(e)}")
        return None


def cleanup_old_files(directory, days=7):
    """
    清理旧文件
    
    Args:
        directory: 目录路径
        days: 保留天数
    """
    import time
    from datetime import datetime, timedelta
    
    if not os.path.exists(directory):
        return
    
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            if os.path.getmtime(filepath) < cutoff_time:
                try:
                    os.remove(filepath)
                    current_app.logger.info(f"已清理旧文件：{filepath}")
                except Exception as e:
                    current_app.logger.error(f"清理文件失败 {filepath}: {str(e)}")


def validate_image_file(file):
    """
    验证图片文件
    
    Args:
        file: 文件对象
    
    Returns:
        dict: 验证结果
    """
    result = {
        'valid': False,
        'errors': []
    }
    
    # 检查文件名
    if not file or not file.filename:
        result['errors'].append('没有选择文件')
        return result
    
    # 检查文件格式
    if not allowed_file(file.filename, ['png', 'jpg', 'jpeg', 'gif', 'webp']):
        result['errors'].append('不支持的文件格式，仅支持 PNG, JPG, JPEG, GIF, WebP')
        return result
    
    # 检查文件大小
    if not validate_file_size(file, max_size_mb=5):
        result['errors'].append('文件大小不能超过 5MB')
        return result
    
    # 验证文件内容（检查是否真的是图片）
    try:
        file.seek(0)
        header = file.read(32)
        file.seek(0)
        
        # 检查文件头部签名
        image_signatures = {
            b'\xFF\xD8\xFF': 'JPEG',
            b'\x89PNG\r\n\x1a\n': 'PNG',
            b'GIF8': 'GIF',
            b'RIFF': 'WebP'  # WebP 文件以 RIFF 开头
        }
        
        is_valid_image = False
        for signature in image_signatures:
            if header.startswith(signature):
                is_valid_image = True
                break
        
        if not is_valid_image:
            result['errors'].append('文件不是有效的图片格式')
            return result
        
    except Exception as e:
        result['errors'].append(f'文件验证失败：{str(e)}')
        return result
    
    result['valid'] = True
    return result


class ImageProcessor:
    """图片处理类"""
    
    def __init__(self, upload_folder=None):
        self.upload_folder = upload_folder or current_app.config.get(
            'UPLOAD_FOLDER', 
            os.path.join(current_app.static_folder, 'uploads')
        )
    
    def process_upload(self, file, subfolder='images', create_thumbnail=False):
        """
        处理图片上传
        
        Args:
            file: 文件对象
            subfolder: 子文件夹名称
            create_thumbnail: 是否创建缩略图
        
        Returns:
            dict: 处理结果
        """
        # 验证文件
        validation = validate_image_file(file)
        if not validation['valid']:
            return {
                'success': False,
                'errors': validation['errors']
            }
        
        try:
            # 设置上传路径
            upload_path = os.path.join(self.upload_folder, subfolder)
            
            # 保存原文件
            filename = generate_unique_filename(file.filename)
            filepath = save_upload_file(file, upload_path, filename)
            
            # 优化图片
            optimized_path = optimize_image(filepath)
            
            # 创建缩略图（如果需要）
            thumbnail_path = None
            if create_thumbnail:
                thumbnail_path = create_thumbnail(optimized_path)
            
            # 获取图片信息
            image_info = get_image_info(optimized_path)
            
            # 生成Web访问URL
            relative_path = os.path.relpath(optimized_path, current_app.static_folder)
            image_url = f"/static/{relative_path.replace(os.sep, '/')}"
            
            thumbnail_url = None
            if thumbnail_path:
                thumb_relative_path = os.path.relpath(thumbnail_path, current_app.static_folder)
                thumbnail_url = f"/static/{thumb_relative_path.replace(os.sep, '/')}"
            
            return {
                'success': True,
                'image_url': image_url,
                'thumbnail_url': thumbnail_url,
                'filename': filename,
                'info': image_info
            }
            
        except Exception as e:
            current_app.logger.error(f"图片处理失败：{str(e)}")
            return {
                'success': False,
                'errors': [f'图片处理失败：{str(e)}']
            }