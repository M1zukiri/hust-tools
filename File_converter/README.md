# File_converter — 万能格式转换器

批量转换图片、音频、视频格式，支持单个目录下的批量处理。

## 调用方法

```bash
# 基本用法：转换当前目录下所有 .mp4 为 .mp3
python converter_cli.py mp4 mp3

# 指定目标目录
python converter_cli.py png jpg --dir "D:\图片目录"

# 查看可用转换器列表
python -c "from base_converter import CONVERTERS; [print(c.__name__) for c in CONVERTERS]"
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `src` | 是 | 源文件后缀（如 `png`、`mp3`、`mp4`） |
| `dst` | 是 | 目标文件后缀（如 `jpg`、`wav`、`avi`） |
| `--dir` | 否 | 待处理目录，默认当前目录 |

输出目录自动创建为 `converted_<时间戳>/`。

## 支持格式

### 图片转换器

| 源格式 | 目标格式 |
|--------|----------|
| jpg, jpeg, png, bmp, gif, tiff, webp | 同上（任意互转） |

### 音频转换器（需 ffmpeg）

| 源格式 | 目标格式 |
|--------|----------|
| mp3, wav, ogg, flac, m4a, wma | 同上（任意互转） |

### 视频转换器（需 ffmpeg）

| 源格式 | 目标格式 |
|--------|----------|
| mp4, avi, mkv, mov, flv, wmv | 同上（视频转封装） |
| mp4, avi, mkv, mov, flv, wmv | mp3, wav, ogg, flac, m4a（视频提取音频） |

## 项目结构

```
File_converter/
├── converter_cli.py     # CLI 入口（参数解析 + 批量处理）
├── base_converter.py    # 转换器基类 + 全局注册表
├── image_converter.py   # 图片转换器（Pillow）
├── audio_converter.py   # 音频转换器（pydub）
├── video_converter.py   # 视频转换器（ffmpeg-python）
├── requirements.txt     # Python 依赖
├── demo.jpg / demo.png  # 测试示例图片
└── README.md            # 本文档
```

## 依赖

```bash
pip install pillow pydub ffmpeg-python
```

音频/视频转换还需要系统级 **ffmpeg**：

- **Windows**: `winget install ffmpeg` 或下载并加入 PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

## 常见示例

```bash
# 图片全部转 webp
python converter_cli.py png webp

# 视频提取音频
python converter_cli.py mp4 mp3

# 批量转换音频格式
python converter_cli.py flac mp3
```
