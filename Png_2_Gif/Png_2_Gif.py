from PIL import Image
import numpy as np

big = Image.open('input.png')
W, H = big.size              # 6000×300
frame_w = W // 20            # 300
frames = []

for i in range(20):
    box = (i*frame_w, 0, (i+1)*frame_w, H)
    frames.append(big.crop(box))

frames[0].save('output.gif',
               save_all=True, append_images=frames[1:],
               duration=30, loop=0, disposal=2)