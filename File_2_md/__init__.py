"""
File2MD - 自适应文件转Markdown转换器

一个简洁、自适应的Python项目，用于将各种常见文件格式转换为Markdown格式。

基本用法:
    >>> from file2md import File2MD
    >>> converter = File2MD()
    >>> result = converter.convert("document.docx")
    >>> print(result.content)

便捷函数:
    >>> from file2md import convert_file
    >>> result = convert_file("report.pdf")

批量转换:
    >>> from file2md import convert_batch
    >>> results = convert_batch(["file1.docx", "file2.pdf"], output_dir="./output")
"""

__version__ = "1.0.0"
__author__ = "File2MD Team"

from .converter_base import (
    BaseConverter,
    ConversionResult,
    ConversionStatus,
    ConverterRegistry,
    get_file_type,
)

from .file2md import (
    File2MD,
    convert_file,
    convert_batch,
    get_supported_formats,
)

__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    
    # 基础类
    "BaseConverter",
    "ConversionResult",
    "ConversionStatus",
    "ConverterRegistry",
    "get_file_type",
    
    # 主接口
    "File2MD",
    "convert_file",
    "convert_batch",
    "get_supported_formats",
]
