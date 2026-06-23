import os, struct

# RealLive PAK format analysis
# Structure: Header + Directory entries + File data

files = [
    (r'C:\Gal\AIR\AIR-P2P\files\SCRIPT.PAK', 'SCRIPT'),
    (r'C:\Gal\AIR\AIR-P2P\files\image\BGCG.PAK', 'BGCG'),
    (r'C:\Gal\AIR\AIR-P2P\files\image\EVENTCG.PAK', 'EVENT'),
    (r'C:\Gal\AIR\AIR-P2P\files\image\SYSCG.PAK', 'SYSCG'),
]

for fpath, label in files:
    sz = os.path.getsize(fpath)
    with open(fpath, 'rb') as f:
        data = f.read()
    
    # Header analysis
    hdr = data[0:16]
    print(f'=== {label} ({sz} bytes) ===')
    vals = struct.unpack_from('<IIII', hdr, 0)
    print(f'  Header: {vals}')
    
    # Try parsing as directory entries (32 bytes each)
    entry_count = vals[0]
    if entry_count > 10000:  # likely not an entry count
        entry_count = vals[1]
    
    if entry_count < 1000:
        print(f'  Entry count: {entry_count}')
        
        # Read entries
        print(f'  First 10 entries (offset/format):')
        for i in range(min(10, entry_count)):
            pos = 16 + i * 32
            if pos + 32 > len(data):
                break
            ent = data[pos:pos+32]
            e_vals = struct.unpack_from('<IIIIIIII', ent, 0)
            # Try: [index/hash] [offset] [size] [flags] [padding...]
            off = e_vals[1]
            sz = e_vals[2]
            print(f'    [{i}] vals={e_vals[:4]} offset={off} size={sz}')
        
        # Show last directory entry
        if entry_count > 10:
            pos = 16 + (entry_count-1) * 32
            if pos + 32 <= len(data):
                ent = data[pos:pos+32]
                e_vals = struct.unpack_from('<IIIIIIII', ent, 0)
                off = e_vals[1]
                sz = e_vals[2]
                print(f'    ...')
                print(f'    [{entry_count-1}] vals={e_vals[:4]} offset={off} size={sz}')
        
        # Verify: does last entry + size match file size?
        if entry_count > 0:
            pos = 16 + (entry_count-1) * 32
            e_vals = struct.unpack_from('<IIIIIIII', data[pos:pos+32], 0)
            last_off = e_vals[1]
            last_sz = e_vals[2]
            dir_end = 16 + entry_count * 32
            print(f'  Dir ends at: {dir_end}')
            print(f'  Last entry: offset={last_off} size={last_sz}')
            print(f'  Expected file end: {last_off + last_sz}')
            print(f'  Actual file size: {sz}')
            print(f'  What is between dir_end ({dir_end}) and first data?')
            if dir_end < len(data):
                gap = last_off - dir_end if last_off > dir_end else 0
                print(f'  Gap between dir and first file: {gap} bytes')
    print()

# Also check a .g00 file
gpath = r'C:\Gal\CLANNAD\CLANNAD FULL VOICE\clfvbak\G00\BG051O.g00'
if os.path.exists(gpath):
    gsz = os.path.getsize(gpath)
    print(f'=== Sample G00 file ({gsz} bytes) ===')
    with open(gpath, 'rb') as f:
        gdata = f.read(min(128, gsz))
    for i in range(0, len(gdata), 16):
        hex_part = ' '.join(f'{gdata[i+j]:02X}' for j in range(16))
        ascii_part = ''.join(chr(gdata[i+j]) if 32 <= gdata[i+j] < 127 else '.' for j in range(16))
        print(f'  {i:04X}  {hex_part}  {ascii_part}')
