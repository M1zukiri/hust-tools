"""
File2MD 基础使用示例
展示如何使用File2MD进行文件转换
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from file2md import File2MD, convert_file


def example_single_file():
    """示例1: 转换单个文件"""
    print("=" * 60)
    print("示例1: 转换单个文件")
    print("=" * 60)
    
    converter = File2MD()
    
    # 假设有一个test.docx文件
    test_file = "test.docx"
    
    # 检查文件是否存在
    if not Path(test_file).exists():
        print(f"注意: {test_file} 不存在，跳过此示例")
        return
    
    result = converter.convert(test_file)
    
    if result.success:
        print(f"✓ 转换成功!")
        print(f"  源格式: {result.source_format}")
        print(f"  内容长度: {len(result.content)} 字符")
        print(f"  内容预览:\n{result.content[:500]}...")
    else:
        print(f"✗ 转换失败: {result.errors}")


def example_with_options():
    """示例2: 使用选项转换"""
    print("\n" + "=" * 60)
    print("示例2: 使用选项转换")
    print("=" * 60)
    
    # 创建带配置的转换器
    config = {
        'pptx': {
            'include_slide_numbers': True,
            'include_notes': False
        },
        'xlsx': {
            'max_rows': 100,
            'max_cols': 10
        },
        'pdf': {
            'extract_tables': True,
            'page_range': (1, 5)  # 只转换前5页
        }
    }
    
    converter = File2MD(config)
    
    # 转换文件时使用额外选项
    test_file = "presentation.pptx"
    
    if not Path(test_file).exists():
        print(f"注意: {test_file} 不存在，跳过此示例")
        return
    
    result = converter.convert(
        test_file,
        include_slide_numbers=True,
        output_path="output.md"  # 保存到文件
    )
    
    if result.success:
        print(f"✓ 转换成功并保存!")
    else:
        print(f"✗ 转换失败: {result.errors}")


def example_batch_conversion():
    """示例3: 批量转换"""
    print("\n" + "=" * 60)
    print("示例3: 批量转换")
    print("=" * 60)
    
    converter = File2MD()
    
    # 文件列表
    files = ["doc1.docx", "doc2.pdf", "doc3.pptx"]
    
    # 过滤存在的文件
    existing_files = [f for f in files if Path(f).exists()]
    
    if not existing_files:
        print("注意: 没有可用的测试文件，跳过此示例")
        return
    
    results = converter.convert_batch(
        existing_files,
        output_dir="./converted",
        preserve_filenames=True
    )
    
    # 统计结果
    success = sum(1 for r in results if r.success)
    failed = len(results) - success
    
    print(f"批量转换完成: 成功 {success}, 失败 {failed}")
    
    for result in results:
        filename = result.metadata.get('filename', 'unknown')
        if result.success:
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename}: {result.errors}")


def example_directory_conversion():
    """示例4: 目录转换"""
    print("\n" + "=" * 60)
    print("示例4: 目录转换")
    print("=" * 60)
    
    converter = File2MD()
    
    test_dir = "./documents"
    
    if not Path(test_dir).exists():
        print(f"注意: {test_dir} 不存在，跳过此示例")
        return
    
    results = converter.convert_directory(
        input_dir=test_dir,
        output_dir="./markdown_output",
        pattern="*.docx",  # 只转换DOCX文件
        recursive=True     # 递归子目录
    )
    
    print(f"目录转换完成，共处理 {len(results)} 个文件")


def example_check_support():
    """示例5: 检查支持的格式"""
    print("\n" + "=" * 60)
    print("示例5: 检查支持的格式")
    print("=" * 60)
    
    converter = File2MD()
    
    # 获取支持的格式
    formats = converter.get_supported_formats()
    print(f"支持的文件格式 ({len(formats)} 种):")
    print(f"  {', '.join(sorted(formats))}")
    
    # 检查特定文件
    test_files = ["document.docx", "report.pdf", "data.xlsx", "unknown.xyz"]
    
    print("\n文件支持检查:")
    for f in test_files:
        is_supported = converter.is_supported(f)
        status = "✓ 支持" if is_supported else "✗ 不支持"
        print(f"  {f}: {status}")


def example_quick_convert():
    """示例6: 使用便捷函数"""
    print("\n" + "=" * 60)
    print("示例6: 使用便捷函数")
    print("=" * 60)
    
    from file2md import convert_file, convert_batch, get_supported_formats
    
    # 快速转换单个文件
    test_file = "readme.md"
    
    if Path(test_file).exists():
        result = convert_file(test_file)
        print(f"快速转换结果: {'成功' if result.success else '失败'}")
    else:
        print(f"注意: {test_file} 不存在，跳过")
    
    # 获取支持的格式
    formats = get_supported_formats()
    print(f"\n支持 {len(formats)} 种格式")


def example_error_handling():
    """示例7: 错误处理"""
    print("\n" + "=" * 60)
    print("示例7: 错误处理")
    print("=" * 60)
    
    converter = File2MD()
    
    # 测试不存在的文件
    result = converter.convert("nonexistent.docx")
    print(f"不存在的文件: {result.status.name}")
    print(f"  错误: {result.errors}")
    
    # 测试不支持的格式
    result = converter.convert("unknown.xyz")
    print(f"\n不支持的格式: {result.status.name}")
    print(f"  错误: {result.errors}")


def main():
    """主函数"""
    print("File2MD 使用示例")
    print("=" * 60)
    
    # 运行所有示例
    example_single_file()
    example_with_options()
    example_batch_conversion()
    example_directory_conversion()
    example_check_support()
    example_quick_convert()
    example_error_handling()
    
    print("\n" + "=" * 60)
    print("所有示例运行完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
