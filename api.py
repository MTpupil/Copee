#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API接口模块
提供前端JavaScript调用的API接口
"""

import json
from typing import List, Dict, Any
from clipboard_manager import ClipboardManager

class ClipboardAPI:
    """
    剪贴板API接口类
    提供给前端调用的方法
    """
    
    def __init__(self, clipboard_manager: ClipboardManager):
        """
        初始化API接口
        
        Args:
            clipboard_manager: 剪贴板管理器实例
        """
        self.clipboard_manager = clipboard_manager
        
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
        复制指定项目到剪贴板
        
        Args:
            index: 项目索引
            
        Returns:
            str: JSON格式的操作结果
        """
        try:
            success = self.clipboard_manager.copy_item_to_clipboard(index)
            return json.dumps({
                'success': success,
                'message': '复制成功' if success else '复制失败'
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'复制失败: {str(e)}'
            }, ensure_ascii=False)
            
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
                'name': '现代剪贴板工具',
                'version': '1.0.0',
                'description': '替代Windows Win+V的现代化剪贴板管理器',
                'author': 'Assistant'
            },
            'message': '获取成功'
        }, ensure_ascii=False)