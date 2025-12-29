# ZeroLossIntro - Video Intro Adding Tool

A professional video intro adding tool that supports lossless concatenation and typewriter effects, automatically adding custom intros to video files.

## Features

- **Lossless Concatenation**: True lossless video concatenation using FFmpeg concat demuxer
- **Smart Matching**: Automatically matches original video parameters (resolution, frame rate, codec, etc.)
- **Typewriter Effect**: Supports dynamic text effects with character-by-character display
- **Multi-format Support**: Supports mainstream video formats like MP4, MKV, AVI, MOV, etc.
- **Batch Processing**: Supports single file, multiple file selection, and directory batch processing
- **GUI Interface**: User-friendly GUI interface with simple and intuitive operation
- **Command Line Support**: Also provides command line version for automation

## System Requirements

- **Operating System**: Windows 10/11 (64-bit)
- **Python**: 3.6+ (for source code execution)
- **FFmpeg**: Static FFmpeg version included in the project

## Quick Start

### Method 1: Direct Execution (Recommended)

1. Download project files
2. Double-click to run `ZeroLossIntro.exe`
3. Select video file and export directory
4. Customize intro text
5. Click "Start Processing"

### Method 2: Python Source Code Execution

```bash
# Install dependencies (optional, project mainly uses standard library)
pip install -r requirements.txt

# Run GUI
python ddys_intro_gui.py

# Or use command line
python ddys_intro.py video.mp4 --text "Custom Text\nSecond Line"
```

## Usage Instructions

### GUI Usage

1. **FFmpeg Path**: Usually keep default, program will automatically use built-in FFmpeg
2. **Select Video**:
   - **Single**: Select a single video file
   - **Multiple**: Batch select multiple video files
   - **Directory**: Select directory containing video files
3. **Export Directory**: Choose save location for processed videos
4. **Subtitle Text**: Customize text content displayed in intro
5. **Intro Duration**: Set intro display time (1-10 seconds)
6. **Typewriter Effect**: When enabled, text will display character by character
7. **Font File**: Optional custom font selection (supports TTF, OTF formats)

### Command Line Usage

```bash
# Basic usage
python ddys_intro.py video.mp4

# Custom parameters
python ddys_intro.py video.mp4 \
  --duration 5 \
  --text "DDYS Encode Group\nWebsite: DDYS.IO" \
  --font font.ttf \
  --typewriter \
  --typewriter-speed 0.1

# Specify FFmpeg path
python ddys_intro.py video.mp4 --ffmpeg-path C:/ffmpeg
```
### Parameter Description

- `--duration`: Intro duration (seconds), default 3.0
- `--text`: Intro text, use `\n` to separate multiple lines
- `--font`: Font file path (optional)
- `--typewriter`: Enable typewriter effect
- `--typewriter-speed`: Typing speed (seconds/character), default 0.15
- `--ffmpeg-path`: FFmpeg directory path
- `--keep-temp`: Keep temporary files

## Technical Features

### Lossless Concatenation Principle

1. **Format Detection**: Automatically detect original video's codec, resolution, frame rate, etc.
2. **Intro Generation**: Generate intro video with parameters matching original video
3. **TS Conversion**: Convert intro and original video to TS format (more tolerant of timestamp handling)
4. **Lossless Concatenation**: Use FFmpeg concat demuxer for lossless concatenation
5. **Format Restoration**: Convert concatenated TS file back to original format

### Supported Codec Formats

- **Video Codecs**: H.264, H.265/HEVC, VP8, VP9, AV1, MPEG-4, etc.
- **Audio Codecs**: AAC, MP3, AC3, Opus, etc.
- **Container Formats**: MP4, MKV, AVI, MOV, FLV, WMV, etc.

### Typewriter Effect

- Supports character-by-character display animation
- Adjustable typing speed
- Supports separate display of multi-line text
- Automatically calculates optimal display duration

## Project Structure

```
ZeroLossIntro/
├── ddys_intro.py          # Core processing module
├── ddys_intro_gui.py      # GUI interface
├── build_gui.py           # Build script
├── font.ttf               # Built-in font file
├── requirements.txt       # Dependencies list
├── ZeroLossIntro.exe      # Executable file
├── ZeroLossIntro.spec     # PyInstaller configuration
└── ffmpeg/                # Static FFmpeg version
    ├── bin/               # Executable files
    ├── doc/               # Documentation
    └── README.txt         # FFmpeg information
```

## Development Guide

### Environment Setup

```bash
# Clone project
git clone <repository-url>
cd ZeroLossIntro

# Install development dependencies
pip install pyinstaller

# Run development version
python ddys_intro_gui.py
```

### Build and Release

```bash
# Use built-in build script
python build_gui.py

# Or manually use PyInstaller
pyinstaller --onefile --windowed --name ZeroLossIntro \
  --add-data "font.ttf;." ddys_intro_gui.py
```

### Code Structure

- **ddys_intro.py**: Core functionality module
  - `get_video_info()`: Get video information
  - `make_intro_video()`: Generate intro video
  - `concat_videos()`: Lossless video concatenation
  - `build_typewriter_filter()`: Build typewriter effect

- **ddys_intro_gui.py**: GUI interface module
  - Built with tkinter
  - Multi-threaded processing support
  - Real-time progress display

## FAQ

### Q: Errors when processing certain videos?
A: Some specially encoded videos may not be able to use concat demuxer for lossless concatenation, which is an issue with the video file itself. Try other videos or convert format before processing.

### Q: How to customize fonts?
A: Click "Browse" button to select TTF or OTF font files, or rename font file to `font.ttf` and place in program directory.

### Q: How to adjust typewriter effect speed?
A: Adjust the value in "Typing Speed", recommended range 0.1-0.2 seconds/character. Smaller values mean faster typing.

### Q: What video formats are supported?
A: Supports all formats supported by FFmpeg, including MP4, MKV, AVI, MOV, FLV, WMV, M4V, etc.

### Q: How to batch process videos?
A: Use "Multiple" button to select multiple files, or use "Directory" button to select folder containing videos.

## Changelog

### v1.0.0
- Initial release
- Lossless video concatenation support
- Dual mode: GUI and command line
- Typewriter effect support
- Batch processing functionality

## License

This project is open source under GPL v3 license.

## Technical Support

For questions or suggestions, please visit the project homepage or contact the development team.

---

**DDYS Encode Group** - Professional Video Processing Solutions  
Website: [DDYS.IO](https://ddys.io)