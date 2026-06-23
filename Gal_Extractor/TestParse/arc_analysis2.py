import os, struct

# Check multiple BURIKO ARC20 files
files = [
    (r'C:\Gal\【PC】巧克甜恋\【PC】巧克甜恋\Amairo Chocolate\data01100.arc', 'data01100'),
    (r'C:\Gal\【PC】巧克甜恋\【PC】巧克甜恋\Amairo Chocolate\data02200.arc', 'data02200'),
    (r'C:\Gal\【PC】巧克甜恋\【PC】巧克甜恋\Amairo Chocolate\sysgrp.arc', 'sysgrp'),
    (r'C:\Gal\宝石夜乐园\宝石夜乐园\data01010.arc', 'data01010'),
]

for fpath, label in files:
    if not os.path.exists(fpath):
        print(f'{label}: NOT FOUND')
        continue
        
    with open(fpath, 'rb') as f:
        data = f.read()
    
    print(f'=== {label} ===')
    print(f'Size: {len(data)} bytes')
    magic = data[0:12].decode('ascii', errors='replace')
    ver = struct.unpack_from('<I', data, 12)[0]
    print(f'Magic: {magic}, Version: {ver}')
    
    # Scan for filename patterns
    # Find all null-terminated ASCII strings > 3 chars
    strings = []
    i = 16  # skip header
    while i < len(data) - 4:
        # Check if this starts a readable string
        if 32 <= data[i] < 127:
            j = i
            while j < len(data) and 32 <= data[j] < 127:
                j += 1
            if j - i >= 4 and b'.' in data[i:j]:
                name = data[i:j].decode('ascii', errors='replace')
                strings.append((i, name))
                i = j
            else:
                i += 1
        else:
            i += 1
    
    print(f'Strings found: {len(strings)}')
    for offset, name in strings[:15]:
        # Look for offset/size fields after the string (at next aligned position)
        name_end = offset + len(name) + 1  # +1 for null terminator
        aligned = ((name_end + 15) // 16) * 16
        if aligned + 8 <= len(data):
            off_val = struct.unpack_from('<I', data, aligned)[0]
            sz_val = struct.unpack_from('<I', data, aligned + 4)[0]
            if 0 < off_val < len(data) and 0 < sz_val < 50000000:
                print(f'  [{offset}] {name:<30} offset={off_val:>10} size={sz_val:>10}  [{aligned}]')
            else:
                print(f'  [{offset}] {name:<30} (bad data at {aligned}: off={off_val} sz={sz_val})')
        else:
            print(f'  [{offset}] {name:<30} (truncated)')
    
    print()
