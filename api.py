#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API接口模块
提供前端JavaScript调用的API接口
"""

import json
import time
import re
import os
import sys
import winreg
from datetime import datetime, timedelta
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
            
    def search_items(self, keyword: str, search_type: str = 'normal', time_filter: str = None) -> str:
        """
        搜索剪贴板项目（支持普通搜索、正则表达式搜索和时间筛选）
        
        Args:
            keyword: 搜索关键词
            search_type: 搜索类型 ('normal', 'regex')
            time_filter: 时间筛选 ('today', 'yesterday', 'week', 'month', None)
            
        Returns:
            str: JSON格式的搜索结果
        """
        try:
            all_items = self.clipboard_manager.get_items()
            
            # 首先根据时间筛选
            if time_filter:
                all_items = self._filter_by_time(all_items, time_filter)
            
            # 如果没有关键词，直接返回时间筛选结果
            if not keyword.strip():
                return json.dumps({
                    'success': True,
                    'data': all_items,
                    'message': f'找到 {len(all_items)} 个匹配项目'
                }, ensure_ascii=False)
            
            # 根据搜索类型进行内容筛选
            filtered_items = []
            
            if search_type == 'regex':
                # 正则表达式搜索
                try:
                    pattern = re.compile(keyword, re.IGNORECASE)
                    for item in all_items:
                        if self._regex_match_item(item, pattern):
                            filtered_items.append(item)
                except re.error as regex_error:
                    return json.dumps({
                        'success': False,
                        'data': [],
                        'message': f'正则表达式错误: {str(regex_error)}'
                    }, ensure_ascii=False)
            else:
                # 普通搜索
                for item in all_items:
                    if self._normal_match_item(item, keyword):
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
    
    def _filter_by_time(self, items: List[Dict], time_filter: str) -> List[Dict]:
        """
        根据时间筛选项目
        
        Args:
            items: 项目列表
            time_filter: 时间筛选类型
            
        Returns:
            List[Dict]: 筛选后的项目列表
        """
        now = datetime.now()
        filtered_items = []
        
        for item in items:
            try:
                # 解析项目时间戳
                item_time = datetime.fromisoformat(item['timestamp'])
                
                if time_filter == 'today':
                    # 今天
                    if item_time.date() == now.date():
                        filtered_items.append(item)
                elif time_filter == 'yesterday':
                    # 昨天
                    yesterday = now - timedelta(days=1)
                    if item_time.date() == yesterday.date():
                        filtered_items.append(item)
                elif time_filter == 'week':
                    # 最近一周
                    week_ago = now - timedelta(days=7)
                    if item_time >= week_ago:
                        filtered_items.append(item)
                elif time_filter == 'month':
                    # 最近一个月
                    month_ago = now - timedelta(days=30)
                    if item_time >= month_ago:
                        filtered_items.append(item)
            except (ValueError, KeyError):
                # 如果时间戳解析失败，跳过该项目
                continue
                
        return filtered_items
    
    def _normal_match_item(self, item: Dict, keyword: str) -> bool:
        """
        普通搜索匹配项目
        
        Args:
            item: 项目数据
            keyword: 搜索关键词
            
        Returns:
            bool: 是否匹配
        """
        keyword_lower = keyword.lower()
        
        # 首先检查备注内容
        note = item.get('note', '')
        if note and keyword_lower in note.lower():
            return True
        
        if item['type'] == 'text':
            # 文本项目：搜索实际内容
            return keyword_lower in item['content'].lower()
        elif item['type'] == 'image':
            # 图片项目：搜索预览文本
            return keyword_lower in item['preview'].lower()
        elif item['type'] == 'file':
            # 文件项目：搜索文件名
            return keyword_lower in item['content'].lower()
        
        return False
    
    def _regex_match_item(self, item: Dict, pattern: re.Pattern) -> bool:
        """
        正则表达式匹配项目
        
        Args:
            item: 项目数据
            pattern: 编译后的正则表达式模式
            
        Returns:
            bool: 是否匹配
        """
        # 首先检查备注内容
        note = item.get('note', '')
        if note and pattern.search(note):
            return True
        
        if item['type'] == 'text':
            # 文本项目：在实际内容中搜索
            return bool(pattern.search(item['content']))
        elif item['type'] == 'image':
            # 图片项目：在预览文本中搜索
            return bool(pattern.search(item['preview']))
        elif item['type'] == 'file':
            # 文件项目：在文件名中搜索
            return bool(pattern.search(item['content']))
        
        return False
            
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
    
    def get_settings(self) -> str:
        """
        获取应用设置
        
        Returns:
            str: JSON格式的设置数据
        """
        try:
            settings = self.clipboard_manager.get_settings()
            return json.dumps({
                'success': True,
                'data': settings,
                'message': '获取设置成功'
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'获取设置失败: {str(e)}'
            }, ensure_ascii=False)
    
    def save_settings(self, settings_data: str) -> str:
        """
        保存应用设置
        
        Args:
            settings_data: JSON格式的设置数据
        
        Returns:
            str: JSON格式的响应
        """
        try:
            settings = json.loads(settings_data)
            self.clipboard_manager.save_settings(settings)
            return json.dumps({
                'success': True,
                'message': '设置保存成功'
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'保存设置失败: {str(e)}'
            }, ensure_ascii=False)
    
    def update_item_note(self, index: int, note: str) -> str:
        """
        更新剪贴板项目的备注
        
        Args:
            index: 项目索引
            note: 备注内容
        
        Returns:
            str: JSON格式的操作结果
        """
        try:
            if 0 <= index < len(self.clipboard_manager.items):
                # 更新备注
                self.clipboard_manager.items[index].note = note
                # 保存数据
                self.clipboard_manager._save_data()
                
                return json.dumps({
                    'success': True,
                    'message': '备注更新成功'
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    'success': False,
                    'message': '项目索引无效'
                }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'更新备注失败: {str(e)}'
            }, ensure_ascii=False)
    
    def set_auto_start(self, enabled: bool) -> str:
        """
        设置开机启动
        
        Args:
            enabled: 是否启用开机启动
        
        Returns:
            str: JSON格式的操作结果
        """
        try:
            # 获取当前程序的路径
            if getattr(sys, 'frozen', False):
                # 如果是打包后的exe文件
                app_path = sys.executable
            else:
                # 如果是Python脚本
                app_path = os.path.abspath(sys.argv[0])
            
            # 注册表路径
            reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            app_name = "Copee剪贴板管理器"
            
            if enabled:
                # 启用开机启动
                try:
                    # 打开注册表项
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE)
                    # 设置注册表值
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                    winreg.CloseKey(key)
                    
                    return json.dumps({
                        'success': True,
                        'message': '开机启动已启用'
                    }, ensure_ascii=False)
                except Exception as e:
                    return json.dumps({
                        'success': False,
                        'message': f'启用开机启动失败: {str(e)}'
                    }, ensure_ascii=False)
            else:
                # 禁用开机启动
                try:
                    # 打开注册表项
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE)
                    # 删除注册表值
                    try:
                        winreg.DeleteValue(key, app_name)
                    except FileNotFoundError:
                        # 如果注册表项不存在，也算成功
                        pass
                    winreg.CloseKey(key)
                    
                    return json.dumps({
                        'success': True,
                        'message': '开机启动已禁用'
                    }, ensure_ascii=False)
                except Exception as e:
                    return json.dumps({
                        'success': False,
                        'message': f'禁用开机启动失败: {str(e)}'
                    }, ensure_ascii=False)
                    
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'设置开机启动失败: {str(e)}'
            }, ensure_ascii=False)
    
    def get_auto_start_status(self) -> str:
        """
        获取开机启动状态
        
        Returns:
            str: JSON格式的开机启动状态
        """
        try:
            # 注册表路径
            reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            app_name = "Copee剪贴板管理器"
            
            try:
                # 打开注册表项
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_READ)
                # 尝试读取注册表值
                value, _ = winreg.QueryValueEx(key, app_name)
                winreg.CloseKey(key)
                
                # 如果能读取到值，说明开机启动已启用
                return json.dumps({
                    'success': True,
                    'enabled': True,
                    'message': '开机启动已启用'
                }, ensure_ascii=False)
            except FileNotFoundError:
                # 如果注册表项不存在，说明开机启动未启用
                return json.dumps({
                    'success': True,
                    'enabled': False,
                    'message': '开机启动未启用'
                }, ensure_ascii=False)
                
        except Exception as e:
            return json.dumps({
                'success': False,
                'enabled': False,
                'message': f'获取开机启动状态失败: {str(e)}'
            }, ensure_ascii=False)