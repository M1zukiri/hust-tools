#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
眼图：32 条两周期正弦波，独立绘制
每条波形随机：
  1. 幅度  (1±AMP_NOISE)
  2. 相位  ±PHASE_NOISE*pi
  3. 极性  正相 / 反相 / 直接为 0
"""

import numpy as np
import matplotlib.pyplot as plt

# ---------------- 参数 -----------------
N_WAVES = 32          # 曲线条数
FS = 1000             # 每周期采样点数
N_CYCLES = 1          # 画两个周期
AMP_NOISE = 0.2      # 幅度随机差异比例
PHASE_NOISE = 0.1    # 相位随机差异比例（以 π 为单位）
PROB_ZERO = 0.20      # 某条波形被置 0 的概率
PROB_INVERT = 0.40    # 某条波形被反相的概率
# -------------------------------------

t = np.linspace(0, N_CYCLES * 2*np.pi, N_CYCLES*FS, endpoint=False)

plt.figure(figsize=(8, 4))

for _ in range(N_WAVES):
    # 1. 随机幅度
    amp = 1 + np.random.uniform(-AMP_NOISE, AMP_NOISE)
    # 2. 随机相位
    phase = np.random.uniform(-PHASE_NOISE*np.pi, PHASE_NOISE*np.pi)
    # 3. 随机极性
    r = np.random.rand()
    if r < PROB_ZERO:          # 直接为 0
        y = np.zeros_like(t)
    else:
        if r < PROB_ZERO + PROB_INVERT:
            amp *= -1          # 反相
        y = amp * np.sin(t + phase)
    # 4. 画到同一张图
    plt.plot(t, y, lw=0.6, color='darkblue', alpha=0.7)

plt.title("Eye Diagram – 2 cycles, {} individual sine waves".format(N_WAVES))
plt.xlabel("Time (rad)")
plt.ylabel("Amplitude")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()