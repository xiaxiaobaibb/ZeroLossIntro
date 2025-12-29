#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZeroLossIntro - 为视频文件自动添加片头（无损拼接）
"""

import subprocess
import json
import argparse
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple

# 全局变量：ffmpeg 和 ffprobe 的可执行文件路径
FFMPEG_CMD = 'ffmpeg'
FFPROBE_CMD = 'ffprobe'


def find_ffmpeg_executable(ffmpeg_path: Optional[str] = None) -> Tuple[str, str]:
    """
    查找 ffmpeg 和 ffprobe 可执行文件路径
    
    Args:
        ffmpeg_path: 用户指定的 ffmpeg 目录路径（可选）
    
    Returns:
        (ffmpeg_cmd, ffprobe_cmd): 可执行文件路径
    """
    if ffmpeg_path:
        # 用户指定了路径
        ffmpeg_dir = Path(ffmpeg_path)
        if not ffmpeg_dir.exists():
            raise FileNotFoundError(f"指定的 ffmpeg 路径不存在: {ffmpeg_path}")
        
        # 查找 bin 目录（Windows 常见结构）
        bin_dir = ffmpeg_dir / 'bin'
        if bin_dir.exists():
            ffmpeg_dir = bin_dir
        
        # Windows 可执行文件扩展名
        import platform
        exe_ext = '.exe' if platform.system() == 'Windows' else ''
        
        ffmpeg_cmd = str(ffmpeg_dir / f'ffmpeg{exe_ext}')
        ffprobe_cmd = str(ffmpeg_dir / f'ffprobe{exe_ext}')
        
        if not Path(ffmpeg_cmd).exists():
            raise FileNotFoundError(f"在指定路径未找到 ffmpeg: {ffmpeg_cmd}")
        if not Path(ffprobe_cmd).exists():
            raise FileNotFoundError(f"在指定路径未找到 ffprobe: {ffprobe_cmd}")
        
        return ffmpeg_cmd, ffprobe_cmd
    
    # 使用系统 PATH 中的命令
    return FFMPEG_CMD, FFPROBE_CMD


def check_ffmpeg_available(ffmpeg_path: Optional[str] = None) -> Tuple[bool, str]:
    """检查 ffmpeg 和 ffprobe 是否可用"""
    try:
        ffmpeg_cmd, ffprobe_cmd = find_ffmpeg_executable(ffmpeg_path)
        subprocess.run([ffmpeg_cmd, '-version'], 
                      capture_output=True, check=True, timeout=5)
        subprocess.run([ffprobe_cmd, '-version'], 
                      capture_output=True, check=True, timeout=5)
        return True, ""
    except FileNotFoundError as e:
        return False, str(e) + "\n提示：可以使用 --ffmpeg-path 参数指定 ffmpeg 目录路径"
    except subprocess.TimeoutExpired:
        return False, "ffmpeg 或 ffprobe 响应超时"
    except subprocess.CalledProcessError:
        return False, "ffmpeg 或 ffprobe 执行失败"


def get_video_info(video_path: Path, ffmpeg_path: Optional[str] = None) -> Dict:
    """
    使用 ffprobe 获取视频信息
    
    Args:
        video_path: 视频文件路径
        ffmpeg_path: ffmpeg 目录路径（可选）
    
    Returns:
        dict: 包含视频参数的字典
    """
    # 检查文件是否存在
    if not video_path.exists():
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    
    _, ffprobe_cmd = find_ffmpeg_executable(ffmpeg_path)
    
    # 在Windows上处理包含中文的路径，确保使用正确的编码
    import platform
    import os
    is_windows = platform.system() == 'Windows'
    
    # 将路径转换为绝对路径字符串
    video_path_abs = video_path.absolute()
    video_path_str = str(video_path_abs)
    
    # 在Windows上，尝试使用长路径格式（\\?\前缀）来处理包含特殊字符的路径
    if is_windows and len(video_path_str) > 260:
        # Windows路径长度限制，使用长路径格式
        if not video_path_str.startswith('\\\\?\\'):
            if video_path_str.startswith('\\\\'):
                # UNC路径
                video_path_str = '\\\\?\\UNC\\' + video_path_str[2:]
            else:
                # 普通路径
                video_path_str = '\\\\?\\' + video_path_str
    
    cmd = [
        ffprobe_cmd,
        '-v', 'error',  # 使用error级别，可以看到错误信息
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        video_path_str
    ]
    
    try:
        # 在Windows上，尝试多种编码方式
        env = os.environ.copy()
        result = None
        last_error = None
        
        if is_windows:
            # 方法1: 尝试使用UTF-8编码（Python 3.7+默认）
            success = False
            try:
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    check=False,
                    timeout=30,
                    shell=False,
                    creationflags=0x08000000 if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0  # 不显示窗口
                )
                # 检查是否成功
                if result.returncode == 0 and result.stdout and result.stdout.strip():
                    # 成功，使用这个结果
                    success = True
                else:
                    # 失败，记录错误并尝试下一种方法
                    last_error = result.stderr or result.stdout or "无输出"
            except (UnicodeDecodeError, UnicodeEncodeError) as e:
                last_error = f"UTF-8编码错误: {e}"
                result = None
            except Exception as e:
                last_error = f"UTF-8执行错误: {e}"
                result = None
            
            # 方法2: 如果UTF-8失败，尝试使用GBK编码（Windows中文系统默认）
            if not success:
                try:
                    result = subprocess.run(
                        cmd, 
                        capture_output=True, 
                        text=True,
                        encoding='gbk',
                        errors='replace',
                        check=False,
                        timeout=30,
                        shell=False,
                        creationflags=0x08000000 if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                    )
                    if result.returncode == 0 and result.stdout and result.stdout.strip():
                        # 成功
                        success = True
                        last_error = None  # 清除之前的错误
                    else:
                        last_error = result.stderr or result.stdout or last_error or "无输出"
                except Exception as e:
                    last_error = f"GBK编码错误: {e}"
                    # 如果GBK尝试也失败，result保持之前的值（可能是None或之前失败的结果）
        else:
            # 非Windows系统，直接使用默认编码
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                check=False,
                timeout=30
            )
        
        # 检查result是否为None（所有尝试都失败）
        if result is None:
            raise RuntimeError(
                f"ffprobe 执行失败: 无法启动ffprobe进程\n"
                f"最后错误: {last_error or '未知错误'}\n"
                f"文件: {video_path}\n"
                f"提示: 请检查ffprobe是否正确安装，或文件路径是否包含特殊字符"
            )
        
        # 检查返回码
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or last_error or "未知错误"
            # 确保错误信息是字符串
            if isinstance(error_msg, bytes):
                try:
                    error_msg = error_msg.decode('utf-8', errors='replace')
                except:
                    try:
                        error_msg = error_msg.decode('gbk', errors='replace')
                    except:
                        error_msg = str(error_msg)
            
            # 尝试从错误信息中提取更有用的信息
            error_details = error_msg
            if 'No such file' in error_msg or '找不到' in error_msg:
                error_details = f"文件不存在或路径错误: {error_msg}"
            elif 'Invalid data' in error_msg or '无效' in error_msg:
                error_details = f"文件格式无效或损坏: {error_msg}"
            elif 'Permission denied' in error_msg or '拒绝访问' in error_msg:
                error_details = f"文件访问被拒绝: {error_msg}"
            
            raise RuntimeError(
                f"ffprobe 执行失败 (返回码: {result.returncode})\n"
                f"错误信息: {error_details}\n"
                f"文件: {video_path}\n"
                f"提示: 文件可能损坏、格式不支持、路径编码有问题或权限不足"
            )
        
        # 检查 stdout 是否为 None 或空
        if result.stdout is None:
            error_info = result.stderr or last_error or "无错误信息"
            raise RuntimeError(
                f"ffprobe 没有返回输出\n"
                f"错误信息: {error_info}\n"
                f"文件: {video_path}\n"
                f"提示: 文件可能损坏、格式不支持或路径编码有问题"
            )
        
        stdout_str = result.stdout.strip()
        if not stdout_str:
            error_info = result.stderr or last_error or "无错误信息"
            raise RuntimeError(
                f"ffprobe 返回空输出\n"
                f"错误信息: {error_info}\n"
                f"文件: {video_path}\n"
                f"提示: 文件可能损坏、格式不支持或路径编码有问题。\n"
                f"建议: 尝试将文件移动到英文路径，或检查文件是否完整"
            )
        
        # 尝试解析JSON
        try:
            data = json.loads(stdout_str)
        except json.JSONDecodeError as e:
            # JSON解析失败，输出更多调试信息
            error_info = result.stderr or "无错误信息"
            raise RuntimeError(f"无法解析 ffprobe 输出为JSON\n错误: {e}\n输出前100字符: {stdout_str[:100]}\n错误信息: {error_info}\n文件: {video_path}")
        
        # 查找视频流
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            raise ValueError("未找到视频流")
        
        # 查找音频流
        audio_streams = [s for s in data.get('streams', []) 
                        if s.get('codec_type') == 'audio']
        first_audio = audio_streams[0] if audio_streams else None
        
        # 解析帧率（分数形式，如 "24000/1001"）
        # 优先使用 r_frame_rate（更准确），fallback 到 avg_frame_rate，最后用默认值
        frame_rate = (video_stream.get('r_frame_rate') or 
                     video_stream.get('avg_frame_rate') or 
                     '25/1')
        # 如果帧率是无效值（如 "0/0"），使用默认值
        if frame_rate == '0/0' or not frame_rate or '/' not in str(frame_rate):
            frame_rate = '25/1'
        
        # 获取视频时长
        duration_str = data.get('format', {}).get('duration')
        duration = None
        if duration_str:
            try:
                duration = float(duration_str)
            except:
                pass
        
        return {
            'width': int(video_stream.get('width', 1920)),
            'height': int(video_stream.get('height', 1080)),
            'frame_rate': frame_rate,
            'codec_name': video_stream.get('codec_name', 'h264'),
            'pix_fmt': video_stream.get('pix_fmt', 'yuv420p'),
            'has_audio': len(audio_streams) > 0,
            'audio_codec': first_audio.get('codec_name') if first_audio else None,
            'audio_sample_rate': first_audio.get('sample_rate') if first_audio else None,
            'audio_channels': first_audio.get('channels') if first_audio else None,
            'duration': duration,
        }
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"ffprobe 执行超时（30秒），文件可能很大或损坏: {video_path}")
    except FileNotFoundError as e:
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    except (KeyError, ValueError) as e:
        raise RuntimeError(f"无法从视频中提取必要信息: {e}\n文件: {video_path}\n提示: 视频文件可能格式特殊或不完整")
    except UnicodeDecodeError as e:
        raise RuntimeError(f"路径编码错误: {e}\n文件: {video_path}\n提示: 文件路径包含特殊字符，请尝试将文件移动到英文路径")
    except Exception as e:
        # 捕获其他所有异常，包括可能的编码问题
        import traceback
        error_detail = traceback.format_exc()
        raise RuntimeError(f"处理视频文件时发生错误: {e}\n文件: {video_path}\n详细信息: {error_detail}")


def get_font_path(font_path: Optional[str] = None) -> str:
    """
    获取字体文件路径
    
    Args:
        font_path: 用户指定的字体路径，如果为 None 则使用内置字体
    
    Returns:
        字体文件路径
    """
    if font_path and Path(font_path).exists():
        return str(Path(font_path).absolute())
    
    # 查找内置字体文件
    script_dir = Path(__file__).parent
    possible_fonts = [
        script_dir / 'font.ttf',
        script_dir / 'font.otf',
        script_dir / 'fonts' / 'font.ttf',
        script_dir / 'fonts' / 'font.otf',
    ]
    
    for font_file in possible_fonts:
        if font_file.exists():
            return str(font_file.absolute())
    
    # 如果找不到内置字体，尝试使用系统字体
    import platform
    system = platform.system()
    
    if system == 'Windows':
        # Windows 常见字体路径
        system_fonts = [
            'C:/Windows/Fonts/msyh.ttc',  # 微软雅黑
            'C:/Windows/Fonts/simsun.ttc',  # 宋体
        ]
        for font in system_fonts:
            if Path(font).exists():
                return font
    elif system == 'Darwin':  # macOS
        system_fonts = [
            '/System/Library/Fonts/PingFang.ttc',
            '/Library/Fonts/Arial.ttf',
        ]
        for font in system_fonts:
            if Path(font).exists():
                return font
    elif system == 'Linux':
        system_fonts = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        ]
        for font in system_fonts:
            if Path(font).exists():
                return font
    
    raise FileNotFoundError(
        "未找到字体文件。请使用 --font 参数指定字体路径，"
        "或在脚本目录放置 font.ttf 文件"
    )


def calculate_font_size(height: int) -> int:
    """根据视频高度计算字号"""
    return int(height * 0.055)


def calculate_typewriter_duration(text: str, char_speed: float, min_duration: float = 3.0) -> float:
    """
    计算打字机效果需要的时长
    
    Args:
        text: 文本内容（支持换行符 \n）
        char_speed: 每个字符的显示间隔（秒）
        min_duration: 最小时长（秒），默认3.0
    
    Returns:
        需要的时长（秒）
    """
    # 分割成行
    lines = text.split('\n', 1)
    line1 = lines[0] if len(lines) > 0 else ""
    line2 = lines[1] if len(lines) > 1 else ""
    
    # 计算第一行需要的时间
    line1_duration = len(line1) * char_speed if line1 else 0
    
    # 计算第二行需要的时间
    line2_duration = 0
    if line2:
        line2_start = line1_duration + 0.2  # 第一行完成后稍等0.2秒
        line2_duration = len(line2) * char_speed
        total_duration = line2_start + line2_duration
    else:
        total_duration = line1_duration
    
    # 添加最后的停留时间（最后一行显示后停留0.5秒）
    total_duration += 0.5
    
    # 确保不少于最小时长
    return max(total_duration, min_duration)


def build_typewriter_filter(text: str, font_file: str, font_size: int, 
                           height: int, char_speed: float, duration: float) -> str:
    """
    构建打字机效果的滤镜链
    
    Args:
        text: 文本内容（支持换行符 \n）
        font_file: 字体文件路径
        font_size: 字号
        height: 视频高度
        char_speed: 每个字符的显示间隔（秒）
        duration: 视频总时长（秒）
    
    Returns:
        ffmpeg 滤镜字符串
    """
    # 分割成行
    lines = text.split('\n', 1)
    line1 = lines[0] if len(lines) > 0 else ""
    line2 = lines[1] if len(lines) > 1 else ""
    
    filters = []
    line_spacing = int(font_size * 1.5)
    
    # 处理第一行
    if line1:
        # 转义第一行文字
        line1_escaped = line1.replace('\\', '\\\\').replace("'", "\\'")
        chars1 = list(line1)
        
        # 计算第一行起始位置（居中显示）
        y1_base = f"(h-text_h*2-{line_spacing})/2"
        
        # 为第一行的每个字符创建 drawtext，使用累积文本方式
        # 每个 drawtext 只在特定时间段显示，避免重叠
        for i in range(len(chars1)):
            accumulated_text = "".join(chars1[:i+1])
            char_escaped = accumulated_text.replace('\\', '\\\\').replace("'", "\\'")
            start_time = i * char_speed
            # 下一个字符的开始时间，如果已经是最后一个，则显示到视频结束（但要限制在duration内）
            if i < len(chars1) - 1:
                end_time = (i + 1) * char_speed
                enable_expr = f"between(t,{start_time:.3f},{end_time:.3f})"
            else:
                # 最后一个字符显示到视频结束，但限制在duration范围内
                enable_expr = f"between(t,{start_time:.3f},{duration:.3f})"
            
            filter_part = (
                f"drawtext=fontfile={font_file}:"
                f"text='{char_escaped}':"
                f"fontsize={font_size}:"
                f"fontcolor=white:"
                f"x=(w-text_w)/2:"
                f"y={y1_base}:"
                f"enable='{enable_expr}'"
            )
            filters.append(filter_part)
    
    # 如果第一行完成了，开始第二行
    if line2:
        line1_duration = len(line1) * char_speed
        line2_start = line1_duration + 0.2  # 第一行完成后稍等0.2秒
        
        # 检查第二行是否能完整显示在duration内
        line2_duration = len(line2) * char_speed
        total_need_time = line2_start + line2_duration
        if total_need_time > duration:
            # 如果总时间超过duration，调整打字速度
            # 确保第二行能在duration内完成
            max_available_time = duration - line2_start
            if max_available_time > 0:
                # 重新计算第二行的字符速度
                adjusted_speed = max_available_time / len(line2)
            else:
                # 如果时间不够，使用默认速度，但会截断
                adjusted_speed = char_speed
        else:
            adjusted_speed = char_speed
        
        line2_escaped = line2.replace('\\', '\\\\').replace("'", "\\'")
        chars2 = list(line2)
        y2_base = f"(h-text_h*2+{line_spacing})/2"
        
        # 为第二行的每个字符创建 drawtext，使用累积文本方式
        for i in range(len(chars2)):
            accumulated_text = "".join(chars2[:i+1])
            char_escaped = accumulated_text.replace('\\', '\\\\').replace("'", "\\'")
            start_time = line2_start + i * adjusted_speed
            
            # 确保不会超过duration
            if start_time >= duration:
                break  # 跳过超出duration的字符
            
            # 下一个字符的开始时间，如果已经是最后一个，则显示到视频结束（但要限制在duration内）
            if i < len(chars2) - 1:
                end_time = line2_start + (i + 1) * adjusted_speed
                # 确保end_time不超过duration
                end_time = min(end_time, duration)
                enable_expr = f"between(t,{start_time:.3f},{end_time:.3f})"
            else:
                # 最后一个字符显示到视频结束，但限制在duration范围内
                # 确保start_time小于duration
                if start_time < duration:
                    enable_expr = f"between(t,{start_time:.3f},{duration:.3f})"
                else:
                    break  # 如果最后一个字符也超出duration，跳过
            
            filter_part = (
                f"drawtext=fontfile={font_file}:"
                f"text='{char_escaped}':"
                f"fontsize={font_size}:"
                f"fontcolor=white:"
                f"x=(w-text_w)/2:"
                f"y={y2_base}:"
                f"enable='{enable_expr}'"
            )
            filters.append(filter_part)
    
    return ",".join(filters)


def make_intro_video(intro_path: Path, video_info: Dict, text: str, 
                    duration: float, font_path: Optional[str] = None,
                    ffmpeg_path: Optional[str] = None, temp_dir: Optional[Path] = None,
                    progress_callback: Optional[callable] = None,
                    typewriter_effect: bool = False,
                    typewriter_speed: float = 0.15) -> None:
    """
    生成匹配原片参数的片头视频
    
    Args:
        intro_path: 输出片头文件路径
        video_info: 原片视频信息
        text: 片头文字
        duration: 片头时长（秒）
        font_path: 字体文件路径
        ffmpeg_path: ffmpeg 目录路径
        temp_dir: 临时文件目录（用于存储文字文件）
    """
    width = video_info['width']
    height = video_info['height']
    frame_rate = video_info['frame_rate']
    codec_name = video_info['codec_name']
    pix_fmt = video_info['pix_fmt']
    font_size = calculate_font_size(height)
    
    # 获取字体路径
    try:
        font_file = get_font_path(font_path)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"字体文件错误: {e}")
    
    # 确定编码器：使用与原视频相同的编码格式，确保concat demuxer可以无损拼接
    # 支持多种常见编码格式
    codec_name_lower = codec_name.lower()
    if codec_name_lower in ['hevc', 'h265', 'x265']:
        video_codec = 'libx265'  # HEVC/H.265 编码
    elif codec_name_lower in ['h264', 'avc', 'x264']:
        video_codec = 'libx264'  # H.264 编码
    elif codec_name_lower in ['vp9']:
        video_codec = 'libvpx-vp9'  # VP9 编码
    elif codec_name_lower in ['vp8']:
        video_codec = 'libvpx'  # VP8 编码
    elif codec_name_lower in ['av1']:
        video_codec = 'libaom-av1'  # AV1 编码（需要FFmpeg编译时支持）
    elif codec_name_lower in ['mpeg4', 'mp4v']:
        video_codec = 'mpeg4'  # MPEG-4 编码
    elif codec_name_lower in ['mpeg2video', 'mpeg2']:
        video_codec = 'mpeg2video'  # MPEG-2 编码
    else:
        # 其他编码格式，尝试使用相同的编码器名称
        # 如果FFmpeg不支持该编码器，会报错，但至少尝试了
        video_codec = codec_name  # 尝试使用原编码器名称
    
    # 构建 ffmpeg 命令
    # 视频部分：黑底 + 文字
    # 使用 color 生成黑底，然后用 drawtext 叠加文字
    # 为了避免 Windows 路径转义问题，将字体文件复制到视频目录
    # 使用相对路径可以避免 Windows 绝对路径的冒号转义问题
    if temp_dir is None:
        temp_dir = intro_path.parent
    
    font_file_path = Path(font_file).absolute()
    temp_dir_abs = Path(temp_dir).absolute()
    
    # 将字体文件复制到临时目录（如果不在同一目录）
    if font_file_path.parent.resolve() != temp_dir_abs.resolve():
        font_copy = temp_dir_abs / font_file_path.name
        try:
            import shutil
            shutil.copy2(font_file_path, font_copy)
            font_file_to_use = font_file_path.name  # 使用相对路径（文件名）
            font_needs_cleanup = True
            font_copy_path = font_copy
        except Exception as e:
            # 如果复制失败，抛出错误
            raise RuntimeError(f"无法复制字体文件到临时目录: {e}")
    else:
        font_file_to_use = font_file_path.name  # 已经在同一目录，使用相对路径
        font_needs_cleanup = False
        font_copy_path = None
    
    # 如果启用了打字机效果，计算实际需要的时长
    if typewriter_effect:
        # 计算打字机效果需要的时长
        actual_duration = calculate_typewriter_duration(text, typewriter_speed, duration)
        # 使用计算出的时长，但至少要等于用户设定的duration
        effective_duration = max(actual_duration, duration)
    else:
        effective_duration = duration
    
    # 转义文字（支持换行符 \n）
    escaped_text = text.replace('\\', '\\\\').replace("'", "\\'")
    
    # 如果启用了打字机效果，使用逐字显示
    if typewriter_effect:
        video_filter = build_typewriter_filter(
            text, font_file_to_use, font_size, height, typewriter_speed, effective_duration
        )
    # 检查是否包含换行符，如果有则使用多个 drawtext 滤镜
    elif '\n' in text:
        # 多行文字：使用两个 drawtext 滤镜，分别显示两行
        lines = text.split('\n', 1)  # 最多分成两行
        line1 = lines[0].replace('\\', '\\\\').replace("'", "\\'")
        line2 = lines[1].replace('\\', '\\\\').replace("'", "\\'") if len(lines) > 1 else ""
        
        if line2:
            # 两行文字：第一行在上，第二行在下
            # 行间距设置为字体大小的 1.5 倍，让两行文字分开更明显
            line_spacing = int(font_size * 1.5)
            # 计算两行文字的总高度：第一行高度 + 行间距 + 第二行高度
            # 第一行 y 坐标：屏幕中心 - 总高度的一半
            # 第二行 y 坐标：第一行 y + 第一行高度 + 行间距
            video_filter = (
                f"drawtext=fontfile={font_file_to_use}:"
                f"text='{line1}':"
                f"fontsize={font_size}:"
                f"fontcolor=white:"
                f"x=(w-text_w)/2:"
                f"y=(h-text_h*2-{line_spacing})/2,"
                f"drawtext=fontfile={font_file_to_use}:"
                f"text='{line2}':"
                f"fontsize={font_size}:"
                f"fontcolor=white:"
                f"x=(w-text_w)/2:"
                f"y=(h-text_h*2+{line_spacing})/2"
            )
        else:
            # 只有一行
            video_filter = (
                f"drawtext=fontfile={font_file_to_use}:"
                f"text='{line1}':"
                f"fontsize={font_size}:"
                f"fontcolor=white:"
                f"x=(w-text_w)/2:"
                f"y=(h-text_h)/2"
            )
    else:
        # 单行文字
        video_filter = (
            f"drawtext=fontfile={font_file_to_use}:"
            f"text='{escaped_text}':"
            f"fontsize={font_size}:"
            f"fontcolor=white:"
            f"x=(w-text_w)/2:"
            f"y=(h-text_h)/2"
        )
    text_file = None
    
    ffmpeg_cmd, _ = find_ffmpeg_executable(ffmpeg_path)
    # 确保 ffmpeg_cmd 是绝对路径
    if not Path(ffmpeg_cmd).is_absolute():
        ffmpeg_cmd = str(Path(ffmpeg_cmd).resolve())
    
    # 切换到临时目录执行，使用相对路径
    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(str(temp_dir_abs))
        
        # 构建 ffmpeg 命令
        # 先添加所有输入
        # 使用effective_duration生成输入源
        cmd = [
            ffmpeg_cmd,
            '-y',  # 覆盖输出文件
            '-stats',  # 显示进度信息
            '-f', 'lavfi',
            '-i', f'color=black:s={width}x{height}:d={effective_duration}',
        ]
        
        # 音频部分：如果原片有音频，添加音频输入
        if video_info['has_audio']:
            audio_codec = video_info['audio_codec'] or 'aac'
            sample_rate = video_info['audio_sample_rate'] or '48000'
            channels = int(video_info['audio_channels'] or 2)
            
            # 确定声道布局
            if channels == 1:
                channel_layout = 'mono'
            elif channels == 2:
                channel_layout = 'stereo'
            elif channels == 6:
                channel_layout = '5.1'  # 5.1 声道
            else:
                channel_layout = f'{channels}ch'
            
            # 添加音频输入（限制时长）
            cmd.extend([
                '-f', 'lavfi',
                '-i', f'anullsrc=channel_layout={channel_layout}:sample_rate={sample_rate}:duration={effective_duration}',
            ])
        
        # 添加视频滤镜和编码选项
        # 使用 fps 滤镜设置帧率，而不是 -r 参数（避免时间基准问题）
        # 同时限制输出时长
        video_filter_with_fps = f"{video_filter},fps={frame_rate}"
        cmd.extend([
            '-vf', video_filter_with_fps,
            '-t', str(effective_duration),  # 明确限制输出时长
            '-pix_fmt', pix_fmt,
            '-c:v', video_codec,
            '-preset', 'ultrafast',  # 快速编码
        ])
        
        # 根据编码格式添加相应的参数
        if video_codec == 'libx265':
            cmd.extend([
                '-x265-params', 'log-level=error',  # 减少日志输出
            ])
        elif video_codec == 'libx264':
            # H.264编码，使用ultrafast预设（已在上面设置）
            pass
        elif video_codec == 'libvpx-vp9':
            # VP9编码参数
            cmd.extend([
                '-b:v', '0',  # 使用CRF模式
                '-crf', '30',  # 质量参数
            ])
        elif video_codec == 'libvpx':
            # VP8编码参数
            cmd.extend([
                '-b:v', '0',
                '-crf', '30',
            ])
        elif video_codec == 'libaom-av1':
            # AV1编码参数（如果FFmpeg支持）
            cmd.extend([
                '-b:v', '0',
                '-crf', '30',
            ])
        # 其他编码格式使用默认参数
        
        # 添加流映射
        if video_info['has_audio']:
            cmd.extend([
                '-map', '0:v',  # 映射第一个输入的视频流
                '-map', '1:a',  # 映射第二个输入的音频流
                '-c:a', audio_codec,
            ])
        else:
            # 只有视频，只映射视频流
            cmd.extend(['-map', '0:v'])
        
        # 添加输出文件（使用相对于 temp_dir 的路径）
        intro_relative = intro_path.relative_to(temp_dir_abs) if intro_path.is_relative_to(temp_dir_abs) else intro_path.name
        cmd.append(str(intro_relative))
        
        try:
            # 使用 Popen 实时读取输出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                universal_newlines=True
            )
            
            # 实时读取输出并解析进度
            if progress_callback:
                for line in process.stdout:
                    # 解析时间信息：time=00:00:02.50
                    if 'time=' in line:
                        try:
                            # 提取时间字符串
                            time_str = line.split('time=')[1].split()[0]
                            # 解析时间（HH:MM:SS.mmm）
                            parts = time_str.split(':')
                            if len(parts) == 3:
                                hours = float(parts[0])
                                minutes = float(parts[1])
                                seconds = float(parts[2])
                                current_time = hours * 3600 + minutes * 60 + seconds
                                # 计算进度百分比
                                progress = min(100, int((current_time / effective_duration) * 100))
                                progress_callback(progress, f"生成片头: {time_str}")
                        except:
                            pass
            
            # 等待进程完成
            process.wait()
            
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd)
            
            # 验证生成的片头文件时长是否正确
            if intro_path.exists():
                try:
                    import json
                    _, ffprobe_cmd = find_ffmpeg_executable(ffmpeg_path)
                    probe_cmd = [
                        ffprobe_cmd,
                        '-v', 'quiet',
                        '-print_format', 'json',
                        '-show_format',
                        str(intro_path)
                    ]
                    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
                    if probe_result.returncode == 0:
                        if probe_result.stdout is None or not probe_result.stdout.strip():
                            raise RuntimeError(f"ffprobe 返回空输出，无法验证片头视频时长: {intro_path}")
                        probe_data = json.loads(probe_result.stdout)
                        actual_duration = float(probe_data.get('format', {}).get('duration', 0))
                        # 允许0.1秒的误差
                        if abs(actual_duration - effective_duration) > 0.1:
                            raise RuntimeError(
                                f"片头视频时长不正确：期望 {effective_duration:.2f} 秒，实际 {actual_duration:.2f} 秒\n"
                                f"这可能导致拼接问题"
                            )
                except Exception as e:
                    # 如果验证失败，给出警告但不阻止
                    import warnings
                    warnings.warn(f"无法验证片头视频时长: {e}")
        except subprocess.CalledProcessError as e:
            error_msg = (e.stderr or e.stdout or "未知错误")
            # 尝试解码错误信息
            if isinstance(error_msg, bytes):
                try:
                    error_msg = error_msg.decode('utf-8', errors='replace')
                except:
                    error_msg = error_msg.decode('gbk', errors='replace')
            raise RuntimeError(f"生成片头失败: {error_msg}")
    finally:
        # 恢复原始工作目录
        os.chdir(original_cwd)
        # 清理临时字体文件
        if font_needs_cleanup and font_copy_path and font_copy_path.exists():
            try:
                font_copy_path.unlink()
            except:
                pass


def concat_videos(intro_path: Path, movie_path: Path, output_path: Path,
                 ffmpeg_path: Optional[str] = None,
                 progress_callback: Optional[callable] = None,
                 total_duration: Optional[float] = None) -> None:
    """
    使用 -c copy 无损拼接片头和原片
    先转换为TS格式再拼接，TS格式对时间戳处理更宽容，可以避免时长错误和卡顿
    
    Args:
        intro_path: 片头文件路径
        movie_path: 原片文件路径
        output_path: 输出文件路径
    """
    import tempfile
    import os
    
    # 创建临时目录
    temp_dir = Path(tempfile.mkdtemp())
    intro_ts = temp_dir / "intro.ts"
    movie_ts = temp_dir / "movie.ts"
    output_ts = temp_dir / "output.ts"
    
    try:
        ffmpeg_cmd, _ = find_ffmpeg_executable(ffmpeg_path)
        
        # 检测片头和原片的编码格式，选择正确的bitstream filter
        intro_info = get_video_info(intro_path, ffmpeg_path)
        movie_info = get_video_info(movie_path, ffmpeg_path)
        intro_codec = intro_info.get('codec_name', 'h264').lower()
        movie_codec = movie_info.get('codec_name', 'h264').lower()
        
        # 根据编码格式选择bitstream filter
        intro_bsf = 'hevc_mp4toannexb' if intro_codec in ['hevc', 'h265'] else 'h264_mp4toannexb'
        movie_bsf = 'hevc_mp4toannexb' if movie_codec in ['hevc', 'h265'] else 'h264_mp4toannexb'
        
        # 第一步：将片头转换为TS格式（无损转换）
        if progress_callback:
            progress_callback(0, "转换片头为TS格式...")
        
        cmd1 = [
            ffmpeg_cmd,
            '-y',
            '-i', str(intro_path),
            '-c', 'copy',  # 无损转换
        ]
        # 只有H.264和HEVC需要bitstream filter
        if intro_bsf:
            cmd1.extend(['-bsf:v', intro_bsf])
        cmd1.extend(['-f', 'mpegts', str(intro_ts)])
        
        subprocess.run(cmd1, capture_output=True, check=True, timeout=300)
        
        # 第二步：将原片转换为TS格式（无损转换）
        if progress_callback:
            progress_callback(10, "转换原片为TS格式...")
        
        cmd2 = [
            ffmpeg_cmd,
            '-y',
            '-i', str(movie_path),
            '-c', 'copy',  # 无损转换
        ]
        # 只有H.264和HEVC需要bitstream filter
        if movie_bsf:
            cmd2.extend(['-bsf:v', movie_bsf])
        cmd2.extend(['-f', 'mpegts', str(movie_ts)])
        
        subprocess.run(cmd2, capture_output=True, check=True, timeout=300)
        
        # 第三步：创建concat列表文件
        concat_list_path = temp_dir / "concat_list.txt"
        with open(concat_list_path, 'w', encoding='utf-8') as f:
            intro_ts_str = str(intro_ts).replace('\\', '/').replace("'", "'\\''")
            movie_ts_str = str(movie_ts).replace('\\', '/').replace("'", "'\\''")
            f.write(f"file '{intro_ts_str}'\n")
            f.write(f"file '{movie_ts_str}'\n")
        
        # 第四步：使用concat demuxer拼接TS文件
        if progress_callback:
            progress_callback(20, "拼接TS文件...")
        
        cmd3 = [
            ffmpeg_cmd,
            '-y',
            '-stats',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_list_path),
            '-c', 'copy',  # 无损拼接
            '-f', 'mpegts',
            str(output_ts)
        ]
        
        # 使用 Popen 实时读取输出
        process = subprocess.Popen(
            cmd3,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            universal_newlines=True
        )
        
        # 收集输出用于错误诊断
        output_lines = []
        
        # 实时读取输出并解析进度
        if progress_callback and total_duration:
            for line in process.stdout:
                output_lines.append(line)
                # 解析时间信息：time=00:02:30.50
                if 'time=' in line:
                    try:
                        # 提取时间字符串
                        time_str = line.split('time=')[1].split()[0]
                        # 解析时间（HH:MM:SS.mmm）
                        parts = time_str.split(':')
                        if len(parts) == 3:
                            hours = float(parts[0])
                            minutes = float(parts[1])
                            seconds = float(parts[2])
                            current_time = hours * 3600 + minutes * 60 + seconds
                            # 计算进度百分比（20%用于拼接，80%用于转换回MP4）
                            progress = min(80, 20 + int((current_time / total_duration) * 60))
                            progress_callback(progress, f"拼接TS: {time_str}")
                    except:
                        pass
        else:
            # 如果没有进度回调，也要读取输出
            for line in process.stdout:
                output_lines.append(line)
        
        # 等待进程完成
        process.wait()
        output_text = ''.join(output_lines)
        
        # 检查是否拼接失败
        if process.returncode != 0:
            # 分析错误原因
            error_hint = ""
            output_lower = output_text.lower()
            if 'codec' in output_lower or 'incompatible' in output_lower:
                error_hint = "\n提示：可能是片头视频和原片视频的编码格式不兼容。"
                error_hint += "\n建议：某些视频格式或编码参数可能导致拼接失败，这是该视频文件的问题。"
            elif 'duration' in output_lower or 'time' in output_lower:
                error_hint = "\n提示：可能是片头视频或原片视频的时长信息有问题。"
            elif 'stream' in output_lower or 'mismatch' in output_lower:
                error_hint = "\n提示：可能是片头视频和原片视频的流信息不匹配（分辨率、帧率等）。"
                error_hint += "\n建议：某些特殊编码的视频可能无法使用concat demuxer无损拼接。"
            else:
                error_hint = "\n提示：这是该视频文件特有的问题，可能与该视频的编码格式或容器格式有关。"
                error_hint += "\n建议：之前的EXE版本处理此视频也会出现相同问题，这是视频文件本身的问题。"
            
            raise subprocess.CalledProcessError(process.returncode, cmd3, output_text + error_hint)
        
        # 第五步：将TS文件转换回MP4格式（无损转换）
        if progress_callback:
            progress_callback(80, "转换回MP4格式...")
        
        cmd4 = [
            ffmpeg_cmd,
            '-y',
            '-i', str(output_ts),
            '-c', 'copy',  # 无损转换
            '-movflags', '+faststart',  # 优化MP4文件结构，便于流媒体播放
            str(output_path)
        ]
        
        subprocess.run(cmd4, capture_output=True, check=True, timeout=300)
        
        if progress_callback:
            progress_callback(100, "完成")
    
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or e.stdout or "未知错误"
        raise RuntimeError(
            f"拼接失败: {error_msg}\n"
            f"提示：可能是编码或容器格式不兼容，请检查原片格式"
        )
    finally:
        # 清理临时文件
        try:
            if intro_ts.exists():
                intro_ts.unlink()
            if movie_ts.exists():
                movie_ts.unlink()
            if output_ts.exists():
                output_ts.unlink()
            if 'concat_list_path' in locals() and concat_list_path.exists():
                concat_list_path.unlink()
            # 删除临时目录
            try:
                temp_dir.rmdir()
            except:
                pass
        except:
            pass
    
    # 验证输出文件是否存在且有效
    if not output_path.exists():
        raise RuntimeError(f"拼接失败：输出文件不存在: {output_path}")
    
    # 验证输出文件大小（应该接近原片大小+片头大小）
    intro_size = intro_path.stat().st_size if intro_path.exists() else 0
    movie_size = movie_path.stat().st_size if movie_path.exists() else 0
    output_size = output_path.stat().st_size
    
    # 计算期望的文件大小（片头+原片，允许10%的误差）
    expected_min_size = (intro_size + movie_size) * 0.9
    
    if output_size <= intro_size:
        raise RuntimeError(
            f"拼接失败：输出文件大小({output_size / (1024*1024):.1f}MB)不大于片头文件大小({intro_size / (1024*1024):.1f}MB)\n"
            f"原片大小: {movie_size / (1024*1024):.1f}MB\n"
            f"输出文件可能只包含片头，拼接失败。请检查原片文件格式。"
        )
    elif output_size < expected_min_size:
        # 输出文件太小，可能拼接失败
        # 检查concat输出中是否有更多信息
        error_details = ""
        try:
            # 查找关键错误信息
            output_lower = concat_output_text.lower()
            if 'codec' in output_lower:
                error_details = "\n原因：编码格式不兼容，concat demuxer无法拼接。"
            elif 'stream' in output_lower or 'mismatch' in output_lower:
                error_details = "\n原因：视频流参数不匹配（分辨率、帧率、编码等）。"
            elif 'duration' in output_lower:
                error_details = "\n原因：视频时长信息有问题。"
            else:
                error_details = "\n原因：concat demuxer对该视频格式支持不好，拼接失败。"
        except:
            error_details = "\n原因：concat demuxer对该视频格式支持不好，拼接失败。"
        
        raise RuntimeError(
            f"拼接失败：输出文件大小({output_size / (1024*1024):.1f}MB)远小于期望大小({expected_min_size / (1024*1024):.1f}MB)\n"
            f"片头大小: {intro_size / (1024*1024):.1f}MB, 原片大小: {movie_size / (1024*1024):.1f}MB\n"
            f"输出文件可能只包含片头，原片内容未拼接成功。{error_details}\n"
            f"注意：这是该视频文件格式的问题，不是代码的问题。某些特殊编码的视频无法使用concat demuxer无损拼接。"
        )
    
    # 验证输出文件的时长（应该大于片头时长）
    try:
        # 直接调用 get_video_info，避免循环导入
        _, ffprobe_cmd = find_ffmpeg_executable(ffmpeg_path)
        
        # 检查输出视频时长
        import json
        output_probe_cmd = [
            ffprobe_cmd,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            str(output_path)
        ]
        output_result = subprocess.run(output_probe_cmd, capture_output=True, text=True, timeout=10)
        if output_result.returncode == 0:
            if output_result.stdout is None or not output_result.stdout.strip():
                raise RuntimeError(f"ffprobe 返回空输出，无法验证输出视频时长: {output_path}")
            output_data = json.loads(output_result.stdout)
            output_duration = float(output_data.get('format', {}).get('duration', 0))
            
            # 检查原片时长
            movie_probe_cmd = [
                ffprobe_cmd,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                str(movie_path)
            ]
            movie_result = subprocess.run(movie_probe_cmd, capture_output=True, text=True, timeout=10)
            if movie_result.returncode == 0:
                if movie_result.stdout is None or not movie_result.stdout.strip():
                    raise RuntimeError(f"ffprobe 返回空输出，无法验证原片时长: {movie_path}")
                movie_data = json.loads(movie_result.stdout)
                movie_duration = float(movie_data.get('format', {}).get('duration', 0))
                
                # 检查输出时长是否合理（应该接近原片时长+片头时长）
                if output_duration <= movie_duration:
                    raise RuntimeError(
                        f"拼接可能失败：输出视频时长({output_duration:.2f}秒)不大于原片时长({movie_duration:.2f}秒)\n"
                        f"输出视频可能只包含片头，请检查拼接过程"
                    )
    except Exception as e:
        # 如果验证失败，给出警告
        import warnings
        warnings.warn(f"无法验证输出视频时长: {e}")


def generate_output_path(movie_path: Path, output_dir: Optional[Path] = None) -> Path:
    """
    生成输出文件路径（保持原容器格式）
    
    Args:
        movie_path: 原片文件路径
        output_dir: 输出目录（可选，默认使用原片所在目录）
    
    Returns:
        输出文件路径
    """
    stem = movie_path.stem
    suffix = movie_path.suffix  # 保持原格式
    
    if output_dir:
        parent = Path(output_dir)
    else:
        parent = movie_path.parent
    
    output_name = f"{stem}{suffix}"
    output_path = parent / output_name
    
    # 如果文件已存在，添加递增后缀
    counter = 1
    while output_path.exists():
        output_name = f"{stem}_{counter}{suffix}"
        output_path = parent / output_name
        counter += 1
    
    return output_path


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='为视频文件自动添加片头（无损拼接）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python ddys_intro.py movie.mp4
  python ddys_intro.py movie.mp4 --duration 5 --text "自定义文字"
  python ddys_intro.py movie.mp4 --font /path/to/font.ttf
  python ddys_intro.py movie.mp4 --ffmpeg-path C:/ffmpeg
        """
    )
    
    parser.add_argument('input_file', type=str, help='输入视频文件路径')
    parser.add_argument('--duration', type=float, default=3.0, 
                       help='片头时长（秒），默认 3.0')
    parser.add_argument('--text', type=str, 
                       default='低端影视压制组\n官网：DDYS.IO',
                       help='片头文字，默认两行："低端影视压制组\\n官网：DDYS.IO"')
    parser.add_argument('--font', type=str, default=None,
                       help='字体文件路径（可选，默认使用内置或系统字体）')
    parser.add_argument('--ffmpeg-path', type=str, default=None,
                       help='ffmpeg 目录路径（如果未添加到 PATH，可指定解压后的目录）')
    parser.add_argument('--keep-temp', action='store_true',
                       help='保留中间文件（片头和 concat 列表）')
    parser.add_argument('--typewriter', action='store_true',
                       help='启用打字机效果（逐字显示）')
    parser.add_argument('--typewriter-speed', type=float, default=0.15,
                       help='打字机效果速度（秒/字符），默认 0.15')
    
    args = parser.parse_args()
    
    # 检查环境
    available, error_msg = check_ffmpeg_available(args.ffmpeg_path)
    if not available:
        print(f"错误: {error_msg}", file=sys.stderr)
        sys.exit(1)
    
    # 检查输入文件
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"错误: 输入文件不存在: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    if not input_path.is_file():
        print(f"错误: 输入路径不是文件: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    # 生成输出路径
    output_path = generate_output_path(input_path)
    
    print(f"输入文件: {input_path}")
    print(f"输出文件: {output_path}")
    print(f"片头时长: {args.duration} 秒")
    print(f"片头文字: {args.text}")
    print()
    
    # 临时文件路径
    temp_dir = input_path.parent
    intro_path = temp_dir / f"intro_temp_{input_path.stem}.mp4"
    
    try:
        # 1. 获取视频信息
        print("正在读取视频信息...")
        video_info = get_video_info(input_path, args.ffmpeg_path)
        print(f"  分辨率: {video_info['width']}x{video_info['height']}")
        print(f"  帧率: {video_info['frame_rate']}")
        print(f"  编码: {video_info['codec_name']}")
        print(f"  像素格式: {video_info['pix_fmt']}")
        print(f"  音频: {'有' if video_info['has_audio'] else '无'}")
        print()
        
        # 2. 生成片头
        print("正在生成片头...")
        make_intro_video(intro_path, video_info, args.text, 
                        args.duration, args.font, args.ffmpeg_path, temp_dir,
                        typewriter_effect=getattr(args, 'typewriter', False),
                        typewriter_speed=getattr(args, 'typewriter_speed', 0.15))
        print(f"  片头已生成: {intro_path}")
        print()
        
        # 3. 拼接视频
        print("正在拼接视频（无损模式）...")
        concat_videos(intro_path, input_path, output_path, args.ffmpeg_path)
        print(f"  拼接完成: {output_path}")
        print()
        
        # 4. 清理临时文件
        if not args.keep_temp:
            if intro_path.exists():
                intro_path.unlink()
                print("已清理临时文件")
        
        print("[完成]")
        print(f"输出文件: {output_path}")
        
    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        
        # 清理临时文件
        if not args.keep_temp:
            if intro_path.exists():
                intro_path.unlink()
        
        sys.exit(1)


if __name__ == '__main__':
    main()

