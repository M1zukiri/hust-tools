"""
文本文件转 Markdown 转换器
处理纯文本、代码文件等
"""

from pathlib import Path
from typing import Optional, Dict, Any
import mimetypes

from converter_base import BaseConverter, ConversionResult, ConversionStatus


class TextConverter(BaseConverter):
    """文本文件转Markdown转换器"""
    
    supported_extensions = [
        'txt', 'md', 'markdown',
        'py', 'js', 'java', 'c', 'cpp', 'h', 'hpp', 'cs', 'go', 'rs', 'swift',
        'rb', 'php', 'pl', 'sh', 'bat', 'ps1',
        'html', 'htm', 'xml', 'json', 'yaml', 'yml', 'toml',
        'css', 'scss', 'sass', 'less',
        'sql', 'r', 'm', 'scala', 'kt', 'ts', 'tsx', 'jsx',
        'vue', 'svelte', 'dart', 'lua', 'vim',
    ]
    
    supported_mime_types = [
        'text/plain',
        'text/markdown',
        'text/html',
        'text/xml',
        'text/css',
        'application/json',
        'application/javascript',
        'text/x-python',
        'text/x-java-source',
        'text/x-c',
        'text/x-c++',
    ]
    
    # 代码文件扩展名到语言标识的映射
    CODE_LANGUAGE_MAP = {
        'py': 'python',
        'js': 'javascript',
        'java': 'java',
        'c': 'c',
        'cpp': 'cpp',
        'h': 'c',
        'hpp': 'cpp',
        'cs': 'csharp',
        'go': 'go',
        'rs': 'rust',
        'swift': 'swift',
        'rb': 'ruby',
        'php': 'php',
        'pl': 'perl',
        'sh': 'bash',
        'bat': 'batch',
        'ps1': 'powershell',
        'html': 'html',
        'htm': 'html',
        'xml': 'xml',
        'json': 'json',
        'yaml': 'yaml',
        'yml': 'yaml',
        'toml': 'toml',
        'css': 'css',
        'scss': 'scss',
        'sass': 'sass',
        'less': 'less',
        'sql': 'sql',
        'r': 'r',
        'm': 'matlab',
        'scala': 'scala',
        'kt': 'kotlin',
        'ts': 'typescript',
        'tsx': 'tsx',
        'jsx': 'jsx',
        'vue': 'vue',
        'svelte': 'svelte',
        'dart': 'dart',
        'lua': 'lua',
        'vim': 'vim',
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_size = config.get('max_size', 10 * 1024 * 1024) if config else 10 * 1024 * 1024  # 10MB
        self.detect_encoding = config.get('detect_encoding', True) if config else True
    
    def convert(self, file_path: Path, **options) -> ConversionResult:
        """
        将文本文件转换为Markdown
        
        Args:
            file_path: 文本文件路径
            **options: 额外选项
                - wrap_code: 是否将代码文件包装在代码块中
                - max_size: 最大文件大小限制
                - encoding: 指定编码
                
        Returns:
            ConversionResult: 转换结果
        """
        if not self.validate_file(file_path):
            return self._create_error_result(file_path, "文件验证失败", "text")
        
        # 检查文件大小
        max_size = options.get('max_size', self.max_size)
        file_size = file_path.stat().st_size
        if file_size > max_size:
            return self._create_error_result(
                file_path,
                f"文件过大 ({file_size} bytes)，超过限制 ({max_size} bytes)",
                "text"
            )
        
        try:
            # 检测编码
            encoding = options.get('encoding', None)
            if not encoding and self.detect_encoding:
                encoding = self._detect_encoding(file_path)
            
            if not encoding:
                encoding = 'utf-8'
            
            # 读取文件内容
            content = file_path.read_text(encoding=encoding, errors='replace')
            
            # 处理内容
            md_content = self._process_content(file_path, content, **options)
            
            metadata = self.extract_metadata(file_path)
            metadata['encoding'] = encoding
            metadata['line_count'] = len(content.splitlines())
            
            return ConversionResult(
                content=md_content,
                status=ConversionStatus.SUCCESS,
                source_format='text',
                metadata=metadata,
                errors=[]
            )
            
        except Exception as e:
            self.logger.error(f"转换失败: {e}")
            return self._create_error_result(file_path, str(e), "text")
    
    def _detect_encoding(self, file_path: Path) -> Optional[str]:
        """
        检测文件编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: 检测到的编码或None
        """
        try:
            import chardet
        except ImportError:
            return None
        
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # 读取前10KB
                result = chardet.detect(raw_data)
                return result.get('encoding')
        except Exception:
            return None
    
    def _process_content(self, file_path: Path, content: str, **options) -> str:
        """
        处理文件内容
        
        Args:
            file_path: 文件路径
            content: 原始内容
            **options: 额外选项
            
        Returns:
            str: 处理后的Markdown内容
        """
        ext = file_path.suffix.lower().lstrip('.')
        
        # Markdown文件直接返回
        if ext in ['md', 'markdown']:
            return content
        
        # 代码文件包装在代码块中
        wrap_code = options.get('wrap_code', True)
        if wrap_code and ext in self.CODE_LANGUAGE_MAP:
            language = self.CODE_LANGUAGE_MAP[ext]
            return f"```{language}\n{content}\n```"
        
        # 其他文本文件
        return content
    
    def can_convert(self, file_path: Path) -> bool:
        """
        检查是否可以转换指定文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否支持转换
        """
        # 首先检查扩展名
        ext = file_path.suffix.lower().lstrip('.')
        if ext in self.supported_extensions:
            return True
        
        # 检查MIME类型
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            if mime_type.startswith('text/'):
                return True
            if mime_type in self.supported_mime_types:
                return True
        
        # 尝试读取文件内容检测
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(1024)
                # 检查是否是文本内容
                if b'\x00' not in sample:
                    try:
                        sample.decode('utf-8')
                        return True
                    except UnicodeDecodeError:
                        pass
        except Exception:
            pass
        
        return False
