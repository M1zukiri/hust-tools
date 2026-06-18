# Lrc_match — 歌词全能管家

自动扫描目录中的歌曲和歌词文件，进行格式转换（VTT/SRT → LRC）、乱码修复和文件整理。

## 调用方法

```bash
python main.py
```

运行后输入要扫描的根目录路径（如 `M:\device\Resources`），程序自动完成扫描、修复、整理。

## 功能说明

| 功能 | 说明 |
|------|------|
| 格式修复 | 修复 `[00:00.00][]` 等错误残留标记 |
| 格式转换 | 精准处理 WebVTT / SRT 结构，转换为标准 LRC 时间戳 |
| 乱码修复 | 多重编码探测（UTF-8 / GB18030 / Shift-JIS / UTF-16） |
| 文件整理 | 自动将转换/修复后的歌词移动至对应的歌曲文件夹 |
| 模糊匹配 | 当歌词文件名与歌曲名不完全一致时，自动模糊匹配（相似度 > 80%） |

## 项目结构

```
Lrc_match/
├── main.py       # 主程序（含 RobustLyricEngine + LyricManager）
└── README.md     # 本文档
```

## 核心类

### RobustLyricEngine
- `read_file_safe(file_path)` — 多重编码安全读取文件
- `parse_and_rebuild(raw_content)` — 将混乱的歌词内容重构为标准 LRC 格式

### LyricManager
- `scan()` — 递归扫描目录，识别歌曲文件（mp3/wav/flac/m4a/ogg）和歌词素材（lrc/vtt/srt/txt）
- `process_and_sync()` — 执行修复、转换、整理全流程

## 依赖

无额外依赖（仅使用 Python 标准库 `os`、`re`、`difflib`、`pathlib`）
