#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copee剪贴板管理器 - 打包脚本
使用PyInstaller将Python程序打包成exe文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    """
    主打包函数
    """
    print("=== Copee剪贴板管理器 打包工具 ===")
    print("正在准备打包环境...")
    
    # 获取项目根目录
    project_root = Path(__file__).parent
    print(f"项目根目录: {project_root}")
    
    # 检查必要文件是否存在
    required_files = [
        'main.py',
        'api.py', 
        'clipboard_manager.py',
        'ui/index.html',
        'ui/script.js',
        'ui/styles.css',
        'ui/logo.jpg'
    ]
    
    print("\n检查必要文件...")
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            print(f"❌ 缺少必要文件: {file_path}")
            return False
        else:
            print(f"✅ {file_path}")
    
    # 检查PyInstaller是否已安装
    print("\n检查PyInstaller...")
    try:
        result = subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ PyInstaller版本: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller未安装，正在安装...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
            print("✅ PyInstaller安装成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ PyInstaller安装失败: {e}")
            return False
    
    # 创建输出目录
    dist_dir = project_root / 'dist'
    build_dir = project_root / 'build'
    
    print("\n清理旧的构建文件...")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("✅ 清理dist目录")
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("✅ 清理build目录")
    
    # 构建PyInstaller命令
    print("\n开始打包...")
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',  # 打包成单个exe文件
        '--windowed',  # 不显示控制台窗口
        '--name=Copee剪贴板管理器',  # 设置exe文件名
        '--add-data=ui;ui',  # 包含ui目录
        '--hidden-import=win32timezone',  # 隐式导入
        '--hidden-import=pystray._win32',  # 系统托盘相关
        '--hidden-import=PIL._tkinter_finder',  # PIL相关
        '--collect-submodules=pywebview',  # 收集pywebview子模块
        '--collect-submodules=webview',  # 收集webview子模块
        '--icon=ui/logo.jpg',  # 设置图标（如果支持的话）
        'main.py'  # 主程序文件
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        # 执行打包命令
        result = subprocess.run(cmd, cwd=project_root, check=True, 
                              capture_output=True, text=True)
        print("✅ 打包成功！")
        
        # 检查生成的exe文件
        exe_path = dist_dir / 'Copee剪贴板管理器.exe'
        if exe_path.exists():
            file_size = exe_path.stat().st_size / (1024 * 1024)  # 转换为MB
            print(f"\n📦 生成的exe文件:")
            print(f"   路径: {exe_path}")
            print(f"   大小: {file_size:.2f} MB")
            
            print("\n🎉 打包完成！")
            print("\n使用说明:")
            print("1. 可以直接运行生成的exe文件")
            print("2. 在设置页面中可以启用开机启动功能")
            print("3. 程序会在系统托盘中运行")
            print("4. 使用Ctrl+Shift+V快捷键打开剪贴板管理器")
            
            return True
        else:
            print("❌ 未找到生成的exe文件")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

if __name__ == '__main__':
    success = main()
    if not success:
        print("\n打包失败，请检查错误信息并重试。")
        sys.exit(1)
    else:
        print("\n按任意键退出...")
        input()