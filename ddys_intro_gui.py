#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZeroLossIntro GUI - 为视频文件自动添加片头（无损拼接）
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import sys
from pathlib import Path
from ddys_intro import (
    check_ffmpeg_available,
    get_video_info,
    make_intro_video,
    concat_videos,
    generate_output_path,
    find_ffmpeg_executable
)


class ZeroLossIntroGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ZeroLossIntro - 视频片头添加工具")
        self.root.geometry("600x560")  # 减少高度
        
        # 变量
        self.video_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.ffmpeg_path = tk.StringVar(value="ffmpeg")  # 默认值
        self.text_line1 = tk.StringVar(value="低端影视压制组")
        self.text_line2 = tk.StringVar(value="官网：DDYS.IO")
        self.duration = tk.DoubleVar(value=3.0)
        self.font_path = tk.StringVar()
        self.typewriter_effect = tk.BooleanVar(value=True)  # 默认启用打字机效果
        self.typewriter_speed = tk.DoubleVar(value=0.15)
        self.is_processing = False
        self.is_batch_mode = False  # 是否为批量模式
        self.selected_video_files = []  # 存储选中的多个视频文件
        
        self.create_widgets()
        self.check_ffmpeg()
    
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # FFmpeg 路径
        ttk.Label(main_frame, text="FFmpeg 路径:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ffmpeg_frame = ttk.Frame(main_frame)
        ffmpeg_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        ffmpeg_frame.columnconfigure(0, weight=1)
        ttk.Entry(ffmpeg_frame, textvariable=self.ffmpeg_path, width=40).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(ffmpeg_frame, text="浏览", command=self.browse_ffmpeg).grid(row=0, column=1, padx=(5, 0))
        row += 1
        
        # 分隔线
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # 视频文件选择（支持文件、多文件和目录）
        ttk.Label(main_frame, text="选择视频:").grid(row=row, column=0, sticky=tk.W, pady=5)
        video_frame = ttk.Frame(main_frame)
        video_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        video_frame.columnconfigure(0, weight=1)
        ttk.Entry(video_frame, textvariable=self.video_path, width=40, state="readonly").grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(video_frame, text="单个", command=self.browse_video).grid(row=0, column=1, padx=(5, 0))
        ttk.Button(video_frame, text="多个", command=self.browse_videos).grid(row=0, column=2, padx=(5, 0))
        ttk.Button(video_frame, text="目录", command=self.browse_video_dir).grid(row=0, column=3, padx=(5, 0))
        row += 1
        
        # 导出目录
        ttk.Label(main_frame, text="导出目录:").grid(row=row, column=0, sticky=tk.W, pady=5)
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        output_frame.columnconfigure(0, weight=1)
        ttk.Entry(output_frame, textvariable=self.output_dir, width=40, state="readonly").grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(output_frame, text="浏览", command=self.browse_output_dir).grid(row=0, column=1, padx=(5, 0))
        row += 1
        
        # 分隔线
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # 字幕文案
        ttk.Label(main_frame, text="字幕文案:").grid(row=row, column=0, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(main_frame, text="第一行:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.text_line1, width=50).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        row += 1
        
        ttk.Label(main_frame, text="第二行:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.text_line2, width=50).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        row += 1
        
        # 片头时长
        ttk.Label(main_frame, text="片头时长(秒):").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(main_frame, from_=1.0, to=10.0, increment=0.5, textvariable=self.duration, width=10).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # 打字机效果
        ttk.Checkbutton(main_frame, text="启用打字机效果（逐字显示）", 
                       variable=self.typewriter_effect).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(main_frame, text="打字速度(秒/字):").grid(row=row, column=0, sticky=tk.W, pady=2)
        speed_frame = ttk.Frame(main_frame)
        speed_frame.grid(row=row, column=1, sticky=tk.W, pady=2)
        ttk.Spinbox(speed_frame, from_=0.05, to=0.5, increment=0.05, 
                   textvariable=self.typewriter_speed, width=10).grid(row=0, column=0)
        ttk.Label(speed_frame, text="(建议: 0.1-0.2)", foreground="gray").grid(row=0, column=1, padx=(5, 0))
        row += 1
        
        # 字体文件（可选）
        ttk.Label(main_frame, text="字体文件(可选):").grid(row=row, column=0, sticky=tk.W, pady=5)
        font_frame = ttk.Frame(main_frame)
        font_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        font_frame.columnconfigure(0, weight=1)
        ttk.Entry(font_frame, textvariable=self.font_path, width=40, state="readonly").grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(font_frame, text="浏览", command=self.browse_font).grid(row=0, column=1, padx=(5, 0))
        ttk.Button(font_frame, text="预览", command=self.preview_font).grid(row=0, column=2, padx=(5, 0))
        ttk.Button(font_frame, text="清除", command=self.clear_font).grid(row=0, column=3, padx=(5, 0))
        row += 1
        
        # 分隔线
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # 进度条
        self.progress_var = tk.StringVar(value="就绪")
        ttk.Label(main_frame, text="状态:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.status_label = ttk.Label(main_frame, textvariable=self.progress_var, foreground="blue")
        self.status_label.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate', maximum=100)
        self.progress_bar.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        self.process_button = ttk.Button(button_frame, text="开始处理", command=self.start_processing, width=20)
        self.process_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="退出", command=self.root.quit, width=20).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # 版权信息（动态年份）
        import datetime
        current_year = datetime.datetime.now().year
        copyright_frame = ttk.Frame(main_frame)
        copyright_frame.grid(row=row, column=0, columnspan=2, pady=(5, 2))  # 减少底部空白
        ttk.Label(copyright_frame, text=f"© {current_year} DDYS.IO", foreground="gray", font=("Arial", 8)).pack()
    
    def check_ffmpeg(self):
        """检查 FFmpeg 是否可用"""
        ffmpeg_path = self.ffmpeg_path.get().strip()
        if not ffmpeg_path:
            ffmpeg_path = "ffmpeg"
        
        available, error_msg = check_ffmpeg_available(ffmpeg_path)
        if not available:
            self.progress_var.set(f"FFmpeg 未找到: {error_msg}")
            self.status_label.config(foreground="red")
        else:
            self.progress_var.set("就绪")
            self.status_label.config(foreground="blue")
    
    def browse_ffmpeg(self):
        """浏览 FFmpeg 目录"""
        path = filedialog.askdirectory(title="选择 FFmpeg 目录")
        if path:
            self.ffmpeg_path.set(path)
            self.check_ffmpeg()
    
    def browse_video(self):
        """浏览单个视频文件"""
        path = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=[
                ("视频文件", "*.mp4 *.mkv *.avi *.mov *.flv *.wmv *.m4v"),
                ("所有文件", "*.*")
            ]
        )
        if path:
            self.video_path.set(path)
            self.is_batch_mode = False
            self.selected_video_files = []
            # 自动设置导出目录为视频文件所在目录
            if not self.output_dir.get():
                self.output_dir.set(str(Path(path).parent))
    
    def browse_videos(self):
        """浏览多个视频文件（批量处理）"""
        paths = filedialog.askopenfilenames(
            title="选择多个视频文件（批量处理）",
            filetypes=[
                ("视频文件", "*.mp4 *.mkv *.avi *.mov *.flv *.wmv *.m4v"),
                ("所有文件", "*.*")
            ]
        )
        if paths:
            self.selected_video_files = [Path(p) for p in paths]
            # 显示文件数量
            if len(paths) == 1:
                self.video_path.set(paths[0])
            else:
                self.video_path.set(f"已选择 {len(paths)} 个文件")
            self.is_batch_mode = True
            # 自动设置导出目录为第一个文件所在目录
            if not self.output_dir.get() and paths:
                self.output_dir.set(str(Path(paths[0]).parent))
    
    def browse_video_dir(self):
        """浏览视频目录（批量处理）"""
        path = filedialog.askdirectory(title="选择视频目录（批量处理）")
        if path:
            self.video_path.set(path)
            self.is_batch_mode = True
            self.selected_video_files = []
            # 自动设置导出目录为视频目录
            if not self.output_dir.get():
                self.output_dir.set(path)
    
    def browse_output_dir(self):
        """浏览导出目录"""
        path = filedialog.askdirectory(title="选择导出目录")
        if path:
            self.output_dir.set(path)
    
    def browse_font(self):
        """浏览字体文件"""
        path = filedialog.askopenfilename(
            title="选择字体文件",
            filetypes=[
                ("字体文件", "*.ttf *.otf *.ttc"),
                ("所有文件", "*.*")
            ]
        )
        if path:
            self.font_path.set(path)
    
    def clear_font(self):
        """清除字体文件选择"""
        self.font_path.set("")
    
    def preview_font(self):
        """预览字体样式"""
        font_path = self.font_path.get().strip()
        if not font_path:
            messagebox.showinfo("提示", "请先选择字体文件")
            return
        
        if not Path(font_path).exists():
            messagebox.showerror("错误", "字体文件不存在")
            return
        
        # 创建预览窗口
        preview_window = tk.Toplevel(self.root)
        preview_window.title("字体预览")
        preview_window.geometry("500x300")
        
        # 预览文字
        text_line1 = self.text_line1.get().strip() or "低端影视压制组"
        text_line2 = self.text_line2.get().strip() or "官网：DDYS.IO"
        
        # 创建预览画布
        canvas = tk.Canvas(preview_window, bg="black", width=500, height=300)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        try:
            # 计算字体大小
            font_size = 60
            from PIL import Image, ImageDraw, ImageFont
            
            # 创建图像
            img = Image.new('RGB', (500, 300), color='black')
            draw = ImageDraw.Draw(img)
            
            # 加载字体
            try:
                font = ImageFont.truetype(font_path, font_size)
            except:
                font = ImageFont.load_default()
            
            # 绘制文字
            text1 = text_line1
            text2 = text_line2
            
            # 计算文字位置（居中）
            bbox1 = draw.textbbox((0, 0), text1, font=font)
            text1_width = bbox1[2] - bbox1[0]
            text1_height = bbox1[3] - bbox1[1]
            
            bbox2 = draw.textbbox((0, 0), text2, font=font)
            text2_width = bbox2[2] - bbox2[0]
            text2_height = bbox2[3] - bbox2[1]
            
            line_spacing = int(font_size * 1.5)
            total_height = text1_height + line_spacing + text2_height
            
            y1 = (300 - total_height) // 2
            y2 = y1 + text1_height + line_spacing
            
            x1 = (500 - text1_width) // 2
            x2 = (500 - text2_width) // 2
            
            draw.text((x1, y1), text1, fill='white', font=font)
            draw.text((x2, y2), text2, fill='white', font=font)
            
            # 转换为 PhotoImage 并显示
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(img)
            canvas.create_image(250, 150, image=photo)
            canvas.image = photo  # 保持引用
            
        except ImportError:
            # 如果没有 PIL，使用 tkinter 字体
            canvas.create_text(250, 120, text=text_line1, fill="white", 
                             font=("Arial", 24), anchor="center")
            canvas.create_text(250, 180, text=text_line2, fill="white", 
                             font=("Arial", 24), anchor="center")
            messagebox.showinfo("提示", "安装 Pillow 库可获得更好的预览效果\npip install Pillow")
        except Exception as e:
            messagebox.showerror("错误", f"预览失败: {str(e)}")
    
    def start_processing(self):
        """开始处理"""
        if self.is_processing:
            messagebox.showwarning("警告", "正在处理中，请稍候...")
            return
        
        # 验证输入
        if not self.video_path.get():
            messagebox.showerror("错误", "请选择视频文件或目录")
            return
        
        if not self.output_dir.get():
            messagebox.showerror("错误", "请选择导出目录")
            return
        
        if not self.text_line1.get().strip() and not self.text_line2.get().strip():
            messagebox.showerror("错误", "请输入至少一行字幕文案")
            return
        
        # 检查是否为批量模式
        if self.selected_video_files:
            # 多文件选择模式
            self.is_batch_mode = True
            if len(self.selected_video_files) == 0:
                messagebox.showerror("错误", "未选择任何视频文件")
                return
        else:
            video_path = Path(self.video_path.get())
            if video_path.is_dir():
                # 目录模式
                self.is_batch_mode = True
                # 查找目录中的视频文件
                video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.m4v']
                video_files = [f for f in video_path.iterdir() 
                              if f.is_file() and f.suffix.lower() in video_extensions]
                if not video_files:
                    messagebox.showerror("错误", "所选目录中没有找到视频文件")
                    return
            else:
                # 单文件模式
                self.is_batch_mode = False
        
        # 在新线程中处理
        self.is_processing = True
        self.process_button.config(state="disabled")
        self.progress_bar['value'] = 0
        self.progress_var.set("正在处理...")
        self.status_label.config(foreground="blue")
        
        thread = threading.Thread(target=self.process_video, daemon=True)
        thread.start()
    
    def process_video(self):
        """处理视频（在后台线程中运行）"""
        try:
            # 获取参数
            video_path = Path(self.video_path.get())
            output_dir = Path(self.output_dir.get())
            ffmpeg_path = self.ffmpeg_path.get().strip() or "ffmpeg"
            text_line1 = self.text_line1.get().strip()
            text_line2 = self.text_line2.get().strip()
            duration = self.duration.get()
            font_path = self.font_path.get().strip() or None
            
            # 组合文字
            if text_line1 and text_line2:
                text = f"{text_line1}\n{text_line2}"
            elif text_line1:
                text = text_line1
            elif text_line2:
                text = text_line2
            else:
                text = "低端影视压制组\n官网：DDYS.IO"
            
            # 检查 FFmpeg
            self.update_status("检查 FFmpeg...")
            available, error_msg = check_ffmpeg_available(ffmpeg_path)
            if not available:
                raise Exception(f"FFmpeg 未找到: {error_msg}")
            
            # 确定要处理的视频文件列表
            if self.selected_video_files:
                # 多文件选择模式
                video_files = self.selected_video_files
                video_files.sort()  # 按文件名排序
            elif self.is_batch_mode and video_path.is_dir():
                # 目录模式：处理目录中的所有视频
                video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.m4v']
                video_files = [f for f in video_path.iterdir() 
                              if f.is_file() and f.suffix.lower() in video_extensions]
                video_files.sort()  # 按文件名排序
            else:
                # 单文件模式
                video_files = [video_path]
            
            # 处理每个视频
            total_files = len(video_files)
            processed = 0
            failed = []
            
            for idx, current_video_path in enumerate(video_files, 1):
                try:
                    self.update_status(f"处理文件 {idx}/{total_files}: {current_video_path.name}")
                    
                    # 读取视频信息
                    video_info = get_video_info(current_video_path, ffmpeg_path)
                    
                    # 生成输出路径（会自动处理重复文件名）
                    output_path = generate_output_path(current_video_path, output_dir)
                    
                    # 创建临时目录
                    import tempfile
                    temp_dir = Path(tempfile.mkdtemp())
                    intro_path = temp_dir / f"intro_temp_{current_video_path.stem}.mp4"
                    
                    try:
                        # 生成片头
                        # 使用默认参数捕获 idx 和 total_files 的值，避免闭包问题
                        def make_progress_callback(file_idx, total):
                            return lambda p, m: self.update_progress(
                                int((file_idx - 1) * 100 / total + p / total),
                                f"[{file_idx}/{total}] {m}"
                            )
                        
                        make_intro_video(
                            intro_path,
                            video_info,
                            text,
                            duration,
                            font_path,
                            ffmpeg_path,
                            temp_dir,
                            progress_callback=make_progress_callback(idx, total_files),
                            typewriter_effect=self.typewriter_effect.get(),
                            typewriter_speed=self.typewriter_speed.get()
                        )
                        
                        # 计算实际片头时长（如果启用了打字机效果，时长会不同）
                        from ddys_intro import calculate_typewriter_duration
                        if self.typewriter_effect.get():
                            actual_intro_duration = calculate_typewriter_duration(
                                text, self.typewriter_speed.get(), duration
                            )
                            actual_intro_duration = max(actual_intro_duration, duration)
                        else:
                            actual_intro_duration = duration
                        
                        # 拼接视频
                        total_duration = video_info.get('duration')
                        if total_duration:
                            total_duration += actual_intro_duration  # 实际片头时长 + 原片时长
                        concat_videos(
                            intro_path, 
                            current_video_path, 
                            output_path, 
                            ffmpeg_path,
                            progress_callback=make_progress_callback(idx, total_files),
                            total_duration=total_duration
                        )
                        
                        # 清理临时文件
                        if intro_path.exists():
                            intro_path.unlink()
                        temp_dir.rmdir()
                        
                        processed += 1
                        
                    except Exception as e:
                        # 清理临时文件
                        if intro_path.exists():
                            intro_path.unlink()
                        if temp_dir.exists():
                            try:
                                temp_dir.rmdir()
                            except:
                                pass
                        raise e
                        
                except Exception as e:
                    failed.append((current_video_path.name, str(e)))
                    continue
            
            # 完成
            if failed:
                failed_msg = "\n".join([f"{name}: {error}" for name, error in failed[:5]])
                if len(failed) > 5:
                    failed_msg += f"\n... 还有 {len(failed) - 5} 个文件失败"
                self.update_status(f"完成！成功: {processed}/{total_files}, 失败: {len(failed)}")
                self.root.after(0, lambda: messagebox.showwarning(
                    "处理完成（部分失败）",
                    f"成功处理: {processed}/{total_files} 个文件\n\n失败的文件:\n{failed_msg}"
                ))
            else:
                self.update_status("完成！")
                self.root.after(0, lambda: messagebox.showinfo(
                    "完成",
                    f"成功处理 {processed} 个文件！\n输出目录: {output_dir}"
                ))
                
        except Exception as e:
            self.update_status(f"错误: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"处理失败:\n{str(e)}"))
        
        finally:
            self.is_processing = False
            self.root.after(0, self.processing_done)
    
    def update_status(self, message):
        """更新状态（线程安全）"""
        self.root.after(0, lambda: self.progress_var.set(message))
    
    def update_progress(self, progress, message=""):
        """更新进度条（线程安全）"""
        def _update():
            self.progress_bar['value'] = progress
            if message:
                self.progress_var.set(f"{message} ({progress}%)")
        self.root.after(0, _update)
    
    def processing_done(self):
        """处理完成后的UI更新"""
        self.process_button.config(state="normal")
        self.progress_bar['value'] = 100
        if "完成" in self.progress_var.get() or "错误" not in self.progress_var.get():
            self.status_label.config(foreground="green")
        else:
            self.status_label.config(foreground="red")


def main():
    root = tk.Tk()
    app = ZeroLossIntroGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()

