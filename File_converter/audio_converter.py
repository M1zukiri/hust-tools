import os
import shutil
import subprocess
from pathlib import Path

# ── ffmpeg 查找：优先系统 PATH，其次 imageio-ffmpeg 内置二进制 ──
_ffmpeg_bin = shutil.which("ffmpeg")
if _ffmpeg_bin is None:
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        _ffmpeg_bin = get_ffmpeg_exe()
        _bin_dir = Path(_ffmpeg_bin).parent
        # 确保目录下存在 ffmpeg.exe 别名（ffmpeg-python / pydub 可能依赖它）
        _ffmpeg_link = _bin_dir / "ffmpeg.exe"
        if not _ffmpeg_link.exists():
            try:
                os.symlink(_ffmpeg_bin, _ffmpeg_link)
            except (OSError, AttributeError):
                try:
                    os.link(_ffmpeg_bin, _ffmpeg_link)
                except OSError:
                    shutil.copy2(_ffmpeg_bin, _ffmpeg_link)
        os.environ["PATH"] = str(_bin_dir) + os.pathsep + os.environ.get("PATH", "")
    except (ImportError, RuntimeError):
        raise RuntimeError(
            "ffmpeg not found in PATH nor via imageio-ffmpeg. "
            "Install it: pip install imageio-ffmpeg, or add ffmpeg to PATH manually."
        )

from base_converter import BaseConverter, CONVERTERS


class AudioConverter(BaseConverter):
    SUPPORT_EXT = ("mp3", "wav", "ogg", "flac", "m4a", "wma")
    TARGET_EXT  = SUPPORT_EXT

    def convert(self) -> None:
        """使用 ffmpeg 转换，保留所有原始元数据（标题、艺术家、专辑等）。"""
        dst_ext = self.dst.suffix.lower()[1:]

        # 基础参数：覆盖输出 + 输入文件
        cmd = [_ffmpeg_bin, "-y", "-i", str(self.src)]

        # 只取音频流（可选存在，兼容纯音频文件）
        cmd += ["-map", "0:a?"]

        # ── 元数据保留 ──
        # 全局级（容器/格式级标签，如 FLAC/WAV 的块注释）
        cmd += ["-map_metadata", "0"]
        # 流级（流内嵌标签，如 OGG Vorbis Comment → TITLE/ARTIST/ALBUM）
        # 0:s:0 = 输入 0 的第 0 号流（首个音频流）
        cmd += ["-map_metadata", "0:s:0"]

        # 音频编码器：根据目标格式自动选择
        cmd += ["-codec:a", self._codec_for(dst_ext)]

        # ── 格式专用参数 ──
        if dst_ext == "mp3":
            # ID3v2.3 + ID3v1 以获得最广泛播放器兼容性
            cmd += ["-id3v2_version", "3", "-write_id3v1", "1"]
        elif dst_ext == "ogg":
            # libvorbis 默认品质 (0-10, 5=中等)
            cmd += ["-q:a", "5"]
        elif dst_ext == "m4a":
            # AAC 品质 (0.1-1.0, 0.5=中等)
            cmd += ["-q:a", "0.5"]

        cmd.append(str(self.dst))

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg conversion failed (exit {result.returncode}):\n"
                f"{result.stderr[-500:]}"
            )

    @staticmethod
    def _codec_for(ext: str) -> str:
        """返回与目标格式匹配的推荐音频编码器。"""
        return {
            "mp3": "libmp3lame",
            "ogg": "libvorbis",
            "m4a": "aac",
            "wma": "wmav2",
            "flac": "flac",
            "wav": "pcm_s16le",
        }.get(ext, "copy")


CONVERTERS.append(AudioConverter)
