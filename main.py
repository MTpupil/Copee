#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
现代化剪贴板工具 - 主程序
现代化剪贴板管理器
支持Win+Z全局快捷键调用

作者: MTpupil
创建时间: 2025
"""

import webview
import threading
import time
import json

import win32gui
import win32con
import win32api
import win32process
import win32clipboard
import sys
import pystray
from PIL import Image, ImageDraw

from clipboard_manager import ClipboardManager
from api import ClipboardAPI



class ModernClipboardApp:
    """
    现代化剪贴板应用主类
    Win+Z快捷键调用模式
    """
    
    def __init__(self):
        """
        初始化应用
        """
        # 初始化组件
        self.clipboard_manager = ClipboardManager()
        self.api = ClipboardAPI(self.clipboard_manager, self.hide_window)
        self.window = None
        self.is_window_visible = False
        self.window_hwnd = None
        self.tray_icon = None
        self.running = True
        self.previous_focus_hwnd = None  # 保存之前获得焦点的窗口
        
        # 快捷键相关
        self.hotkey_listener = None  # 快捷键监听器
        

    

    

    
    def update_tray_menu(self):
        """
        更新托盘菜单
        """
        if self.tray_icon:
            # 重新创建菜单（移除系统剪贴板历史相关选项）
            menu = pystray.Menu(
                pystray.MenuItem("显示剪贴板", self.show_window_from_tray),
                pystray.MenuItem("关于", self.show_about),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", self.quit_application)
            )
            
            # 更新托盘图标菜单
            self.tray_icon.menu = menu

    def create_tray_icon(self):
        """
        创建系统托盘图标
        """
        # 创建一个简单的剪贴板图标
        def create_icon_image():
            # 创建32x32的图标
            image = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # 绘制剪贴板图标
            # 外框
            draw.rectangle([4, 2, 28, 30], outline='#667eea', width=2, fill='white')
            # 夹子
            draw.rectangle([10, 0, 22, 6], outline='#667eea', width=2, fill='#667eea')
            # 内容线条
            draw.line([8, 10, 24, 10], fill='#333', width=1)
            draw.line([8, 14, 24, 14], fill='#333', width=1)
            draw.line([8, 18, 20, 18], fill='#333', width=1)
            
            return image
        
        # 创建托盘菜单（移除系统剪贴板历史相关选项）
        menu = pystray.Menu(
            pystray.MenuItem("显示剪贴板", self.show_window_from_tray),
            pystray.MenuItem("关于", self.show_about),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self.quit_application)
        )
        
        # 创建托盘图标
        self.tray_icon = pystray.Icon(
            "Copee",
            create_icon_image(),
            "win+Z 调用",
            menu
        )
        
    def show_window_from_tray(self, icon=None, item=None):
        """
        从托盘图标显示窗口
        """
        # 从托盘图标显示窗口
        self.show_window()
        
    def show_about(self, icon=None, item=None):
        """
        显示关于信息
        使用线程避免阻塞主线程
        """
        def show_about_dialog():
            try:
                import tkinter as tk
                from tkinter import messagebox
                
                # 创建一个隐藏的根窗口
                root = tk.Tk()
                root.withdraw()
                
                # 设置窗口属性确保可以正常关闭
                root.attributes('-topmost', True)
                root.focus_force()
                
                messagebox.showinfo(
                    "关于Copee",
                    "Copee v1.0.0\n\n"
                    "一个现代化的剪贴板管理器\n"
                    "现代化剪贴板管理器\n\n"
                    "使用方法：\n"
                    "• Win+Z：显示剪贴板历史\n"
                    "• 点击项目：复制到剪贴板\n"
                    "• Escape：隐藏窗口\n\n"
                    "作者: MTpupil"
                )
                
                # 确保根窗口被正确销毁
                root.quit()
                root.destroy()
                
            except Exception as e:
                pass  # 静默处理关于对话框错误
        
        # 在新线程中显示对话框，避免阻塞主线程
        about_thread = threading.Thread(target=show_about_dialog, daemon=True)
        about_thread.start()
        
    def quit_application(self, icon=None, item=None):
        """
        退出应用程序
        """
        self.running = False
        
        # 清理所有快捷键
        self.cleanup_hotkeys()
        
        # 快速退出逻辑
        try:
            if self.tray_icon:
                self.tray_icon.stop()
        except:
            pass
        
        try:
            if self.window:
                self.window.hide()
        except:
            pass
        
        import os
        os._exit(0)
        
    def create_window(self):
        """
        创建主窗口 - 无边框，类似系统剪贴板窗口，初始隐藏
        """
        # 创建webview窗口
        self.window = webview.create_window(
            title='',                 # 无标题
            url='ui/index.html',      # HTML界面文件
            js_api=self.api,          # JavaScript API接口
            width=350,                # 窗口宽度（类似系统剪贴板）
            height=450,               # 窗口高度
            min_size=(350, 300),      # 最小尺寸
            resizable=False,          # 不可调整大小
            shadow=True,              # 窗口阴影
            on_top=True,              # 置顶显示
            transparent=True,         # 支持透明
            frameless=True,           # 无边框
            hidden=True,              # 初始隐藏窗口
        )
        

    
    def setup_global_hotkey(self):
        """
        设置全局快捷键 Win+Z
        """
        def show_clipboard_window():
            """
            显示剪贴板窗口的回调函数
            """
            if self.is_window_visible:
                self.hide_window()
            else:
                self.show_window()
        
        # 清理之前的快捷键
        self.cleanup_hotkeys()
        
        # 使用简单的快捷键注册
        try:
            import keyboard
            keyboard.add_hotkey('win+z', show_clipboard_window)
        except Exception as e:
            pass
    
    def cleanup_hotkeys(self):
        """
        清理所有快捷键
        """
        try:
            import keyboard
            keyboard.clear_all_hotkeys()
        except Exception as e:
            pass
    

    
    def get_cursor_position(self):
        """
        获取当前鼠标光标位置
        
        Returns:
            tuple: (x, y) 坐标
        """
        import win32api
        return win32api.GetCursorPos()
    
    def show_window(self):
        """
        在光标位置显示窗口
        """
        
        # 尝试显示窗口
        if not self.window:
            # 错误: 窗口对象不存在
            return
            
        if not self.window_hwnd:
            # 错误: 窗口句柄不存在
            return
            
        try:
            # 保存当前获得焦点的窗口
            try:
                self.previous_focus_hwnd = win32gui.GetForegroundWindow()
                # 保存之前的焦点窗口
            except Exception as e:
                pass  # 静默处理焦点窗口保存错误
                self.previous_focus_hwnd = None
            
            # 获取光标位置
            cursor_x, cursor_y = self.get_cursor_position()
            # 获取屏幕尺寸
            screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            
            # 计算窗口位置，确保不超出屏幕边界
            window_width = 350
            window_height = 450
            
            # 调整X坐标
            if cursor_x + window_width > screen_width:
                x = screen_width - window_width - 10
            else:
                x = cursor_x
                
            # 调整Y坐标
            if cursor_y + window_height > screen_height:
                y = cursor_y - window_height - 10
            else:
                y = cursor_y + 10
                
            x = max(0, x)
            y = max(0, y)
            
            win32gui.ShowWindow(self.window_hwnd, win32con.SW_SHOWNOACTIVATE)
            
            win32gui.SetWindowPos(
                self.window_hwnd, 
                win32con.HWND_TOPMOST,
                x, y, 0, 0, 
                win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
            )
            
            self.is_window_visible = True
            
            try:
                self.window.evaluate_js('updateClipboardList()')
            except Exception as js_error:
                pass
                
        except Exception as e:
            pass
    
    def hide_window(self):
        """
        隐藏窗口
        """
        try:
            if self.window_hwnd:
                win32gui.ShowWindow(self.window_hwnd, win32con.SW_HIDE)
                self.is_window_visible = False
                
                # 恢复之前获得焦点的窗口
                if self.previous_focus_hwnd:
                    try:
                        # 检查之前的窗口是否仍然存在
                        if win32gui.IsWindow(self.previous_focus_hwnd):
                            win32gui.SetForegroundWindow(self.previous_focus_hwnd)
                    except Exception as e:
                        pass  # 静默处理焦点恢复错误
                    finally:
                        self.previous_focus_hwnd = None
                        

        except Exception as e:
            pass  # 静默处理窗口隐藏错误
    
    def setup_window_events(self):
        """
        设置窗口事件处理
        """
        def on_window_loaded():
            """
            窗口加载完成后的回调
            """
            # 获取窗口句柄
            try:
                import time
                time.sleep(1.0)  # 等待窗口完全加载
                
                # 使用更精确的方法查找webview窗口
                def find_webview_window():
                    webview_hwnd = None
                    
                    def enum_callback(hwnd, param):
                        nonlocal webview_hwnd
                        # 检查窗口类名是否包含webview相关信息
                        class_name = win32gui.GetClassName(hwnd)
                        window_text = win32gui.GetWindowText(hwnd)
                        
                        # 查找Chrome/Edge WebView窗口或无标题的顶级窗口
                        if ('Chrome' in class_name or 'WebView' in class_name or 
                            class_name == 'Chrome_WidgetWin_1' or 
                            (window_text == '' and win32gui.GetParent(hwnd) == 0)):
                            # 检查窗口是否属于当前进程
                            _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                            current_pid = win32api.GetCurrentProcessId()
                            if window_pid == current_pid:
                                webview_hwnd = hwnd
                                return False  # 停止枚举
                        return True
                    
                    win32gui.EnumWindows(enum_callback, None)
                    return webview_hwnd
                
                self.window_hwnd = find_webview_window()
                
                if self.window_hwnd:
                    ex_style = win32gui.GetWindowLong(self.window_hwnd, win32con.GWL_EXSTYLE)
                    ex_style |= win32con.WS_EX_TOOLWINDOW
                    ex_style &= ~win32con.WS_EX_APPWINDOW
                    ex_style &= ~win32con.WS_EX_TRANSPARENT
                    ex_style &= ~win32con.WS_EX_LAYERED
                    win32gui.SetWindowLong(self.window_hwnd, win32con.GWL_EXSTYLE, ex_style)
                    
                    style = win32gui.GetWindowLong(self.window_hwnd, win32con.GWL_STYLE)
                    style |= win32con.WS_VISIBLE
                    win32gui.SetWindowLong(self.window_hwnd, win32con.GWL_STYLE, style)
                    
                    win32gui.ShowWindow(self.window_hwnd, win32con.SW_HIDE)
                    self.is_window_visible = False
            except Exception as e:
                pass
        
        # 窗口加载完成后执行
        if self.window:
            threading.Timer(1.0, on_window_loaded).start()
    
    def start_clipboard_monitor(self):
        """
        启动剪贴板监控线程
        """
        def monitor_thread():
            """
            剪贴板监控线程函数
            """
            while self.running:
                try:
                    if self.clipboard_manager.check_clipboard_change():
                        if self.window and self.is_window_visible:
                            self.window.evaluate_js('updateClipboardList()')
                    time.sleep(0.5)
                except Exception as e:
                    pass
                    time.sleep(1)
        
        # 启动监控线程
        monitor = threading.Thread(target=monitor_thread, daemon=True)
        monitor.start()
    

    
    def start_click_monitor(self):
        """
        启动鼠标点击监控，点击窗口外部时隐藏窗口
        """
        def on_click(x, y, button, pressed):
            """
            鼠标点击事件处理
            """
            if pressed and self.is_window_visible and self.window_hwnd:
                try:
                    # 获取点击位置的窗口句柄
                    clicked_hwnd = win32gui.WindowFromPoint((x, y))
                    
                    # 检查点击的窗口是否是我们的窗口或其子窗口
                    is_our_window = False
                    current_hwnd = clicked_hwnd
                    
                    # 向上遍历窗口层次结构，检查是否属于我们的窗口
                    while current_hwnd:
                        if current_hwnd == self.window_hwnd:
                            is_our_window = True
                            break
                        current_hwnd = win32gui.GetParent(current_hwnd)
                    
                    if not is_our_window:
                        self.hide_window()
                        
                except Exception as e:
                    pass
        
        # 启动鼠标监听
        try:
            from pynput import mouse
            self.mouse_listener = mouse.Listener(on_click=on_click)
            self.mouse_listener.daemon = True
            self.mouse_listener.start()
            # 鼠标点击监听已启动
        except ImportError:
            # 警告: 未安装pynput库，无法监听鼠标点击事件
            # 请运行: pip install pynput
            pass
        except Exception as e:
            pass  # 静默处理鼠标监听启动错误
        
    def run(self):
        """
        运行应用
        """
        try:
            # 创建系统托盘图标
            self.create_tray_icon()
            
            # 创建窗口
            self.create_window()
            
            # 设置窗口事件
            self.setup_window_events()
            
            # 启动剪贴板监控
            self.start_clipboard_monitor()
            
            # 启动鼠标点击监控
            self.start_click_monitor()
            
            # 设置全局快捷键Win+Z
            self.setup_global_hotkey()
            
            # 启动系统托盘
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
            
            # 短暂等待确保所有组件初始化完成
            time.sleep(0.5)
            
            # 启动webview界面
            webview.start(debug=False)
            
        except KeyboardInterrupt:
            self.quit_application()
        except Exception as e:
            pass
            self.quit_application()

def main():
    """
    主函数
    """
    app = ModernClipboardApp()
    app.run()

if __name__ == '__main__':
    main()