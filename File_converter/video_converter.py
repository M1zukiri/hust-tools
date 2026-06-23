import os
import shutil
from pathlib import Path

# ── ffmpeg 查找：优先 PATH，其次 imageio-ffmpeg 提供的内置二进制 ──
_ffmpeg_bin = shutil.which("ffmpeg")
if _ffmpeg_bin is None:
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        _ffmpeg_bin = get_ffmpeg_exe()
        _bin_dir = Path(_ffmpeg_bin).parent
        # 确保目录下存在 ffmpeg.exe 别名，否则 ffmpeg-python(subprocess) 找不到
        _ffmpeg_link = _bin_dir / "ffmpeg.exe"
        if not _ffmpeg_link.exists():
            try:
                os.symlink(_ffmpeg_bin, _ffmpeg_link)
            except (OSError, AttributeError):
                # 无管理员/开发模式权限时 fallback 为硬链接或拷贝
                try:
                    os.link(_ffmpeg_bin, _ffmpeg_link)
                except OSError:
                    shutil.copy2(_ffmpeg_bin, _ffmpeg_link)
        # 加入 PATH
        os.environ["PATH"] = str(_bin_dir) + os.pathsep + os.environ.get("PATH", "")
    except (ImportError, RuntimeError):
        raise RuntimeError(
            "ffmpeg not found in PATH nor via imageio-ffmpeg. "
            "Install it: pip install imageio-ffmpeg, or add ffmpeg to PATH manually."
        )

import ffmpeg
from base_converter import BaseConverter, CONVERTERS


class VideoConverter(BaseConverter):
    # 视频↔视频
    VIDEO_EXT = ("mp4", "avi", "mkv", "mov", "flv", "wmv")
    # 视频→音频
    AUDIO_EXT = ("mp3", "wav", "ogg", "flac", "m4a")

    SUPPORT_EXT = VIDEO_EXT
    TARGET_EXT  = VIDEO_EXT + AUDIO_EXT

    def convert(self) -> None:
        dst_ext = self.dst.suffix.lower()[1:]
        if dst_ext in self.AUDIO_EXT:
            # 提取音频，不指定 acodec—ffmpeg 根据后缀自动选择正确编码器
            # （如 mp3→libmp3lame, flac→flac, m4a→aac），而非直接用 acodec="copy"
            # 复制原始流导致容器/编码不匹配。
            (
                ffmpeg
                .input(str(self.src))
                .output(str(self.dst), vn=None)
                .overwrite_output()
                .run(quiet=True)
            )
        else:
            # 视频转封装/转码
            (
                ffmpeg
                .input(str(self.src))
                .output(str(self.dst), vcodec="copy", acodec="copy")
                .overwrite_output()
                .run(quiet=True)
            )


CONVERTERS.append(VideoConverter)
