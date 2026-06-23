import os, struct

# Analyze Entergram/FAVORITE .bin archive format
# Files like graph.bin, bgm.bin, voice.bin are actually archives

files = [
    (r'C:\Gal\樱花萌放\graph.bin', 'sakuramoyu_graph'),
    (r'C:\Gal\樱花萌放\bgm.bin', 'sakuramoyu_bgm'),
    (r'C:\Gal\星空的记忆 HD 4K重置版\星空的记忆 HD 4K重置版\graph.bin', 'hoshimemo_graph'),
    (r'C:\Gal\星辰恋曲的白色永恒 Finale\graph.bin', 'astralair_graph'),
]

for fpath, label in files:
    if not os.path.exists(fpath):
        print(f'{label}: NOT FOUND')
        continue
    sz = os.path.getsize(fpath)
    print(f'=== {label} ({sz} bytes) ===')
    with open(fpath, 'rb') as f:
        head = f.read(256)
    for i in range(0, min(256, len(head)), 16):
        hex_part = ' '.join(f'{head[i+j]:02X}' for j in range(16))
        ascii_part = ''.join(chr(head[i+j]) if 32 <= head[i+j] < 127 else '.' for j in range(16))
        print(f'{i:04X}  {hex_part}  {ascii_part}')
    print()
