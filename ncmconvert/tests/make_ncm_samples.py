# -*- coding: utf-8 -*-
"""
依据公开的 ncm 文件格式规范构造合法的 .ncm 测试样本（纯黑盒输入构造，
不涉及对被测工具 ncm2music.py 的任何源码阅读）。

格式（公开资料）:
  8B  magic "CTENFDAM"
  2B  跳过
  4B  LE 密钥块长度
  NB  密钥块: 每字节 xor 0x64, AES-128-ECB(core_key) 解密, 去 PKCS7,
      去掉 17 字节前缀 "neteasecloudmusic" -> RC4 变体密钥
  4B  LE 元数据块长度
  NB  元数据块: xor 0x63, 前缀 "163 key(Don't modify):" + base64,
      base64 解码后 AES-128-ECB(meta_key) 解密, 去 PKCS7,
      去掉 6 字节前缀 "music:" -> JSON
  4B  CRC
  5B  间隔
  4B  LE 封面长度
  NB  封面
  ..  音频流: 每字节与 KSA 生成的 box 密钥流异或
"""
import base64
import json
import struct
import zlib

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

CORE_KEY = b"hzHRAmso5kInbaxW"
META_KEY = b"#14ljk_!\\]&0U<'("


def aes_ecb_encrypt(key: bytes, data: bytes) -> bytes:
    pad = 16 - (len(data) % 16)
    data = data + bytes([pad]) * pad
    enc = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    return enc.update(data) + enc.finalize()


def build_box(key: bytes):
    box = list(range(256))
    c = 0
    last = 0
    key_offset = 0
    for i in range(256):
        swap = box[i]
        c = (swap + last + key[key_offset]) & 0xFF
        key_offset += 1
        if key_offset >= len(key):
            key_offset = 0
        box[i] = box[c]
        box[c] = swap
        last = c
    return box


def crypt_audio(key: bytes, data: bytes) -> bytes:
    """加密与解密相同（异或密钥流）。"""
    box = build_box(key)
    out = bytearray(len(data))
    for i in range(len(data)):
        j = (i + 1) & 0xFF
        out[i] = data[i] ^ box[(box[j] + box[(box[j] + j) & 0xFF]) & 0xFF]
    return bytes(out)


def build_ncm(audio: bytes, fmt: str = "flac", rc4key: bytes = b"0123456789abcdef",
              music_name="Test Song", artist="Test Artist",
              cover: bytes = b"", corrupt_crc: bool = False) -> bytes:
    # --- 密钥块 ---
    key_plain = b"neteasecloudmusic" + rc4key
    key_enc = aes_ecb_encrypt(CORE_KEY, key_plain)
    key_block = bytes(b ^ 0x64 for b in key_enc)

    # --- 元数据块 ---
    meta = {
        "musicName": music_name,
        "artist": [[artist, 12345]],
        "album": "Test Album",
        "albumId": 1,
        "albumPicId": 0,
        "albumPic": "",
        "bitrate": 320000,
        "mp3DocId": 0,
        "duration": 180000,
        "mvId": 0,
        "alias": [],
        "transNames": [],
        "format": fmt,
    }
    meta_plain = b"music:" + json.dumps(meta, ensure_ascii=False).encode("utf-8")
    meta_enc = aes_ecb_encrypt(META_KEY, meta_plain)
    meta_block = bytes(b ^ 0x63 for b in b"163 key(Don't modify):" + base64.b64encode(meta_enc))

    audio_enc = crypt_audio(rc4key, audio)

    buf = bytearray()
    buf += b"CTENFDAM"            # magic
    buf += b"\x00\x00"            # 2 字节跳过
    buf += struct.pack("<I", len(key_block))
    buf += key_block
    buf += struct.pack("<I", len(meta_block))
    buf += meta_block
    buf += struct.pack("<I", 0xDEADBEEF if corrupt_crc else zlib.crc32(audio) & 0xFFFFFFFF)
    buf += b"\x00" * 5            # 5 字节间隔
    buf += struct.pack("<I", len(cover))
    buf += cover
    buf += audio_enc
    return bytes(buf)


def pseudo_audio(size: int, header: bytes) -> bytes:
    """确定性伪随机音频内容（便于解密后逐字节比对）。"""
    import random
    rnd = random.Random(20240601)
    return header + bytes(rnd.randrange(256) for _ in range(size - len(header)))


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    # FLAC 样本 ~4MB（开头是合法的 fLaC 魔数）
    flac_audio = pseudo_audio(4 * 1024 * 1024, b"fLaC")
    with open(os.path.join(here, "good_flac.ncm"), "wb") as f:
        f.write(build_ncm(flac_audio, "flac"))
    with open(os.path.join(here, "expected_flac.bin"), "wb") as f:
        f.write(flac_audio)
    # MP3 样本 ~512KB（开头是合法的 ID3 头）
    mp3_audio = pseudo_audio(512 * 1024, b"ID3\x04\x00\x00\x00\x00\x00\x21")
    with open(os.path.join(here, "good_mp3.ncm"), "wb") as f:
        f.write(build_ncm(mp3_audio, "mp3", music_name="MP3 Song"))
    with open(os.path.join(here, "expected_mp3.bin"), "wb") as f:
        f.write(mp3_audio)
    # 0 字节音频的合法 ncm
    with open(os.path.join(here, "zero_audio.ncm"), "wb") as f:
        f.write(build_ncm(b"", "flac", music_name="Zero Audio"))
    # 300 字节音频（跨 256 字节密钥流周期边界）
    small_audio = pseudo_audio(300, b"fLaC")
    with open(os.path.join(here, "small300.ncm"), "wb") as f:
        f.write(build_ncm(small_audio, "flac", music_name="Small300"))
    with open(os.path.join(here, "expected_small300.bin"), "wb") as f:
        f.write(small_audio)
    # 带封面的合法 ncm
    with open(os.path.join(here, "with_cover.ncm"), "wb") as f:
        f.write(build_ncm(small_audio, "flac", music_name="With Cover",
                          cover=b"\x89PNG\r\n\x1a\n" + b"C" * 100))
    print("样本构造完成: good_flac.ncm, good_mp3.ncm, zero_audio.ncm, small300.ncm, with_cover.ncm")
