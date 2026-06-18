"""
PDF 转 Markdown 转换器
支持多种PDF解析方式
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import re

from converter_base import BaseConverter, ConversionResult, ConversionStatus


class PdfConverter(BaseConverter):
    """PDF文档转Markdown转换器"""
    
    supported_extensions = ['pdf']
    supported_mime_types = ['application/pdf']
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.extract_tables = config.get('extract_tables', True) if config else True
        self.preserve_layout = config.get('preserve_layout', True) if config else True
        self.page_range = config.get('page_range', None) if config else None
    
    def convert(self, file_path: Path, **options) -> ConversionResult:
        """
        将PDF文件转换为Markdown
        
        Args:
            file_path: PDF文件路径
            **options: 额外选项
                - extract_tables: 是否提取表格
                - preserve_layout: 是否保留布局
                - page_range: 页码范围 (start, end)
                - backend: 指定解析后端 ('pdfplumber', 'pymupdf', 'pypdf')
                
        Returns:
            ConversionResult: 转换结果
        """
        if not self.validate_file(file_path):
            return self._create_error_result(file_path, "文件验证失败", "pdf")
        
        backend = options.get('backend', 'auto')
        
        # 尝试不同的后端
        backends_to_try = self._get_backends(backend)
        
        errors = []
        for backend_name, backend_func in backends_to_try:
            try:
                result = backend_func(file_path, **options)
                if result.status == ConversionStatus.SUCCESS:
                    return result
            except Exception as e:
                errors.append(f"{backend_name}: {str(e)}")
                continue
        
        # 所有后端都失败
        return self._create_error_result(
            file_path,
            f"所有PDF解析后端都失败: {'; '.join(errors)}",
            "pdf"
        )
    
    def _get_backends(self, preferred: str) -> List[tuple]:
        """
        获取要尝试的后端列表
        
        Args:
            preferred: 首选后端
            
        Returns:
            List[tuple]: (名称, 函数)列表
        """
        backends = {
            'pdfplumber': self._convert_with_pdfplumber,
            'pymupdf': self._convert_with_pymupdf,
            'pypdf': self._convert_with_pypdf,
        }
        
        if preferred == 'auto':
            # 按优先级排序
            return [
                ('pdfplumber', backends['pdfplumber']),
                ('pymupdf', backends['pymupdf']),
                ('pypdf', backends['pypdf']),
            ]
        elif preferred in backends:
            return [(preferred, backends[preferred])]
        else:
            return list(backends.items())
    
    def _convert_with_pdfplumber(self, file_path: Path, **options) -> ConversionResult:
        """
        使用pdfplumber转换PDF
        
        Args:
            file_path: PDF文件路径
            **options: 额外选项
            
        Returns:
            ConversionResult: 转换结果
        """
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("缺少依赖: pdfplumber。请运行: pip install pdfplumber")
        
        md_parts = []
        errors = []
        
        with pdfplumber.open(str(file_path)) as pdf:
            page_range = options.get('page_range', self.page_range)
            
            if page_range:
                start, end = page_range
                pages = pdf.pages[start-1:end]
            else:
                pages = pdf.pages
            
            for page_num, page in enumerate(pages, 1):
                try:
                    page_md = self._extract_page_with_pdfplumber(
                        page, 
                        extract_tables=options.get('extract_tables', self.extract_tables)
                    )
                    if page_md.strip():
                        md_parts.append(f"## 第 {page_num} 页\n\n{page_md}")
                except Exception as e:
                    errors.append(f"第{page_num}页: {str(e)}")
        
        metadata = self.extract_metadata(file_path)
        metadata['page_count'] = len(pages) if 'pages' in locals() else 0
        
        status = ConversionStatus.SUCCESS if md_parts else ConversionStatus.FAILED
        if errors and md_parts:
            status = ConversionStatus.PARTIAL
        
        return ConversionResult(
            content='\n\n---\n\n'.join(md_parts),
            status=status,
            source_format='pdf',
            metadata=metadata,
            errors=errors
        )
    
    def _extract_page_with_pdfplumber(self, page, extract_tables: bool = True) -> str:
        """
        使用pdfplumber提取页面内容
        
        Args:
            page: pdfplumber页面对象
            extract_tables: 是否提取表格
            
        Returns:
            str: Markdown内容
        """
        md_parts = []
        
        # 提取文本
        text = page.extract_text()
        if text:
            md_parts.append(text)
        
        # 提取表格
        if extract_tables:
            tables = page.extract_tables()
            for table in tables:
                if table:
                    md_table = self._table_to_markdown(table)
                    if md_table:
                        md_parts.append(md_table)
        
        return '\n\n'.join(md_parts)
    
    def _convert_with_pymupdf(self, file_path: Path, **options) -> ConversionResult:
        """
        使用PyMuPDF (fitz)转换PDF
        
        Args:
            file_path: PDF文件路径
            **options: 额外选项
            
        Returns:
            ConversionResult: 转换结果
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("缺少依赖: PyMuPDF。请运行: pip install PyMuPDF")
        
        md_parts = []
        errors = []
        
        doc = fitz.open(str(file_path))
        
        page_range = options.get('page_range', self.page_range)
        if page_range:
            start, end = page_range
            page_indices = range(start-1, min(end, len(doc)))
        else:
            page_indices = range(len(doc))
        
        for page_num in page_indices:
            try:
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    md_parts.append(f"## 第 {page_num + 1} 页\n\n{text}")
            except Exception as e:
                errors.append(f"第{page_num + 1}页: {str(e)}")
        
        doc.close()
        
        metadata = self.extract_metadata(file_path)
        metadata['page_count'] = len(page_indices)
        
        status = ConversionStatus.SUCCESS if md_parts else ConversionStatus.FAILED
        
        return ConversionResult(
            content='\n\n---\n\n'.join(md_parts),
            status=status,
            source_format='pdf',
            metadata=metadata,
            errors=errors
        )
    
    def _convert_with_pypdf(self, file_path: Path, **options) -> ConversionResult:
        """
        使用pypdf转换PDF
        
        Args:
            file_path: PDF文件路径
            **options: 额外选项
            
        Returns:
            ConversionResult: 转换结果
        """
        try:
            from pypdf import PdfReader
        except ImportError:
            try:
                from PyPDF2 import PdfReader
            except ImportError:
                raise ImportError("缺少依赖: pypdf 或 PyPDF2。请运行: pip install pypdf")
        
        md_parts = []
        errors = []
        
        reader = PdfReader(str(file_path))
        
        page_range = options.get('page_range', self.page_range)
        if page_range:
            start, end = page_range
            pages = reader.pages[start-1:end]
        else:
            pages = reader.pages
        
        for page_num, page in enumerate(pages, 1):
            try:
                text = page.extract_text()
                if text and text.strip():
                    md_parts.append(f"## 第 {page_num} 页\n\n{text}")
            except Exception as e:
                errors.append(f"第{page_num}页: {str(e)}")
        
        metadata = self.extract_metadata(file_path)
        metadata['page_count'] = len(reader.pages)
        
        status = ConversionStatus.SUCCESS if md_parts else ConversionStatus.FAILED
        
        return ConversionResult(
            content='\n\n---\n\n'.join(md_parts),
            status=status,
            source_format='pdf',
            metadata=metadata,
            errors=errors
        )
    
    def _table_to_markdown(self, table: List[List]) -> str:
        """
        将表格转换为Markdown
        
        Args:
            table: 表格数据
            
        Returns:
            str: Markdown表格
        """
        if not table or not table[0]:
            return ""
        
        md_lines = []
        
        # 表头
        header = [str(cell) if cell is not None else "" for cell in table[0]]
        md_lines.append('| ' + ' | '.join(header) + ' |')
        md_lines.append('|' + '|'.join(['---' for _ in header]) + '|')
        
        # 数据行
        for row in table[1:]:
            cells = [str(cell) if cell is not None else "" for cell in row]
            # 确保列数一致
            while len(cells) < len(header):
                cells.append("")
            cells = cells[:len(header)]
            
            # 转义管道符
            cells = [c.replace('|', '\\|') for c in cells]
            
            md_lines.append('| ' + ' | '.join(cells) + ' |')
        
        return '\n'.join(md_lines)
