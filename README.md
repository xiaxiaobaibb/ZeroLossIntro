# ZeroLossIntro - 视频片头添加工具

一个专业的视频片头添加工具，支持无损拼接和打字机效果，为视频文件自动添加自定义片头。

## 功能特点

- **无损拼接**：使用 FFmpeg concat demuxer 实现真正的无损视频拼接
- **智能匹配**：自动匹配原视频的分辨率、帧率、编码格式等参数
- **打字机效果**：支持逐字显示的动态文字效果
- **多格式支持**：支持 MP4、MKV、AVI、MOV 等主流视频格式
- **批量处理**：支持单文件、多文件选择和目录批量处理
- **图形界面**：提供友好的 GUI 界面，操作简单直观
- **命令行支持**：同时提供命令行版本，适合自动化处理

## 系统要求

- **操作系统**：Windows 10/11（64位）
- **Python**：3.6+ （源码运行）
- **FFmpeg**：项目已内置 FFmpeg 静态版本

## 快速开始

### 方式一：直接运行（推荐）

1. 下载项目文件
2. 双击运行 `ZeroLossIntro.exe`
3. 选择视频文件和导出目录
4. 自定义片头文字
5. 点击"开始处理"

### 方式二：Python 源码运行

```bash
# 安装依赖（可选，项目主要使用标准库）
pip install -r requirements.txt

# 运行图形界面
python ddys_intro_gui.py

# 或使用命令行
python ddys_intro.py video.mp4 --text "自定义文字\n第二行文字"
```

## 使用说明

### 图形界面使用

1. **FFmpeg 路径**：通常保持默认即可，程序会自动使用内置的 FFmpeg
2. **选择视频**：
   - **单个**：选择单个视频文件
   - **多个**：批量选择多个视频文件
   - **目录**：选择包含视频文件的目录
3. **导出目录**：选择处理后视频的保存位置
4. **字幕文案**：自定义片头显示的文字内容
5. **片头时长**：设置片头显示时间（1-10秒）
6. **打字机效果**：启用后文字会逐字显示
7. **字体文件**：可选择自定义字体（支持 TTF、OTF 格式）

### 命令行使用

```bash
# 基本用法
python ddys_intro.py video.mp4

# 自定义参数
python ddys_intro.py video.mp4 \
  --duration 5 \
  --text "低端影视压制组\n官网：DDYS.IO" \
  --font font.ttf \
  --typewriter \
  --typewriter-speed 0.1

# 指定 FFmpeg 路径
python ddys_intro.py video.mp4 --ffmpeg-path C:/ffmpeg
```

### 参数说明

- `--duration`：片头时长（秒），默认 3.0
- `--text`：片头文字，使用 `\n` 分隔多行
- `--font`：字体文件路径（可选）
- `--typewriter`：启用打字机效果
- `--typewriter-speed`：打字速度（秒/字符），默认 0.15
- `--ffmpeg-path`：FFmpeg 目录路径
- `--keep-temp`：保留临时文件

## 技术特性

### 无损拼接原理

1. **格式检测**：自动检测原视频的编码格式、分辨率、帧率等参数
2. **片头生成**：生成与原视频参数完全匹配的片头视频
3. **TS转换**：将片头和原片转换为 TS 格式（对时间戳处理更宽容）
4. **无损拼接**：使用 FFmpeg concat demuxer 进行无损拼接
5. **格式还原**：将拼接后的 TS 文件转换回原格式

### 支持的编码格式

- **视频编码**：H.264、H.265/HEVC、VP8、VP9、AV1、MPEG-4 等
- **音频编码**：AAC、MP3、AC3、Opus 等
- **容器格式**：MP4、MKV、AVI、MOV、FLV、WMV 等

### 打字机效果

- 支持逐字显示动画
- 可调节打字速度
- 支持多行文字的分别显示
- 自动计算最佳显示时长

## 项目结构

```
ZeroLossIntro/
├── ddys_intro.py          # 核心处理模块
├── ddys_intro_gui.py      # 图形界面
├── build_gui.py           # 打包脚本
├── font.ttf               # 内置字体文件
├── requirements.txt       # 依赖列表
├── ZeroLossIntro.exe      # 可执行文件
├── ZeroLossIntro.spec     # PyInstaller 配置
└── ffmpeg/                # FFmpeg 静态版本
    ├── bin/               # 可执行文件
    ├── doc/               # 文档
    └── README.txt         # FFmpeg 信息
```

## 开发说明

### 环境配置

```bash
# 克隆项目
git clone <repository-url>
cd ZeroLossIntro

# 安装开发依赖
pip install pyinstaller

# 运行开发版本
python ddys_intro_gui.py
```

### 打包发布

```bash
# 使用内置打包脚本
python build_gui.py

# 或手动使用 PyInstaller
pyinstaller --onefile --windowed --name ZeroLossIntro \
  --add-data "font.ttf;." ddys_intro_gui.py
```

### 代码结构

- **ddys_intro.py**：核心功能模块
  - `get_video_info()`：获取视频信息
  - `make_intro_video()`：生成片头视频
  - `concat_videos()`：无损拼接视频
  - `build_typewriter_filter()`：构建打字机效果

- **ddys_intro_gui.py**：图形界面模块
  - 基于 tkinter 构建
  - 支持多线程处理
  - 实时进度显示

## 常见问题

### Q: 处理某些视频时出现错误？
A: 某些特殊编码的视频可能无法使用 concat demuxer 无损拼接，这是视频文件本身的问题。建议尝试其他视频或转换格式后再处理。

### Q: 如何自定义字体？
A: 点击"浏览"按钮选择 TTF 或 OTF 字体文件，或将字体文件命名为 `font.ttf` 放在程序目录下。

### Q: 打字机效果速度如何调节？
A: 在"打字速度"中调节数值，建议范围 0.1-0.2 秒/字符。数值越小打字越快。

### Q: 支持哪些视频格式？
A: 支持所有 FFmpeg 支持的格式，包括 MP4、MKV、AVI、MOV、FLV、WMV、M4V 等。

### Q: 如何批量处理视频？
A: 使用"多个"按钮选择多个文件，或使用"目录"按钮选择包含视频的文件夹。

## 更新日志

### v1.0.0
- 初始版本发布
- 支持无损视频拼接
- 图形界面和命令行双模式
- 打字机效果支持
- 批量处理功能

## 许可证

本项目基于 GPL v3 许可证开源。

## 技术支持

如有问题或建议，请访问项目主页或联系开发团队。

---

**低端影视压制组** - 专业的视频处理解决方案  
官网：[低端影视](https://ddys.io)