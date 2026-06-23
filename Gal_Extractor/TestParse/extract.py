import os, struct, sys

path = r'C:\Gal\纸上的魔法使\纸上的魔法使\data.xp3'
output_dir = r'C:\Gal_EXTRACTED\纸上的魔法使'

with open(path, 'rb') as f:
    data = f.read()

os.makedirs(output_dir, exist_ok=True)

print(f'XP3 file size: {len(data)} bytes')
print()

# Strategy: scan for known file signatures and extract based on 
# finding the next signature or using heuristic headers

# Define file signatures with their extractors
signatures = {
    b'\xff\xd8\xff': ('jpg', 'JPEG image'),
    b'\x89PNG\r\n\x1a\n': ('png', 'PNG image'),
    b'OggS': ('ogg', 'Ogg Vorbis audio'),
    b'RIFF': ('wav', 'WAV audio'),
}

extracted = []

# Scan for all JPEG starts
pos = 0
jpg_count = 0
png_count = 0
ogg_count = 0

# Extract JPEGs by finding FF D8 (SOI) and then the next FF D8 or end of file
all_jpegs = []
p = -1
while True:
    p = data.find(b'\xff\xd8', p + 1)
    if p < 0:
        break
    all_jpegs.append(p)

print(f'Found {len(all_jpegs)} JPEG images')
print(f'Found {data.count(b"\x89PNG")} PNG images')  
print(f'Found {data.count(b"OggS")} OGG audio files')

# Also look for image dimensions in headers to figure out boundaries
# Let me look at the 32-byte headers I found
print()
print('=== Analysis of 32-byte pre-file headers ===')

# Structure analysis: every JPEG (beyond the first pair) has a 32-byte header
# that appears right before the FF D8. These headers have consistent sizes.

# Let me verify the pattern: [32 bytes] [FF D8 ... JPEG data ... FF D9] [32 bytes] [FF D8 ...]
# Actually, the 32-byte header might encode the file size.

# Check if the header value at offset -24 to -21 (4 bytes) is the actual file size
for jpg_idx in range(2, min(8, len(all_jpegs))):
    jpg_off = all_jpegs[jpg_idx]
    if jpg_off >= 32:
        hdr = data[jpg_off-32:jpg_off]
        # Interpret as various 32-bit LE values
        sizes = struct.unpack_from('<IIIIIIII', hdr, 0)
        # Check if any of the values match the gap to the next JPEG
        next_jpg = all_jpegs[jpg_idx + 1] if jpg_idx + 1 < len(all_jpegs) else len(data)
        actual_size = next_jpg - jpg_off
        print(f'JPEG {jpg_idx} @ {jpg_off}: hdr={sizes[0]:>10} {sizes[1]:>10} {sizes[2]:>10} {sizes[3]:>10} | actual_size={actual_size}')

        # Find the FF D9 end marker within this range
        d9pos = data.find(b'\xff\xd9', jpg_off, next_jpg)
        if d9pos >= 0:
            jpeg_data_end = d9pos + 2
            # Check if sizes[1] or sizes[2] matches the JPEG data size
            jpeg_raw_size = jpeg_data_end - jpg_off
            print(f'  JPEG raw size (to FF D9): {jpeg_raw_size}')

        # Also try: the value at offset -8 to -5 as 32-bit LE might be size
        # Check hdr[-8:-4] = bytes 24-27 of header
        size_candidate = struct.unpack_from('<I', hdr, 24)[0]
        print(f'  Size at hdr[24:28] = {size_candidate} (0x{size_candidate:x})')
