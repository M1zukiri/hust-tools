# 创建时间：2026-08-11 09:38:48
"""bilidown CLI 入口：B 站为主的视频/音频下载工具。"""
__version__ = "1.1.0"
import argparse
import os
import re
import sys

from bilibili_extra import (extract_bvid, fetch_cid, fetch_cover,
                            fetch_danmaku, is_bilibili_url)
from downloader import build_opts, download, extract_info, prepare_paths
from bilibili_login import COOKIE_FILE, load_cookie_file, login as run_login


def parse_args(argv=None):
    """解析命令行参数。"""
    p = argparse.ArgumentParser(
        prog="bilidown",
        description="bilidown：视频/音频下载工具（B 站为主，兼容多站）")
    p.add_argument("url", nargs="?", help="视频链接（B 站或其他 yt-dlp 支持网站）")
    p.add_argument("--audio", nargs="?", const="m4a", choices=["mp3", "m4a"],
                   metavar="mp3|m4a",
                   help="只下载音频；缺省取原生 m4a（无需 ffmpeg），指定 mp3 需 ffmpeg 转码")
    p.add_argument("--quality", type=str,
                   choices=["360", "480", "720", "1080", "1080p60", "2160"], default="1080",
                   help="视频清晰度（默认 1080；1080p60/2160 需登录）")
    p.add_argument("--p", metavar="SPEC", help="选择分 P（如 1-3,5，仅合集/多 P）")
    p.add_argument("--danmaku", action="store_true", help="同时下载弹幕 xml（仅 B 站）")
    p.add_argument("--cover", action="store_true", help="同时下载封面")
    p.add_argument("--cookies", metavar="FILE", help="cookie 文件（大会员内容）")
    p.add_argument("--login", nargs="?", const="auto",
                   choices=["auto", "file", "browser", "scan", "web"], metavar="方式",
                   help="登录 B 站并保存 cookie（默认 auto 自动按序：已存 cookie→浏览器→扫码→打开登录页）")
    p.add_argument("-o", "--out", default="downloads", help="输出目录（默认 downloads）")
    p.add_argument("--format", dest="format_expr", metavar="FMT",
                   help="高级：透传 yt-dlp format 表达式")
    return p.parse_args(argv)


def parse_page_spec(text, total):
    """校验并规范化分 P 选择字符串；空串返回 None（全部）。

    支持 '1-3,5' 形式；自动排序去重；超范围或非法字符抛 ValueError。
    """
    text = (text or "").strip()
    if not text:
        return None
    if not re.fullmatch(r"[\d,\-\s]+", text):
        raise ValueError(f"无效的分 P 选择：{text!r}（示例：1-3,5）")
    pages = []
    for part in text.split(","):
        part = part.strip()
        if "-" in part:
            a, b = (int(x) for x in part.split("-", 1))
            if a > b:
                a, b = b, a
            pages.extend(range(a, b + 1))
        else:
            pages.append(int(part))
    for n in pages:
        if n < 1 or n > total:
            raise ValueError(f"分 P 编号 {n} 超出范围（共 {total} 个分 P）")
    return ",".join(str(n) for n in sorted(set(pages)))


def selected_indexes(spec, total):
    """选中分 P 的 0 基索引集合；spec 为 None 时返回全部。"""
    if not spec:
        return set(range(total))
    idx = set()
    for part in spec.split(","):
        if "-" in part:
            a, b = (int(x) for x in part.split("-", 1))
            idx.update(range(a, b + 1))
        else:
            idx.add(int(part))
    return {i - 1 for i in idx}


def choose_pages(entries):
    """交互式列出分 P 并让用户选择；返回选择字符串或空串（全部）。"""
    print(f"\n该视频共 {len(entries)} 个分 P：")
    for i, e in enumerate(entries, 1):
        title = e.get("title", "未知标题")
        dur = e.get("duration")
        dur_s = f"{int(dur // 60)}:{int(dur % 60):02d}" if dur else "?"
        print(f"  {i:>3}. {title}（{dur_s}）")
    return input("\n选择要下载的分 P（如 1-3,5，回车下载全部）：").strip()


def fetch_extras(info, opts, spec, want_cover, want_danmaku, bili, url):
    """按选中分 P 下载封面/弹幕，返回成功数量。

    yt-dlp 单视频 info 不含 cid 时，通过 B 站 view API 回退获取。
    """
    entries = info.get("entries") or [info]
    total = len(entries)
    sel = selected_indexes(spec, total)
    try:
        paths = prepare_paths(info, opts)
    except Exception:
        paths = [""] * total
    video_id = extract_bvid(url) if bili else None
    count = 0
    for i, e in enumerate(entries):
        if i not in sel:
            continue
        stem, _ = os.path.splitext(paths[i])
        if want_cover and e.get("thumbnail"):
            fetch_cover(e["thumbnail"], stem + ".cover.jpg")
            count += 1
        if want_danmaku and bili:
            cid = e.get("cid")
            if not cid and video_id:
                try:
                    cid = fetch_cid(video_id, i)
                except Exception as ex:
                    print(f"[警告] 获取弹幕 cid 失败：{ex}")
                    cid = None
            if cid:
                fetch_danmaku(cid, stem + ".danmaku.xml")
                count += 1
    return count


def main(argv=None):
    """CLI 入口；返回进程退出码。"""
    args = parse_args(argv)
    if args.url is None and args.login is None:
        print("[错误] 缺少视频链接（或使用 --login 登录）")
        print("用法：python bilidown.py <URL> [选项]  |  python bilidown.py --login")
        return 2
    bili = is_bilibili_url(args.url) if args.url else False
    os.makedirs(args.out, exist_ok=True)
    if args.login is not None:
        mode = None if args.login == "auto" else args.login
        try:
            path = run_login(mode)
        except Exception as e:
            print(f"[错误] 登录失败：{e}")
            return 1
        if path:
            print(f"[完成] 登录成功，cookie 已保存：{path}")
        return 0

    cookies = args.cookies
    if not cookies and os.path.exists(COOKIE_FILE):
        if load_cookie_file():
            cookies = COOKIE_FILE
        else:
            print("[提示] 已保存的 cookie 已失效，可运行 bilidown --login 更新")

    extract_opts = {"quiet": True}
    if cookies:
        extract_opts["cookiefile"] = cookies
    try:
        info = extract_info(args.url, extract_opts)
    except Exception as e:
        print(f"[错误] 无法解析链接：{e}")
        return 1

    entries = info.get("entries") or [info]
    is_multi = len(entries) > 1

    spec = None
    if is_multi:
        if args.p:
            try:
                spec = parse_page_spec(args.p, len(entries))
            except ValueError as e:
                print(f"[错误] {e}")
                return 1
        else:
            choice = choose_pages(entries)
            try:
                spec = parse_page_spec(choice, len(entries))
            except ValueError as e:
                print(f"[错误] {e}")
                return 1

    opts = build_opts(
        out_dir=args.out,
        quality=args.quality,
        audio_codec=args.audio,
        cookies=cookies,
        format_expr=args.format_expr,
        playlist_items=spec,
        multi=is_multi,
    )
    if not download(args.url, opts):
        return 1

    if args.cover or args.danmaku:
        n = fetch_extras(info, opts, spec, args.cover, args.danmaku, bili, args.url)
        print(f"[完成] 已下载 {n} 个附件（封面/弹幕）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
