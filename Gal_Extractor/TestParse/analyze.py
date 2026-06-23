import os, struct

path = r'C:\Gal\纸上的魔法使\纸上的魔法使\data.xp3'
with open(path, 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')
print()

# Analyze the header
print('=== Header (first 48 bytes) ===')
for i in range(0, 48, 16):
    hex_part = ' '.join(f'{data[i+j]:02X}' for j in range(16))
    ascii_part = ''.join(chr(data[i+j]) if 32 <= data[i+j] < 127 else '.' for j in range(16))
    print(f'{i:06X}  {hex_part}  {ascii_part}')

print()
print('=== Potential file entries ===')
# Look for patterns: 4-byte offset or size followed by 4-byte size
# Try to find structured entries between the end of JPEG data and the next image

# First, find the end of the first JPEG (FF D9 = end of image marker)
jpeg_end = data.find(b'\xff\xd9', 0x28)
if jpeg_end >= 0:
    print(f'First JPEG ends at: {jpeg_end} (0x{jpeg_end:x})')
    # Show data after JPEG
    print(f'Data after JPEG:')
    after = data[jpeg_end+2:jpeg_end+2+64]
    for i in range(0, len(after), 16):
        hex_part = ' '.join(f'{after[i+j]:02X}' for j in range(min(16, len(after)-i)))
        ascii_part = ''.join(chr(after[i+j]) if 32 <= after[i+j] < 127 else '.' for j in range(min(16, len(after)-i)))
        print(f'  {jpeg_end+2+i:06X}  {hex_part}  {ascii_part}')
    print()

print('=== Scan for sequential file entries ===')
# Look for potential offset/size pairs that point to data + JPEG start
# Search for 'az' marker (0x61 0x7A)
az_positions = []
search_start = 0
while True:
    pos = data.find(b'\x61\x7a', search_start)
    if pos < 0:
        break
    az_positions.append(pos)
    search_start = pos + 1
print(f'Found {len(az_positions)} occurrences of 0x61 0x7A (az)')
# Show first 10
for pos in az_positions[:15]:
    ctx = data[max(0,pos-8):pos+16]
    hex_ctx = ' '.join(f'{b:02X}' for b in ctx)
    print(f'  Offset {pos:>8} (0x{pos:x}): {hex_ctx}')

print()
# Also check the structure at offset 11 more carefully
print('=== Interpreting offset 11 header structure ===')
# What if: [11-14: file_count] [15-18: index_offset] [19-22: ???] [23-26: ???] [27-30: ???]
# Or: [11-14: version_flag] [15-18: ???] etc.
vals = []
for i in range(0, 24, 4):
    off = 11 + i
    val = struct.unpack_from('<I', data, off)[0]
    vals.append(val)
    print(f'  32-bit LE at offset {off}: {val} (0x{val:x})')

# What if offset 11 is the number of directories/files?
file_count = vals[0]  # 23
if file_count < 1000:
    print(f'\nAssuming file_count = {file_count}')
    # If so, maybe the file entries start at some offset
    # Try to find 23 sequential entries starting after the header
    entry_start = 11 + 4  # after the count
    
    # Try reading entries: each entry might be [name_length(2)] + [name] + [offset(4)] + [size(4)]
    pos = entry_start
    for i in range(min(file_count, 5)):
        if pos + 2 >= len(data):
            break
        name_len = struct.unpack_from('<H', data, pos)[0]
        print(f'  Entry {i}: name_len={name_len} at offset {pos}')
        if 0 < name_len < 200 and pos + 2 + name_len + 8 < len(data):
            name = data[pos+2:pos+2+name_len]
            try:
                name_str = name.decode('utf-8', errors='replace')
            except:
                name_str = repr(name)
            ent_offset = struct.unpack_from('<I', data, pos + 2 + name_len)[0]
            ent_size = struct.unpack_from('<I', data, pos + 4 + name_len)[0]
            print(f'    name={name_str}, offset={ent_offset}, size={ent_size}')
            pos += 2 + name_len + 8
        else:
            break
