import os, struct

path = r'C:\Gal\纸上的魔法使\纸上的魔法使\data.xp3'
with open(path, 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')
print()

# Check for common Kirikiri/KrKr patterns
extensions = [b'.ks', b'.tjs', b'.png', b'.jpg', b'.ogg', b'.mp3', b'.wav', 
              b'.tlg', b'.bmp', b'.gif', b'.webp', b'.txt', b'.json', b'.xml']

print('=== Searching for file extensions ===')
for ext in extensions:
    positions = []
    pos = -1
    while True:
        pos = data.find(ext, pos + 1)
        if pos < 0 or len(positions) >= 10:
            break
        # Check if preceded by a dot and followed by null or valid separator
        if pos > 0:
            positions.append(pos)
    if positions:
        print(f'  {ext.decode()}: found {positions[0]} positions - first at offset {positions[0]}')

# Try a different approach - look at the 'az' marker more carefully
# The first 'az' at offset 32 before JPEG suggests it's part of the entry structure
# Maybe it's: [az + type + size] [filename] [data]
print()
print('=== Analyzing entry structure at beginning ===')

# Try: each entry = [12 bytes header] + [filename] + [data]
# Where header might be: [offset(4)] [size(4)] [name_len(2)] [flags(2)] or similar

# Let me check: after header (offset 11), what structure leads to data at 0x28?
# 11 bytes header + some info + JPEG at 0x28
# 0x28 - 11 = 29 bytes between header end and JPEG data

# At offset 32 (0x20): 'az' marker appears
# 0x20 - 11 = 21 bytes between header and 'az'

# What if the structure is:
# [11 bytes: magic]
# [4 bytes: count? or flag?]  
# [4 bytes: something]
# [4 bytes: something]
# [4 bytes: offset to first entry]
# [4 bytes: size of something]
# Then first entry:
#   [2 bytes: 'az' marker]
#   [4 bytes: ???]
#   [filename?]
#   [data]

# Let's try: first file is at offset where 'az' is (32)
# And the 4 bytes before 'az' (28-31): 00 00 00 00
# If that's a size field for the entry, entry size = 0? No.
# If that's padding...

# What if there's no per-file header and the file just has:
# Standard XP3 header + direct file data + index at end?

# Let me search the last 1000 bytes for any structured index
print()
print('=== Last 1000 bytes of file (potential index location) ===')
end_data = data[-1000:]
for i in range(0, len(end_data), 32):
    hex_part = ' '.join(f'{end_data[i+j]:02X}' for j in range(min(32, len(end_data)-i)))
    ascii_part = ''.join(chr(end_data[i+j]) if 32 <= end_data[i+j] < 127 else '.' for j in range(min(32, len(end_data)-i)))
    print(f'  {len(data)-1000+i:08X}  {hex_part:<96}  {ascii_part}')

# Check for any structured patterns throughout the file
print()
print('=== Searching for binary structures ===')
# Look for patterns where: [4-byte offset][4-byte size][2-byte name_len] -> filename -> data
# This is the standard XP3v3/Adpe-style entry format

# Also look for TJS script data
print('Searching for script/text patterns...')
tjs_starts = []
for ext in [b'.ks', b'.tjs']:
    pos = data.find(ext)
    if pos >= 0:
        # Try to read backward to find the beginning of the name
        start = max(0, pos - 60)
        chunk = data[start:pos+10]
        print(f'\nFound {ext.decode()} at offset {pos} (0x{pos:x})')
        print(f'  Context before: ', end='')
        before = data[max(0,pos-20):pos]
        print(' '.join(f'{b:02X}' for b in before))
        print(f'  Text: ', end='')
        # Try to extract readable text before the extension
        for j in range(max(0, pos-60), pos):
            if 32 <= data[j] < 127:
                print(chr(data[j]), end='')
        print(ext.decode())

# Let me look at some 'az' occurrences that AREN'T the first one
# to see if they have a different pattern
print()
print('=== First 5 non-header az occurrences ===')
count = 0
for p in sorted(set(data.find(b'\x61\x7a', i) for i in range(0, len(data), 10000))):
    if p >= 0 and p > 100:  # skip the one in the header
        ctx_before = data[max(0,p-24):p]
        ctx_after = data[p:p+32]
        hex_before = ' '.join(f'{b:02X}' for b in ctx_before)
        hex_after = ' '.join(f'{b:02X}' for b in ctx_after)
        print(f'  Offset {p:>8}: ...{hex_before} | 61 7A {hex_after}')
        count += 1
        if count >= 10:
            break
