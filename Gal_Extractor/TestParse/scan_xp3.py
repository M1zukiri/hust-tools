import os, struct

# Scan 爱上火车's data.xp3 for BE entries
fpath = r'C:\Gal\爱上火车LastRun+全部更新DLC\LastRun\data.xp3'
sz = os.path.getsize(fpath)
mb = sz / (1024*1024)
print(f'爱上火车 data.xp3: {mb:.1f} MB')

with open(fpath, 'rb') as f:
    head = f.read(11)
    hex_h = ' '.join(f'{b:02X}' for b in head)
    print(f'Header: {hex_h}')

# Sample at intervals
found_any = False
for sample_off in range(0, min(int(sz), 100*1024*1024), 5*1024*1024):
    with open(fpath, 'rb') as f:
        f.seek(sample_off)
        chunk = f.read(512*1024)  # 512KB per sample
        be_count = 0
        for i in range(32, len(chunk)-2):
            if chunk[i] == 0xff and chunk[i+1] == 0xd8:
                pre = chunk[i-32:i]
                marker = struct.unpack_from('>I', pre, 0)[0]
                cf = struct.unpack_from('>I', pre, 4)[0]
                if marker == 0x02020004 and cf == 1:
                    be_count += 1
                    if be_count <= 2:
                        sz_f = struct.unpack_from('>I', pre, 8)[0]
                        print(f'  BE entry at offset {sample_off+i}: size={sz_f}')
        if be_count > 0:
            found_any = True
            print(f'  Sample {sample_off//(1024*1024)}MB: {be_count} entries')

if not found_any:
    print('No BE header entries found in this file')
    
    # Try a different approach: scan for OGG/PNG signatures directly
    print('Checking for known file signatures...')
    for ext_name, ext_bytes in [('OGG', b'OggS'), ('PNG', b'\x89PNG'), ('JPEG', b'\xff\xd8\xff')]:
        with open(fpath, 'rb') as f:
            f.seek(0)
            chunk = f.read(5*1024*1024)  # First 5MB
            count = chunk.count(ext_bytes)
            print(f'  {ext_name}: {count} in first 5MB')
