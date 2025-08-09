#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API接口模块
提供前端JavaScript调用的API接口
"""

import json
import time
import win32api
import win32con
from typing import List, Dict, Any
from clipboard_manager import ClipboardManager

class ClipboardAPI:
    """
    剪贴板API接口类
    提供给前端调用的方法
    """
    
    def __init__(self, clipboard_manager: ClipboardManager, hide_window_callback=None):
        """
        初始化API接口
        
        Args:
            clipboard_manager: 剪贴板管理器实例
            hide_window_callback: 隐藏窗口的回调函数
        """
        self.clipboard_manager = clipboard_manager
        self.hide_window_callback = hide_window_callback
        
    def get_clipboard_items(self) -> str:
        """
        获取所有剪贴板项目
        
        Returns:
            str: JSON格式的项目列表
        """
        try:
            items = self.clipboard_manager.get_items()
            return json.dumps({
                'success': True,
                'data': items,
                'message': '获取成功'
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'data': [],
                'message': f'获取失败: {str(e)}'
            }, ensure_ascii=False)
            
    def copy_item(self, index: int) -> str:
        """
        复制指定项目到剪贴板并自动粘贴到输入框
        
        Args:
            index: 项目索引
            
        Returns:
            str: JSON格式的操作结果
        """
        try:
            # 复制内容到剪贴板
            success = self.clipboard_manager.copy_item_to_clipboard(index)
            if not success:
                return json.dumps({
                    'success': False,
                    'message': '复制失败'
                }, ensure_ascii=False)
            
            # 隐藏窗口但不改变焦点
            if self.hide_window_callback:
                try:
                    self.hide_window_callback()
                    time.sleep(0.1)  # 短暂等待窗口隐藏
                except Exception:
                    pass
            
            # 执行自动粘贴
            self._auto_paste()
            
            return json.dumps({
                'success': True,
                'message': '已自动粘贴'
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'操作失败: {str(e)}'
            }, ensure_ascii=False)
    
    def _auto_paste(self):
        """
        执行自动粘贴操作
        使用简化的方法，直接发送Ctrl+V键盘事件
        """
        try:
            # 短暂延迟确保剪贴板内容已更新
            time.sleep(0.05)
            
            # 使用全局键盘事件发送Ctrl+V
            # 清除可能的按键状态
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.02)
            
            # 执行Ctrl+V组合键
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)  # Ctrl按下
            time.sleep(0.02)
            win32api.keybd_event(ord('V'), 0, 0, 0)  # V按下
            time.sleep(0.02)
            win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)  # V释放
            time.sleep(0.02)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)  # Ctrl释放
            
        except Exception as e:
            # 静默处理错误，不输出详细信息
            pass
    
    def copy_text_only(self, index: int) -> str:
        """
        仅复制纯文本内容（去除格式）
        
        Args:
            index: 项目索引
            
        Returns:
            str: JSON格式的操作结果
        """
        try:
            # 获取项目
            items = self.clipboard_manager.get_items()
            if index < 0 or index >= len(items):
                return json.dumps({
                    'success': False,
                    'message': '索引超出范围'
                }, ensure_ascii=False)
            
            item = items[index]
            
            # 只有文本类型才支持仅复制文本功能
            if item['type'] != 'text':
                return json.dumps({
                    'success': False,
                    'message': '只有文本类型支持此功能'
                }, ensure_ascii=False)
            
            # 复制纯文本到剪贴板（去除可能的格式）
            success = self.clipboard_manager.copy_text_only_to_clipboard(index)
            if not success:
                return json.dumps({
                    'success': False,
                    'message': '复制失败'
                }, ensure_ascii=False)
            
            # 隐藏窗口并自动粘贴
            if self.hide_window_callback:
                try:
                    self.hide_window_callback()
                    time.sleep(0.1)
                except Exception:
                    pass
            
            self._auto_paste()
            
            return json.dumps({
                'success': True,
                'message': '已复制纯文本'
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'操作失败: {str(e)}'
            }, ensure_ascii=False)
    
    def toggle_favorite(self, index: int) -> str:
        """
        切换项目的收藏状态
        
        Args:
            index: 项目索引
            
        Returns:
            str: JSON格式的操作结果
        """
        try:
            # 获取项目
            items = self.clipboard_manager.get_items()
            if index < 0 or index >= len(items):
                return json.dumps({
                    'success': False,
                    'message': '索引超出范围'
                }, ensure_ascii=False)
            
            # 切换收藏状态
            success, is_favorite = self.clipboard_manager.toggle_favorite(index)
            if not success:
                return json.dumps({
                    'success': False,
                    'message': '操作失败'
                }, ensure_ascii=False)
            
            message = '已添加到收藏' if is_favorite else '已取消收藏'
            return json.dumps({
                'success': True,
                'message': message
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'操作失败: {str(e)}'
            }, ensure_ascii=False)
            
    def delete_item(self, index) -> str:
        """
        删除指定项目
        
        Args:
            index: 项目索引（可能是字符串或整数）
            
        Returns:
            str: JSON格式的操作结果
        """
        
        
        
        try:
            # 先检查索引是否有效
            items = self.clipboard_manager.get_items()
            
            
            # 检查索引是否为None或无效
            if index is None:
                
                return json.dumps({
                    'success': False,
                    'message': '无效的索引参数: null (类型: object)'
                }, ensure_ascii=False)
            
            # 尝试将索引转换为整数（处理pywebview传递字符串的情况）
            
            try:
                original_index = index
                index = int(index)
                
            except (ValueError, TypeError) as e:
                
                return json.dumps({
                    'success': False,
                    'message': f'无效的索引参数: {index} (类型: {type(index).__name__})'
                }, ensure_ascii=False)
            
            # 检查索引范围
            
            if index < 0 or index >= len(items):
                
                return json.dumps({
                    'success': False,
                    'message': f'索引超出范围: {index}，当前共有 {len(items)} 个项目'
                }, ensure_ascii=False)
            
            # 获取要删除的项目信息
            item_to_delete = items[index]
            item_type = item_to_delete.get('type', 'unknown')
            
            
            # 执行删除操作
            
            success = self.clipboard_manager.delete_item(index)
            
            
            if success:
                
                
                return json.dumps({
                    'success': True,
                    'message': f'成功删除{item_type}项目'
                }, ensure_ascii=False)
            else:
                
                
                return json.dumps({
                    'success': False,
                    'message': f'删除{item_type}项目失败，请检查文件权限或重试'
                }, ensure_ascii=False)
                
        except Exception as e:
            
            import traceback
            
            
            return json.dumps({
                'success': False,
                'message': f'删除操作异常: {type(e).__name__}: {str(e)}'
            }, ensure_ascii=False)
            
    def clear_all_items(self) -> str:
        """
        清空所有项目
        
        Returns:
            str: JSON格式的操作结果
        """
        try:
            success = self.clipboard_manager.clear_all()
            return json.dumps({
                'success': success,
                'message': '清空成功' if success else '清空失败'
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'清空失败: {str(e)}'
            }, ensure_ascii=False)
            
    def search_items(self, keyword: str) -> str:
        """
        搜索剪贴板项目
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            str: JSON格式的搜索结果
        """
        try:
            all_items = self.clipboard_manager.get_items()
            
            # 过滤包含关键词的项目
            filtered_items = []
            for item in all_items:
                if keyword.lower() in item['content'].lower():
                    filtered_items.append(item)
                    
            return json.dumps({
                'success': True,
                'data': filtered_items,
                'message': f'找到 {len(filtered_items)} 个匹配项目'
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'data': [],
                'message': f'搜索失败: {str(e)}'
            }, ensure_ascii=False)
            
    def get_item_count(self) -> str:
        """
        获取项目总数
        
        Returns:
            str: JSON格式的项目总数
        """
        try:
            count = len(self.clipboard_manager.items)
            return json.dumps({
                'success': True,
                'data': count,
                'message': '获取成功'
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'data': 0,
                'message': f'获取失败: {str(e)}'
            }, ensure_ascii=False)
            
    def get_app_info(self) -> str:
        """
        获取应用信息
        
        Returns:
            str: JSON格式的应用信息
        """
        return json.dumps({
            'success': True,
            'data': {
                'name': 'Copee',
                'version': '1.0.0',
                'description': '现代化剪贴板管理器',
                'author': 'MTpupil'
            },
            'message': '获取成功'
        }, ensure_ascii=False)
    
    def get_image_data(self, filename: str) -> str:
        """
        获取图片文件的Base64编码数据
        
        Args:
            filename: 图片文件名
            
        Returns:
            str: JSON格式的结果，包含图片的Base64数据
        """
        try:
            import os
            import base64
            
            image_path = os.path.join(self.clipboard_manager.images_dir, filename)
            
            if os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                    data_url = f"data:image/png;base64,{base64_data}"
                    
                    return json.dumps({
                        'success': True,
                        'data_url': data_url,
                        'message': '获取成功'
                    }, ensure_ascii=False)
            else:
                return json.dumps({
                    'success': False,
                    'data_url': '',
                    'message': '图片文件不存在'
                }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'data_url': '',
                'message': f'获取失败: {str(e)}'
            }, ensure_ascii=False)
    
    def hide_window(self) -> str:
        """
        隐藏窗口
        
        Returns:
            str: JSON格式的操作结果
        """
        try:
            if self.hide_window_callback:
                self.hide_window_callback()
            
            return json.dumps({
                'success': True,
                'message': '窗口已隐藏'
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'隐藏窗口失败: {str(e)}'
            }, ensure_ascii=False)