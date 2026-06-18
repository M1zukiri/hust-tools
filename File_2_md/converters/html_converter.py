"""
HTML 转 Markdown 转换器
使用 html2text 或 BeautifulSoup
"""

from pathlib import Path
from typing import Optional, Dict, Any
import re

from converter_base import BaseConverter, ConversionResult, ConversionStatus


class HtmlConverter(BaseConverter):
    """HTML转Markdown转换器"""
    
    supported_extensions = ['html', 'htm']
    supported_mime_types = ['text/html', 'application/xhtml+xml']
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.ignore_links = config.get('ignore_links', False) if config else False
        self.ignore_images = config.get('ignore_images', True) if config else True
        self.body_width = config.get('body_width', 0) if config else 0  # 0表示不限制
    
    def convert(self, file_path: Path, **options) -> ConversionResult:
        """
        将HTML文件转换为Markdown
        
        Args:
            file_path: HTML文件路径
            **options: 额外选项
                - ignore_links: 是否忽略链接
                - ignore_images: 是否忽略图片
                - body_width: 文本宽度限制
                - backend: 指定解析后端 ('html2text', 'beautifulsoup')
                
        Returns:
            ConversionResult: 转换结果
        """
        if not self.validate_file(file_path):
            return self._create_error_result(file_path, "文件验证失败", "html")
        
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
        
        return self._create_error_result(
            file_path,
            f"所有HTML解析后端都失败: {'; '.join(errors)}",
            "html"
        )
    
    def _get_backends(self, preferred: str) -> list:
        """
        获取要尝试的后端列表
        
        Args:
            preferred: 首选后端
            
        Returns:
            list: (名称, 函数)列表
        """
        backends = {
            'html2text': self._convert_with_html2text,
            'beautifulsoup': self._convert_with_beautifulsoup,
        }
        
        if preferred == 'auto':
            return [
                ('html2text', backends['html2text']),
                ('beautifulsoup', backends['beautifulsoup']),
            ]
        elif preferred in backends:
            return [(preferred, backends[preferred])]
        else:
            return list(backends.items())
    
    def _convert_with_html2text(self, file_path: Path, **options) -> ConversionResult:
        """
        使用html2text转换HTML
        
        Args:
            file_path: HTML文件路径
            **options: 额外选项
            
        Returns:
            ConversionResult: 转换结果
        """
        try:
            import html2text
        except ImportError:
            raise ImportError("缺少依赖: html2text。请运行: pip install html2text")
        
        try:
            html_content = file_path.read_text(encoding='utf-8', errors='replace')
            
            # 配置html2text
            h = html2text.HTML2Text()
            h.ignore_links = options.get('ignore_links', self.ignore_links)
            h.ignore_images = options.get('ignore_images', self.ignore_images)
            h.body_width = options.get('body_width', self.body_width)
            h.escape_snob = True
            
            md_content = h.handle(html_content)
            
            # 清理内容
            md_content = self._clean_markdown(md_content)
            
            metadata = self.extract_metadata(file_path)
            
            return ConversionResult(
                content=md_content,
                status=ConversionStatus.SUCCESS,
                source_format='html',
                metadata=metadata,
                errors=[]
            )
            
        except Exception as e:
            raise e
    
    def _convert_with_beautifulsoup(self, file_path: Path, **options) -> ConversionResult:
        """
        使用BeautifulSoup转换HTML
        
        Args:
            file_path: HTML文件路径
            **options: 额外选项
            
        Returns:
            ConversionResult: 转换结果
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("缺少依赖: beautifulsoup4。请运行: pip install beautifulsoup4")
        
        try:
            html_content = file_path.read_text(encoding='utf-8', errors='replace')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除script和style标签
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 转换为Markdown
            md_content = self._soup_to_markdown(soup, **options)
            
            # 清理内容
            md_content = self._clean_markdown(md_content)
            
            metadata = self.extract_metadata(file_path)
            
            return ConversionResult(
                content=md_content,
                status=ConversionStatus.SUCCESS,
                source_format='html',
                metadata=metadata,
                errors=[]
            )
            
        except Exception as e:
            raise e
    
    def _soup_to_markdown(self, soup, **options) -> str:
        """
        将BeautifulSoup对象转换为Markdown
        
        Args:
            soup: BeautifulSoup对象
            **options: 额外选项
            
        Returns:
            str: Markdown内容
        """
        md_parts = []
        
        # 处理标题
        for i in range(1, 7):
            for header in soup.find_all(f'h{i}'):
                text = header.get_text(strip=True)
                if text:
                    header.replace_with(f"{'#' * i} {text}\n\n")
        
        # 处理段落
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text:
                p.replace_with(f"{text}\n\n")
        
        # 处理列表
        for ul in soup.find_all('ul'):
            items = []
            for li in ul.find_all('li'):
                text = li.get_text(strip=True)
                if text:
                    items.append(f"- {text}")
            if items:
                ul.replace_with('\n'.join(items) + '\n\n')
        
        for ol in soup.find_all('ol'):
            items = []
            for idx, li in enumerate(ol.find_all('li'), 1):
                text = li.get_text(strip=True)
                if text:
                    items.append(f"{idx}. {text}")
            if items:
                ol.replace_with('\n'.join(items) + '\n\n')
        
        # 处理链接
        if not options.get('ignore_links', self.ignore_links):
            for a in soup.find_all('a'):
                href = a.get('href', '')
                text = a.get_text(strip=True)
                if text and href:
                    a.replace_with(f"[{text}]({href})")
        
        # 处理代码
        for code in soup.find_all('code'):
            text = code.get_text(strip=True)
            if text:
                code.replace_with(f"`{text}`")
        
        for pre in soup.find_all('pre'):
            text = pre.get_text(strip=True)
            if text:
                pre.replace_with(f"```\n{text}\n```\n\n")
        
        # 处理强调
        for strong in soup.find_all(['strong', 'b']):
            text = strong.get_text(strip=True)
            if text:
                strong.replace_with(f"**{text}**")
        
        for em in soup.find_all(['em', 'i']):
            text = em.get_text(strip=True)
            if text:
                em.replace_with(f"*{text}*")
        
        # 处理表格
        for table in soup.find_all('table'):
            md_table = self._table_to_markdown(table)
            if md_table:
                table.replace_with(md_table + '\n\n')
        
        # 获取剩余文本
        text = soup.get_text()
        
        return text
    
    def _table_to_markdown(self, table) -> str:
        """
        将HTML表格转换为Markdown
        
        Args:
            table: HTML表格元素
            
        Returns:
            str: Markdown表格
        """
        from bs4 import BeautifulSoup
        
        rows = table.find_all('tr')
        if not rows:
            return ""
        
        md_lines = []
        
        # 处理表头
        header_row = rows[0]
        headers = header_row.find_all(['th', 'td'])
        header_texts = [cell.get_text(strip=True) for cell in headers]
        md_lines.append('| ' + ' | '.join(header_texts) + ' |')
        md_lines.append('|' + '|'.join(['---' for _ in header_texts]) + '|')
        
        # 处理数据行
        for row in rows[1:]:
            cells = row.find_all(['th', 'td'])
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            # 确保列数一致
            while len(cell_texts) < len(header_texts):
                cell_texts.append("")
            cell_texts = cell_texts[:len(header_texts)]
            
            md_lines.append('| ' + ' | '.join(cell_texts) + ' |')
        
        return '\n'.join(md_lines)
    
    def _clean_markdown(self, content: str) -> str:
        """
        清理Markdown内容
        
        Args:
            content: 原始内容
            
        Returns:
            str: 清理后的内容
        """
        # 移除多余的空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 移除行首行尾空白
        lines = [line.strip() for line in content.split('\n')]
        
        return '\n'.join(lines)
