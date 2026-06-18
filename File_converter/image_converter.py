from pathlib import Path
from PIL import Image
from base_converter import BaseConverter, CONVERTERS

class ImageConverter(BaseConverter):
    SUPPORT_EXT = ("jpg", "jpeg", "png", "bmp", "gif", "tiff", "webp")
    TARGET_EXT  = SUPPORT_EXT

    def convert(self) -> None:
        with Image.open(self.src) as im:
            im.save(self.dst)

CONVERTERS.append(ImageConverter)