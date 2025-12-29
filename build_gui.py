#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZeroLossIntro GUI 打包脚本
使用 PyInstaller 打包成 Windows 可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    print("=" * 50)
    print("ZeroLossIntro GUI 打包脚本")
    print("=" * 50)
    print()
    
    # 检查 PyInstaller
    print("[1/4] 检查打包依赖...")
    try:
        import PyInstaller
        print("[OK] PyInstaller 已安装")
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "--quiet"], check=True)
        print("[OK] PyInstaller 安装完成")
    print()
    
    # 清理旧文件
    print("[2/4] 清理旧的打包文件...")
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"[OK] 已删除 {dir_name}/")
            except Exception as e:
                print(f"[WARNING] 无法删除 {dir_name}/: {e}")
                # 尝试继续，可能目录为空或不存在
    
    # 清理spec文件（但保留当前目录的）
    for spec_file in Path('.').glob('*.spec'):
        if spec_file.name != 'ZeroLossIntro.spec':  # 保留现有的spec文件
            try:
                spec_file.unlink()
                print(f"[OK] 已删除 {spec_file.name}")
            except Exception as e:
                print(f"[WARNING] 无法删除 {spec_file.name}: {e}")
    print()
    
    # 检查必要文件
    print("[3/4] 检查必要文件...")
    required_files = ['ddys_intro_gui.py', 'ddys_intro.py', 'font.ttf']
    for file in required_files:
        if not os.path.exists(file):
            print(f"[ERROR] 找不到文件 {file}")
            return 1
        print(f"[OK] {file}")
    print()
    
    # 打包
    print("[4/4] 正在打包 GUI 程序...")
    print("这可能需要几分钟，请稍候...")
    print()
    
    # Windows 路径分隔符使用分号
    import platform
    if platform.system() == 'Windows':
        data_sep = ';'
    else:
        data_sep = ':'
    
    # 使用 python -m PyInstaller 方式，更可靠
    cmd = [
        sys.executable,
        '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name', 'ZeroLossIntro',
        f'--add-data=font.ttf{data_sep}.',
        '--hidden-import=tkinter',
        'ddys_intro_gui.py'
    ]
    
    try:
        # 确保build和dist目录存在（PyInstaller会自动创建，但先创建更安全）
        os.makedirs('build', exist_ok=True)
        os.makedirs('dist', exist_ok=True)
        
        # 设置环境变量，确保使用UTF-8编码
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'
        
        # 运行打包命令，捕获输出以便调试
        print("正在执行打包命令...")
        result = subprocess.run(
            cmd, 
            check=False,  # 先不检查，手动处理错误
            env=env,
            encoding='utf-8',
            errors='replace',
            capture_output=False  # 直接显示输出
        )
        
        if result.returncode != 0:
            print()
            print("[ERROR] 打包失败")
            print(f"错误代码: {result.returncode}")
            return 1
        
        print()
        print("=" * 50)
        print("打包完成！")
        print("=" * 50)
        print()
        
        exe_path = Path('dist') / 'ZeroLossIntro.exe'
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"可执行文件: {exe_path}")
            print(f"文件大小: {size_mb:.2f} MB")
            print()
            print("[OK] 打包成功！")
        else:
            print("[ERROR] 找不到生成的可执行文件")
            print(f"请检查 dist 目录: {Path('dist').absolute()}")
            return 1
            
    except subprocess.CalledProcessError as e:
        print()
        print("[ERROR] 打包失败")
        print(f"错误代码: {e.returncode}")
        if e.stdout:
            print("标准输出:")
            print(e.stdout)
        if e.stderr:
            print("错误输出:")
            print(e.stderr)
        return 1
    except Exception as e:
        print()
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

