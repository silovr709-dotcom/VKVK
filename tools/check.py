#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПРОВЕРКА МАКЕТОВ
================
Прогоняет генератор и следит за каждой нарисованной строкой:
не вылезла ли она за холст, не попала ли в зону, которую ВК обрежет.

    python3 tools/check.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import make_pack as M  # noqa: E402
from PIL import ImageDraw  # noqa: E402

# Зоны, которые ВК обрезает. Ключ — размер холста.
# Обложка 1920×768: верх ~130 px срезается на десктопе, низ ~200 px на
# телефоне, по бокам не видны полосы шире центральных 1120 px.
SAFE = {
    (1920, 768): (400, 140, 1520, 568),
}

problems = []
state = {'img': None, 'name': ''}

_cmaps = {}


def _cmap(path):
    if path not in _cmaps:
        from fontTools.ttLib import TTFont
        _cmaps[path] = set(TTFont(os.path.join(M.FONTS, path)).getBestCmap())
    return _cmaps[path]


def missing_glyphs(text, spec):
    """Кириллица и знаки лежат в разных поднаборах веб-шрифтов,
    поэтому проверяем литеру ровно в том файле, куда её отправит
    make_pack._pick."""
    cyr, lat = M.FONT_FILES[spec]
    out = []
    for ch in text:
        code = ord(ch)
        path = cyr if (0x0400 <= code <= 0x04FF or code in (0x0301, 0x2116)) else lat
        if code not in _cmap(path):
            out.append(ch)
    return out


def patched_draw(img, *args, **kwargs):
    d = ImageDraw.Draw.__wrapped__(img, *args, **kwargs) if hasattr(ImageDraw.Draw, '__wrapped__') else None
    return d


_orig_draw = ImageDraw.Draw


def draw_factory(img, *args, **kwargs):
    d = _orig_draw(img, *args, **kwargs)
    state['img'] = img
    return d


_orig_text = M.draw_text
_orig_save = M.save


def patched_text(draw, xy, text, spec, size, fill, tracking=0, anchor='la'):
    # литера, которой нет в шрифте, печатается пустым прямоугольником —
    # это первое, что выдаёт дешёвую вёрстку, поэтому ловим её здесь
    for ch in missing_glyphs(text, spec):
        problems.append(f'  ✗ {state["name"]}: в гарнитуре «{spec}» нет литеры '
                        f'«{ch}» (U+{ord(ch):04X}) — строка «{text[:38]}»')

    # декоративные элементы с прозрачностью (водяные знаки) не проверяем:
    # они намеренно выходят за край
    if isinstance(fill, tuple) and len(fill) == 4:
        return _orig_text(draw, xy, text, spec, size, fill, tracking, anchor)

    width = M.text_width(text, spec, size, tracking)
    x, y = xy
    if anchor == 'ma':
        x0 = x - width / 2
    elif anchor == 'ra':
        x0 = x - width
    else:
        x0 = x
    x1 = x0 + width

    # примерные границы глифов относительно базовой линии
    top = y - size * 0.92
    bottom = y + size * 0.30

    img = state['img']
    if img is not None:
        w, h = img.size
        name = state['name']

        if x0 < -2 or x1 > w + 2:
            problems.append(f'  ✗ {name}: «{text[:38]}» выходит по ширине '
                            f'({round(x0)}…{round(x1)} при {w})')
        if top < -2 or bottom > h + 2:
            problems.append(f'  ✗ {name}: «{text[:38]}» выходит по высоте '
                            f'({round(top)}…{round(bottom)} при {h})')

        box = SAFE.get((w, h))
        if box:
            sx0, sy0, sx1, sy1 = box
            if not (sx0 - 2 <= x0 and x1 <= sx1 + 2 and sy0 - 2 <= top and bottom <= sy1 + 2):
                problems.append(f'  ✗ {name}: «{text[:38]}» за безопасной зоной '
                                f'(x {round(x0)}…{round(x1)}, y {round(top)}…{round(bottom)})')
    return _orig_text(draw, xy, text, spec, size, fill, tracking, anchor)


def patched_save(img, path, quality=92):
    state['name'] = os.path.basename(path)
    return _orig_save(img, path, quality)


M.ImageDraw.Draw = draw_factory
M.draw_text = patched_text
M.save = patched_save

print('Проверяю макеты…\n')
M.main()

print('\n' + '=' * 60)
if problems:
    print(f'НАЙДЕНО ПРОБЛЕМ: {len(problems)}\n')
    for p in problems:
        print(p)
else:
    print('Проблем нет: весь текст внутри холста и безопасных зон.')
print('=' * 60)
