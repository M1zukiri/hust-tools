import shutil
import ffmpeg
from pathlib import Path
from base_converter import BaseConverter, CONVERTERS

if shutil.which("ffmpeg") is None:
    raise RuntimeError("ffmpeg not found in PATH")

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
            # 提取音频
            (
                ffmpeg
                .input(str(self.src))
                .output(str(self.dst), vn=None, acodec="copy")
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