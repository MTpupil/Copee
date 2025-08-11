@echo off
chcp 65001 >nul
echo =================================
echo    Copee剪贴板管理器 打包工具
echo =================================
echo.
echo 正在启动打包程序...
echo.

:: 运行Python打包脚本
python build.py

echo.
echo 打包完成！
pause