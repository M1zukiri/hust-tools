"""
File2MD - 自适应文件转Markdown转换器
主模块，提供统一的转换接口
"""

from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import logging

from converter_base import (
    BaseConverter, 
    ConversionResult, 
    ConversionStatus,
    ConverterRegistry,
    get_file_type
)

# 导入所有具体转换器
from converters import (
    DocxConverter,
    PptxConverter,
    XlsxConverter,
    PdfConverter,
    TextConverter,
    HtmlConverter,
    ImageConverter,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class File2MD:
    """
    自适应文件转Markdown转换器
    
    自动检测文件类型并选择合适的转换器
    
    示例:
        >>> converter = File2MD()
        >>> result = converter.convert('document.docx')
        >>> print(result.content)
        
        >>> # 批量转换
        >>> results = converter.convert_batch(['file1.pdf', 'file2.pptx'])
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化File2MD转换器
        
        Args:
            config: 全局配置字典，可包含各转换器的配置
                例如: {
                    'docx': {'preserve_images': True},
                    'pdf': {'extract_tables': True},
                    ...
                }
        """
        self.config = config or {}
        self.registry = ConverterRegistry()
        self._register_default_converters()
    
    def _register_default_converters(self) -> None:
        """注册默认的转换器"""
        # 获取各转换器的配置
        docx_config = self.config.get('docx', {})
        pptx_config = self.config.get('pptx', {})
        xlsx_config = self.config.get('xlsx', {})
        pdf_config = self.config.get('pdf', {})
        text_config = self.config.get('text', {})
        html_config = self.config.get('html', {})
        image_config = self.config.get('image', {})
        
        # 注册转换器
        self.registry.register(DocxConverter(docx_config))
        self.registry.register(PptxConverter(pptx_config))
        self.registry.register(XlsxConverter(xlsx_config))
        self.registry.register(PdfConverter(pdf_config))
        self.registry.register(TextConverter(text_config))
        self.registry.register(HtmlConverter(html_config))
        self.registry.register(ImageConverter(image_config))
        
        logger.info(f"已注册 {len(self.registry.list_converters())} 个转换器")
    
    def convert(
        self, 
        file_path: Union[str, Path], 
        **options
    ) -> ConversionResult:
        """
        转换单个文件为Markdown
        
        Args:
            file_path: 文件路径
            **options: 转换选项，会传递给具体的转换器
                - output_path: 可选的输出文件路径
                - fallback_to_text: 是否回退到文本转换（默认True）
                
        Returns:
            ConversionResult: 转换结果
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return ConversionResult(
                content="",
                status=ConversionStatus.FAILED,
                source_format="unknown",
                metadata={'file_path': str(file_path)},
                errors=[f"文件不存在: {file_path}"]
            )
        
        # 获取合适的转换器
        converter = self.registry.get_converter(file_path)
        
        if converter is None:
            # 尝试文本转换作为回退
            if options.get('fallback_to_text', True):
                logger.warning(f"未找到专用转换器，尝试作为文本文件处理: {file_path}")
                text_converter = TextConverter(self.config.get('text', {}))
                if text_converter.can_convert(file_path):
                    result = text_converter.convert(file_path, **options)
                    if result.success:
                        return result
            
            file_type = get_file_type(file_path)
            return ConversionResult(
                content="",
                status=ConversionStatus.UNSUPPORTED,
                source_format=file_type,
                metadata=self._extract_metadata(file_path),
                errors=[f"不支持的文件类型: {file_type} ({file_path.suffix})"]
            )
        
        # 执行转换
        try:
            result = converter.convert(file_path, **options)
            
            # 如果指定了输出路径，保存结果
            output_path = options.get('output_path')
            if output_path and result.success:
                self._save_result(result, Path(output_path))
            
            return result
            
        except Exception as e:
            logger.error(f"转换过程中发生错误: {e}")
            return ConversionResult(
                content="",
                status=ConversionStatus.FAILED,
                source_format=get_file_type(file_path),
                metadata=self._extract_metadata(file_path),
                errors=[str(e)]
            )
    
    def convert_batch(
        self, 
        file_paths: List[Union[str, Path]], 
        output_dir: Optional[Union[str, Path]] = None,
        **options
    ) -> List[ConversionResult]:
        """
        批量转换文件
        
        Args:
            file_paths: 文件路径列表
            output_dir: 可选的输出目录
            **options: 转换选项
                - preserve_filenames: 是否保留原文件名（默认True）
                
        Returns:
            List[ConversionResult]: 转换结果列表
        """
        results = []
        output_dir = Path(output_dir) if output_dir else None
        
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in file_paths:
            file_path = Path(file_path)
            
            # 确定输出路径
            if output_dir:
                if options.get('preserve_filenames', True):
                    output_name = file_path.stem + '.md'
                else:
                    output_name = f"{file_path.stem}_converted.md"
                output_path = output_dir / output_name
                options['output_path'] = str(output_path)
            
            result = self.convert(file_path, **options)
            results.append(result)
            
            # 记录转换状态
            if result.success:
                logger.info(f"✓ 转换成功: {file_path.name}")
            else:
                logger.warning(f"✗ 转换失败: {file_path.name} - {result.errors}")
        
        return results
    
    def convert_directory(
        self,
        input_dir: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        pattern: str = "*",
        recursive: bool = False,
        **options
    ) -> List[ConversionResult]:
        """
        转换目录中的所有文件
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录（默认与输入目录相同）
            pattern: 文件匹配模式（默认"*"匹配所有）
            recursive: 是否递归子目录
            **options: 转换选项
            
        Returns:
            List[ConversionResult]: 转换结果列表
        """
        input_dir = Path(input_dir)
        
        if not input_dir.exists():
            logger.error(f"输入目录不存在: {input_dir}")
            return []
        
        if output_dir is None:
            output_dir = input_dir / "converted"
        else:
            output_dir = Path(output_dir)
        
        # 收集文件
        if recursive:
            files = list(input_dir.rglob(pattern))
        else:
            files = list(input_dir.glob(pattern))
        
        # 过滤出文件（排除目录）
        files = [f for f in files if f.is_file()]
        
        logger.info(f"在 {input_dir} 中找到 {len(files)} 个文件")
        
        return self.convert_batch(files, output_dir, **options)
    
    def get_supported_formats(self) -> List[str]:
        """
        获取支持的文件格式列表
        
        Returns:
            List[str]: 支持的扩展名列表
        """
        return self.registry.get_supported_extensions()
    
    def is_supported(self, file_path: Union[str, Path]) -> bool:
        """
        检查文件是否受支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否支持
        """
        file_path = Path(file_path)
        converter = self.registry.get_converter(file_path)
        return converter is not None
    
    def _save_result(self, result: ConversionResult, output_path: Path) -> None:
        """
        保存转换结果到文件
        
        Args:
            result: 转换结果
            output_path: 输出路径
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result.content, encoding='utf-8')
            logger.info(f"已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
    
    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        提取文件元数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict: 元数据字典
        """
        try:
            stat = file_path.stat()
            return {
                'filename': file_path.name,
                'extension': file_path.suffix.lower(),
                'size_bytes': stat.st_size,
                'modified_time': stat.st_mtime,
            }
        except Exception:
            return {'filename': file_path.name}


# 便捷函数
def convert_file(file_path: Union[str, Path], **options) -> ConversionResult:
    """
    便捷函数：转换单个文件
    
    Args:
        file_path: 文件路径
        **options: 转换选项
        
    Returns:
        ConversionResult: 转换结果
        
    示例:
        >>> result = convert_file('document.docx')
        >>> print(result.content)
    """
    converter = File2MD()
    return converter.convert(file_path, **options)


def convert_batch(
    file_paths: List[Union[str, Path]], 
    output_dir: Optional[Union[str, Path]] = None,
    **options
) -> List[ConversionResult]:
    """
    便捷函数：批量转换文件
    
    Args:
        file_paths: 文件路径列表
        output_dir: 输出目录
        **options: 转换选项
        
    Returns:
        List[ConversionResult]: 转换结果列表
        
    示例:
        >>> results = convert_batch(['file1.pdf', 'file2.docx'], './output')
    """
    converter = File2MD()
    return converter.convert_batch(file_paths, output_dir, **options)


def get_supported_formats() -> List[str]:
    """
    便捷函数：获取支持的文件格式
    
    Returns:
        List[str]: 支持的扩展名列表
    """
    converter = File2MD()
    return converter.get_supported_formats()


# 命令行接口
if __name__ == '__main__':
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description='File2MD - 将各种文件格式转换为Markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s document.docx                    # 转换单个文件
  %(prog)s file1.pdf file2.pptx -o ./output # 批量转换到指定目录
  %(prog)s ./docs -r -o ./markdown          # 递归转换目录
  %(prog)s *.xlsx --max-rows 100            # 限制Excel行数
        '''
    )
    
    parser.add_argument('input', nargs='+', help='输入文件或目录')
    parser.add_argument('-o', '--output', help='输出目录')
    parser.add_argument('-r', '--recursive', action='store_true', help='递归处理子目录')
    parser.add_argument('--max-rows', type=int, help='Excel最大行数限制')
    parser.add_argument('--max-cols', type=int, help='Excel最大列数限制')
    parser.add_argument('--include-notes', action='store_true', help='包含PPT演讲者备注')
    parser.add_argument('--page-range', help='PDF页码范围 (如: 1-10)')
    parser.add_argument('--backend', help='指定转换后端')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 构建选项
    options = {}
    if args.max_rows:
        options['max_rows'] = args.max_rows
    if args.max_cols:
        options['max_cols'] = args.max_cols
    if args.include_notes:
        options['include_notes'] = True
    if args.page_range:
        try:
            start, end = map(int, args.page_range.split('-'))
            options['page_range'] = (start, end)
        except ValueError:
            print(f"错误: 页码范围格式无效: {args.page_range}")
            sys.exit(1)
    if args.backend:
        options['backend'] = args.backend
    
    # 执行转换
    converter = File2MD()
    
    all_results = []
    for input_path in args.input:
        input_path = Path(input_path)
        
        if input_path.is_file():
            result = converter.convert(input_path, **options)
            all_results.append(result)
        elif input_path.is_dir():
            results = converter.convert_directory(
                input_path, 
                args.output, 
                recursive=args.recursive,
                **options
            )
            all_results.extend(results)
        else:
            print(f"错误: 路径不存在: {input_path}")
    
    # 输出统计
    success_count = sum(1 for r in all_results if r.success)
    failed_count = len(all_results) - success_count
    
    print(f"\n转换完成: 成功 {success_count}, 失败 {failed_count}")
    
    # 如果有失败，显示错误
    if failed_count > 0:
        print("\n失败的文件:")
        for result in all_results:
            if not result.success:
                filename = result.metadata.get('filename', 'unknown')
                print(f"  - {filename}: {result.errors}")
