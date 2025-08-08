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
    

            
    def delete_item(self, index: int) -> str:
        """
        删除指定项目
        
        Args:
            index: 项目索引
            
        Returns:
            str: JSON格式的操作结果
        """
        try:
            success = self.clipboard_manager.delete_item(index)
            return json.dumps({
                'success': success,
                'message': '删除成功' if success else '删除失败'
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'删除失败: {str(e)}'
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
                'description': '替代Windows Win+V的现代化剪贴板管理器',
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
            import datetime
            
            # 记录调试信息
            timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
            print(f"[{timestamp}] 后端调试: 请求获取图片数据 - 文件名: {filename}")
            
            # 构建图片文件的完整路径
            image_path = os.path.join(self.clipboard_manager.images_dir, filename)
            print(f"[{timestamp}] 后端调试: 图片目录: {self.clipboard_manager.images_dir}")
            print(f"[{timestamp}] 后端调试: 完整路径: {image_path}")
            
            # 检查文件是否存在
            file_exists = os.path.exists(image_path)
            print(f"[{timestamp}] 后端调试: 文件是否存在: {file_exists}")
            
            if file_exists:
                # 读取图片文件并转换为Base64
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                    file_size = len(image_data)
                    print(f"[{timestamp}] 后端调试: 读取文件大小: {file_size} 字节")
                    
                    # 转换为Base64编码
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                    print(f"[{timestamp}] 后端调试: Base64编码完成，长度: {len(base64_data)} 字符")
                    
                    # 生成data URL格式
                    data_url = f"data:image/png;base64,{base64_data}"
                    print(f"[{timestamp}] 后端调试: 生成data URL成功")
                    
                    return json.dumps({
                        'success': True,
                        'data_url': data_url,
                        'message': '获取成功'
                    }, ensure_ascii=False)
            else:
                # 列出图片目录中的所有文件，帮助调试
                try:
                    if os.path.exists(self.clipboard_manager.images_dir):
                        files_in_dir = os.listdir(self.clipboard_manager.images_dir)
                        print(f"[{timestamp}] 后端调试: 图片目录中的文件: {files_in_dir}")
                    else:
                        print(f"[{timestamp}] 后端调试: 图片目录不存在")
                except Exception as list_error:
                    print(f"[{timestamp}] 后端调试: 列出目录文件失败: {list_error}")
                
                return json.dumps({
                    'success': False,
                    'data_url': '',
                    'message': '图片文件不存在'
                }, ensure_ascii=False)
        except Exception as e:
            import datetime
            timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
            print(f"[{timestamp}] 后端调试: 获取图片数据异常: {str(e)}")
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
    
    def log_debug(self, message: str) -> str:
        """
        记录调试信息到控制台
        
        Args:
            message: 调试信息
            
        Returns:
            str: JSON格式的操作结果
        """
        try:
            # 输出调试信息到控制台，带时间戳
            import datetime
            timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
            print(f"[{timestamp}] 前端调试: {message}")
            
            return json.dumps({
                'success': True,
                'message': '调试信息已记录'
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'记录调试信息失败: {str(e)}'
            }, ensure_ascii=False)