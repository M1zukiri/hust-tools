import os, struct

path = r'C:\Gal\纸上的魔法使\纸上的魔法使\data.xp3'
with open(path, 'rb') as f:
    data = f.read()

# Search for ALL types of file signatures
sigs = {
    b'\x89PNG\r\n\x1a\n': 'PNG',
    b'OggS': 'OGG',
    b'RIFF': 'WAV/AVI',
    b'\x1aE\xdf\xa3': 'MKV/WebM',
    b'II*\x00': 'TIFF',
    b'MM\x00*': 'TIFF',
    b'GIF8': 'GIF',
    b'BMP': 'BMP (maybe)',
    b'\xff\xfb': 'MP3',
    b'\xff\xf3': 'MP3',
    b'\xff\xf2': 'MP3',
}

print('=== File signatures found ===')
for sig_bytes, sig_name in sigs.items():
    sig_len = len(sig_bytes)
    count = 0
    pos = -1
    positions = []
    while True:
        pos = data.find(sig_bytes, pos + 1)
        if pos < 0 or count >= 5:
            break
        positions.append(pos)
        count += 1
    if count > 0:
        print(f'  {sig_name}: {count} occurrences')
        for p in positions[:5]:
            print(f'    offset {p:>8} (0x{p:x})')

# Look for TJS script files by searching for common patterns
print()
print('=== Searching for script/configuration files ===')
# Look for text strings that might be filenames
# Search for typical KrKr file paths
patterns = [
    b'data/', b'scenario/', b'image/', b'bgimage/', b'fgimage/', 
    b'evimage/', b'bgm/', b'voice/', b'video/', b'font/', b'system/',
    b'sys/', b'patch/', b'arc/', b'others/'
]
for pat in patterns:
    pos = data.find(pat)
    if pos >= 0:
        # Show context
        ctx_start = max(0, pos - 20)
        ctx = data[ctx_start:pos+32]
        # Try to see if there's a readable path
        text_parts = []
        for b in data[pos:pos+80]:
            if 32 <= b < 127:
                text_parts.append(chr(b))
            else:
                break
        path_text = ''.join(text_parts)
        print(f'  Found "{pat.decode()}" at offset {pos}:')
        print(f'    Path: {path_text}')

# Also search for typical KrKr file extensions with better context
print()
print('=== Extended filename search ===')
for ext in [b'.ks', b'.tjs', b'.asd', b'.ksd', b'.kep', b'.cf', b'.sig', b'.ini', b'.tpm', b'.kdt']:
    pos = data.find(ext)
    if pos >= 0:
        # Try to extract readable string before the extension
        start = max(0, pos - 60)
        text = []
        for i in range(start, pos):
            if 32 <= data[i] < 127 or data[i] == ord('/') or data[i] == ord('\\') or data[i] == ord('.'):
                text.append(chr(data[i]))
            elif len(text) > 3:
                # Stop if we hit binary data after getting some text
                break
        text_str = ''.join(text[-10:])  # Last 10 chars before extension
        if len(text_str) > 1:
            print(f'  "{ext.decode()}" at offset {pos}: ...{text_str}{ext.decode()}')

# Check the actual structure of embedded files
print()
print('=== Structure around first 4 JPEGs ===')
jpeg_starts = []
pos = -1
while True:
    pos = data.find(b'\xff\xd8', pos + 1)
    if pos < 0 or len(jpeg_starts) >= 10:
        break
    jpeg_starts.append(pos)

for i in range(min(6, len(jpeg_starts)-1)):
    s1 = jpeg_starts[i]
    s2 = jpeg_starts[i+1]
    gap = s2 - s1
    print(f'JPEG {i}: offset {s1} -> JPEG {i+1}: offset {s2} (gap: {gap})')
    # Show what's right before this JPEG
    if i == 0:
        print(f'  Before first JPEG: bytes 0-39 = header + metadata')
    else:
        before = data[max(0,s1-32):s1]
        hex_before = ' '.join(f'{b:02X}' for b in before)
        ascii_before = ''.join(chr(b) if 32 <= b < 127 else '.' for b in before)
        print(f'  32 bytes before: {hex_before}  {ascii_before}')
    
    if gap < 500:
        # Close JPEGs - show the data between them
        between = data[s1:s2]
        print(f'  Small gap ({gap} bytes):')
        for j in range(0, min(64, len(between)), 16):
            hex_part = ' '.join(f'{between[j+k]:02X}' for k in range(min(16, len(between)-j)))
            ascii_part = ''.join(chr(between[j+k]) if 32 <= between[j+k] < 127 else '.' for k in range(min(16, len(between)-j)))
            print(f'    {s1+j:06X}: {hex_part}  {ascii_part}')
