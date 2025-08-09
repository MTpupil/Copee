#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪贴板管理器模块
负责监控、存储和管理剪贴板内容
"""

import win32clipboard
import win32con
import hashlib
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from PIL import Image
import io
import uuid

class ClipboardItem:
    """
    剪贴板项目类
    """
    
    def __init__(self, content: str, item_type: str, timestamp: datetime = None, favorite: bool = False):
        """
        初始化剪贴板项目
        
        Args:
            content: 内容
            item_type: 类型 (text, image, file)
            timestamp: 时间戳
            favorite: 是否收藏
        """
        self.content = content
        self.item_type = item_type
        self.timestamp = timestamp or datetime.now()
        self.favorite = favorite
        self.hash = self._generate_hash()
        
    def _generate_hash(self) -> str:
        """
        生成内容哈希值，用于去重
        
        Returns:
            str: 哈希值
        """
        content_str = f"{self.content}_{self.item_type}"
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()
        
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict: 字典格式的数据
        """
        return {
            'content': self.content,
            'type': self.item_type,
            'timestamp': self.timestamp.isoformat(),
            'hash': self.hash,
            'preview': self._get_preview(),
            'favorite': self.favorite
        }
        
    def _get_preview(self) -> str:
        """
        获取预览文本
        
        Returns:
            str: 预览文本
        """
        if self.item_type == 'text':
            # 文本类型，截取前50个字符作为预览
            return self.content[:50] + ('...' if len(self.content) > 50 else '')
        elif self.item_type == 'image':
            return '[图片]'
        elif self.item_type == 'file':
            return f'[文件] {self.content}'
        else:
            return '[未知类型]'

class ClipboardManager:
    """
    剪贴板管理器
    """
    
    def __init__(self, max_items: int = 100):
        """
        初始化剪贴板管理器
        
        Args:
            max_items: 最大存储项目数量
        """
        self.max_items = max_items
        self.items: List[ClipboardItem] = []
        self.last_clipboard_hash = ""
        
        # 使用AppData目录存储数据和图片
        import os
        appdata_dir = os.path.join(os.environ['APPDATA'], 'Copee')
        if not os.path.exists(appdata_dir):
            os.makedirs(appdata_dir)
            
        self.data_file = os.path.join(appdata_dir, "clipboard_data.json")
        self.images_dir = os.path.join(appdata_dir, 'images')  # 图片存储目录
        
        # 创建图片存储目录
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
        
        # 加载历史数据
        self._load_data()
        self._cleanup_orphaned_images()  # 清理孤立的图片文件
        
        # 初始化当前剪贴板状态，避免启动时自动保存当前剪贴板内容
        self._init_clipboard_state()
        
    def _init_clipboard_state(self):
        """
        初始化剪贴板状态，获取当前剪贴板内容的hash但不保存
        """
        try:
            win32clipboard.OpenClipboard()
            
            # 检查文本内容
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                content = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                self.last_clipboard_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            # 检查图片内容
            elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                try:
                    dib_data = win32clipboard.GetClipboardData(win32con.CF_DIB)
                    self.last_clipboard_hash = hashlib.md5(dib_data).hexdigest()
                except:
                    self.last_clipboard_hash = ""
            else:
                self.last_clipboard_hash = ""
                
            win32clipboard.CloseClipboard()
        except Exception as e:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            self.last_clipboard_hash = ""
        
    def _load_data(self):
        """
        从文件加载历史数据
        """
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item_data in data:
                        # 兼容旧版本数据，如果没有favorite字段则默认为False
                        favorite = item_data.get('favorite', False)
                        item = ClipboardItem(
                            content=item_data['content'],
                            item_type=item_data['type'],
                            timestamp=datetime.fromisoformat(item_data['timestamp']),
                            favorite=favorite
                        )
                        self.items.append(item)
            else:
                self.items = []
        except Exception as e:
            # 如果加载失败，创建空列表
            self.items = []
            
    def _save_data(self):
        """
        保存数据到文件
        """
        try:
            data = [item.to_dict() for item in self.items]
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass  # 静默处理数据保存错误
            
    def check_clipboard_change(self) -> bool:
        """
        检查剪贴板是否有变化
        
        Returns:
            bool: 是否有变化
        """
        try:
            # 打开剪贴板
            win32clipboard.OpenClipboard()
            
            # 检查是否有文本内容
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                content = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
                
                if content_hash != self.last_clipboard_hash:
                    self.last_clipboard_hash = content_hash
                    self._add_text_item(content)
                    win32clipboard.CloseClipboard()
                    return True
                    
            # 检查是否有图片内容
            elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                # 获取图片数据并生成哈希
                try:
                    dib_data = win32clipboard.GetClipboardData(win32con.CF_DIB)
                    image_hash = hashlib.md5(dib_data).hexdigest()
                    
                    # 检查是否与上次的图片相同
                    if image_hash != self.last_clipboard_hash:
                        self.last_clipboard_hash = image_hash
                        self._handle_image_clipboard()
                        win32clipboard.CloseClipboard()
                        return True
                except:
                    # 如果获取图片数据失败，仍然处理图片内容
                    self._handle_image_clipboard()
                    win32clipboard.CloseClipboard()
                    return True
                
            win32clipboard.CloseClipboard()
            return False
    
        except Exception as e:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            return False
    
    def _cleanup_orphaned_images(self):
        """
        清理孤立的图片文件（不在items列表中引用的图片文件）
        """
        try:
            if not os.path.exists(self.images_dir):
                return
            
            # 获取所有当前引用的图片文件名
            referenced_images = set()
            for item in self.items:
                if item.item_type == 'image':
                    referenced_images.add(item.content)
            
            # 遍历images目录中的所有文件
            for filename in os.listdir(self.images_dir):
                if filename.endswith('.png') and filename not in referenced_images:
                    # 删除未被引用的图片文件
                    orphaned_path = os.path.join(self.images_dir, filename)
                    try:
                        os.remove(orphaned_path)
                    except:
                        pass  # 静默处理文件删除错误
                        
            # 清理之前删除失败的文件
            self._cleanup_failed_deletions()
                        
        except Exception as e:
            pass  # 静默处理清理错误
            
    def _cleanup_failed_deletions(self):
        """
        清理之前删除失败的图片文件
        """
        if not hasattr(self, '_failed_deletions') or not self._failed_deletions:
            return
            
        # 尝试删除失败列表中的文件
        remaining_failed = []
        for file_path in self._failed_deletions:
            try:
                if os.path.exists(file_path):
                    import stat
                    os.chmod(file_path, stat.S_IWRITE)
                    os.remove(file_path)
            except Exception:
                # 仍然删除失败，保留在列表中
                remaining_failed.append(file_path)
                
        # 更新失败列表
        self._failed_deletions = remaining_failed
            
    def _add_text_item(self, content: str):
        """
        添加文本项目
        
        Args:
            content: 文本内容
        """
        # 预处理文本内容，清理可能有问题的字符
        try:
            # 确保文本是有效的Unicode字符串
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='replace')
            
            # 清理可能导致编码问题的字符
            # 替换一些特殊的Unicode字符为标准字符
            content = content.replace('\u2028', '\n')  # 行分隔符
            content = content.replace('\u2029', '\n\n')  # 段落分隔符
            content = content.replace('\u00a0', ' ')  # 不间断空格
            
            # 移除或替换其他可能有问题的控制字符
            import re
            # 保留常见的控制字符（换行、制表符等），移除其他控制字符
            content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', content)
            
        except Exception as e:
            pass  # 静默处理文本预处理错误
            # 如果处理失败，确保至少是字符串类型
            content = str(content)
        
        # 创建新项目
        new_item = ClipboardItem(content, 'text')
        
        # 检查是否已存在（去重）
        for existing_item in self.items:
            if existing_item.hash == new_item.hash:
                # 如果已存在，移动到最前面
                self.items.remove(existing_item)
                self.items.insert(0, existing_item)
                self._save_data()
                return
                
        # 添加新项目到最前面
        self.items.insert(0, new_item)
        
        # 限制最大数量
        if len(self.items) > self.max_items:
            self.items = self.items[:self.max_items]
            
        # 保存数据
        self._save_data()
        
    def _handle_image_clipboard(self):
        """
        处理图片剪贴板内容 - 优化版本，将图片保存为单独文件
        """
        try:
            # 获取剪贴板中的图片数据
            dib_data = win32clipboard.GetClipboardData(win32con.CF_DIB)
            
            # 将DIB数据转换为PIL Image对象
            # DIB格式需要添加文件头才能被PIL识别
            img_size = len(dib_data)
            # 创建BMP文件头
            bmp_header = b'BM' + (img_size + 14).to_bytes(4, 'little') + b'\x00\x00\x00\x00' + b'\x36\x00\x00\x00'
            bmp_data = bmp_header + dib_data
            
            # 使用PIL打开图片
            image = Image.open(io.BytesIO(bmp_data))
            
            # 生成图片的哈希值用于去重检查
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            img_data = img_buffer.getvalue()
            img_hash = hashlib.md5(img_data).hexdigest()
            
            # 检查是否已存在相同的图片项目（去重）
            for i, existing_item in enumerate(self.items):
                if existing_item.item_type == 'image' and existing_item.hash == img_hash:
                    # 如果找到相同项目，将其移到最前面
                    self.items.pop(i)
                    self.items.insert(0, existing_item)
                    self._save_data()
                    return
            
            # 生成唯一的文件名
            image_filename = f"{uuid.uuid4().hex}.png"
            image_path = os.path.join(self.images_dir, image_filename)
            
            # 确保图片目录存在
            if not os.path.exists(self.images_dir):
                os.makedirs(self.images_dir)
            
            # 保存图片到文件
            with open(image_path, 'wb') as f:
                f.write(img_data)
            
            # 创建图片项目，content存储文件路径
            new_item = ClipboardItem(image_filename, 'image')
            # 手动设置哈希值，因为我们已经计算过了
            new_item.hash = img_hash
            
            # 添加新项目到列表最前面
            self.items.insert(0, new_item)
            
            # 限制最大数量，删除多余项目时也要删除对应的图片文件
            if len(self.items) > self.max_items:
                # 删除多余项目对应的图片文件
                for item_to_remove in self.items[self.max_items:]:
                    if item_to_remove.item_type == 'image':
                        old_image_path = os.path.join(self.images_dir, item_to_remove.content)
                        if os.path.exists(old_image_path):
                            try:
                                os.remove(old_image_path)
                            except Exception as del_error:
                                pass
                
                self.items = self.items[:self.max_items]
                
            self._save_data()
        except Exception as e:
            pass
            
    def get_items(self) -> List[Dict[str, Any]]:
        """
        获取所有剪贴板项目
        
        Returns:
            List[Dict]: 项目列表
        """
        return [item.to_dict() for item in self.items]
        
    def copy_item_to_clipboard(self, index: int) -> bool:
        """
        将指定项目复制到剪贴板
        
        Args:
            index: 项目索引
            
        Returns:
            bool: 是否成功
        """
        try:
            if 0 <= index < len(self.items):
                item = self.items[index]
                
                # 打开剪贴板
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                
                if item.item_type == 'text':
                    # 处理文本内容，确保编码正确
                    text_content = item.content
                    
                    # 处理可能的编码问题
                    try:
                        # 确保文本是有效的Unicode字符串
                        if isinstance(text_content, bytes):
                            text_content = text_content.decode('utf-8', errors='replace')
                        
                        # 清理可能导致编码问题的字符
                        # 替换一些特殊的Unicode字符为标准字符
                        text_content = text_content.replace('\u2028', '\n')  # 行分隔符
                        text_content = text_content.replace('\u2029', '\n\n')  # 段落分隔符
                        text_content = text_content.replace('\u00a0', ' ')  # 不间断空格
                        
                        # 移除或替换其他可能有问题的控制字符
                        import re
                        # 保留常见的控制字符（换行、制表符等），移除其他控制字符
                        text_content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text_content)
                        
                    except Exception as encoding_error:
                        pass  # 静默处理文本编码错误
                        # 如果处理失败，尝试使用原始内容
                        text_content = str(item.content)
                    
                    # 设置文本内容到剪贴板
                    win32clipboard.SetClipboardText(text_content)
                    
                elif item.item_type == 'image':
                    # 处理图片内容 - 从文件读取
                    try:
                        # 构建图片文件路径
                        image_path = os.path.join(self.images_dir, item.content)
                        
                        # 检查文件是否存在
                        if not os.path.exists(image_path):
                            win32clipboard.CloseClipboard()
                            return False
                        
                        # 从文件读取图片
                        image = Image.open(image_path)
                        
                        # 将图片转换为DIB格式
                        img_buffer = io.BytesIO()
                        image.save(img_buffer, format='BMP')
                        img_buffer.seek(0)
                        
                        # 读取BMP数据并跳过文件头（14字节）
                        bmp_data = img_buffer.read()
                        dib_data = bmp_data[14:]  # 跳过BMP文件头，只保留DIB数据
                        
                        # 设置图片到剪贴板
                        win32clipboard.SetClipboardData(win32con.CF_DIB, dib_data)
                        
                    except Exception as img_error:
                        pass  # 静默处理图片复制错误
                        # 如果图片处理失败，关闭剪贴板并返回失败
                        win32clipboard.CloseClipboard()
                        return False
                    
                win32clipboard.CloseClipboard()
                
                # 移动到最前面
                self.items.remove(item)
                self.items.insert(0, item)
                self._save_data()
                
                return True
                
        except Exception as e:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            pass  # 静默处理剪贴板复制错误
            
        return False
        
    def copy_text_only_to_clipboard(self, index: int) -> bool:
        """
        将指定项目的纯文本内容复制到剪贴板（图片项目复制其预览文本）
        
        Args:
            index: 项目索引
            
        Returns:
            bool: 是否成功
        """
        try:
            if 0 <= index < len(self.items):
                item = self.items[index]
                
                # 打开剪贴板
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                
                if item.item_type == 'text':
                    text_content = item.content
                elif item.item_type == 'image':
                    text_content = '[图片]'
                elif item.item_type == 'file':
                    text_content = f'[文件] {item.content}'
                else:
                    text_content = '[未知类型]'
                
                # 处理文本内容，确保编码正确
                try:
                    # 确保文本是有效的Unicode字符串
                    if isinstance(text_content, bytes):
                        text_content = text_content.decode('utf-8', errors='replace')
                    
                    # 清理可能导致编码问题的字符
                    text_content = text_content.replace('\u2028', '\n')  # 行分隔符
                    text_content = text_content.replace('\u2029', '\n\n')  # 段落分隔符
                    text_content = text_content.replace('\u00a0', ' ')  # 不间断空格
                    
                    # 移除或替换其他可能有问题的控制字符
                    import re
                    text_content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text_content)
                    
                except Exception as encoding_error:
                    text_content = str(text_content)
                
                # 设置文本内容到剪贴板
                win32clipboard.SetClipboardText(text_content)
                win32clipboard.CloseClipboard()
                
                # 移动到最前面
                self.items.remove(item)
                self.items.insert(0, item)
                self._save_data()
                
                return True
                
        except Exception as e:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            
        return False
        
    def toggle_favorite(self, index: int) -> tuple[bool, bool]:
        """
        切换指定项目的收藏状态
        
        Args:
            index: 项目索引
            
        Returns:
            tuple[bool, bool]: (是否成功, 收藏状态)
        """
        try:
            if 0 <= index < len(self.items):
                self.items[index].favorite = not self.items[index].favorite
                self._save_data()
                return True, self.items[index].favorite
            return False, False
        except Exception as e:
            return False, False
        
    def delete_item(self, index: int) -> bool:
        """
        删除指定项目
        
        Args:
            index: 项目索引
            
        Returns:
            bool: 是否成功
        """
        try:
            if 0 <= index < len(self.items):
                item_to_delete = self.items[index]
                
                # 如果是图片项目，删除对应的图片文件
                if item_to_delete.item_type == 'image':
                    image_path = os.path.join(self.images_dir, item_to_delete.content)
                    
                    if os.path.exists(image_path):
                        try:
                            # 尝试多次删除，处理文件被占用的情况
                            import stat
                            import time
                            
                            max_retries = 3
                            for retry in range(max_retries):
                                try:
                                    os.chmod(image_path, stat.S_IWRITE)  # 确保文件可写
                                    os.remove(image_path)
                                    break  # 删除成功，跳出重试循环
                                except (PermissionError, OSError):
                                    if retry < max_retries - 1:
                                        time.sleep(0.1)  # 等待100ms后重试
                                        continue
                                    else:
                                        # 最后一次重试失败，记录到待清理列表
                                        if hasattr(self, '_failed_deletions'):
                                            self._failed_deletions.append(image_path)
                                        else:
                                            self._failed_deletions = [image_path]
                                        break
                                        
                        except Exception:
                            # 即使文件删除失败，也继续删除项目记录
                            if hasattr(self, '_failed_deletions'):
                                self._failed_deletions.append(image_path)
                            else:
                                self._failed_deletions = [image_path]
                
                # 删除项目记录
                deleted_item = self.items.pop(index)
                
                # 保存数据到文件
                self._save_data()
                return True
            else:
                return False
        except Exception:
            return False
        
    def clear_all(self) -> bool:
        """
        清空所有项目（保留收藏的项目）
        
        Returns:
            bool: 是否成功
        """
        try:
            # 删除非收藏项目的图片文件
            for item in self.items:
                if not item.favorite and item.item_type == 'image':
                    image_path = os.path.join(self.images_dir, item.content)
                    if os.path.exists(image_path):
                        try:
                            os.remove(image_path)
                        except:
                            pass  # 静默处理文件删除错误
            
            # 只保留收藏的项目
            self.items = [item for item in self.items if item.favorite]
            self._save_data()
            return True
        except Exception as e:
            pass  # 静默处理清空错误
            return False