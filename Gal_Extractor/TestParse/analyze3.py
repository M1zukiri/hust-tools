import os, struct

path = r'C:\Gal\纸上的魔法使\纸上的魔法使\data.xp3'
with open(path, 'rb') as f:
    data = f.read()

# Find all JPEG SOI markers (FF D8)
jpeg_starts = []
pos = -1
while True:
    pos = data.find(b'\xff\xd8', pos + 1)
    if pos < 0 or len(jpeg_starts) >= 20:
        break
    jpeg_starts.append(pos)

print(f'Found {len(jpeg_starts)} JPEG images in the archive')
for i, pos in enumerate(jpeg_starts[:8]):
    print(f'  JPEG {i}: offset {pos:>8} (0x{pos:x})')

if len(jpeg_starts) >= 2:
    gap = jpeg_starts[1] - jpeg_starts[0]
    print(f'\nGap between JPEG 0 and JPEG 1: {gap} bytes')
    
    # Check what's between header end and first JPEG
    print(f'\n=== What is between header end (offset 11) and first JPEG start (offset 40)? ===')
    for j in range(11, 42, 1):
        print(f'  offset {j:3d} (0x{j:02x}): 0x{data[j]:02x} ({chr(data[j]) if 32 <= data[j] < 127 else "?"})')

    # Check for pattern between files
    print(f'\n=== Data between JPEG 0 end and JPEG 1 start ===')
    # Find FF D9 (JPEG end)
    d9pos0 = data.find(b'\xff\xd9', jpeg_starts[0], jpeg_starts[1])
    if d9pos0 >= 0:
        print(f'JPEG 0 end (FF D9) at: {d9pos0} (0x{d9pos0:x})')
        # Show data from end of metadata to next JPEG
        between = data[d9pos0+2:jpeg_starts[1]]
        print(f'Bytes between JPEGs: {len(between)}')
        if len(between) > 0:
            for j in range(0, min(len(between), 128), 16):
                hex_part = ' '.join(f'{between[j+k]:02X}' for k in range(min(16, len(between)-j)))
                print(f'  {d9pos0+2+j:06X}: {hex_part}')

    # Also check between JPEG 1 and JPEG 2
    if len(jpeg_starts) >= 3:
        d9pos1 = data.find(b'\xff\xd9', jpeg_starts[1], jpeg_starts[2])
        if d9pos1 >= 0:
            between = data[d9pos1+2:jpeg_starts[2]]
            print(f'\nBytes between JPEG 1 and JPEG 2: {len(between)}')
            if len(between) < 200:
                for j in range(0, len(between), 16):
                    hex_part = ' '.join(f'{between[j+k]:02X}' for k in range(min(16, len(between)-j)))
                    print(f'  {d9pos1+2+j:06X}: {hex_part}')

# Also check the 5-byte sequence at offset 0x22 (02 07 00 00 00)
print(f'\n=== First file header analysis ===')
print(f'Offset 0x20: 61 7A = "az" marker')
print(f'Offset 0x22: {data[0x22]:02X} {data[0x23]:02X} = type/version')
print(f'Offset 0x24: {" ".join(f"{data[0x24+j]:02X}" for j in range(4))} = size?')
# If 0x24-0x27 = size, and size = 0? No that can't be right.
# What if 02 07 00 00 00 00 are 2 bytes of type + 4 bytes of size?
type_val = struct.unpack_from('<H', data, 0x22)[0]
size_val = struct.unpack_from('<I', data, 0x24)[0]
print(f'  16-bit type at 0x22: {type_val} (0x{type_val:x})')
print(f'  32-bit size at 0x24: {size_val} (0x{size_val:x})')
