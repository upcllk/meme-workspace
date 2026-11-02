# Motion-Kit 16-Bit 像素动画与游戏视频引擎

基于纯 Python 与 NumPy 实现的 16-bit 复古像素动画与 8-bit Chiptune 音效合成引擎。原生输出 1920×1080 30FPS MP4 视频（4× 整数像素最近邻缩放）。

---

## 模块结构

- `palette.py`：16-bit 有限调色板（SNES / MegaDrive 风格调色板定义）。
- `sprites.py`：奶娃原生动作帧、特写面部与半身像。
- `scene.py`：夜晚城市场景（三层视差卷轴、星空、明月、霓虹看板、路灯光晕）。
- `audio.py`：8-bit 芯片音乐与音效合成器（方波、三角波、白噪声及 ADSR 包络）。
- `director.py`：夜晚城市 20 秒动画短片总控调度器。
- `mario_sprites.py`：超级奶里奥（Naiwa Mario）纯代码像素人设与动作帧库。
- `mario_game.py`：卡水管喜剧版《超级奶里奥》20 秒游戏短片生成器。
- `naiwa_world.py`：无敌星通关版《Super Naiwa World》20 秒游戏短片生成器（含跑酷、踩怪、无敌星冲刺、滑旗杆、城堡烟花与爆笑结算）。

---

## 视频生成命令

### 1. 生成《Super Naiwa World》通关短片（20 秒，1080p）
```bash
python3 -m motion_kit.naiwa_world super_naiwa_world_20s.mp4
```

### 2. 生成《超级奶里奥：卡水管篇》（20 秒，1080p）
```bash
python3 -m motion_kit.mario_game
```

### 3. 生成《夜晚城市漫步与爆笑》（20 秒，1080p）
```bash
python3 -m motion_kit.director
```

### 4. 导出角色像素设定图板
```bash
python3 -m motion_kit.mario_sprites
```
