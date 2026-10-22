#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ГЕНЕРАТОР ПАКЕТА ОФОРМЛЕНИЯ СООБЩЕСТВА ВК
=========================================
Собирает все картинки для оформления сообщества «РЕцепт» (Тверь):
обложку, живую обложку, аватар, плитки меню, карточки услуг, сторис,
шаблоны постов, обложку видео и обложки альбомов.

Запуск:
    python3 tools/make_pack.py
    python3 tools/check.py     # проверить, что текст нигде не обрежется

Всё пересобирается из одного места: поправили текст в блоке ТЕКСТЫ,
положили другое фото в tools/src — и запустили заново.

Зависимости: Pillow (pip install Pillow)
"""

import os
import shutil
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

# ==================================================================
# ПУТИ
# ==================================================================

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'tools', 'src')
FONTS = os.path.join(ROOT, 'tools', 'fonts')
OUT = os.path.join(ROOT, 'vk')

# ==================================================================
# ПАЛИТРА
# Основа — глубокая синь почти в чёрное, тёплый свет и один металл.
# Роскошь здесь держится не на золоте, а на глубине теней: чем темнее
# поле, тем дороже выглядит лежащая на нём тонкая светлая линия.
# ==================================================================

INK = (19, 41, 74)
SOOT = (11, 26, 48)
ABYSS = (6, 14, 27)          # почти чёрная синь для глубоких плашек
CREAM = (255, 252, 247)
BONE = (246, 240, 231)
SAND = (236, 227, 213)
LINE = (221, 212, 197)
STONE = (107, 99, 92)
CLAY = (162, 152, 140)
GOLD = (122, 97, 60)
GOLDLINE = (182, 154, 99)
GOLDSOFT = (211, 189, 149)
GOLD_LIGHT = (232, 214, 176)

GOLD_ON_DARK = GOLDSOFT
CREAM_DIM = (206, 213, 229)
CREAM_SOFT = (178, 187, 208)

# ==================================================================
# ШРИФТЫ
# Кириллица и знаки пунктуации лежат в разных поднаборах (так
# устроены веб-шрифты), поэтому каждую литеру рисуем своим файлом.
# ==================================================================

FONT_FILES = {
    'display-light': ('cormorant-300-cyr.ttf', 'cormorant-300-lat.ttf'),
    'display': ('cormorant-400-cyr.ttf', 'cormorant-400-lat.ttf'),
    'display-italic': ('cormorant-400-italic-cyr.ttf', 'cormorant-400-italic-lat.ttf'),
    'sans': ('golos-400-cyr.ttf', 'golos-400-lat.ttf'),
    'sans-medium': ('golos-500-cyr.ttf', 'golos-500-lat.ttf'),
    'sans-bold': ('golos-600-cyr.ttf', 'golos-600-lat.ttf'),
}

_font_cache = {}


def _pair(spec, size):
    key = (spec, size)
    if key not in _font_cache:
        cyr, lat = FONT_FILES[spec]
        _font_cache[key] = (
            ImageFont.truetype(os.path.join(FONTS, cyr), size),
            ImageFont.truetype(os.path.join(FONTS, lat), size),
        )
    return _font_cache[key]


def _pick(fonts, ch):
    code = ord(ch)
    if 0x0400 <= code <= 0x04FF or code in (0x0301, 0x2116):
        return fonts[0]
    return fonts[1]


def text_width(text, spec, size, tracking=0):
    fonts = _pair(spec, size)
    total = sum(_pick(fonts, ch).getlength(ch) for ch in text)
    return total + tracking * max(0, len(text) - 1)


def draw_text(draw, xy, text, spec, size, fill, tracking=0, anchor='la'):
    """
    Рисует строку с разрядкой. anchor: 'la' — левый край по базовой линии,
    'ma' — по центру, 'ra' — по правому краю.
    """
    fonts = _pair(spec, size)
    width = text_width(text, spec, size, tracking)
    x, y = xy
    if anchor == 'ma':
        x -= width / 2
    elif anchor == 'ra':
        x -= width

    for ch in text:
        font = _pick(fonts, ch)
        draw.text((x, y), ch, font=font, fill=fill, anchor='ls')
        x += font.getlength(ch) + tracking


def wrap(text, spec, size, max_width, tracking=0):
    lines, current = [], ''
    for word in text.split():
        probe = (current + ' ' + word).strip()
        if text_width(probe, spec, size, tracking) <= max_width or not current:
            current = probe
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_paragraph(draw, xy, text, spec, size, fill, max_width, tracking=0,
                   leading=1.5, anchor='la'):
    # text может быть строкой (тогда переносим по словам) или списком строк
    if isinstance(text, (list, tuple)):
        lines = list(text)
    else:
        lines = wrap(text, spec, size, max_width, tracking)
    x, y = xy
    step = size * leading
    for line in lines:
        draw_text(draw, (x, y), line, spec, size, fill, tracking, anchor)
        y += step
    return y


# ==================================================================
# ФОТО И ЦВЕТОКОРРЕКЦИЯ
# ==================================================================

def photo(name, size, bright=1.0, focus=(0.5, 0.5)):
    """Открывает фото из tools/src, кадрирует под размер без искажений."""
    path = os.path.join(SRC, name)
    img = Image.open(path).convert('RGB')

    target_w, target_h = size
    ratio = target_w / target_h
    src_ratio = img.width / img.height

    if src_ratio > ratio:
        new_h = img.height
        new_w = int(new_h * ratio)
    else:
        new_w = img.width
        new_h = int(new_w / ratio)
        if new_h > img.height:
            new_h = img.height
            new_w = int(new_h * ratio)

    left = max(0, min(img.width - new_w, int((img.width - new_w) * focus[0])))
    top = max(0, min(img.height - new_h, int((img.height - new_h) * focus[1])))
    img = img.crop((left, top, left + new_w, top + new_h))
    img = img.resize(size, Image.LANCZOS)

    if bright != 1.0:
        img = ImageEnhance.Brightness(img).enhance(bright)
    return img


def grade(img, contrast=1.14, color=1.08, shadow=(228, 234, 255), highlight=(22, 14, 5)):
    """
    Плёночная цветокоррекция. Контраст и насыщенность — чтобы картинка
    перестала быть плоской, сплит-тонирование — чтобы тени ушли в холодную
    синь, а света остались тёплыми. Именно этот приём отличает дорогую
    картинку от «просто затемнённого фото».
    """
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Color(img).enhance(color)
    img = ImageChops.multiply(img, Image.new('RGB', img.size, shadow))
    img = ImageChops.screen(img, Image.new('RGB', img.size, highlight))
    return img


def warm_glow(img, cx=0.72, cy=0.16, radius=1.0, color=(255, 206, 140), strength=0.42,
              falloff=1.0):
    """Тёплое световое пятно. Плоская заливка — самый дешёвый фон, какой
    бывает: в природе и в печати ровного света не существует."""
    w, h = img.size
    big = Image.radial_gradient('L').resize((w * 2, h * 2), Image.LANCZOS)
    big = Image.eval(big, lambda v: 255 - v)
    left = int(w - cx * w)
    top = int(h - cy * h)
    mask = big.crop((left, top, left + w, top + h))
    if falloff != 1.0:
        # сжимаем градиент: свет остаётся пятном, а не заливает весь холст
        mask = mask.point(lambda v: int(255 * (v / 255) ** falloff))
    mask = Image.eval(mask, lambda v: int(v * strength * radius))
    glow = Image.new('RGB', (w, h), color)
    return Image.composite(ImageChops.screen(img, glow), img, mask)


def vignette(img, strength=0.5):
    """Затемнение по краям: взгляд уходит в центр, как на снимке
    с хорошим объективом."""
    w, h = img.size
    mask = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(mask)
    steps = 120
    for i in range(steps):
        t = i / steps
        inset_x = int(w * 0.5 * (1 - t))
        inset_y = int(h * 0.5 * (1 - t))
        value = int(255 * (1 - strength * (1 - t) ** 1.6))
        # заливаем: каждый следующий прямоугольник меньше и светлее,
        # поэтому центр остаётся чистым, а края уходят в тень
        d.rectangle([inset_x, inset_y, w - inset_x, h - inset_y], fill=value)
    mask = mask.filter(ImageFilter.GaussianBlur(int(min(w, h) * 0.045)))
    return Image.composite(img, Image.new('RGB', (w, h), ABYSS), mask)


def fade_mask(size, start=0.28, end=0.86, power=1.25):
    """Маска, которой фотография вплавляется в тёмное поле: слева поле
    остаётся чистым, справа снимок раскрывается полностью."""
    w, h = size
    x0, x1 = int(w * start), int(w * end)
    data = []
    for x in range(w):
        t = (x - x0) / max(1, x1 - x0)
        data.append(int(255 * min(1, max(0, t)) ** power))
    m = Image.new('L', (w, 1))
    m.putdata(data)
    return m.resize((w, h))


def vertical_fade(size, start=0.42, end=1.0, power=1.5):
    """То же по вертикали: низ уходит в глубокую синь под подписи."""
    w, h = size
    y0, y1 = int(h * start), int(h * end)
    data = [int(255 * min(1, max(0, (y - y0) / max(1, y1 - y0))) ** power) for y in range(h)]
    m = Image.new('L', (1, h))
    m.putdata(data)
    return m.resize((w, h))


def grain(img, sigma=6, opacity=0.045):
    noise = Image.effect_noise((img.width, img.height), sigma).convert('RGB')
    # шум центрируем вокруг нуля: зерно должно быть фактурой, а не серой дымкой
    noise = Image.eval(noise, lambda v: v - 128)
    return Image.blend(img, ImageChops.add(img, noise), opacity)


def ink_field(size, glow=True):
    """Глубокое тёпло-синее поле с мягким светом и зерном.
    Это и есть та самая «дорогая» подложка: не чёрный прямоугольник,
    а почти чёрная синь с живым светом внутри."""
    w, h = size
    img = Image.new('RGB', (w, h), ABYSS)
    if glow:
        img = warm_glow(img, cx=0.24, cy=0.14, color=(52, 70, 112), strength=0.22, falloff=2.0)
        img = warm_glow(img, cx=0.86, cy=0.84, color=(82, 60, 34), strength=0.16, falloff=2.2)
    return grain(img, sigma=7, opacity=0.05)


# ==================================================================
# УКРАШЕНИЯ
# Металл работает только тонкими линиями. Заливок, градиентов
# и «золотых» кнопок здесь нет — от них дизайн дешевеет первым делом.
# ==================================================================

def inner_frame(draw, w, h, inset, color, width=1, alpha=255):
    """Тонкая рамка внутри холста — как паспарту в багете."""
    if alpha < 255:
        color = color + (alpha,)
    draw.rectangle([inset, inset, w - inset - 1, h - inset - 1],
                   outline=color, width=width)


def corner_marks(draw, w, h, inset, arm, color, width=1):
    """Угловые метки — приём из типографики: они собирают композицию,
    не отвлекая на себя внимания."""
    pairs = [
        [(inset, inset + arm), (inset, inset), (inset + arm, inset)],
        [(w - inset - arm, inset), (w - inset - 1, inset), (w - inset - 1, inset + arm)],
        [(inset, h - inset - arm), (inset, h - inset - 1), (inset + arm, h - inset - 1)],
        [(w - inset - arm, h - inset - 1), (w - inset - 1, h - inset - 1),
         (w - inset - 1, h - inset - arm)],
    ]
    for pts in pairs:
        draw.line(pts, fill=color, width=width, joint='curve')


def ornament_rule(draw, x, y, length, color, diamond=7, thickness=1):
    """Разделитель: линия, ромб, линия. Ровная черта смотрится как
    разделитель таблицы, ромб возвращает ей характер."""
    cx = x + length / 2
    draw.line([(x, y), (cx - diamond * 2.4, y)], fill=color, width=thickness)
    draw.line([(cx + diamond * 2.4, y), (x + length, y)], fill=color, width=thickness)
    draw.polygon(
        [(cx, y - diamond), (cx + diamond, y), (cx, y + diamond), (cx - diamond, y)],
        fill=color,
    )


def double_rule(draw, x, y, length, color, gap=5, thickness=1):
    """Двойная линейка — классический приём дорогой печати."""
    draw.line([(x, y), (x + length, y)], fill=color, width=thickness)
    draw.line([(x, y + gap), (x + length, y + gap)], fill=color, width=thickness)


def rule(draw, x0, x1, y, fill, thickness=1):
    draw.rectangle([x0, y, x1, y + thickness], fill=fill)


def draw_mark(draw, box, color=GOLDSOFT, accent=GOLD_LIGHT, lw=3):
    """Фирменный знак: фасад шкафа в разрезе с профилями-ручками."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0

    draw.rectangle([x0, y0, x1, y1], outline=color, width=lw)
    for i in (1, 2):
        y = y0 + int(h * i / 3)
        draw.line([(x0, y), (x1, y)], fill=color, width=lw)
    for i in (1, 2):
        x = x0 + int(w * i / 3)
        draw.line([(x, y0), (x, y1)], fill=color, width=lw)

    lw_a = max(2, int(lw * 1.5))
    draw.line([(x0 + w / 6, y0 + h / 3), (x0 + w / 6, y0 + 2 * h / 3)], fill=accent, width=lw_a)
    draw.line([(x0 + w / 2, y0), (x0 + w / 2, y0 + h / 3)], fill=accent, width=lw_a)
    draw.line([(x0 + 5 * w / 6, y0 + 2 * h / 3), (x0 + 5 * w / 6, y1)], fill=accent, width=lw_a)


def watermark(w, h, spec, size, color, alpha=16, center=(0.5, 0.5)):
    """Крупная буква в подложке. Видна только как фактура — добавляет
    глубины, но не читается как элемент оформления."""
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # базовая линия ниже оптического центра примерно на треть кегля
    y = h * center[1] + size * 0.33
    draw_text(d, (w * center[0], y), 'Р', spec, size, color + (alpha,), anchor='ma')
    return layer


# ==================================================================
# СЛУЖЕБНОЕ
# ==================================================================

def ensure(path):
    os.makedirs(path, exist_ok=True)
    return path


def save(img, path, quality=94):
    ensure(os.path.dirname(path))
    if path.lower().endswith('.png'):
        img.save(path, optimize=True)
    else:
        img.save(path, quality=quality, optimize=True, progressive=True, subsampling=0)
    size_kb = os.path.getsize(path) / 1024
    print(f'  {os.path.relpath(path, ROOT):54s} {img.width}×{img.height}  {size_kb:6.0f} КБ')


BRAND = 'РЕцепт'
CITY = 'Тверь'
PHONE = '+7 (910) 537-89-91'


# ==================================================================
# 01 · ГЛАВНАЯ ОБЛОЖКА 1920×768
# Композиция: слева чистое глубокое поле под текст, справа photograph
# вплавляется в него светом. Безопасная зона 1120×430 соблюдена: весь
# смысл лежит в центральных 920 px по горизонтали.
# ==================================================================

def make_cover():
    print('01 · Главная обложка')
    w, h = 1920, 768
    x_text = 480

    base = ink_field((w, h))
    snap = photo('kitchens/kitchen-11@2x.webp', (w, h), bright=1.04, focus=(0.66, 0.45))
    snap = grade(snap, contrast=1.18, color=1.1)
    snap = warm_glow(snap, cx=0.62, cy=0.1, color=(255, 208, 146), strength=0.30, falloff=2.2)
    snap = vignette(snap, strength=0.24)
    base.paste(snap, (0, 0), fade_mask((w, h), start=0.48, end=0.72, power=1.1))

    # крупная буква в подложке: читается только как фактура поля
    mark_layer = watermark(w, h, 'display-light', 660, GOLD_LIGHT, 16, center=(0.13, 0.52))
    base.paste(mark_layer, (0, 0), mark_layer)

    d = ImageDraw.Draw(base)

    inner_frame(d, w, h, 44, GOLDLINE, width=1)
    corner_marks(d, w, h, 44, 30, GOLDSOFT, width=1)

    # надзаголовок с золотым штрихом слева — как на сайте
    rule(d, x_text, x_text + 58, 208, GOLD_ON_DARK, 1)
    draw_text(d, (x_text + 78, 215), 'МЕБЕЛЬНОЕ АТЕЛЬЕ · ТВЕРЬ', 'sans-medium', 25,
              GOLD_ON_DARK, tracking=7)

    draw_text(d, (x_text, 340), BRAND, 'display-light', 172, CREAM, tracking=3)

    ornament_rule(d, x_text, 434, 300, GOLD_ON_DARK, diamond=7)

    draw_text(d, (x_text, 492), 'Кухни на заказ', 'sans', 40, CREAM, tracking=0.6)

    draw_text(d, (x_text, 530),
              'Проект, визуализация и схемы электрики — бесплатно',
              'sans', 23, CREAM_DIM, tracking=0.6)
    draw_text(d, (x_text, 558),
              'Гарантия 24 месяца · Оплата 50 / 50',
              'sans', 23, CREAM_SOFT, tracking=0.6)

    # знак в правом нижнем углу, в зоне фотографии
    draw_mark(d, (w - 236, h - 190, w - 136, h - 90), color=GOLDSOFT, accent=GOLD_LIGHT, lw=3)

    save(base, os.path.join(OUT, '01-oblozhka', 'oblozhka-1920x768.jpg'))

    # контрольный макет: красным — то, что ВК обрежет
    check = base.copy()
    dd = ImageDraw.Draw(check, 'RGBA')
    dd.rectangle([0, 0, w, 130], fill=(255, 80, 80, 55))
    dd.rectangle([0, 568, w, h], fill=(255, 80, 80, 55))
    dd.rectangle([0, 0, 460, h], fill=(255, 80, 80, 38))
    dd.rectangle([1460, 0, w, h], fill=(255, 80, 80, 38))
    dd.rectangle([460, 130, 1460, 568], outline=(211, 189, 149, 170), width=2)
    save(check, os.path.join(OUT, '01-oblozhka', '_proverka-bezopasnoi-zony.jpg'))


# ==================================================================
# 02 · ЖИВАЯ ОБЛОЖКА 1080×1920 (до 5 слайдов)
# ==================================================================

SLIDES = [
    ('kitchens/kitchen-02@2x.webp', ['Кухни, в которых', 'удобно готовить'],
     'Роберт и Екатерина ведут проект лично — от первого замера до сборки', (0.5, 0.42)),
    ('kitchens/kitchen-03@2x.webp', ['Проект —', 'бесплатно'],
     'Планировка, визуализация и схемы электрики. 0 ₽, без обязательств', (0.5, 0.5)),
    ('kitchens/kitchen-07@2x.webp', ['Свою кухню вы', 'увидите до оплаты'],
     'Правим проект столько, сколько нужно, чтобы вам действительно нравилось', (0.5, 0.44)),
    ('kitchens/kitchen-09@2x.webp', ['Гарантия', '24 месяца'],
     'И телефон, который продолжает работать после сборки', (0.5, 0.5)),
    ('team/hero-rob-kate-portrait@2x.webp', ['Приедем', 'на замер'],
     'Тверь и область. Замер бесплатный, дальше решаете вы', (0.5, 0.4)),
]


def make_live_cover():
    print('02 · Живая обложка (5 слайдов)')
    w, h = 1080, 1920

    for i, (src, title_lines, sub, focus) in enumerate(SLIDES, 1):
        snap = photo(src, (w, h), focus=focus)
        snap = grade(snap, contrast=1.16, color=1.1)
        snap = warm_glow(snap, cx=0.5, cy=0.2, color=(255, 206, 140), strength=0.34, falloff=2.2)
        snap = vignette(snap, strength=0.26)
        img = Image.new('RGB', (w, h), ABYSS)
        img.paste(snap, (0, 0))
        img = Image.composite(Image.new('RGB', (w, h), ABYSS), img,
                              vertical_fade((w, h), start=0.30, end=0.52, power=0.8))
        img = warm_glow(img, cx=0.5, cy=0.74, color=(52, 68, 104), strength=0.18, falloff=2.0)
        img = grain(img, sigma=6, opacity=0.045)

        d = ImageDraw.Draw(img)
        cx = w // 2

        inner_frame(d, w, h, 40, GOLDLINE, width=2)
        corner_marks(d, w, h, 40, 34, GOLDSOFT, width=2)

        # номер слайда между двумя штрихами
        label = f'{i:02d}'
        lw = text_width(label, 'sans-medium', 24, 6)
        rule(d, cx - lw / 2 - 76, cx - lw / 2 - 24, 1030, GOLD_ON_DARK, 2)
        rule(d, cx + lw / 2 + 24, cx + lw / 2 + 76, 1030, GOLD_ON_DARK, 2)
        draw_text(d, (cx, 1030), label, 'sans-medium', 24, GOLD_ON_DARK, tracking=6, anchor='ma')

        y = 1110
        for line in title_lines:
            draw_text(d, (cx, y), line, 'display-light', 104, CREAM, tracking=2, anchor='ma')
            y += 112

        ornament_rule(d, cx - 130, y + 26, 260, GOLD_ON_DARK, diamond=8, thickness=2)

        draw_paragraph(d, (cx, y + 76), sub, 'sans', 32, CREAM_DIM,
                       max_width=780, leading=1.55, anchor='ma')

        draw_mark(d, (cx - 40, 1620, cx + 40, 1700), color=GOLDSOFT, accent=GOLD_LIGHT, lw=2)
        draw_text(d, (cx, 1748), BRAND, 'display-light', 62, CREAM, tracking=6, anchor='ma')
        draw_text(d, (cx, 1826), 'КУХНИ НА ЗАКАЗ · ТВЕРЬ', 'sans-medium', 22,
                  GOLD_ON_DARK, tracking=7, anchor='ma')

        save(img, os.path.join(OUT, '02-zhivaya-oblozhka', f'slaid-{i:02d}-1080x1920.jpg'))


# ==================================================================
# 03 · АВАТАР 1000×1000
# ВК вырезает из центра круг 200×200, поэтому всё важное — в круге
# диаметром 82% холста.
# ==================================================================

def make_avatar():
    print('03 · Аватар')
    size = 1000
    img = ink_field((size, size), glow=True)
    img = warm_glow(img, cx=0.5, cy=0.42, color=(255, 210, 150), strength=0.14, falloff=3.2)
    d = ImageDraw.Draw(img)

    cx = size // 2
    r_out = int(size * 0.455)

    # два тонких кольца — рамка вместо заливки
    d.ellipse([cx - r_out, cx - r_out, cx + r_out, cx + r_out], outline=GOLDLINE, width=3)
    d.ellipse([cx - r_out + 26, cx - r_out + 26, cx + r_out - 26, cx + r_out - 26],
              outline=(78, 96, 128), width=1)

    # два ромба сверху и снизу — метки по вертикальной оси
    for cy in (cx - r_out - 16, cx + r_out + 16):
        d.polygon([(cx, cy - 18), (cx + 9, cy), (cx, cy + 18), (cx - 9, cy)],
                  fill=GOLD_ON_DARK)

    mark_w = 268
    draw_mark(d, (cx - mark_w // 2, 232, cx + mark_w // 2, 232 + mark_w),
              color=GOLDSOFT, accent=GOLD_LIGHT, lw=5)

    ornament_rule(d, cx - 150, 578, 300, GOLD_ON_DARK, diamond=9, thickness=2)

    draw_text(d, (cx, 700), BRAND, 'display-light', 176, CREAM, tracking=6, anchor='ma')

    draw_text(d, (cx, 742), 'КУХНИ НА ЗАКАЗ · ТВЕРЬ', 'sans-medium', 24,
              GOLD_ON_DARK, tracking=8, anchor='ma')

    save(img, os.path.join(OUT, '03-avatar', 'avatar-1000x1000.png'))

    small = img.resize((400, 400), Image.LANCZOS)
    save(small, os.path.join(OUT, '03-avatar', 'avatar-400x400.png'))

    # как это выглядит в ленте
    preview = Image.new('RGB', (620, 260), BONE)
    mini = img.resize((200, 200), Image.LANCZOS)
    mask = Image.new('L', (200, 200), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 199, 199], fill=255)
    preview.paste(mini, (40, 30), mask)
    preview.paste(mini, (380, 30), mask)
    dp = ImageDraw.Draw(preview)
    draw_text(dp, (310, 128), 'так в ленте', 'sans', 20, STONE, tracking=1, anchor='ma')
    save(preview, os.path.join(OUT, '03-avatar', '_proverka-v-lente.png'))


# ==================================================================
# 04 · ПЛИТКИ МЕНЮ 752×512 (минимум ВК — 376×256)
# ==================================================================

MENU = [
    ('kitchens/kitchen-07@2x.webp', 'Кухни'),
    ('rooms/wardrobe@2x.webp', 'Гардеробные'),
    ('rooms/closet@2x.webp', 'Шкафы'),
    ('rooms/bathroom@2x.webp', 'Мебель в ванную'),
    ('rooms/hall@2x.webp', 'Прихожие'),
    ('kitchens/kitchen-04@2x.webp', 'Наши работы'),
    ('team/robert-measure@2x.webp', 'Отзывы'),
]


def make_menu():
    print('04 · Плитки меню')
    w, h = 752, 512

    for i, (src, title) in enumerate(MENU, 1):
        snap = photo(src, (w, h), focus=(0.5, 0.34) if 'team' in src else (0.5, 0.5))
        snap = grade(snap, contrast=1.14, color=1.08)
        img = Image.composite(Image.new('RGB', (w, h), ABYSS), snap,
                              vertical_fade((w, h), start=0.34, end=0.72, power=0.75))
        img = vignette(img, strength=0.22)
        img = warm_glow(img, cx=0.78, cy=0.16, color=(255, 206, 140), strength=0.40, falloff=2.2)

        d = ImageDraw.Draw(img)
        inner_frame(d, w, h, 16, GOLDLINE, width=2)
        corner_marks(d, w, h, 16, 20, GOLDSOFT, width=2)

        draw_text(d, (46, 44), f'{i:02d}', 'sans-medium', 22, GOLD_ON_DARK, tracking=4)
        rule(d, 46, 46 + 26, 84, GOLD_ON_DARK, 2)

        y = h - 128
        size_t = 58 if len(title) <= 15 else 48
        draw_text(d, (46, y), title, 'display-light', size_t, CREAM, tracking=1)
        ornament_rule(d, 46, y + size_t + 12, 150, GOLD_ON_DARK, diamond=5, thickness=2)

        save(img, os.path.join(OUT, '04-menu',
                               f'menu-{i:02d}-{slug(title)}-752x512.jpg'))


def slug(text):
    table = str.maketrans({
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    })
    return text.lower().translate(table).replace(' ', '-')


# ==================================================================
# 05 · КАРТОЧКИ УСЛУГ 1000×1000
# Светлая карточка: двойная рамка, фотография как вклеенная пластина,
# водяной знак в подложке.
# ==================================================================

SERVICES = [
    ('kitchens/kitchen-05@2x.webp', 'Кухни на заказ',
     'От компактной кухни в хрущёвке до кухни-гостиной с островом',
     'Проект — бесплатно'),
    ('rooms/wardrobe@2x.webp', 'Гардеробные',
     'Система хранения по вашим вещам: штанги, полки, обувь, чемоданы',
     'Любые размеры'),
    ('rooms/closet@2x.webp', 'Шкафы',
     'Распашные и купе, в нишу или отдельно, строго до потолка',
     'Без пыльной щели'),
    ('rooms/bathroom@2x.webp', 'Мебель для ванной',
     'Тумбы, пеналы и зеркальные шкафы во влагостойком исполнении',
     'Подрез под трубы'),
    ('rooms/hall@2x.webp', 'Прихожие и детские',
     'Корпусная мебель для остальных комнат в одной стилистике с кухней',
     'В тон кухне'),
    ('team/katya-plan@2x.webp', 'Проект и схемы электрики',
     'Планировка, визуализация и схема выводов для вашего электрика',
     '0 ₽'),
]


def make_services():
    print('05 · Карточки услуг')
    w, h = 1000, 1000
    pad = 56
    plate_h = 560

    for i, (src, title, text, tag) in enumerate(SERVICES, 1):
        card = Image.new('RGB', (w, h), CREAM)
        card = Image.blend(card, Image.effect_noise((w, h), 4).convert('RGB'), 0.03)

        focus = (0.5, 0.3) if 'team' in src else (0.5, 0.46)
        snap = photo(src, (w - pad * 2, plate_h), focus=focus)
        snap = grade(snap, contrast=1.12, color=1.06)
        card.paste(snap, (pad, pad))

        d = ImageDraw.Draw(card)
        # пластина ограничена золотым волосяным контуром
        d.rectangle([pad, pad, w - pad - 1, pad + plate_h - 1], outline=GOLDLINE, width=2)
        # и внутренняя тень-подводка, отделяющая снимок от поля
        d.rectangle([pad - 6, pad - 6, w - pad + 5, pad + plate_h + 5], outline=LINE, width=1)

        y = pad + plate_h + 54
        draw_text(d, (pad, y), f'{i:02d}', 'sans-medium', 20, GOLD, tracking=5)
        rule(d, pad, pad + 28, y + 8, GOLDLINE, 2)

        y += 40
        size_t = 60 if len(title) <= 22 else 50
        y = draw_paragraph(d, (pad, y), title, 'display', size_t, INK,
                           max_width=w - pad * 2, leading=1.12) + 16

        y = draw_paragraph(d, (pad, y + 8), text, 'sans', 26, STONE,
                           max_width=w - pad * 2, leading=1.5)

        ornament_rule(d, pad, h - 138, 200, GOLDLINE, diamond=6, thickness=2)

        draw_text(d, (pad, h - 108), tag, 'display-italic', 40, GOLD)
        draw_text(d, (w - pad, h - 100), BRAND, 'display', 30, CLAY, anchor='ra')

        d.rectangle([0, 0, w - 1, h - 1], outline=LINE, width=2)
        d.rectangle([18, 18, w - 19, h - 19], outline=SAND, width=1)

        save(card, os.path.join(OUT, '05-uslugi', f'usluga-{i:02d}-{slug(title)}-1000x1000.jpg'))


# ==================================================================
# 06 · СТОРИС 1080×1920
# ==================================================================

def make_stories():
    print('06 · Сторис')
    w, h = 1080, 1920
    pad = 80

    # 1 — маленькая кухня
    snap = photo('kitchens/kitchen-18@2x.webp', (w, h), focus=(0.5, 0.3))
    snap = grade(snap, contrast=1.16, color=1.1)
    snap = warm_glow(snap, cx=0.5, cy=0.18, color=(255, 206, 140), strength=0.34, falloff=2.2)
    snap = vignette(snap, strength=0.28)
    img = Image.composite(Image.new('RGB', (w, h), ABYSS), snap,
                          vertical_fade((w, h), start=0.26, end=0.44, power=0.8))
    img = warm_glow(img, cx=0.5, cy=0.68, color=(52, 68, 104), strength=0.18, falloff=2.0)
    img = grain(img, sigma=6, opacity=0.05)
    d = ImageDraw.Draw(img)
    inner_frame(d, w, h, 44, GOLDLINE, width=2)
    corner_marks(d, w, h, 44, 34, GOLDSOFT, width=2)

    draw_text(d, (pad, 900), 'МАЛЕНЬКАЯ КУХНЯ', 'sans-medium', 26, GOLD_ON_DARK, tracking=8)
    rule(d, pad, pad + 120, 940, GOLD_ON_DARK, 2)
    y = 1000
    for line in ['Два с половиной', 'метра, из которых', 'выжато всё']:
        draw_text(d, (pad, y), line, 'display-light', 108, CREAM, tracking=2)
        y += 116
    ornament_rule(d, pad, y + 24, 260, GOLD_ON_DARK, diamond=8, thickness=2)
    draw_paragraph(d, (pad, y + 74),
                   'Хранение достаём из высоты, углов и нестандартных глубин. '
                   'Половина наших работ — как раз такие кухни.',
                   'sans', 34, CREAM_DIM, max_width=w - pad * 2, leading=1.55)
    draw_text(d, (pad, 1800), f'{BRAND} · {CITY}', 'display', 46, CREAM, tracking=4)
    save(img, os.path.join(OUT, '06-storis', 'storis-01-malenkaya-kuhnya-1080x1920.jpg'))

    # 2 — отзыв
    img = ink_field((w, h))
    img = warm_glow(img, cx=0.5, cy=0.3, color=(255, 206, 140), strength=0.13, falloff=3.0)
    d = ImageDraw.Draw(img)
    inner_frame(d, w, h, 44, GOLDLINE, width=2)
    corner_marks(d, w, h, 44, 34, GOLDSOFT, width=2)

    draw_text(d, (pad, 300), '5,0 ИЗ 5 НА ЯНДЕКС КАРТАХ', 'sans-medium', 26,
              GOLD_ON_DARK, tracking=8)
    rule(d, pad, pad + 120, 340, GOLD_ON_DARK, 2)
    draw_text(d, (pad, 420), '«', 'display-light', 260, GOLD_ON_DARK)
    y = 640
    for line in ['Меняли проект', 'до тех пор, пока', 'не нашли решение']:
        draw_text(d, (pad, y), line, 'display-italic', 76, CREAM, tracking=1)
        y += 96
    ornament_rule(d, pad, y + 26, 260, GOLD_ON_DARK, diamond=8, thickness=2)
    draw_paragraph(d, (pad, y + 76),
                   '«Вместе со мной выбирали цвета, материалы и меняли проект '
                   'до тех пор, пока не нашли идеальное решение.»',
                   'sans', 32, CREAM_DIM, max_width=w - pad * 2, leading=1.6)
    double_rule(d, pad, 1600, 420, GOLD_ON_DARK, gap=6, thickness=2)
    draw_text(d, (pad, 1666), 'Анна', 'display', 54, CREAM)
    draw_text(d, (pad, 1748), 'ОТЗЫВ С ЯНДЕКС КАРТ', 'sans-medium', 24,
              GOLD_ON_DARK, tracking=7)
    draw_text(d, (pad, 1800), f'{BRAND} · {CITY}', 'display', 46, CREAM, tracking=4)
    save(img, os.path.join(OUT, '06-storis', 'storis-02-otzyv-1080x1920.jpg'))

    # 3 — замер
    snap = photo('team/hero-rob-kate-portrait@2x.webp', (w, h), focus=(0.5, 0.3))
    snap = grade(snap, contrast=1.16, color=1.1)
    snap = warm_glow(snap, cx=0.5, cy=0.2, color=(255, 206, 140), strength=0.34, falloff=2.2)
    snap = vignette(snap, strength=0.28)
    img = Image.composite(Image.new('RGB', (w, h), ABYSS), snap,
                          vertical_fade((w, h), start=0.34, end=0.52, power=0.8))
    img = warm_glow(img, cx=0.5, cy=0.74, color=(52, 68, 104), strength=0.18, falloff=2.0)
    img = grain(img, sigma=6, opacity=0.05)
    d = ImageDraw.Draw(img)
    inner_frame(d, w, h, 44, GOLDLINE, width=2)
    corner_marks(d, w, h, 44, 34, GOLDSOFT, width=2)

    draw_text(d, (pad, 1120), 'ЗАМЕР', 'sans-medium', 26, GOLD_ON_DARK, tracking=8)
    rule(d, pad, pad + 120, 1160, GOLD_ON_DARK, 2)
    y = 1220
    for line in ['Приедем,', 'снимем размеры', 'и скажем правду']:
        draw_text(d, (pad, y), line, 'display-light', 100, CREAM, tracking=2)
        y += 108
    ornament_rule(d, pad, y + 24, 260, GOLD_ON_DARK, diamond=8, thickness=2)
    draw_paragraph(d, (pad, y + 74),
                   'Что реально помещается в вашей кухне и сколько это будет стоить. '
                   'Проект и схемы электрики — бесплатно.',
                   'sans', 34, CREAM_DIM, max_width=w - pad * 2, leading=1.55)

    # кнопка: только контур, без заливки
    d.rectangle([pad, 1640, w - pad, 1760], outline=GOLD_ON_DARK, width=2)
    d.rectangle([pad + 8, 1648, w - pad - 8, 1752], outline=(120, 132, 158), width=1)
    draw_text(d, (w / 2, 1688), PHONE, 'sans-medium', 48, CREAM, anchor='ma')
    draw_text(d, (w / 2, 1820), f'{BRAND} · {CITY}', 'display', 46, CREAM,
              tracking=4, anchor='ma')
    save(img, os.path.join(OUT, '06-storis', 'storis-03-zamer-1080x1920.jpg'))


# ==================================================================
# 07 · ШАБЛОНЫ ПОСТОВ 1080×1350
# ==================================================================

def make_posts():
    print('07 · Шаблоны постов')
    w, h = 1080, 1350

    # --- Пост 1: проект ---
    img = Image.new('RGB', (w, h), CREAM)
    img = Image.blend(img, Image.effect_noise((w, h), 4).convert('RGB'), 0.03)
    snap = photo('kitchens/kitchen-01@2x.webp', (w, 720), focus=(0.5, 0.46))
    snap = grade(snap, contrast=1.13, color=1.07)
    img.paste(snap, (0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 720, w, 724], fill=GOLDLINE)
    y = 792
    draw_text(d, (0, y), 'ПРОЕКТ', 'sans-medium', 22, GOLD, tracking=7)
    rule(d, 0, 70, y + 10, GOLDLINE, 2)
    y += 46
    y = draw_paragraph(d, (0, y), 'Прямая кухня в нише с латунью', 'display', 62, INK,
                       max_width=w - 160, leading=1.14)
    y += 6
    ornament_rule(d, 0, y + 26, 220, GOLDLINE, diamond=6, thickness=2)
    y = draw_paragraph(d, (0, y + 66),
                       'Рабочая зона утоплена в деревянную нишу: она собирает кухню '
                       'в единый объём и прячет подсветку. Верхний ряд антресолей '
                       'доведён до потолка, а профиль-ручка, рамки и вытяжка '
                       'выполнены в одном металле.',
                       'sans', 29, STONE, max_width=w - 160, leading=1.55)
    draw_text(d, (0, h - 118), 'Тёплый светлый тон · латунный профиль · каменная столешница',
              'sans', 25, CLAY)
    draw_text(d, (w, h - 118), f'{BRAND}', 'display', 34, INK, anchor='ra')
    save(add_margins(img, 72), os.path.join(OUT, '07-posti', 'post-01-proekt-1080x1350.jpg'))

    # --- Пост 2: польза ---
    items = [
        'Кто и как часто готовит',
        'Где стоит чайник и кофемашина',
        'Нужен ли обеденный стол',
        'Куда девать крупы и сушилку',
        'Какая техника будет встраиваться',
    ]
    img = Image.new('RGB', (w, h), INK)
    img = warm_glow(img, cx=0.5, cy=0.14, color=(64, 86, 132), strength=0.28, falloff=2.4)
    img = warm_glow(img, cx=0.88, cy=0.94, color=(92, 68, 36), strength=0.20, falloff=2.6)
    img = grain(img, sigma=6, opacity=0.05)
    d = ImageDraw.Draw(img)
    inner_frame(d, w, h, 40, GOLDLINE, width=2)
    corner_marks(d, w, h, 40, 30, GOLDSOFT, width=2)

    y = 150
    draw_text(d, (0, y), 'ПЕРЕД ЗАМЕРОМ', 'sans-medium', 22, GOLD_ON_DARK, tracking=7)
    rule(d, 0, 70, y + 10, GOLD_ON_DARK, 2)
    y += 52
    y = draw_paragraph(d, (0, y), ['Пять вопросов,', 'которые мы задаём', 'на первой встрече'],
                       'display-light', 68, CREAM, max_width=w - 180, leading=1.14)
    y += 12
    ornament_rule(d, 0, y + 24, 240, GOLD_ON_DARK, diamond=7, thickness=2)
    y += 86
    for i, item in enumerate(items, 1):
        draw_text(d, (0, y), f'{i:02d}', 'display', 40, GOLD_ON_DARK)
        draw_paragraph(d, (92, y + 4), item, 'sans', 33, CREAM, max_width=w - 260, leading=1.4)
        y += 116
        d.line([(0, y - 40), (w - 180, y - 40)], fill=(52, 68, 96), width=1)
    draw_text(d, (0, h - 190), 'Хорошая кухня начинается с привычек,', 'display-italic', 38,
              GOLD_ON_DARK)
    draw_text(d, (0, h - 138), 'а не с фасадов.', 'display-italic', 38, GOLD_ON_DARK)
    save(add_margins(img, 72), os.path.join(OUT, '07-posti',
                                            'post-02-pyat-voprosov-1080x1350.jpg'))

    # --- Пост 3: честность ---
    img = ink_field((w, h))
    img = warm_glow(img, cx=0.26, cy=0.1, color=(64, 86, 132), strength=0.26, falloff=2.6)
    d = ImageDraw.Draw(img)
    inner_frame(d, w, h, 40, GOLDLINE, width=2)
    corner_marks(d, w, h, 40, 30, GOLDSOFT, width=2)

    y = 150
    draw_text(d, (0, y), 'ЧЕСТНО', 'sans-medium', 22, GOLD_ON_DARK, tracking=7)
    rule(d, 0, 70, y + 10, GOLD_ON_DARK, 2)
    y += 52
    y = draw_paragraph(d, (0, y), ['Чего вы здесь', 'не найдёте'], 'display-light', 76, CREAM,
                       max_width=w - 180, leading=1.1)
    y += 10
    ornament_rule(d, 0, y + 24, 240, GOLD_ON_DARK, diamond=7, thickness=2)
    y += 74
    pairs = [
        ('Собственное производство', 'Своего цеха нет: размещаем заказ и ведём его сами'),
        ('Скидка 50% только сегодня', 'Скидок и таймеров нет — цена не зависит от дня'),
        ('Более 1000 клиентов', '34 отзыва на Яндекс Картах, их можно проверить'),
        ('Работаем по всей России', 'Тверь и область — дальше не поедем сами'),
    ]
    for old, new in pairs:
        draw_text(d, (0, y), old, 'sans', 29, (126, 138, 164))
        ow = text_width(old, 'sans', 29)
        d.line([(0, y - 4), (ow, y - 4)], fill=(126, 138, 164), width=1)
        y = draw_paragraph(d, (0, y + 40), new, 'sans', 31, CREAM, max_width=w - 180,
                           leading=1.4) + 46
    draw_text(d, (0, h - 150), f'{BRAND} · {CITY}', 'display', 40, CREAM, tracking=4)
    save(add_margins(img, 72), os.path.join(OUT, '07-posti', 'post-03-chesno-1080x1350.jpg'))

    # --- Пост 4: мы ---
    img = Image.new('RGB', (w, h), CREAM)
    img = Image.blend(img, Image.effect_noise((w, h), 4).convert('RGB'), 0.03)
    snap = photo('team/robert-measure@2x.webp', (w, 700), focus=(0.5, 0.26))
    snap = grade(snap, contrast=1.12, color=1.06)
    img.paste(snap, (0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 700, w, 704], fill=GOLDLINE)
    y = 776
    draw_text(d, (0, y), 'ЭТО МЫ', 'sans-medium', 22, GOLD, tracking=7)
    rule(d, 0, 70, y + 10, GOLDLINE, 2)
    y += 46
    y = draw_paragraph(d, (0, y), '«На замер приеду я сам»', 'display-italic', 58, INK,
                       max_width=w - 160, leading=1.16)
    y += 8
    ornament_rule(d, 0, y + 26, 220, GOLDLINE, diamond=6, thickness=2)
    y = draw_paragraph(d, (0, y + 66),
                       'Снимает размеры, смотрит короба, вентиляцию и выводы коммуникаций. '
                       'Потом сам звонит вашему прорабу и электрику — чтобы розетки '
                       'оказались там, где нужно.',
                       'sans', 29, STONE, max_width=w - 160, leading=1.55)
    draw_text(d, (0, h - 118), '+7 (910) 836-05-06 · Роберт', 'sans-medium', 27, INK)
    draw_text(d, (w, h - 118), f'{BRAND}', 'display', 34, INK, anchor='ra')
    save(add_margins(img, 72), os.path.join(OUT, '07-posti', 'post-04-eto-my-1080x1350.jpg'))


def add_margins(img, pad):
    """Паспарту: макет целиком в масштабе внутри, снаружи — чистое поле."""
    w, h = img.size
    bg = img.getpixel((w - 2, h - 2))
    frame = Image.new('RGB', (w, h), bg)
    frame.paste(img.resize((w - pad * 2, h - pad * 2), Image.LANCZOS), (pad, pad))
    return frame


# ==================================================================
# 08 · ОБЛОЖКА ВИДЕО 1280×720
# ==================================================================

def make_video_cover():
    print('08 · Обложка видео')
    w, h = 1280, 720

    base = ink_field((w, h))
    snap = photo('kitchens/kitchen-17@2x.webp', (w, h), focus=(0.62, 0.45))
    snap = grade(snap, contrast=1.16, color=1.1)
    snap = warm_glow(snap, cx=0.6, cy=0.12, color=(255, 208, 146), strength=0.28, falloff=2.2)
    snap = vignette(snap, strength=0.26)
    base.paste(snap, (0, 0), fade_mask((w, h), start=0.34, end=0.78, power=1.1))

    d = ImageDraw.Draw(base)
    inner_frame(d, w, h, 36, GOLDLINE, width=1)
    corner_marks(d, w, h, 36, 26, GOLDSOFT, width=1)

    draw_text(d, (92, 210), 'КАК МЫ ЭТО ДЕЛАЕМ', 'sans-medium', 22, GOLD_ON_DARK, tracking=7)
    rule(d, 92, 92 + 54, 224, GOLD_ON_DARK, 1)
    y = 262
    for line in ['Кухня от замера', 'до первой готовки']:
        draw_text(d, (92, y), line, 'display-light', 76, CREAM, tracking=2)
        y += 82
    ornament_rule(d, 92, y + 16, 220, GOLD_ON_DARK, diamond=6, thickness=1)
    draw_text(d, (92, y + 48), '10 шагов · проект бесплатно · гарантия 24 месяца',
              'sans', 25, CREAM_DIM)

    draw_mark(d, (w - 168, 84, w - 84, 168), color=GOLDSOFT, accent=GOLD_LIGHT, lw=2)
    save(base, os.path.join(OUT, '08-video', 'oblozhka-video-1280x720.jpg'))


# ==================================================================
# 09 · ОБЛОЖКИ АЛЬБОМОВ 1200×800
# ==================================================================

ALBUMS = [
    ('kitchens/kitchen-06@2x.webp', 'Кухни', '19 проектов'),
    ('rooms/wardrobe@2x.webp', 'Гардеробные и шкафы', 'системы хранения'),
    ('textures/brass.jpg', 'Детали и материалы', 'макро'),
]


def make_albums():
    print('09 · Обложки альбомов')
    w, h = 1200, 800

    for i, (src, title, sub) in enumerate(ALBUMS, 1):
        snap = photo(src, (w, h), focus=(0.5, 0.5))
        snap = grade(snap, contrast=1.14, color=1.08)
        img = Image.composite(Image.new('RGB', (w, h), ABYSS), snap,
                              vertical_fade((w, h), start=0.34, end=0.70, power=0.75))
        img = vignette(img, strength=0.24)
        img = warm_glow(img, cx=0.8, cy=0.14, color=(255, 206, 140), strength=0.42, falloff=2.2)

        d = ImageDraw.Draw(img)
        inner_frame(d, w, h, 26, GOLDLINE, width=2)
        corner_marks(d, w, h, 26, 24, GOLDSOFT, width=2)

        draw_text(d, (74, 66), f'{i:02d}', 'sans-medium', 22, GOLD_ON_DARK, tracking=4)
        rule(d, 74, 74 + 26, 106, GOLD_ON_DARK, 2)

        y = h - 214
        draw_text(d, (74, y), title, 'display-light', 78, CREAM, tracking=2)
        ornament_rule(d, 74, y + 100, 220, GOLD_ON_DARK, diamond=7, thickness=2)
        draw_text(d, (74, y + 138), sub.upper(), 'sans-medium', 22, GOLD_ON_DARK, tracking=7)

        save(img, os.path.join(OUT, '09-albomy', f'albom-{i:02d}-{slug(title)}-1200x800.jpg'))


# ==================================================================

def main():
    # старые файлы удаляем: имена слагов менялись, дубли не нужны
    shutil.rmtree(OUT, ignore_errors=True)

    print(f'Собираю пакет оформления для «{BRAND}» ({CITY})\n')
    for fn in (make_cover, make_live_cover, make_avatar, make_menu, make_services,
               make_stories, make_posts, make_video_cover, make_albums):
        fn()
        print()
    print('Готово: папка vk/')


if __name__ == '__main__':
    main()
