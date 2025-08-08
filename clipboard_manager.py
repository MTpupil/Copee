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
import base64

class ClipboardItem:
    """
    剪贴板项目类
    """
    
    def __init__(self, content: str, item_type: str, timestamp: datetime = None):
        """
        初始化剪贴板项目
        
        Args:
            content: 内容
            item_type: 类型 (text, image, file)
            timestamp: 时间戳
        """
        self.content = content
        self.item_type = item_type
        self.timestamp = timestamp or datetime.now()
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
            'preview': self._get_preview()
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
        self.data_file = "clipboard_data.json"
        
        # 加载历史数据
        self._load_data()
        
    def _load_data(self):
        """
        从文件加载历史数据
        """
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item_data in data:
                        item = ClipboardItem(
                            content=item_data['content'],
                            item_type=item_data['type'],
                            timestamp=datetime.fromisoformat(item_data['timestamp'])
                        )
                        self.items.append(item)
        except Exception as e:
            print(f"加载历史数据失败: {e}")
            
    def _save_data(self):
        """
        保存数据到文件
        """
        try:
            data = [item.to_dict() for item in self.items]
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据失败: {e}")
            
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
                # 处理图片内容
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
            print(f"检查剪贴板失败: {e}")
            return False
            
    def _add_text_item(self, content: str):
        """
        添加文本项目
        
        Args:
            content: 文本内容
        """
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
        处理图片剪贴板内容
        """
        try:
            # 这里可以扩展图片处理逻辑
            # 暂时添加一个占位符
            new_item = ClipboardItem('[图片内容]', 'image')
            self.items.insert(0, new_item)
            
            # 限制最大数量
            if len(self.items) > self.max_items:
                self.items = self.items[:self.max_items]
                
            self._save_data()
        except Exception as e:
            print(f"处理图片剪贴板失败: {e}")
            
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
                    # 设置文本内容
                    win32clipboard.SetClipboardText(item.content)
                    
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
            print(f"复制到剪贴板失败: {e}")
            
        return False
        
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
                self.items.pop(index)
                self._save_data()
                return True
        except Exception as e:
            print(f"删除项目失败: {e}")
            
        return False
        
    def clear_all(self) -> bool:
        """
        清空所有项目
        
        Returns:
            bool: 是否成功
        """
        try:
            self.items.clear()
            self._save_data()
            return True
        except Exception as e:
            print(f"清空失败: {e}")
            return False