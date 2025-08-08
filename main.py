#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
现代化剪贴板工具 - 主程序
替代Windows Win+V功能的现代化剪贴板管理器

作者: Assistant
创建时间: 2024
"""

import webview
import threading
import time
import json
from clipboard_manager import ClipboardManager
from api import ClipboardAPI

class ModernClipboardApp:
    """
    现代化剪贴板应用主类
    """
    
    def __init__(self):
        """
        初始化应用
        """
        self.clipboard_manager = ClipboardManager()
        self.api = ClipboardAPI(self.clipboard_manager)
        self.window = None
        
    def create_window(self):
        """
        创建主窗口
        """
        # 创建webview窗口，使用现代化样式
        self.window = webview.create_window(
            title='现代剪贴板工具',
            url='ui/index.html',  # HTML界面文件
            js_api=self.api,      # JavaScript API接口
            width=400,            # 窗口宽度
            height=600,           # 窗口高度
            min_size=(350, 500),  # 最小尺寸
            resizable=True,       # 可调整大小
            shadow=True,          # 窗口阴影
            on_top=False,         # 不置顶
            transparent=True,     # 支持透明
        )
        
    def start_clipboard_monitor(self):
        """
        启动剪贴板监控线程
        """
        def monitor_thread():
            """
            剪贴板监控线程函数
            """
            while True:
                try:
                    # 检查剪贴板变化
                    if self.clipboard_manager.check_clipboard_change():
                        # 通知前端更新
                        if self.window:
                            self.window.evaluate_js('updateClipboardList()')
                    time.sleep(0.5)  # 每0.5秒检查一次
                except Exception as e:
                    print(f"剪贴板监控错误: {e}")
                    time.sleep(1)
        
        # 启动监控线程
        monitor = threading.Thread(target=monitor_thread, daemon=True)
        monitor.start()
        
    def run(self):
        """
        运行应用
        """
        # 创建窗口
        self.create_window()
        
        # 启动剪贴板监控
        self.start_clipboard_monitor()
        
        # 启动webview
        webview.start(debug=False)  # 生产环境设为False

def main():
    """
    主函数
    """
    app = ModernClipboardApp()
    app.run()

if __name__ == '__main__':
    main()