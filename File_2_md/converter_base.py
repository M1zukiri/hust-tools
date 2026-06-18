"""
文件转Markdown转换器基础模块
定义抽象基类和通用接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Dict, Any, List
import mimetypes
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConversionStatus(Enum):
    """转换状态枚举"""
    SUCCESS = auto()
    FAILED = auto()
    PARTIAL = auto()
    UNSUPPORTED = auto()


@dataclass
class ConversionResult:
    """转换结果数据类"""
    content: str
    status: ConversionStatus
    source_format: str
    metadata: Dict[str, Any]
    errors: List[str]
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def success(self) -> bool:
        return self.status == ConversionStatus.SUCCESS
    
    def __str__(self) -> str:
        preview = self.content[:200] + "..." if len(self.content) > 200 else self.content
        return f"ConversionResult(format={self.source_format}, status={self.status.name}, preview={preview!r})"


class BaseConverter(ABC):
    """
    文件转换器抽象基类
    所有具体转换器都应继承此类
    """
    
    # 支持的文件扩展名列表（小写，不含点）
    supported_extensions: List[str] = []
    
    # 支持的MIME类型列表
    supported_mime_types: List[str] = []
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化转换器
        
        Args:
            config: 可选的配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def convert(self, file_path: Path, **options) -> ConversionResult:
        """
        将文件转换为Markdown
        
        Args:
            file_path: 输入文件路径
            **options: 额外的转换选项
            
        Returns:
            ConversionResult: 转换结果
        """
        pass
    
    def can_convert(self, file_path: Path) -> bool:
        """
        检查是否可以转换指定文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否支持转换
        """
        ext = file_path.suffix.lower().lstrip('.')
        if ext in self.supported_extensions:
            return True
        
        # 尝试MIME类型检测
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and mime_type in self.supported_mime_types:
            return True
        
        return False
    
    def validate_file(self, file_path: Path) -> bool:
        """
        验证文件是否存在且可读
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 验证是否通过
        """
        import os
        
        if not file_path.exists():
            self.logger.error(f"文件不存在: {file_path}")
            return False
        
        if not file_path.is_file():
            self.logger.error(f"路径不是文件: {file_path}")
            return False
        
        if not os.access(str(file_path), os.R_OK):
            self.logger.error(f"文件不可读: {file_path}")
            return False
        
        return True
    
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        提取文件元数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict: 元数据字典
        """
        stat = file_path.stat()
        return {
            'filename': file_path.name,
            'extension': file_path.suffix.lower(),
            'size_bytes': stat.st_size,
            'modified_time': stat.st_mtime,
        }
    
    def _create_error_result(self, file_path: Path, error_msg: str, 
                            source_format: str = "unknown") -> ConversionResult:
        """
        创建错误结果
        
        Args:
            file_path: 文件路径
            error_msg: 错误信息
            source_format: 源格式
            
        Returns:
            ConversionResult: 错误结果
        """
        return ConversionResult(
            content="",
            status=ConversionStatus.FAILED,
            source_format=source_format,
            metadata=self.extract_metadata(file_path),
            errors=[error_msg]
        )


class ConverterRegistry:
    """
    转换器注册表
    管理所有可用的转换器
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._converters: Dict[str, BaseConverter] = {}
            cls._instance._extension_map: Dict[str, BaseConverter] = {}
        return cls._instance
    
    def register(self, converter: BaseConverter) -> None:
        """
        注册转换器
        
        Args:
            converter: 转换器实例
        """
        converter_class = converter.__class__.__name__
        self._converters[converter_class] = converter
        
        # 注册扩展名映射
        for ext in converter.supported_extensions:
            self._extension_map[ext.lower()] = converter
        
        logger.info(f"已注册转换器: {converter_class}")
    
    def unregister(self, converter_class: str) -> None:
        """
        注销转换器
        
        Args:
            converter_class: 转换器类名
        """
        if converter_class in self._converters:
            converter = self._converters[converter_class]
            
            # 移除扩展名映射
            for ext in list(self._extension_map.keys()):
                if self._extension_map[ext] == converter:
                    del self._extension_map[ext]
            
            del self._converters[converter_class]
            logger.info(f"已注销转换器: {converter_class}")
    
    def get_converter(self, file_path: Path) -> Optional[BaseConverter]:
        """
        根据文件路径获取合适的转换器
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[BaseConverter]: 转换器实例或None
        """
        ext = file_path.suffix.lower().lstrip('.')
        
        # 直接扩展名匹配
        if ext in self._extension_map:
            return self._extension_map[ext]
        
        # 尝试让各转换器检查
        for converter in self._converters.values():
            if converter.can_convert(file_path):
                return converter
        
        return None
    
    def get_supported_extensions(self) -> List[str]:
        """
        获取所有支持的扩展名
        
        Returns:
            List[str]: 扩展名列表
        """
        return list(self._extension_map.keys())
    
    def list_converters(self) -> List[str]:
        """
        列出所有已注册的转换器
        
        Returns:
            List[str]: 转换器类名列表
        """
        return list(self._converters.keys())


def get_file_type(file_path: Path) -> str:
    """
    智能检测文件类型
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 检测到的文件类型
    """
    # 首先尝试扩展名
    ext = file_path.suffix.lower().lstrip('.')
    if ext:
        return ext
    
    # 尝试MIME类型
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type:
        return mime_type.split('/')[-1]
    
    # 尝试文件内容检测（魔术数字）
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
            
        # PDF
        if header.startswith(b'%PDF'):
            return 'pdf'
        
        # ZIP (DOCX, PPTX, XLSX都是ZIP格式)
        if header.startswith(b'PK'):
            return 'zip'
        
        # Office旧格式
        if header.startswith(b'\xd0\xcf\x11\xe0'):
            return 'ole'  # DOC, PPT, XLS
            
    except Exception:
        pass
    
    return 'unknown'
