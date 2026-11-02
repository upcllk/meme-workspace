"""
Super Naiwa World —— 20 秒超级玛丽风格像素游戏短片。

角色直接使用 mario_sprites.NaiwaMarioPixelArt（红帽 N 徽章 / 绿眼 / 黄色梨形身体 / 蓝色背带裤）。
剧情：标题画面 -> WORLD 1-1 -> 顶问号砖出金币 -> 踩栗子怪 -> 跳水管 -> 顶出无敌星
-> 彩虹无敌冲刺撞飞敌人、飞越深坑吃金币 -> 顶碎砖块 -> 爬台阶 -> 跳上旗杆滑下
-> 城堡前烟花 + 招牌捧腹大笑 -> COURSE CLEAR。

运行：python3 -m motion_kit.naiwa_world [输出路径]
"""

import os
import sys
import math
import wave
import subprocess
import numpy as np

from .mario_sprites import NaiwaMarioPixelArt

FPS = 30
TOTAL = 600
W, H = 480, 270
SCALE = 4
SR = 44100
G = 222  # 地面顶部 y
TITLE_END = 54  # 1.8s
WORLD_END = 78  # 2.6s

# ---------------------------------------------------------------- colors
SKY = (107, 140, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CREAM = (252, 216, 168)
GOLD = (255, 220, 40)


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


# ---------------------------------------------------------------- basic drawing
def surf(w, h):
    return np.zeros((h, w, 4), np.uint8)


def rect(a, x, y, w, h, c):
    y1, y2 = max(0, y), min(a.shape[0], y + h)
    x1, x2 = max(0, x), min(a.shape[1], x + w)
    if y1 < y2 and x1 < x2:
        a[y1:y2, x1:x2, :3] = c[:3]
        if a.shape[2] == 4:
            a[y1:y2, x1:x2, 3] = 255


def pix(rows, cmap):
    h, w = len(rows), max(len(r) for r in rows)
    a = surf(w, h)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in cmap:
                a[y, x] = rgba(cmap[ch])
    return a


def outline(a, c):
    m = a[:, :, 3] > 0
    p = np.pad(m, 1)
    d = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    o = a.copy()
    o[d & ~m] = rgba(c)
    return o


def blit(dst, src, x, y, alpha=1.0, flipx=False, flipy=False):
    if flipx:
        src = src[:, ::-1]
    if flipy:
        src = src[::-1]
    h, w = src.shape[:2]
    x, y = int(round(x)), int(round(y))
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 >= x2 or y1 >= y2:
        return
    s = src[y1 - y:y2 - y, x1 - x:x2 - x]
    d = dst[y1:y2, x1:x2]
    m = s[:, :, 3] > 0
    if alpha >= 1.0:
        d[m, :3] = s[m, :3]
        if d.shape[2] == 4:
            d[m, 3] = 255
    else:
        d[m, :3] = (d[m, :3] * (1 - alpha) + s[m, :3] * alpha).astype(np.uint8)


def circle_blob(w, h, circles, fill, line, shade=None):
    a = surf(w, h)
    yy, xx = np.mgrid[0:h, 0:w]
    m = np.zeros((h, w), bool)
    for cx, cy, r in circles:
        m |= (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
    a[m] = rgba(fill)
    if shade is not None:
        sm = m & (yy > h * 0.62)
        a[sm] = rgba(shade)
    return outline(a, line)


# ---------------------------------------------------------------- 5x7 pixel font
_F = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    "-": [".....", ".....", ".....", ".###.", ".....", ".....", "....."],
    "x": [".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"],
    ":": [".....", "..#..", ".....", ".....", ".....", "..#..", "....."],
    ".": [".....", ".....", ".....", ".....", ".....", ".....", "..#.."],
    "*": [".....", "..#..", "#.#.#", ".###.", "#.#.#", "..#..", "....."],
    " ": ["....."] * 7,
}
_FONT = {k: np.array([[c == "#" for c in r] for r in v]) for k, v in _F.items()}


def text(img, x, y, s, c=WHITE, scale=1, shadow=True, center=False):
    if center:
        x = x - len(s) * 6 * scale // 2
    for pass_ in ((1, BLACK), (0, c)) if shadow else ((0, c),):
        off, col = pass_
        cx = x
        for ch in s:
            g = _FONT.get(ch, _FONT[" "])
            for gy in range(7):
                for gx in range(5):
                    if g[gy, gx]:
                        rect(img, cx + gx * scale + off * scale, y + gy * scale + off * scale, scale, scale, col)
            cx += 6 * scale


# ---------------------------------------------------------------- sprites
def brick_tile():
    a = surf(16, 16)
    rect(a, 0, 0, 16, 16, (200, 76, 12))
    for yy in (0, 4, 8, 12):
        rect(a, 0, yy + 3, 16, 1, (40, 12, 0))
        rect(a, 0, yy, 16, 1, (252, 160, 110))
        off = 0 if (yy // 4) % 2 == 0 else 8
        rect(a, (off + 7) % 16, yy, 1, 4, (40, 12, 0))
        rect(a, (off + 15) % 16, yy, 1, 4, (40, 12, 0))
    return a


def ground_tile():
    a = surf(16, 16)
    rect(a, 0, 0, 16, 16, (200, 76, 12))
    rect(a, 0, 0, 16, 1, (252, 188, 140))
    rect(a, 0, 0, 1, 16, (252, 188, 140))
    rect(a, 15, 0, 1, 16, (60, 20, 0))
    rect(a, 0, 15, 16, 1, (60, 20, 0))
    rect(a, 9, 1, 1, 9, (60, 20, 0))
    rect(a, 1, 9, 8, 1, (60, 20, 0))
    rect(a, 10, 10, 5, 1, (252, 188, 140))
    return a


def hard_block():
    a = surf(16, 16)
    rect(a, 0, 0, 16, 16, (196, 108, 52))
    rect(a, 0, 0, 16, 2, (252, 196, 150))
    rect(a, 0, 0, 2, 16, (252, 196, 150))
    rect(a, 0, 14, 16, 2, (80, 32, 8))
    rect(a, 14, 0, 2, 16, (80, 32, 8))
    rect(a, 4, 4, 8, 8, (172, 88, 36))
    return a


def q_block(shade):
    base = [(255, 170, 20), (240, 140, 10), (210, 110, 0)][shade]
    a = surf(16, 16)
    rect(a, 0, 0, 16, 16, (100, 40, 10))
    rect(a, 0, 0, 15, 15, base)
    rect(a, 0, 0, 15, 1, (255, 220, 140))
    for px, py in ((2, 2), (12, 2), (2, 12), (12, 12)):
        rect(a, px, py, 1, 1, (100, 40, 10))
    q = [".###.", "##.##", "...##", "..##.", "..#..", ".....", "..#.."]
    for yy, r in enumerate(q):
        for xx, ch in enumerate(r):
            if ch == "#":
                rect(a, 5 + xx + 1, 4 + yy + 1, 1, 1, (100, 40, 10))
                rect(a, 5 + xx, 4 + yy, 1, 1, (255, 245, 220))
    return a


def used_block():
    a = surf(16, 16)
    rect(a, 0, 0, 16, 16, (60, 24, 4))
    rect(a, 1, 1, 14, 14, (160, 96, 48))
    for px, py in ((2, 2), (12, 2), (2, 12), (12, 12)):
        rect(a, px, py, 2, 2, (60, 24, 4))
    return a


GOOMBA_ROWS = [
    "......DDDD......",
    "....DDBBBBDD....",
    "...DBBBBBBBBD...",
    "..DBBBBBBBBBBD..",
    ".DBKKBBBBBBKKBD.",
    ".DBBWKBBBBKWBBD.",
    "DBBBWKKBBKKWBBBD",
    "DBBBWWKBBKWWBBBD",
    "DBBBBBBBBBBBBBBD",
    ".DBBBBBBBBBBBBD.",
    "..DDDTTTTTTDDD..",
    "....DTTTTTTD....",
    "...DKKTTTTKKD...",
    "..DKKKKDDKKKKD..",
    "..DKKKKD.DKKKD..",
    "...DDDD...DDD...",
]
GOOMBA_C = {"D": (60, 20, 0), "B": (180, 70, 20), "K": (20, 10, 5), "W": (250, 240, 220), "T": (240, 190, 140)}

KOOPA_ROWS = [
    "..OOO...........",
    ".OYYYO..........",
    "OYYKYYO.........",
    "OYYKYYO.........",
    "OYYYYYYO........",
    ".OYYYYYO........",
    "..OYYYO.OOOOO...",
    "..OYYO.OGGLGGO..",
    "..OYYOOGLGGGLGO.",
    "...OYOGGGLGGGLGO",
    "...OYOGLGGGLGGGO",
    "...OOOGGGLGGGLGO",
    "....OGGLGGGLGGGO",
    "....OWWWWWWWWWWO",
    ".....OOOOOOOOOO.",
    "......OYYO.OYYO.",
    ".....OYYYO.OYYYO",
    ".....OOOOO.OOOOO",
]
KOOPA_C = {"O": (20, 60, 10), "Y": (250, 210, 90), "K": (10, 10, 10), "G": (40, 170, 40),
           "L": (140, 230, 90), "W": (250, 250, 240)}

STAR_ROWS = [
    ".......##.......",
    "......####......",
    "......####......",
    ".....######.....",
    "################",
    ".##############.",
    "..#####K#K####..",
    "...####K#K###...",
    "....#########...",
    "....#########...",
    "...###########..",
    "...####...####..",
    "..###.......###.",
    "..##.........##.",
]


def star_sprite(col):
    return outline(pix(STAR_ROWS, {"#": col, "K": (20, 20, 20)}), (120, 60, 0))


def coin_sprite(w):
    a = surf(10, 14)
    yy, xx = np.mgrid[0:14, 0:10]
    if w <= 2:
        rect(a, 4, 1, 2, 12, (230, 140, 10))
        rect(a, 4, 1, 1, 12, (255, 240, 150))
        return a
    m = ((xx - 4.5) / (w / 2.0)) ** 2 + ((yy - 6.5) / 6.5) ** 2 <= 1
    a[m] = rgba((255, 210, 30))
    inner = ((xx - 4.5) / (w / 2.0 - 1.5)) ** 2 + ((yy - 6.5) / 5.0) ** 2 <= 1
    a[m & ~inner] = rgba((200, 110, 0))
    rect(a, 4, 4, 1, 6, (255, 250, 200))
    return a


def pipe_sprite(h):
    a = surf(34, h)
    rect(a, 2, 0, 30, h, (0, 60, 0))
    rect(a, 3, 0, 28, h, (0, 168, 0))
    rect(a, 6, 0, 4, h, (140, 240, 80))
    rect(a, 24, 0, 5, h, (0, 100, 0))
    rect(a, 0, 0, 34, 13, (0, 60, 0))
    rect(a, 1, 1, 32, 11, (0, 168, 0))
    rect(a, 4, 1, 4, 11, (140, 240, 80))
    rect(a, 25, 1, 6, 11, (0, 100, 0))
    return a


def castle_sprite():
    a = surf(96, 88)
    def bricks(x, y, w, h):
        rect(a, x, y, w, h, (200, 76, 12))
        for yy in range(y, y + h, 6):
            rect(a, x, yy, w, 1, (60, 20, 0))
            off = 0 if ((yy - y) // 6) % 2 == 0 else 6
            for xx in range(x + off, x + w, 12):
                rect(a, xx, yy, 1, 6, (60, 20, 0))
    bricks(0, 40, 96, 48)
    for i in range(0, 96, 16):
        bricks(i, 32, 10, 8)
    bricks(24, 8, 48, 24)
    for i in range(24, 72, 12):
        bricks(i, 0, 8, 8)
    rect(a, 36, 14, 8, 12, BLACK)
    rect(a, 52, 14, 8, 12, BLACK)
    yy, xx = np.mgrid[0:88, 0:96]
    door = ((xx >= 38) & (xx < 58) & (yy >= 62)) | (((xx - 48) ** 2 + (yy - 62) ** 2) <= 100)
    a[door] = rgba(BLACK)
    return a


def flag_sprite():
    rows = [
        "################",
        ".###############",
        "..##############",
        "...###GG##GG####",
        "....##GGG#GG####",
        ".....#GG#GGG####",
        "......#G##GG####",
        ".......#########",
        "........########",
        ".........#######",
        "..........######",
        "...........#####",
        "............####",
        ".............###",
    ]
    return pix(rows, {"#": WHITE, "G": (40, 180, 50)})


# ---------------------------------------------------------------- Naiwa sprites (人设来自 mario_sprites.py)
NAIWA = {
    ("idle", 0): NaiwaMarioPixelArt.create_ingame_sprite("idle", 0),
    ("idle", 1): NaiwaMarioPixelArt.create_ingame_sprite("idle", 1),
    ("run", 0): NaiwaMarioPixelArt.create_ingame_sprite("run", 0),
    ("run", 1): NaiwaMarioPixelArt.create_ingame_sprite("run", 1),
    ("run", 2): NaiwaMarioPixelArt.create_ingame_sprite("run", 2),
    ("jump", 0): NaiwaMarioPixelArt.create_ingame_sprite("jump", 0),
    ("laugh", 0): NaiwaMarioPixelArt.create_ingame_sprite("laugh", 0),
}
PORTRAIT = NaiwaMarioPixelArt.create_large_portrait()
STAR_COLS = [(255, 70, 70), (255, 200, 30), (60, 220, 255), (255, 255, 255)]
_tint_cache = {}


def naiwa_sprite(pose, fi, tint=None):
    key = (pose, fi if pose in ("idle", "run") else 0)
    spr = NAIWA[key]
    if tint is None:
        return spr
    ck = key + (tint,)
    if ck not in _tint_cache:
        t = spr.copy()
        m = t[:, :, 3] > 0
        t[m, :3] = (t[m, :3] * 0.45 + np.array(STAR_COLS[tint]) * 0.55).astype(np.uint8)
        _tint_cache[ck] = t
    return _tint_cache[ck]


# ---------------------------------------------------------------- timeline
class Track:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.fr = []
        self.marks = {}
        self.dist = 0.0
        self.star = False

    def _add(self, pose, **kw):
        d = dict(x=self.x, y=self.y, pose=pose, fi=0, star=self.star, flip=False)
        d.update(kw)
        self.fr.append(d)

    def mark(self, name):
        self.marks[name] = len(self.fr) - 1

    def idle(self, dur, pose="idle", **kw):
        for i in range(round(dur * FPS)):
            self._add(pose, fi=(i // 8) % 2, t=i, **kw)

    def run(self, dur, v):
        for i in range(round(dur * FPS)):
            self.x += v / FPS
            self.dist += v / FPS
            self._add("run", fi=int(self.dist / 9) % 3)

    def jump(self, dur, v, y1=None, h=40, name=None):
        y0 = self.y
        y1 = y0 if y1 is None else y1
        n = round(dur * FPS)
        start = len(self.fr)
        for i in range(1, n + 1):
            s = i / n
            self.x += v / FPS
            self.y = y0 + (y1 - y0) * s - 4 * h * s * (1 - s)
            self._add("jump")
        self.y = y1
        seg = self.fr[start:]
        if name:
            k = min(range(len(seg)), key=lambda j: seg[j]["y"])
            self.marks[name] = start + k
        self.marks[(name or "j") + "_t0"] = start
        self.marks[(name or "j") + "_t1"] = len(self.fr) - 1
        return start, len(self.fr) - 1


def build():
    tr = Track(60, G)
    tr.idle(0.3)
    tr.run(0.5, 120)
    tr.jump(0.6, 120, h=42, name="block1")
    tr.run(0.35, 120)
    tr.jump(0.55, 120, y1=G - 14, h=32)
    tr.mark("stomp1")
    tr.jump(0.3, 120, y1=G, h=18)
    tr.run(0.25, 120)
    tr.jump(0.7, 120, h=60, name="pipe")
    tr.run(0.25, 120)
    tr.jump(0.6, 120, h=42, name="block2")
    tr.run(0.55, 120)
    tr.mark("star_get")
    tr.idle(0.35, pose="jump", freeze=True)
    tr.star = True
    tr.run(0.3, 220)
    tr.mark("k1")
    tr.run(0.3, 220)
    tr.mark("k2")
    tr.run(0.15, 220)
    tr.jump(0.65, 220, h=50, name="pit")
    tr.run(0.25, 220)
    tr.mark("k3")
    tr.run(0.3, 220)
    tr.star = False
    tr.mark("star_end")
    tr.run(0.4, 130)
    tr.jump(0.6, 120, h=42, name="brick")
    tr.run(0.35, 120)
    tr.jump(0.55, 70, y1=G - 32, h=18, name="stairA")
    xA = tr.x
    tr.jump(0.55, 70, y1=G - 64, h=18)
    tr.run(0.15, 64)
    tr.jump(0.9, 115, y1=G - 132, h=30)
    tr.mark("pole")
    pole_x = tr.x + 10
    n = round(0.8 * FPS)
    y0 = tr.y
    for i in range(1, n + 1):
        tr.y = y0 + (G - 16 - y0) * i / n
        tr._add("jump", flip=True)
    tr.mark("slide_end")
    tr.jump(0.4, 80, y1=G, h=16)
    tr.run(0.9, 75)
    tr.mark("arrive")
    rest = TOTAL - WORLD_END - len(tr.fr)
    assert rest >= 100, rest
    tr.idle(0.3)
    tr.mark("laugh")
    for i in range(rest - 9):
        tr._add("laugh", t=i)
    return tr, xA, pole_x


TR, XA, POLE_X = build()
M = TR.marks
FR = TR.fr
LEVEL_W = int(POLE_X + 337)
CASTLE_X = int(POLE_X + 52)


def gtime(gf):
    return (WORLD_END + gf) / FPS


# ---- world objects derived from trajectory
def block_at(mark):
    f = FR[M[mark]]
    return int(round(f["x"])) - 8, int(round(f["y"] - 48)) - 16, M[mark]


B1X, B1Y, B1F = block_at("block1")
B2X, B2Y, B2F = block_at("block2")
BRX, BRY, BRF = block_at("brick")
PIPE_CX = int(round(FR[M["pipe"]]["x"]))
PIPE_H = 30
PIT0 = int(FR[M["pit_t0"]]["x"] + 16)
PIT1 = int(FR[M["pit_t1"]]["x"] - 16)
STAIR_X = int(round(XA - 24))

ENEMIES = [
    dict(kind="goomba", f=M["stomp1"], x=FR[M["stomp1"]]["x"], v=25, death="stomp"),
    dict(kind="goomba", f=M["k1"], x=FR[M["k1"]]["x"] + 18, v=12, death="kick"),
    dict(kind="goomba", f=M["k2"], x=FR[M["k2"]]["x"] + 18, v=12, death="kick"),
    dict(kind="koopa", f=M["k3"], x=FR[M["k3"]]["x"] + 18, v=12, death="kick"),
]

PIT_COINS = []
t0, t1 = M["pit_t0"], M["pit_t1"]
for s in (0.15, 0.32, 0.5, 0.68, 0.85):
    fidx = int(t0 + (t1 - t0) * s)
    PIT_COINS.append((FR[fidx]["x"] + 4, FR[fidx]["y"] - 28, fidx))

# 分数事件 (frame, points, coins, popup text, x, y)
SCORE = [
    (B1F + 10, 200, 1, "200", B1X + 8, B1Y - 30),
    (M["stomp1"], 100, 0, "100", ENEMIES[0]["x"], G - 30),
    (M["star_get"], 1000, 0, "1000", FR[M["star_get"]]["x"], FR[M["star_get"]]["y"] - 60),
    (M["k1"], 200, 0, "200", ENEMIES[1]["x"], G - 30),
    (M["k2"], 400, 0, "400", ENEMIES[2]["x"], G - 30),
    (M["k3"], 800, 0, "800", ENEMIES[3]["x"], G - 36),
    (BRF, 50, 0, "50", BRX + 8, BRY - 12),
    (M["pole"], 5000, 0, "5000", POLE_X + 6, FR[M["pole"]]["y"] - 50),
]
for cx, cy, cf in PIT_COINS:
    SCORE.append((cf, 200, 1, "", cx, cy))

TIME_START = 400
POLE_TIME = TIME_START - M["pole"] // 12
TALLY_F0 = M["laugh"] + 24
TALLY_LEN = 36


def hud_values(gf):
    sc = sum(p for f, p, *_ in SCORE if f <= gf)
    coins = sum(c for f, _, c, *_ in SCORE if f <= gf)
    if gf < M["pole"]:
        tm = TIME_START - max(0, gf) // 12
    else:
        p = min(1.0, max(0.0, (gf - TALLY_F0) / TALLY_LEN))
        tm = int(round(POLE_TIME * (1 - p)))
        sc += (POLE_TIME - tm) * 50
    return sc, coins, tm


# ---------------------------------------------------------------- static layers
GT, BT, HB = ground_tile(), brick_tile(), hard_block()
QB = [q_block(i) for i in range(3)]
UB = used_block()
PIPE = pipe_sprite(PIPE_H)
CASTLE = castle_sprite()
FLAG = flag_sprite()
GOOMBA = outline(pix(GOOMBA_ROWS, GOOMBA_C), (0, 0, 0))[1:-1, 1:-1].copy()
GOOMBA_FLAT = GOOMBA[::2].copy()
KOOPA = pix(KOOPA_ROWS, KOOPA_C)
COINS = [coin_sprite(w) for w in (9, 6, 2, 6)]
CLOUD = circle_blob(48, 26, [(12, 16, 9), (24, 11, 11), (36, 16, 9), (24, 18, 8)], WHITE, (60, 90, 200), (220, 230, 255))
CLOUD_S = circle_blob(30, 20, [(9, 12, 7), (19, 9, 8), (22, 13, 6)], WHITE, (60, 90, 200), (220, 230, 255))
HILL = circle_blob(110, 48, [(55, 50, 46)], (0, 168, 68), (0, 90, 30))
HILL_S = circle_blob(64, 28, [(32, 30, 26)], (0, 168, 68), (0, 90, 30))
for hsp, pts in ((HILL, [(46, 22), (62, 22), (54, 32)]), (HILL_S, [(28, 14), (36, 14)])):
    for px, py in pts:
        rect(hsp, px, py, 2, 4, (0, 90, 30))
BUSH = circle_blob(50, 18, [(12, 14, 9), (25, 10, 11), (38, 14, 9)], (120, 220, 40), (0, 110, 0))

FG = surf(LEVEL_W, H)
for x in range(0, LEVEL_W, 16):
    if x + 16 > PIT0 and x < PIT1:
        continue
    for y in range(G, H, 16):
        blit(FG, GT, x, y)
for col in range(5):
    hgt = min(col + 1, 4)
    for r in range(hgt):
        blit(FG, HB, STAIR_X + col * 16, G - 16 * (r + 1))
blit(FG, PIPE, PIPE_CX - 17, G - PIPE_H)
blit(FG, HB, int(POLE_X) - 8, G - 16)
blit(FG, CASTLE, CASTLE_X, G - CASTLE.shape[0])
PIT0_SNAP = (PIT0 // 16 + (1 if PIT0 % 16 else 0)) * 16 - 16


def draw_background(img, cam):
    img[:, :] = SKY
    for i in range(14):
        wx = i * 170 + (i * 73) % 60
        sx = wx - cam * 0.5
        sx = (sx + 200) % (14 * 170 * 0.5 + 600) - 200 if False else sx
        if -60 < sx < W + 10:
            blit(img, CLOUD if i % 3 else CLOUD_S, sx, 28 + (i * 37) % 46)
    for i in range(10):
        wx = i * 260 + (i * 91) % 80
        sx = wx - cam * 0.75
        if -120 < sx < W + 10:
            sp = HILL if i % 2 == 0 else HILL_S
            blit(img, sp, sx, G - sp.shape[0] + 2)
    for i in range(12):
        wx = 140 + i * 233 + (i * 53) % 70
        if PIT0 - 60 < wx < PIT1 + 10 or abs(wx - PIPE_CX) < 50 or wx > STAIR_X - 60:
            continue
        sx = wx - cam
        if -60 < sx < W + 10:
            blit(img, BUSH, sx, G - BUSH.shape[0] + 1)


# ---------------------------------------------------------------- per-frame helpers
def cam_at(gf):
    gf = min(gf, len(FR) - 1)
    best = 0.0
    # 只前进的镜头
    x = FR[gf]["x"] - 200
    return float(np.clip(x, 0, LEVEL_W - W))


CAMS = []
_c = 0.0
for i in range(len(FR)):
    _c = max(_c, cam_at(i))
    CAMS.append(_c)


def draw_block(img, cam, bx, by, hit_f, gf, kind):
    bump = 0
    if hit_f <= gf < hit_f + 8:
        bump = -int(round(math.sin((gf - hit_f) / 8 * math.pi) * 6))
    sx = bx - cam
    if kind == "q":
        sp = UB if gf >= hit_f else QB[[0, 0, 1, 2, 1, 0][(gf // 6) % 6]]
        blit(img, sp, sx, by + bump)
    elif kind == "brick":
        if gf < hit_f:
            blit(img, BT, sx, by)


def draw_world(img, gf):
    cam = CAMS[min(gf, len(CAMS) - 1)]
    draw_background(img, cam)
    # 星星（藏在砖块后面升起）
    rise = 10
    sg = M["star_get"]
    if B2F <= gf < sg:
        col = STAR_COLS[(gf // 2) % 4]
        if gf < B2F + rise:
            p = (gf - B2F) / rise
            blit(img, star_sprite(col), B2X - cam, B2Y - 16 * p)
        else:
            s = (gf - B2F - rise) / max(1, sg - B2F - rise)
            nx, ny = FR[sg]["x"], FR[sg]["y"] - 30
            x = B2X + (nx - 8 - B2X) * s
            y0 = B2Y - 16
            y = y0 + (ny - 8 - y0) * s - 4 * 34 * s * (1 - s)
            blit(img, star_sprite(col), x - cam, y)
    # 前景静态层
    blit(img, FG[:, int(cam):int(cam) + W], 0, 0)
    # 方块
    draw_block(img, cam, B1X - 16, B1Y, 10 ** 9, gf, "brick")
    draw_block(img, cam, B1X + 16, B1Y, 10 ** 9, gf, "brick")
    draw_block(img, cam, B1X, B1Y, B1F, gf, "q")
    draw_block(img, cam, B2X, B2Y, B2F, gf, "q")
    draw_block(img, cam, BRX - 16, BRY, 10 ** 9, gf, "brick")
    draw_block(img, cam, BRX + 16, BRY, 10 ** 9, gf, "brick")
    draw_block(img, cam, BRX, BRY, BRF, gf, "brick")
    # 金币弹出
    if B1F <= gf < B1F + 14:
        t = (gf - B1F) / FPS
        y = B1Y - 14 - (230 * t - 0.5 * 980 * t * t)
        blit(img, COINS[(gf // 2) % 4], B1X + 3 - cam, y)
    # 碎砖
    if BRF <= gf < BRF + 30:
        t = (gf - BRF) / FPS
        for vx, vy, dx, dy in ((-70, -230, 0, 0), (70, -230, 8, 0), (-50, -150, 0, 8), (50, -150, 8, 8)):
            px = BRX + dx + vx * t - cam
            py = BRY + dy + vy * t + 0.5 * 900 * t * t
            rect(img, int(px), int(py), 6, 6, (60, 20, 0))
            rect(img, int(px), int(py), 5, 5, (200, 76, 12) if (gf // 2) % 2 else (252, 160, 110))
    # 深坑上方金币
    for cx, cy, cf in PIT_COINS:
        if gf < cf:
            blit(img, COINS[(gf // 4) % 4], cx - 5 - cam, cy - 7)
        elif gf < cf + 6:
            r = (gf - cf) * 2
            for ang in range(0, 360, 90):
                a = math.radians(ang + 45)
                rect(img, int(cx - cam + math.cos(a) * r), int(cy + math.sin(a) * r), 2, 2, WHITE)
    # 敌人
    for e in ENEMIES:
        f0 = e["f"]
        if gf < f0:
            x = e["x"] + e["v"] * (f0 - gf) / FPS
            if x - cam > W + 20:
                continue
            if e["kind"] == "goomba":
                blit(img, GOOMBA, x - 8 - cam, G - 16, flipx=(gf // 6) % 2 == 1)
            else:
                spr = KOOPA if (gf // 6) % 2 == 0 else KOOPA[:, :]
                blit(img, spr, x - 8 - cam, G - KOOPA.shape[0] + ((gf // 6) % 2))
        elif e["death"] == "stomp":
            if gf < f0 + 14:
                blit(img, GOOMBA_FLAT, e["x"] - 8 - cam, G - 8)
        else:
            t = (gf - f0) / FPS
            x = e["x"] + 90 * t
            y = -170 * t + 0.5 * 900 * t * t
            spr = GOOMBA if e["kind"] == "goomba" else KOOPA
            if G - spr.shape[0] + y < H:
                blit(img, spr, x - 8 - cam, G - spr.shape[0] + y, flipy=True)
            if gf < f0 + 5:
                for k in range(6):
                    a = k * math.pi / 3
                    r = 6 + (gf - f0) * 3
                    rect(img, int(e["x"] - cam + math.cos(a) * r), int(G - 10 + math.sin(a) * r), 2, 2, WHITE)
    # 旗杆
    px = int(POLE_X - cam)
    rect(img, px - 1, G - 178, 2, 162, (40, 120, 30))
    rect(img, px - 1, G - 178, 1, 162, (150, 240, 110))
    yy, xx = np.mgrid[-4:5, -4:5]
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            if dx * dx + dy * dy <= 16:
                c = (0, 110, 0) if dx * dx + dy * dy > 9 else ((90, 210, 60) if dx < 0 and dy < 0 else (0, 168, 0))
                rect(img, px + dx, G - 182 + dy, 1, 1, c)
    fy = G - 172
    if gf >= M["pole"]:
        p = min(1.0, (gf - M["pole"]) / max(1, M["slide_end"] - M["pole"]))
        fy = int(G - 172 + (G - 36 - (G - 172)) * p)
    blit(img, FLAG, px - 17, fy)
    # 城堡旗帜
    if gf >= M["arrive"]:
        p = min(1.0, (gf - M["arrive"]) / 18)
        cfx = CASTLE_X + 48 - cam
        rect(img, int(cfx), G - CASTLE.shape[0] - 18, 1, 18, (60, 20, 0))
        small = FLAG[::2, ::2]
        blit(img, small, cfx + 1, G - CASTLE.shape[0] - 2 - 14 * p, flipx=True)
    return cam


def draw_naiwa(img, gf, cam):
    f = FR[min(gf, len(FR) - 1)]
    tint = None
    if f.get("freeze"):
        tint = (gf // 2) % 4 if (gf // 2) % 2 == 0 else None
    elif f["star"]:
        tint = (gf // 2) % 4
        for back, al in ((6, 0.25), (3, 0.45)):
            g2 = max(0, gf - back)
            f2 = FR[g2]
            spr2 = naiwa_sprite(f2["pose"], f2["fi"], (gf // 2 + 1) % 4)
            blit(img, spr2, f2["x"] - 24 - cam, f2["y"] - 52, alpha=al)
    x, y = f["x"], f["y"]
    pose = f["pose"]
    if pose == "laugh":
        t = f.get("t", 0)
        x += (1 if (t // 2) % 2 else -1)
        y -= (2 if (t // 4) % 2 else 0)
    spr = naiwa_sprite(pose, f["fi"], tint)
    blit(img, spr, x - 24 - cam, y - 52, flipx=f.get("flip", False))
    if f["star"] or f.get("freeze"):
        for k in range(4):
            a = gf * 0.5 + k * math.pi / 2
            rect(img, int(x - cam + math.cos(a) * 22), int(y - 26 + math.sin(a) * 26), 2, 2, WHITE)


def draw_popups(img, gf, cam):
    for f, p, c, s, x, y in SCORE:
        if s and f <= gf < f + 20:
            text(img, int(x - cam), int(y - (gf - f) * 1.2), s, WHITE, 1, center=True)


def draw_hud(img, gf, show=True):
    sc, coins, tm = hud_values(gf)
    text(img, 32, 10, "NAIWA")
    text(img, 32, 20, f"{sc:06d}")
    blit(img, COINS[(max(gf, 0) // 6) % 4 if gf > 0 else 0][::1, ::1], 150, 18)
    text(img, 162, 20, f"x{coins:02d}")
    text(img, 260, 10, "WORLD")
    text(img, 266, 20, "1-1")
    text(img, 380, 10, "TIME")
    if show:
        text(img, 386, 20, f"{tm:03d}")


FIREWORKS = [(M["laugh"] + 6, 0.30, 70), (M["laugh"] + 22, 0.62, 52), (M["laugh"] + 40, 0.45, 40),
             (M["laugh"] + 62, 0.75, 62), (M["laugh"] + 84, 0.25, 48)]
FW_COLS = [(255, 90, 90), (255, 230, 80), (120, 220, 255), (180, 255, 120), (255, 140, 230)]


def draw_fireworks(img, gf):
    for i, (f0, fx, fy) in enumerate(FIREWORKS):
        t = (gf - f0) / FPS
        if 0 <= t < 0.9:
            cx, cy = fx * W, fy
            r = 46 * (1 - math.exp(-5 * t))
            col = FW_COLS[i % len(FW_COLS)]
            for k in range(16):
                a = k * math.pi / 8
                for tr_ in (0, 0.25):
                    rr = r * (1 - tr_)
                    x = cx + math.cos(a) * rr
                    y = cy + math.sin(a) * rr + 30 * t * t
                    if t < 0.75 or (gf // 2) % 2:
                        rect(img, int(x), int(y), 2 if tr_ == 0 else 1, 2 if tr_ == 0 else 1, col if tr_ == 0 else WHITE)


def draw_ending(img, gf, cam):
    lf = M["laugh"]
    if gf < lf:
        return
    t = gf - lf
    f = FR[min(gf, len(FR) - 1)]
    hx, hy = f["x"] - cam, f["y"] - 60
    words = [(-34, -6), (20, -14), (-14, -26), (30, 2), (-40, -24)]
    for k, (dx, dy) in enumerate(words):
        st = k * 6
        cyc = (t - st) % 30
        if t >= st and cyc < 22:
            text(img, int(hx + dx - 9), int(hy + dy - cyc * 0.6), "HA!", (255, 230, 60), 1)
    if t >= 24:
        bw, bh = 196, 44
        bx, by = W // 2 - bw // 2, 44
        rect(img, bx - 2, by - 2, bw + 4, bh + 4, WHITE)
        rect(img, bx, by, bw, bh, (30, 50, 160))
        text(img, W // 2, by + 8, "COURSE CLEAR!", (255, 230, 60), 2, center=True)
        sc, _, _ = hud_values(gf)
        text(img, W // 2, by + 30, f"SCORE {sc:06d}", WHITE, 1, center=True)


def render_title(img, f):
    img[:, :] = SKY
    blit(img, CLOUD, 40, 36)
    blit(img, CLOUD_S, 380, 26)
    blit(img, HILL, 0, G - HILL.shape[0] + 2)
    blit(img, BUSH, 220, G - BUSH.shape[0] + 1)
    for x in range(0, W, 16):
        for y in range(G, H, 16):
            blit(img, GT, x, y)
    px, py, pw, ph = 26, 46, 262, 118
    rect(img, px, py, pw, ph, (60, 20, 0))
    rect(img, px + 2, py + 2, pw - 4, ph - 4, (200, 76, 12))
    rect(img, px + 2, py + 2, pw - 4, 2, (252, 188, 140))
    for rx, ry in ((px + 6, py + 6), (px + pw - 9, py + 6), (px + 6, py + ph - 9), (px + pw - 9, py + ph - 9)):
        rect(img, rx, ry, 3, 3, (60, 20, 0))
    text(img, px + 18, py + 14, "SUPER", CREAM, 2)
    text(img, px + 18, py + 38, "NAIWA", CREAM, 4)
    text(img, px + 18, py + 76, "WORLD", CREAM, 4)
    text(img, px + 186, py + 92, "2026", CREAM, 1)
    bob = 0 if (f // 10) % 2 == 0 else -2
    blit(img, PORTRAIT, 306, G - 160 + bob)
    text(img, 157, 182, "1 PLAYER GAME", WHITE, 1, center=False)
    blink = (f // 8) % 2 == 0 if f < 34 else (f // 2) % 2 == 0
    if blink:
        text(img, 163, 198, "PRESS START", (255, 230, 60), 1)
    draw_hud(img, 0)


def render_world_card(img, f):
    img[:, :] = BLACK
    draw_hud(img, 0, show=False)
    text(img, W // 2, 96, "WORLD 1-1", WHITE, 2, center=True)
    blit(img, naiwa_sprite("idle", 0), 186, 128)
    text(img, 248, 150, "x  3", WHITE, 2)


def render_frame(f):
    img = np.zeros((H, W, 3), np.uint8)
    if f < TITLE_END:
        render_title(img, f)
        return img
    if f < WORLD_END:
        render_world_card(img, f)
        return img
    gf = f - WORLD_END
    cam = draw_world(img, gf)
    draw_naiwa(img, gf, cam)
    draw_popups(img, gf, cam)
    draw_fireworks(img, gf)
    draw_ending(img, gf, cam)
    draw_hud(img, gf)
    fade0 = TOTAL - 12
    if f >= fade0:
        k = (f - fade0 + 1) / 13
        img[:] = (img * (1 - k)).astype(np.uint8)
    return img


# ---------------------------------------------------------------- audio
def nf(name):
    if name == "r":
        return 0.0
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    n = names[name[0]]
    rest = name[1:]
    if rest.startswith("#"):
        n += 1
        rest = rest[1:]
    midi = 12 * (int(rest) + 1) + n
    return 440.0 * 2 ** ((midi - 69) / 12)


def sq(freq, dur, duty=0.5, vol=0.2, decay=3.0):
    n = int(dur * SR)
    if freq <= 0 or n <= 0:
        return np.zeros(max(n, 0))
    t = np.arange(n) / SR
    w = np.where((t * freq) % 1 < duty, 1.0, -1.0)
    env = np.exp(-decay * t) * np.minimum(1, (n - np.arange(n)) / (0.01 * SR))
    return w * env * vol


def tri(freq, dur, vol=0.25):
    n = int(dur * SR)
    if freq <= 0 or n <= 0:
        return np.zeros(max(n, 0))
    t = np.arange(n) / SR
    w = 2 * np.abs(2 * ((t * freq) % 1) - 1) - 1
    env = np.minimum(1, (n - np.arange(n)) / (0.01 * SR))
    return w * env * vol


def noise(dur, vol=0.2, decay=20.0, seed=0):
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    return rng.uniform(-1, 1, n) * np.exp(-decay * t) * vol


def slide(f0, f1, dur, duty=0.5, vol=0.2):
    n = int(dur * SR)
    fr = np.linspace(f0, f1, n)
    ph = np.cumsum(fr) / SR
    env = np.minimum(1, (n - np.arange(n)) / (0.01 * SR))
    return np.where(ph % 1 < duty, 1.0, -1.0) * vol * env


class Mixer:
    def __init__(self, sec):
        self.buf = np.zeros(int(sec * SR) + SR)

    def add(self, clip, t, vol=1.0):
        s = int(t * SR)
        if s < 0 or s >= len(self.buf):
            return
        e = min(len(self.buf), s + len(clip))
        self.buf[s:e] += clip[:e - s] * vol


MAIN_MEL = [
    ("C5", 1), ("E5", 1), ("G5", 1), ("E5", 1), ("C6", 2), ("G5", 2),
    ("A5", 1), ("G5", 1), ("E5", 1), ("C5", 1), ("D5", 2), ("E5", 2),
    ("F5", 1), ("A5", 1), ("C6", 1), ("A5", 1), ("G5", 1), ("F5", 1), ("E5", 1), ("D5", 1),
    ("G5", 3), ("r", 1), ("G4", 1), ("A4", 1), ("B4", 1), ("D5", 1),
    ("E5", 1), ("G5", 1), ("C6", 1), ("G5", 1), ("E6", 2), ("D6", 2),
    ("C6", 1), ("A5", 1), ("F5", 1), ("A5", 1), ("C6", 2), ("A5", 2),
    ("B5", 1), ("A5", 1), ("G5", 1), ("F5", 1), ("E5", 1), ("D5", 1), ("B4", 1), ("D5", 1),
    ("C5", 3), ("r", 1), ("G4", 2), ("C5", 2),
]
MAIN_BASS = ["C3", "A2", "F2", "G2", "C3", "F2", "G2", "C3"]


def main_theme(mx, t0, t1, vol=1.0):
    e = 0.2
    loop = 64 * e
    base = t0
    while base < t1:
        t = base
        for note, ln in MAIN_MEL:
            if t >= t1:
                break
            if note != "r":
                mx.add(sq(nf(note), ln * e * 0.92, 0.25, 0.10, 2.5), t, vol)
            t += ln * e
        for bar, root in enumerate(MAIN_BASS):
            rf = nf(root)
            for q, mul in enumerate((1, 1.5, 2, 1.5)):
                bt = base + bar * 8 * e + q * 2 * e
                if bt < t1:
                    mx.add(tri(rf * mul, 2 * e * 0.85, 0.22), bt, vol)
                    mx.add(noise(0.04, 0.05, 60, seed=q), bt + e, vol)
                    if q % 2 == 0:
                        mx.add(slide(140, 50, 0.08, 0.5, 0.12), bt, vol)
        base += loop


def star_theme(mx, t0, t1):
    s16 = 60 / 190 / 4
    pats = [("F5", "A5", "C6", "A5"), ("E5", "G5", "C6", "G5")]
    bass = ["F2", "C3"]
    i = 0
    t = t0
    while t < t1:
        bar = (i // 16) % 2
        n = pats[bar][i % 4]
        mx.add(sq(nf(n), s16 * 0.9, 0.5, 0.09, 6), t, 1.0)
        if i % 2 == 0:
            mx.add(tri(nf(bass[bar]) * (2 if (i // 2) % 2 else 1), s16 * 1.8, 0.22), t)
        if i % 4 == 2:
            mx.add(noise(0.05, 0.08, 50, seed=i), t)
        t += s16
        i += 1


def build_audio(path):
    mx = Mixer(TOTAL / FPS)
    # 标题音乐
    for k, n in enumerate(["C5", "E5", "G5", "C6", "G5", "E5", "G5", "C6"]):
        mx.add(sq(nf(n), 0.14, 0.5, 0.10, 4), 0.1 + k * 0.15)
    mx.add(tri(nf("C3"), 1.2, 0.2), 0.1)
    mx.add(sq(nf("E6"), 0.06, 0.5, 0.12), 34 / FPS)
    mx.add(sq(nf("C7"), 0.12, 0.5, 0.12), 34 / FPS + 0.07)
    # 背景音乐
    g = gtime
    main_theme(mx, g(0), g(M["star_get"]))
    star_theme(mx, g(M["star_get"]), g(M["star_end"]))
    main_theme(mx, g(M["star_end"]), g(M["pole"]))
    # 音效
    jumps = [k for k in M if isinstance(k, str) and k.endswith("_t0")]
    for k in jumps:
        mx.add(slide(320, 900, 0.16, 0.25, 0.10), g(M[k]))
    mx.add(slide(320, 900, 0.16, 0.25, 0.10), g(M["stomp1"]))
    for fb in (B1F, B2F, BRF):
        mx.add(slide(180, 90, 0.08, 0.5, 0.18), g(fb))
    mx.add(sq(nf("B5"), 0.07, 0.5, 0.13, 1), g(B1F))
    mx.add(sq(nf("E6"), 0.35, 0.5, 0.13, 6), g(B1F) + 0.07)
    for cx, cy, cf in PIT_COINS:
        mx.add(sq(nf("B5"), 0.06, 0.5, 0.10, 1), g(cf))
        mx.add(sq(nf("E6"), 0.22, 0.5, 0.10, 8), g(cf) + 0.06)
    mx.add(noise(0.12, 0.25, 25, 3), g(M["stomp1"]))
    mx.add(slide(400, 120, 0.1, 0.5, 0.15), g(M["stomp1"]))
    mx.add(slide(200, 800, 0.4, 0.5, 0.08), g(B2F))
    for k, n in enumerate(["C5", "G4", "C5", "E5", "G5", "C6", "G5", "C6", "E6", "G6"]):
        mx.add(sq(nf(n), 0.04, 0.5, 0.12, 1), g(M["star_get"]) + k * 0.035)
    for key in ("k1", "k2", "k3"):
        mx.add(noise(0.08, 0.25, 30, 7), g(M[key]))
        mx.add(slide(900, 300, 0.1, 0.25, 0.14), g(M[key]))
    mx.add(noise(0.35, 0.35, 10, 9), g(BRF))
    mx.add(slide(1200, 200, 0.8, 0.5, 0.10), g(M["pole"]))
    # 过关号角
    ft = g(M["slide_end"])
    for k, n in enumerate(["G4", "C5", "E5", "G5", "C6", "E6"]):
        mx.add(sq(nf(n), 0.11, 0.5, 0.12, 2), ft + k * 0.1)
        mx.add(tri(nf(n) / 4, 0.1, 0.2), ft + k * 0.1)
    mx.add(sq(nf("G6"), 0.5, 0.5, 0.12, 2), ft + 0.6)
    mx.add(sq(nf("E6"), 0.6, 0.5, 0.12, 2), ft + 1.1)
    mx.add(tri(nf("C3"), 1.1, 0.25), ft + 0.6)
    # 烟花
    for f0, _, _ in FIREWORKS:
        mx.add(slide(300, 1400, 0.25, 0.5, 0.05), g(f0) - 0.25)
        mx.add(noise(0.6, 0.35, 7, f0), g(f0))
        mx.add(slide(120, 40, 0.15, 0.5, 0.2), g(f0))
    # 大笑 HA HA HA
    lt = g(M["laugh"])
    k = 0
    while lt + k * 0.2 < TOTAL / FPS - 0.5:
        p = 1 + 0.08 * ((k * 7) % 5)
        mx.add(slide(760 * p, 520 * p, 0.11, 0.5, 0.11) * np.hanning(int(0.11 * SR)), lt + k * 0.2)
        k += 1
    # 计分
    for i in range(0, TALLY_LEN, 2):
        mx.add(sq(nf("C7"), 0.03, 0.5, 0.06, 1), g(TALLY_F0 + i))
    cc = g(M["laugh"] + 24)
    for k, n in enumerate(["C5", "E5", "G5"]):
        mx.add(sq(nf(n), 0.12, 0.5, 0.1), cc + k * 0.12)
    for n in ("C5", "E5", "G5", "C6"):
        mx.add(sq(nf(n), 1.4, 0.5, 0.06, 1.5), cc + 0.36)
    mx.add(tri(nf("C3"), 1.4, 0.25), cc + 0.36)
    out = mx.buf[: int(TOTAL / FPS * SR)]
    fade = int(0.4 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)
    out = np.tanh(out * 1.2) * 0.85
    data = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(data.tobytes())


# ---------------------------------------------------------------- render
def render(out_mp4, preview_dir=None):
    tmp = "/tmp/naiwa_world_render"
    os.makedirs(tmp, exist_ok=True)
    wav = os.path.join(tmp, "audio.wav")
    build_audio(wav)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav,
           "-vf", f"scale={W * SCALE}:{H * SCALE}:flags=neighbor",
           "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(TOTAL):
        p.stdin.write(render_frame(f).tobytes())
        if (f + 1) % 100 == 0:
            print(f"frame {f + 1}/{TOTAL}")
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg failed")
    print("saved", out_mp4)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getcwd(), "super_naiwa_world_20s.mp4")
    render(out)
