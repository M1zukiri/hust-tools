import os, struct

# Analyze the PackFile format in detail
fpath = r'C:\Gal\秽翼的尤斯蒂娅\秽翼的尤斯蒂娅\system.arc'
with open(fpath, 'rb') as f:
    data = f.read()

print(f'File size: {len(data)}')
print(f'Magic: {data[0:12].decode("ascii", errors="replace")}')
file_count = struct.unpack_from('<I', data, 12)[0]
print(f'File count: {file_count}')

# The entry size appears to be 48 bytes = 0x30
ENTRY_SIZE = 0x30
entry_offset = 16  # After 12-byte magic + 4-byte count

print(f'\nEntry directory at offset {entry_offset}, size per entry = {ENTRY_SIZE}')
print(f'Directory ends at {entry_offset + file_count * ENTRY_SIZE}')

print()
print('Parsed entries (offset_size={}):'.format(ENTRY_SIZE))
print(f'{"#":>3} {"Name":<20} {"Offset":>8} {"Size":>8}')
print('-' * 45)

total_size = 0
for i in range(file_count):
    pos = entry_offset + i * ENTRY_SIZE
    name = data[pos:pos+16].decode('ascii', errors='replace').rstrip('\x00')
    off = struct.unpack_from('<I', data, pos + 16)[0]
    sz = struct.unpack_from('<I', data, pos + 20)[0]
    
    # Verify offsets form a contiguous chain
    if i > 0:
        expected_off = total_size
        match = 'OK' if off == expected_off else f'EXPECTED {expected_off}'
    else:
        match = 'first'
    
    print(f'{i:3d} {name:<20} {off:8d} {sz:8d}  [{match}]')
    total_size = off + sz

print(f'\nLast byte of last file: {total_size}')
print(f'File size: {len(data)}')
print(f'Remainder: {len(data) - total_size}')

# Check BURIKO format
print('\n' + '='*60)
print('BURIKO ARC20 format analysis')
print('='*60)

fpath2 = r'C:\Gal\宝石夜乐园\宝石夜乐园\system.arc'
with open(fpath2, 'rb') as f:
    data2 = f.read()

print(f'\nFile: {fpath2}')
print(f'Size: {len(data2)}')
print(f'Magic: {data2[0:12].decode("ascii", errors="replace")}')
# BURIKO ARC20 + 4 bytes = 16 bytes header
header2 = data2[0:12].decode('ascii', errors='replace')
ver2 = struct.unpack_from('<I', data2, 12)[0]
print(f'Version/type: {ver2}')

# Dump first 128 bytes
print('\nHex dump:')
for i in range(0, min(256, len(data2)), 16):
    hex_part = ' '.join(f'{data2[i+j]:02X}' for j in range(16))
    ascii_part = ''.join(chr(data2[i+j]) if 32 <= data2[i+j] < 127 else '.' for j in range(16))
    print(f'{i:04X}  {hex_part}  {ascii_part}')
