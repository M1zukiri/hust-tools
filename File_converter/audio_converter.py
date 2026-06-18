import shutil
from pathlib import Path
from pydub import AudioSegment
from base_converter import BaseConverter, CONVERTERS

# 需要系统级 ffmpeg
if shutil.which("ffmpeg") is None:
    raise RuntimeError("ffmpeg not found in PATH")

class AudioConverter(BaseConverter):
    SUPPORT_EXT = ("mp3", "wav", "ogg", "flac", "m4a", "wma")
    TARGET_EXT  = SUPPORT_EXT

    def convert(self) -> None:
        sound = AudioSegment.from_file(self.src)
        fmt = self.dst.suffix.lower()[1:]
        sound.export(self.dst, format=fmt)

CONVERTERS.append(AudioConverter)