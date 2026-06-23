import os, struct

path = r'C:\Gal\纸上的魔法使\纸上的魔法使\data.xp3'
output_dir = r'C:\Gal_EXTRACTED\纸上的魔法使'

with open(path, 'rb') as f:
    data = f.read()

os.makedirs(output_dir, exist_ok=True)

# The header format is BIG-ENDIAN!
# After the 11-byte magic, the per-file headers use big-endian

# Let me find candidate file entries using big-endian decoding
all_ffd8 = []
pos = -1
while True:
    pos = data.find(b'\xff\xd8', pos + 1)
    if pos < 0:
        break
    all_ffd8.append(pos)

print(f'Total FF D8 markers: {len(all_ffd8)}')

# Check for the big-endian header pattern: bytes 0-3 = 0x02020004
# and the size field at bytes 8-11 matches actual data
candidates = []
for jpg_pos in all_ffd8:
    if jpg_pos >= 32:
        pre_bytes = data[jpg_pos-32:jpg_pos]
        # Check big-endian values
        marker = struct.unpack_from('>I', pre_bytes, 0)[0]
        count_field = struct.unpack_from('>I', pre_bytes, 4)[0]
        size_field = struct.unpack_from('>I', pre_bytes, 8)[0]
        
        # Marker 0x02020004 is the constant we found
        if marker == 0x02020004 and count_field == 1:
            candidates.append((jpg_pos, size_field))

print(f'Candidates with BE header pattern: {len(candidates)}')
for i, (pos, sz) in enumerate(candidates[:20]):
    # Verify size against actual JPEG data
    next_pos = candidates[i+1][0] if i+1 < len(candidates) else len(data)
    d9pos = data.find(b'\xff\xd9', pos, next_pos)
    if d9pos >= 0:
        actual_size = d9pos + 2 - pos
        status = 'OK' if actual_size == sz else f'DIFF(hdr={sz},act={actual_size})'
    else:
        status = '? no FF D9'
    print(f'  [{i:3d}] offset {pos:>8}: hdr_size={sz:>8} {status}')

# Now check the 'az' marker at the beginning
print()
print(f'=== First entry analysis ===')
print(f'Offset 0x20 (32): az marker')
# After az at 32, we have 02 07 00 00 00 00 then JPEG at 40
# What if the first entry has a different header format?
# az + type(2) + some struct?

# Count entries in the file using our header pattern
print(f'\n=== File entry statistics ===')
# Group JPEGs by their proximity (within 10000 bytes) to count "real images"
groups = []
if candidates:
    current_group = [candidates[0]]
    for i in range(1, len(candidates)):
        if candidates[i][0] - candidates[i-1][0] < 10000:
            current_group.append(candidates[i])
        else:
            groups.append(current_group)
            current_group = [candidates[i]]
    groups.append(current_group)

print(f'File entry groups (using 10000-byte proximity): {len(groups)}')
for i, g in enumerate(groups[:10]):
    offsets = [f'{x[0]}' for x in g]
    sizes = [f'({x[1]}B)' for x in g]
    print(f'  Group {i}: {len(g)} entries starting at {g[0][0]}')

# Also extract a sample file to verify
print()
print('=== Extracting sample files ===')
for i, (pos, sz) in enumerate(candidates[:5]):
    # Find the ACTUAL end of this JPEG (FF D9)
    next_pos = candidates[i+1][0] if i+1 < len(candidates) else pos + sz + 100
    d9pos = data.find(b'\xff\xd9', pos, next_pos)
    if d9pos >= 0:
        actual_end = d9pos + 2
    else:
        actual_end = pos + sz
    
    # Extract the JPEG data
    jpeg_data = data[pos:actual_end]
    ext = 'jpg'
    fname = f'image_{i:04d}.{ext}'
    fpath = os.path.join(output_dir, fname)
    with open(fpath, 'wb') as f:
        f.write(jpeg_data)
    print(f'  [{i}] Saved {fname} ({len(jpeg_data)} bytes)')

print(f'\nSample files saved to {output_dir}')

# Now let me try to understand the FULL file structure
# by parsing from offset 32 sequentially
print()
print('=== Sequential parsing attempt ===')
# Starting after the magic header and initial data, try to parse
# the entire file as a sequence of: [32-byte BE header][data]

entries_found = []
scan_pos = 32  # Start after 'az' marker

# The first entry might be special (has az marker)
# Skip it and start from the next real header
for skip in range(3):  # Skip a few to get to the proper headers
    # Find next candidate header
    found = False
    for cp, cs in candidates:
        if cp > scan_pos:
            gap = cp - scan_pos
            # Check if there's data between
            entries_found.append(('HEADER', cp, cs, gap))
            scan_pos = cp + cs
            found = True
            break
    if not found:
        break

# Show the first few entries found
print(f'Entries found in sequential scan: {len(entries_found)}')
for e in entries_found[:5]:
    print(f'  {e}')
