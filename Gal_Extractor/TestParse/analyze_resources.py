import os, struct

path = r'C:\Gal\纸上的魔法使\纸上的魔法使\data.xp3'
with open(path, 'rb') as f:
    data = f.read()

# Get all entry positions using the big-endian header
candidates = []
pos = -1
while True:
    pos = data.find(b'\xff\xd8', pos + 1)
    if pos < 0:
        break
    if pos >= 32:
        pre = data[pos-32:pos]
        marker = struct.unpack_from('>I', pre, 0)[0]
        count_f = struct.unpack_from('>I', pre, 4)[0]
        size_f = struct.unpack_from('>I', pre, 8)[0]
        if marker == 0x02020004 and count_f == 1:
            candidates.append((pos, size_f))

# For each entry, check what's in the gap (after JPEG data, before next header)
print('=== Files found in gaps between JPEG thumbnails ===')
total_ogg = 0
total_png = 0
total_script = 0

for idx in range(min(len(candidates)-1, 95)):
    pos, sz = candidates[idx]
    next_pos = candidates[idx+1][0] if idx+1 < len(candidates) else len(data)
    
    jpeg_end = pos + sz
    gap_data = data[jpeg_end:next_pos]
    
    # Count file signatures in this gap
    ogg_count = gap_data.count(b'OggS')
    png_count = gap_data.count(b'\x89PNG')
    # Look for TJS/script files by pattern
    ks_count = gap_data.count(b'.ks\x00')  # Script files
    
    if ogg_count > 0 or png_count > 0 or ks_count > 0:
        print(f'Entry {idx:2d} (offset {pos:>8}): JPEG={sz}B, gap={len(gap_data)}B -> OGG={ogg_count}, PNG={png_count}, Script={ks_count}')
        total_ogg += ogg_count
        total_png += png_count
        total_script += ks_count

print()
print(f'Summary: OGG={total_ogg}, PNG={total_png}, Script={total_script}')

# Also check: are there PNG/OGG files in the early entries?
print()
print('=== First entry gap has file signatures at: ===')
pos, sz = candidates[0]
next_pos = candidates[1][0]
jpeg_end = pos + sz
gap = data[jpeg_end:next_pos]

# Search for known signatures in gap
for sig_name, sig_bytes in [('PNG', b'\x89PNG'), ('OGG', b'OggS'), ('JFIF', b'JFIF')]:
    p = gap.find(sig_bytes)
    if p >= 0:
        abs_pos = jpeg_end + p
        print(f'  {sig_name} at absolute offset {abs_pos} (gap offset {p})')

# How many entries actually have substantial data in their gaps?
print()
print('=== Gap size distribution ===')
small_count = sum(1 for i in range(len(candidates)-1) if candidates[i+1][0] - (candidates[i][0] + candidates[i][1]) < 10000)
large_count = len(candidates) - 1 - small_count
print(f'Small gaps (<10KB): {small_count}')
print(f'Large gaps (>=10KB): {large_count}')

# Show the last few entries (often have different structure)
print()
print('=== Last 5 entries ===')
for i in range(max(0, len(candidates)-5), len(candidates)):
    pos, sz = candidates[i]
    next_off = candidates[i+1][0] if i+1 < len(candidates) else len(data)
    gap_sz = next_off - (pos + sz)
    print(f'  [{i:3d}] offset {pos:>10}, JPEG={sz:>8}B, gap={gap_sz:>10}B, total_entry={next_off-pos:>10}B')
