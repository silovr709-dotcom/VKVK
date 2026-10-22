#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ВЫРЕЗАНИЕ ФОНА (GrabCut)
========================
Модели сегментации в этой песочнице недоступны — они скачиваются с хостов,
которые закрыты. Поэтому режем по-старому: GrabCut из OpenCV плюс чистка
маски морфологией. Результат — PNG с альфой, дальше обложка сама решает,
куда и как его вписывать.

    python3 tools/cutout.py
"""

import os
import sys

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'tools', 'src')

# Прямоугольник-подсказка: примерно где стоят люди. Всё, что уверенно фон
# (левые и верхние углы кадра), GrabCut помечает сам.
HINT = {
    'team/new/rob-kate-novye.jpg': (0.24, 0.07, 1.0, 1.0),
}


def grab(name, hint=None):
    path = os.path.join(SRC, name)
    bgr = cv2.imread(path, cv2.IMREAD_COLOR)
    if bgr is None:
        raise SystemExit(f'не открылось: {path}')
    h, w = bgr.shape[:2]

    if hint is None:
        hint = HINT.get(name, (0.12, 0.06, 0.88, 0.98))
    x0 = int(w * hint[0]); y0 = int(h * hint[1])
    x1 = int(w * hint[2]); y1 = int(h * hint[3])
    rect = (max(0, x0), max(0, y0), min(w, x1) - max(0, x0), min(h, y1) - max(0, y0))

    mask = np.zeros((h, w), np.uint8)
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)

    # несколько проходов: первый черновой, дальше алгоритм уточняет границу
    for _ in range(4):
        cv2.grabCut(bgr, mask, rect, bgd, fgd, 3, cv2.GC_INIT_WITH_RECT)
        cv2.grabCut(bgr, mask, None, bgd, fgd, 3, cv2.GC_INIT_WITH_MASK)

    alpha = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)

    # убираем мусор и сглаживаем край
    k = np.ones((7, 7), np.uint8)
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, k)
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))

    # оставляем только самую крупную связную область — люди одни
    n, lab, stats, _ = cv2.connectedComponentsWithStats(alpha, 8)
    if n > 1:
        biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        alpha = np.where(lab == biggest, 255, 0).astype(np.uint8)

    # мягкий край: жёсткая граница сразу выдаёт вырезку
    alpha = cv2.GaussianBlur(alpha, (0, 0), 3)

    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    out = Image.fromarray(rgb, 'RGB').convert('RGBA')
    out.putalpha(Image.fromarray(alpha))
    return out


def report(img):
    a = np.asarray(img.getchannel('A'))
    ys, xs = np.where(a > 40)
    if len(xs) == 0:
        return 'маска пустая — вырезание не удалось'
    h, w = a.shape
    return (f'люди занимают x {xs.min()}…{xs.max()} из {w}, y {ys.min()}…{ys.max()} из {h}; '
            f'плотных пикселей {100.0 * (a > 200).mean():.1f}% кадра')


if __name__ == '__main__':
    for name in HINT:
        img = grab(name)
        dst = os.path.join(SRC, name.replace('.jpg', '-bez-fona.png'))
        img.save(dst)
        print(f'{os.path.relpath(dst, ROOT)}')
        print(f'   {report(img)}')
