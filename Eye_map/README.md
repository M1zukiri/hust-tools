# Eye_map — 眼图生成器

生成 32 条随机幅度/相位/极性的正弦波眼图，用于信号质量可视化演示。

## 调用方法

```bash
python eyemap.py
```

> 无参数，直接运行即弹出 Matplotlib 窗口显示眼图。

## 参数调节

修改 `eyemap.py` 头部常量：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `N_WAVES` | 32 | 曲线条数 |
| `FS` | 1000 | 每周期采样点数 |
| `N_CYCLES` | 1 | 显示周期数 |
| `AMP_NOISE` | 0.2 | 幅度随机差异比例 |
| `PHASE_NOISE` | 0.1 | 相位随机差异比例（×π） |
| `PROB_ZERO` | 0.20 | 波形被置零的概率 |
| `PROB_INVERT` | 0.40 | 波形被反相的概率 |

## 项目结构

```
Eye_map/
├── eyemap.py       # 主程序（眼图生成 + 绘图）
└── README.md       # 本文档
```

## 依赖

```
numpy
matplotlib
```

安装：`pip install numpy matplotlib`
