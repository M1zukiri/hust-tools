from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple

class BaseConverter(ABC):
    SUPPORT_EXT: Tuple[str, ...] = ()   # 可处理的输入后缀
    TARGET_EXT: Tuple[str, ...] = ()    # 可输出的目标后缀

    def __init__(self, src: Path, dst: Path):
        self.src = src
        self.dst = dst

    @abstractmethod
    def convert(self) -> None:
        ...

    @classmethod
    def can_handle(cls, src_ext: str, dst_ext: str) -> bool:
        s, d = src_ext.lower(), dst_ext.lower()
        return s in cls.SUPPORT_EXT and d in cls.TARGET_EXT


# 全局注册表，各模块把子类注册进来
CONVERTERS: List[type[BaseConverter]] = []