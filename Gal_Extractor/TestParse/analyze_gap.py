import os, struct

path = r'C:\Gal\纸上的魔法使\纸上的魔法使\data.xp3'
with open(path, 'rb') as f:
    data = f.read()

# Find all BE header entries (thumbnail positions)
entries = []
for i in range(32, len(data)):
    if data[i] == 0xff and i+1 < len(data) and data[i+1] == 0xd8:
        pre = data[i-32:i]
        if len(pre) == 32:
            marker = struct.unpack_from('>I', pre, 0)[0]
            cf = struct.unpack_from('>I', pre, 4)[0]
            if marker == 0x02020004 and cf == 1:
                sz = struct.unpack_from('>I', pre, 8)[0]
                entries.append((i, sz))

print(f'Found {len(entries)} thumbnail entries')
print()

# For each entry, analyze the gap between thumbnail data and next entry
# The gap could contain actual game files
for idx in range(min(5, len(entries)-1)):
    pos, thumb_sz = entries[idx]
    thumb_end = pos + thumb_sz
    next_pos = entries[idx+1][0]
    gap_data = data[thumb_end:next_pos]
    
    print(f'=== Thumbnail {idx} at offset {pos} ===')
    print(f'  Thumbnail size: {thumb_sz} bytes')
    print(f'  Gap size: {len(gap_data)} bytes (offset {thumb_end} to {next_pos})')
    
    # Search for known file signatures in the gap
    for sig_name, sig in [('PNG', b'\x89PNG'), ('OGG', b'OggS'), ('JFIF', b'JFIF'), 
                          ('RIFF', b'RIFF'), ('ZIP', b'PK\x03\x04')]:
        sig_count = gap_data.count(sig)
        if sig_count > 0:
            positions = []
            p = -1
            for _ in range(min(3, sig_count)):
                p = gap_data.find(sig, p+1)
                if p >= 0:
                    positions.append(thumb_end + p)
            print(f'  {sig_name}: {sig_count} occurrences at {positions}')
    
    # Also check the first 32 bytes of the gap for any structure
    if len(gap_data) > 0:
        first = gap_data[:min(32, len(gap_data))]
        hex_f = ' '.join(f'{b:02X}' for b in first)
        ascii_f = ''.join(chr(b) if 32 <= b < 127 else '.' for b in first)
        print(f'  First 32 bytes of gap: {hex_f}  {ascii_f}')
    
    # Check if gap contains text data (script files)
    text_chars = sum(1 for b in gap_data[:10000] if 32 <= b < 127 or b in (10, 13, 9))
    if text_chars > 5000:
        print(f'  Gap appears to contain TEXT/script data')
    print()
