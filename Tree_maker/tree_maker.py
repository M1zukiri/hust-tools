import argparse
from pathlib import Path
from datetime import datetime


def generate_tree(directory, prefix="", depth=-1, current_depth=0):
    """
    递归生成目录树结构的生成器函数。
    """
    # 深度限制判断
    if depth != -1 and current_depth >= depth:
        return

    try:
        # 按名称排序，文件夹排在前面
        contents = sorted(list(directory.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
    except PermissionError:
        yield f"{prefix}└── <Permission Denied>"
        return

    entries_count = len(contents)
    for index, path_obj in enumerate(contents):
        is_last = (index == entries_count - 1)
        connector = "└── " if is_last else "├── "

        line = f"{prefix}{connector}{path_obj.name}"
        yield line

        if path_obj.is_dir():
            extension = "    " if is_last else "│   "
            yield from generate_tree(path_obj, prefix + extension, depth, current_depth + 1)


def main():
    parser = argparse.ArgumentParser(description="生成当前目录的树状结构图并保存。")
    parser.add_argument(
        '-d', '--depth',
        type=int,
        default=-1,
        help="遍历的深度层级。输入 -1 代表不限制深度（默认）。"
    )

    args = parser.parse_args()
    target_depth = args.depth

    root_dir = Path.cwd()

    # --- 核心修改部分：动态生成文件名 ---
    # 1. 获取当前时间，格式为：年月日_时分秒 (例如 20231027_153000)
    # 使用下划线而非冒号，以确保文件名在 Windows 下合法
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 2. 处理深度字符串 (如果是 -1，在文件名中显示为 'all')
    depth_str = "all" if target_depth == -1 else str(target_depth)

    # 3. 组合文件名: 目录名_depth-[深度]_[时间].txt
    output_filename = f"{root_dir.name}_depth-{depth_str}_{timestamp}.txt"
    # ----------------------------------

    print(f"正在分析目录: {root_dir}")
    print(f"限制深度: {'不限制' if target_depth == -1 else target_depth}")
    print("-" * 30)

    tree_lines = [f"{root_dir.name}/"]
    tree_lines.extend(generate_tree(root_dir, depth=target_depth))

    result_text = "\n".join(tree_lines)

    print(result_text)

    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(result_text)
        print("-" * 30)
        # 打印出的文件名将包含所有信息
        print(f"✅ 成功！结构图已保存至: {output_filename}")
    except Exception as e:
        print(f"❌ 保存文件时出错: {e}")


if __name__ == "__main__":
    main()