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

Всё пересобирается из одного места: поправили текст в блоке ТЕКСТЫ,
положили другое фото в tools/src — и запустили заново.

Зависимости: Pillow (pip install Pillow)
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

# ==================================================================
# ПУТИ
# ==================================================================

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'tools', 'src')
FONTS = os.path.join(ROOT, 'tools', 'fonts')
OUT = os.path.join(ROOT, 'vk')

# ==================================================================
# ПАЛИТРА. Та же, что на сайте ателье.
# ==================================================================

INK = (19, 41, 74)
SOOT = (11, 26, 48)
CREAM = (255, 252, 247)
BONE = (246, 240, 231)
SAND = (236, 227, 213)
LINE = (221, 212, 197)
STONE = (107, 99, 92)
CLAY = (162, 152, 140)
GOLD = (122, 97, 60)
GOLDLINE = (182, 154, 99)
GOLDSOFT = (211, 189, 149)

# На тёмном фото золото всегда светлое: тёмное просто не видно
GOLD_ON_DARK = GOLDSOFT
CREAM_DIM = (214, 220, 235)

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
    """Кириллицу берём из кириллического набора, остальное — из латинского."""
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
    Рисует строку с разрядкой. anchor: 'la' — левый край по верхней линии
    шрифта, 'ma' — по центру, 'ra' — по правому краю.
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
    """Переносит текст по словам с учётом разрядки."""
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
    lines = wrap(text, spec, size, max_width, tracking)
    x, y = xy
    step = size * leading
    for line in lines:
        draw_text(draw, (x, y), line, spec, size, fill, tracking, anchor)
        y += step
    return y


def line_height(spec, size, leading=1.5):
    return size * leading


# ==================================================================
# ФОТО
# ==================================================================

def photo(name, size, bright=1.0, focus=(0.5, 0.5)):
    """
    Открывает фото из tools/src, обрезает под нужный размер без искажений
    и возвращает RGB. focus — точка, которую держим в кадре (0..1).
    """
    path = os.path.join(SRC, name)
    img = Image.open(path).convert('RGB')

    target_w, target_h = size
    ratio = target_w / target_h
    src_ratio = img.width / img.height

    if src_ratio > ratio:
        # картинка шире нужного кадра — режем по бокам
        new_h = img.height
        new_w = int(new_h * ratio)
    else:
        # картинка выше нужного кадра — режем сверху и снизу
        new_w = img.width
        new_h = int(new_w / ratio)
        if new_h > img.height:
            # кадр шире исходника: остаёмся в его границах, не вылезая за поля
            new_h = img.height
            new_w = int(new_h * ratio)

    left = max(0, min(img.width - new_w, int((img.width - new_w) * focus[0])))
    top = max(0, min(img.height - new_h, int((img.height - new_h) * focus[1])))
    img = img.crop((left, top, left + new_w, top + new_h))
    img = img.resize(size, Image.LANCZOS)

    if bright != 1.0:
        img = ImageEnhance.Brightness(img).enhance(bright)
    return img


def darken(img, strength=0.62, direction='bottom'):
    """
    Затемняет фото глубокой синью. Направление: 'bottom' — плотнее снизу,
    'top' — плотнее сверху, 'flat' — равномерно.
    """
    w, h = img.size
    mask = Image.new('L', (1, h))
    if direction == 'bottom':
        mask.putdata([int(255 * strength * (0.35 + 0.65 * (y / max(1, h - 1)))) for y in range(h)])
    elif direction == 'top':
        mask.putdata([int(255 * strength * (1.0 - 0.65 * (y / max(1, h - 1)))) for y in range(h)])
    else:
        mask.putdata([int(255 * strength)] * h)
    mask = mask.resize((w, h))

    layer = Image.new('RGB', (w, h), SOOT)
    return Image.composite(layer, img, mask)


def side_fade(img, side='left', width=0.55, color=SOOT, strength=0.9):
    """Горизонтальный градиент — чтобы текст надёжно читался на фото."""
    w, h = img.size
    span = int(w * width)
    mask = Image.new('L', (w, 1))
    if side == 'left':
        ramp = [int(255 * strength * max(0.0, 1 - x / span)) for x in range(w)]
    else:
        ramp = [int(255 * strength * max(0.0, 1 - (w - 1 - x) / span)) for x in range(w)]
    mask.putdata(ramp)
    mask = mask.resize((w, h))

    layer = Image.new('RGB', (w, h), color)
    return Image.composite(layer, img, mask)


def grain(img, sigma=7, opacity=0.05):
    """Слабое зерно: ровная цифровая заливка выглядит дёшево."""
    noise = Image.effect_noise((img.width, img.height), sigma).convert('RGB')
    return Image.blend(img, noise, opacity)


def vignette(img, strength=0.35):
    w, h = img.size
    mask = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(mask)
    steps = 90
    for i in range(steps):
        t = i / steps
        inset_x = int(w * 0.5 * (1 - t))
        inset_y = int(h * 0.5 * (1 - t))
        # края притемняем, центр оставляем чистым
        value = int(255 * (1 - strength * (1 - t)))
        d.rectangle([inset_x, inset_y, w - inset_x, h - inset_y], outline=value)
    mask = mask.filter(ImageFilter.GaussianBlur(int(min(w, h) * 0.05)))
    layer = Image.new('RGB', (w, h), SOOT)
    return Image.composite(img, layer, mask)


def rule(draw, x0, x1, y, fill, thickness=1):
    draw.rectangle([x0, y, x1, y + thickness], fill=fill)


def gold_rule_centered(draw, cx, y, length=260, fill=GOLDSOFT, thickness=1):
    rule(draw, cx - length // 2, cx + length // 2, y, fill, thickness)


# ==================================================================
# ФИРМЕННЫЙ ЗНАК
# Фасад шкафа в разрезе: две горизонтали, два вертикальных шва
# и золотые профили-ручки. Тот же знак стоит на сайте.
# ==================================================================

def draw_mark(draw, box, color=GOLDSOFT, accent=GOLDSOFT, lw=3, gap_ratio=0.1):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0

    draw.rectangle([x0, y0, x1, y1], outline=color, width=lw)
    # горизонтальные членения
    for i in (1, 2):
        y = y0 + int(h * i / 3)
        draw.line([(x0, y), (x1, y)], fill=color, width=lw)
    # вертикальные швы
    for i in (1, 2):
        x = x0 + int(w * i / 3)
        draw.line([(x, y0), (x, y1)], fill=color, width=lw)

    # профили-ручки — единственные элементы, набранные акцентом
    lw_a = max(2, int(lw * 1.4))
    draw.line([(x0 + w / 6, y0 + h / 3), (x0 + w / 6, y0 + 2 * h / 3)], fill=accent, width=lw_a)
    draw.line([(x0 + w / 2, y0), (x0 + w / 2, y0 + h / 3)], fill=accent, width=lw_a)
    draw.line([(x0 + 5 * w / 6, y0 + 2 * h / 3), (x0 + 5 * w / 6, y1)], fill=accent, width=lw_a)


# ==================================================================
# СЛУЖЕБНОЕ
# ==================================================================

def ensure(path):
    os.makedirs(path, exist_ok=True)
    return path


def save(img, path, quality=92):
    ensure(os.path.dirname(path))
    if path.lower().endswith('.png'):
        img.save(path, optimize=True)
    else:
        img.save(path, quality=quality, optimize=True, progressive=True)
    size_kb = os.path.getsize(path) / 1024
    print(f'  {os.path.relpath(path, ROOT):52s} {img.width}×{img.height}  {size_kb:6.0f} КБ')


BRAND = 'РЕцепт'
CITY = 'Тверь'


# ==================================================================
# 01 · ГЛАВНАЯ ОБЛОЖКА 1920×768
# Безопасная зона: центр 1120×430 — ВК обрезает верх на десктопе
# и низ с боками на телефоне, поэтому вся композиция центрирована.
# ==================================================================

def make_cover():
    print('01 · Главная обложка')
    w, h = 1920, 768
    img = photo('kitchens/kitchen-05@2x.webp', (w, h), bright=0.86, focus=(0.5, 0.45))
    img = darken(img, strength=0.74, direction='bottom')
    img = vignette(img, strength=0.45)
    img = grain(img, sigma=6, opacity=0.045)

    d = ImageDraw.Draw(img)
    cx = w // 2

    # Все базовые линии подобраны так, чтобы текст целиком лежал
    # в центральной зоне 1120×430, которая не обрезается нигде.
    draw_text(d, (cx, 205), 'МЕБЕЛЬНОЕ АТЕЛЬЕ · ТВЕРЬ', 'sans-medium', 25,
              GOLD_ON_DARK, tracking=6, anchor='ma')

    draw_text(d, (cx, 320), BRAND, 'display-light', 172, CREAM, tracking=2, anchor='ma')

    gold_rule_centered(d, cx, 415, 300)

    draw_text(d, (cx, 465), 'Кухни на заказ в Твери', 'sans', 42, CREAM, tracking=0.5, anchor='ma')

    draw_text(d, (cx, 535),
              'Проект и схемы электрики — бесплатно · Гарантия 24 месяца',
              'sans', 24, CREAM_DIM, tracking=1, anchor='ma')

    save(img, os.path.join(OUT, '01-oblozhka', 'oblozhka-1920x768.jpg'))

    # Контрольный макет с безопасной зоной — чтобы увидеть, что не обрежется
    check = img.copy()
    dd = ImageDraw.Draw(check, 'RGBA')
    dd.rectangle([400, 140, 1520, 568], outline=(211, 189, 149, 160), width=2)
    dd.rectangle([0, 0, w, 129], fill=(255, 90, 90, 45))
    dd.rectangle([0, 568, w, h], fill=(255, 90, 90, 45))
    dd.rectangle([0, 0, 400, h], fill=(255, 90, 90, 30))
    dd.rectangle([1520, 0, w, h], fill=(255, 90, 90, 30))
    save(check, os.path.join(OUT, '01-oblozhka', '_proverka-bezopasnoi-zony.jpg'))


# ==================================================================
# 02 · ЖИВАЯ ОБЛОЖКА 1080×1920 (до 5 слайдов)
# ==================================================================

SLIDES = [
    ('kitchens/kitchen-02@2x.webp', 'Кухни, в которых\nудобно готовить',
     'Роберт и Катя ведут проект лично — от замера до сборки', (0.5, 0.4)),
    ('kitchens/kitchen-19@2x.webp', 'Проект — бесплатно',
     'Планировка, визуализация и схемы электрики. 0 ₽ и без обязательств', (0.5, 0.5)),
    ('kitchens/kitchen-01@2x.webp', 'Свою кухню вы увидите\nдо оплаты',
     'Правим проект столько, сколько нужно, чтобы вам нравилось', (0.5, 0.5)),
    ('kitchens/kitchen-15@2x.webp', 'Гарантия 24 месяца',
     'И телефон, который продолжает работать после сборки', (0.5, 0.5)),
    ('team/hero-rob-kate-wide@2x.webp', 'Приедем на замер',
     'Тверь и область. Замер бесплатный, дальше решаете вы', (0.5, 0.45)),
]


def make_live_cover():
    print('02 · Живая обложка (5 слайдов)')
    w, h = 1080, 1920
    for i, (src, title, sub, focus) in enumerate(SLIDES, 1):
        img = photo(src, (w, h), bright=0.88, focus=focus)
        img = darken(img, strength=0.70, direction='bottom')
        img = vignette(img, strength=0.4)
        img = grain(img, sigma=6, opacity=0.045)

        d = ImageDraw.Draw(img)
        cx = w // 2

        draw_text(d, (cx, 250), f'{i:02d} / 05', 'sans-medium', 24, GOLD_ON_DARK,
                  tracking=6, anchor='ma')

        y = 1180 if '\n' in title else 1215
        lines = title.split('\n')
        for line in lines:
            draw_text(d, (cx, y), line, 'display-light', 96, CREAM, tracking=1, anchor='ma')
            y += 104

        gold_rule_centered(d, cx, y + 34, 200)

        draw_paragraph(d, (cx, y + 78), sub, 'sans', 32, CREAM_DIM,
                       max_width=760, leading=1.5, anchor='ma')

        draw_text(d, (cx, 1760), BRAND, 'display', 54, CREAM, tracking=4, anchor='ma')
        draw_text(d, (cx, 1830), 'КУХНИ НА ЗАКАЗ · ТВЕРЬ', 'sans-medium', 22,
                  GOLD_ON_DARK, tracking=6, anchor='ma')

        save(img, os.path.join(OUT, '02-zhivaya-oblozhka', f'slaid-{i:02d}-1080x1920.jpg'))


# ==================================================================
# 03 · АВАТАР 1000×1000
# ВК вырезает из центра круг 200×200, поэтому всё важное — в круге
# диаметром 82% холста.
# ==================================================================

def make_avatar():
    print('03 · Аватар')
    size = 1000
    img = Image.new('RGB', (size, size), SOOT)
    img = grain(img, sigma=5, opacity=0.05)
    d = ImageDraw.Draw(img)

    # тонкая золотая рамка по полю
    d.rectangle([26, 26, size - 27, size - 27], outline=(70, 88, 118), width=2)

    cx = size // 2

    # знак
    mark_w = 300
    mark_y = 250
    draw_mark(d, (cx - mark_w // 2, mark_y, cx + mark_w // 2, mark_y + mark_w),
              color=GOLDSOFT, accent=GOLDSOFT, lw=5)

    # слово
    draw_text(d, (cx, 640), BRAND, 'display-light', 190, CREAM, tracking=4, anchor='ma')

    gold_rule_centered(d, cx, 838, 220, thickness=2)

    draw_text(d, (cx, 872), 'КУХНИ НА ЗАКАЗ', 'sans-medium', 30, GOLD_ON_DARK,
              tracking=9, anchor='ma')

    save(img, os.path.join(OUT, '03-avatar', 'avatar-1000x1000.png'))

    small = img.resize((400, 400), Image.LANCZOS)
    save(small, os.path.join(OUT, '03-avatar', 'avatar-400x400.png'))

    # как это выглядит в ленте — круг 200×200
    preview = Image.new('RGB', (600, 260), BONE)
    mini = img.resize((200, 200), Image.LANCZOS)
    mask = Image.new('L', (200, 200), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 199, 199], fill=255)
    preview.paste(mini, (40, 30), mask)
    preview.paste(mini, (360, 30), mask)
    dp = ImageDraw.Draw(preview)
    draw_text(dp, (270, 120), 'так в ленте', 'sans', 20, STONE, tracking=1, anchor='ma')
    save(preview, os.path.join(OUT, '03-avatar', '_proverka-v-lente.png'))


# ==================================================================
# 04 · ПЛИТКИ МЕНЮ 752×512 (минимум ВК — 376×256, берём с запасом ×2)
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
        img = photo(src, (w, h), bright=0.9)
        img = darken(img, strength=0.72, direction='bottom')
        d = ImageDraw.Draw(img)

        # рамка-волосянка по периметру
        d.rectangle([0, 0, w - 1, h - 1], outline=(90, 106, 134), width=2)

        draw_text(d, (44, 40), f'{i:02d}', 'sans-medium', 22, GOLD_ON_DARK, tracking=3)

        # подложка под подпись: сверху растворяется, снизу плотная
        band_h = 150
        band = Image.new('RGB', (w, band_h), SOOT)
        mask = Image.new('L', (1, band_h))
        mask.putdata([int(255 * (y / (band_h - 1)) ** 1.4) for y in range(band_h)])
        mask = mask.resize((w, band_h))
        img.paste(band, (0, h - band_h), mask)

        d = ImageDraw.Draw(img)
        y_title = h - 108
        if len(title) > 14:
            draw_text(d, (44, y_title), title, 'display-light', 52, CREAM, tracking=0.5)
        else:
            draw_text(d, (44, y_title), title, 'display-light', 60, CREAM, tracking=0.5)
        rule(d, 44, 44 + 64, y_title + 78, GOLD_ON_DARK, 2)

        save(img, os.path.join(OUT, '04-menu', f'menu-{i:02d}-{title.lower().replace(" ", "-")}-752x512.jpg'))


# ==================================================================
# 05 · КАРТОЧКИ УСЛУГ 1000×1000
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
    photo_h = 620

    for i, (src, title, text, tag) in enumerate(SERVICES, 1):
        canvas = Image.new('RGB', (w, h), CREAM)
        focus = (0.5, 0.32) if 'team' in src else (0.5, 0.5)
        top = photo(src, (w, photo_h), bright=0.92, focus=focus)
        top = darken(top, strength=0.45, direction='bottom')
        canvas.paste(top, (0, 0))

        d = ImageDraw.Draw(canvas)
        # плашка поверх стыка фото и поля — как паспарту
        d.rectangle([0, photo_h - 3, w, photo_h + 1], fill=GOLDLINE)

        pad = 64
        y = photo_h + 58
        draw_text(d, (pad, y), f'{i:02d}', 'sans-medium', 20, GOLD, tracking=3)

        y += 34
        size_t = 58 if len(title) <= 22 else 48
        y = draw_paragraph(d, (pad, y), title, 'display', size_t, INK,
                           max_width=w - pad * 2, leading=1.12) + 18

        y = draw_paragraph(d, (pad, y + 6), text, 'sans', 27, STONE,
                           max_width=w - pad * 2, leading=1.5)

        # метка внизу
        d.rectangle([0, h - 104, w, h], fill=BONE)
        draw_text(d, (pad, h - 74), tag, 'display-italic', 40, GOLD)
        draw_text(d, (w - pad, h - 66), BRAND, 'display', 30, CLAY, anchor='ra')

        framed = canvas
        dd = ImageDraw.Draw(framed)
        dd.rectangle([0, 0, w - 1, h - 1], outline=LINE, width=2)

        name = title.lower().replace(' ', '-').replace('ё', 'e')
        save(framed, os.path.join(OUT, '05-uslugi', f'usluga-{i:02d}-{name}-1000x1000.jpg'))


# ==================================================================
# 06 · СТОРИС 1080×1920
# ==================================================================

def make_stories():
    print('06 · Сторис')

    # 1 — польза
    img = photo('kitchens/kitchen-18@2x.webp', (1080, 1920), bright=0.9, focus=(0.5, 0.4))
    img = darken(img, strength=0.66, direction='bottom')
    img = grain(img, sigma=6, opacity=0.05)
    d = ImageDraw.Draw(img)
    draw_text(d, (80, 300), 'МАЛЕНЬКАЯ КУХНЯ', 'sans-medium', 26, GOLD_ON_DARK, tracking=7)
    y = 370
    for line in ['Два с половиной\nметра, из которых\nвыжато всё']:
        for part in line.split('\n'):
            draw_text(d, (80, y), part, 'display-light', 112, CREAM, tracking=1)
            y += 118
    gold_rule = ImageDraw.Draw(img)
    rule(gold_rule, 80, 80 + 180, y + 26, GOLD_ON_DARK, 2)
    draw_paragraph(d, (80, y + 70),
                   'Хранение достаём из высоты, углов и нестандартных глубин. Половина наших работ — как раз такие кухни.',
                   'sans', 34, CREAM_DIM, max_width=920, leading=1.5)
    draw_text(d, (80, 1800), f'{BRAND} · {CITY}', 'display', 46, CREAM, tracking=3)
    save(img, os.path.join(OUT, '06-storis', 'storis-01-malenkaya-kuhnya-1080x1920.jpg'))

    # 2 — цитата
    img = Image.new('RGB', (1080, 1920), INK)
    img = grain(img, sigma=6, opacity=0.05)
    d = ImageDraw.Draw(img)
    draw_text(d, (80, 300), '5,0 ИЗ 5 НА ЯНДЕКС КАРТАХ', 'sans-medium', 26, GOLD_ON_DARK, tracking=7)
    draw_text(d, (80, 380), '«', 'display-light', 260, GOLD_ON_DARK)
    y = 620
    for part in ['Меняли проект\nдо тех пор, пока\nне нашли решение']:
        for line in part.split('\n'):
            draw_text(d, (80, y), line, 'display-italic', 74, CREAM, tracking=0.5)
            y += 96
    rule(d, 80, 80 + 180, y + 40, GOLD_ON_DARK, 2)
    draw_paragraph(d, (80, y + 90),
                   '«Вместе со мной выбирали цвета, материалы и меняли проект до тех пор, пока не нашли идеальное решение.»',
                   'sans', 32, CREAM_DIM, max_width=920, leading=1.55)
    draw_text(d, (80, 1620), 'Анна', 'display', 52, CREAM)
    draw_text(d, (80, 1696), 'ОТЗЫВ С ЯНДЕКС КАРТ', 'sans-medium', 24, GOLD_ON_DARK, tracking=6)
    draw_text(d, (80, 1800), f'{BRAND} · {CITY}', 'display', 46, CREAM, tracking=3)
    save(img, os.path.join(OUT, '06-storis', 'storis-02-otzyv-1080x1920.jpg'))

    # 3 — призыв
    img = photo('team/hero-rob-kate-portrait@2x.webp', (1080, 1920), bright=0.9, focus=(0.5, 0.42))
    img = darken(img, strength=0.70, direction='bottom')
    img = grain(img, sigma=6, opacity=0.05)
    d = ImageDraw.Draw(img)
    draw_text(d, (80, 1090), 'ЗАМЕР', 'sans-medium', 26, GOLD_ON_DARK, tracking=7)
    y = 1160
    for line in ['Приедем,\nснимем размеры\nи скажем правду']:
        for part in line.split('\n'):
            draw_text(d, (80, y), part, 'display-light', 104, CREAM, tracking=1)
            y += 110
    rule(d, 80, 80 + 180, y + 24, GOLD_ON_DARK, 2)
    draw_paragraph(d, (80, y + 70),
                   'Что реально помещается в вашей кухне и сколько это будет стоить. Проект и схемы электрики — бесплатно.',
                   'sans', 34, CREAM_DIM, max_width=920, leading=1.5)
    # кнопка
    d.rectangle([80, 1640, 1000, 1760], outline=GOLD_ON_DARK, width=2)
    draw_text(d, (540, 1686), '+7 (910) 537-89-91', 'sans-medium', 48, CREAM, anchor='ma')
    draw_text(d, (540, 1800), f'{BRAND} · {CITY}', 'display', 46, CREAM, tracking=3, anchor='ma')
    save(img, os.path.join(OUT, '06-storis', 'storis-03-zamer-1080x1920.jpg'))


# ==================================================================
# 07 · ШАБЛОНЫ ПОСТОВ 1080×1350
# ==================================================================

def make_posts():
    print('07 · Шаблоны постов')
    w, h = 1080, 1350

    # --- Пост 1: проект ---
    img = Image.new('RGB', (w, h), CREAM)
    top = photo('kitchens/kitchen-01@2x.webp', (w, 760), bright=0.95)
    img.paste(top, (0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 760, w, 764], fill=GOLDLINE)
    y = 828
    draw_text(d, (0, y), 'ПРОЕКТ', 'sans-medium', 22, GOLD, tracking=6)
    y += 36
    y = draw_paragraph(d, (0, y), 'Прямая кухня в нише\nс латунью', 'display', 66, INK,
                       max_width=w - 140, leading=1.14)
    y += 10
    y = draw_paragraph(d, (0, y + 14),
                       'Рабочая зона утоплена в деревянную нишу, верхний ряд доведён до потолка, '
                       'а профиль-ручка, рамки и вытяжка выполнены в одном металле.',
                       'sans', 30, STONE, max_width=w - 140, leading=1.55)
    rule(d, 0, 70, y + 30, GOLDLINE, 2)
    draw_text(d, (0, y + 62), 'Тёплый светлый тон · латунный профиль · каменная столешница',
              'sans', 26, CLAY)
    draw_text(d, (w, h - 70), f'{BRAND} · {CITY}', 'display', 34, INK, anchor='ra')
    framed = add_margins(img, 70)
    save(framed, os.path.join(OUT, '07-posti', 'post-01-proekt-1080x1350.jpg'))

    # --- Пост 2: польза ---
    items = [
        'Кто и как часто готовит',
        'Где стоит чайник и кофемашина',
        'Нужен ли обеденный стол',
        'Куда девать крупы и сушилку',
        'Какая техника будет встраиваться',
    ]
    img = Image.new('RGB', (w, h), BONE)
    img = grain(img, sigma=4, opacity=0.035)
    d = ImageDraw.Draw(img)
    y = 110
    draw_text(d, (0, y), 'ПЕРЕД ЗАМЕРОМ', 'sans-medium', 22, GOLD, tracking=6)
    y += 36
    y = draw_paragraph(d, (0, y), 'Пять вопросов,\nкоторые мы задаём\nна первой встрече',
                       'display', 68, INK, max_width=w - 170, leading=1.12)
    y += 26
    rule(d, 0, 80, y, GOLDLINE, 2)
    y += 60
    for i, item in enumerate(items, 1):
        draw_text(d, (0, y), f'{i:02d}', 'display', 40, GOLD)
        draw_paragraph(d, (86, y + 6), item, 'sans', 34, INK, max_width=w - 240, leading=1.4)
        y += 118
        d.rectangle([0, y - 34, w - 140, y - 33], fill=LINE)
    draw_text(d, (0, h - 150), 'Хорошая кухня начинается с привычек, а не с фасадов.',
              'display-italic', 38, GOLD)
    framed = add_margins(img, 70)
    save(framed, os.path.join(OUT, '07-posti', 'post-02-pyat-voprosov-1080x1350.jpg'))

    # --- Пост 3: честность ---
    img = Image.new('RGB', (w, h), INK)
    img = grain(img, sigma=6, opacity=0.05)
    d = ImageDraw.Draw(img)
    y = 120
    draw_text(d, (0, y), 'ЧЕСТНО', 'sans-medium', 22, GOLD_ON_DARK, tracking=6)
    y += 36
    y = draw_paragraph(d, (0, y), 'Чего вы здесь\nне найдёте', 'display-light', 78, CREAM,
                       max_width=w - 170, leading=1.1)
    y += 24
    rule(d, 0, 80, y, GOLDSOFT, 2)
    y += 56
    pairs = [
        ('Своё производство', 'Своего цеха нет: размещаем заказ и ведём его сами'),
        ('Скидка 50% сегодня', 'Скидок нет, цена не меняется от дня недели'),
        ('Тысячи клиентов', '34 отзыва на Яндекс Картах, их можно проверить'),
        ('Работаем по всей России', 'Тверь и область — дальше не поедем сами'),
    ]
    for old, new in pairs:
        draw_text(d, (0, y), old, 'sans', 30, (120, 132, 158))
        d.line([(0, y + 22), (text_width(old, 'sans', 30), y + 22)], fill=(120, 132, 158), width=1)
        y = draw_paragraph(d, (0, y + 46), new, 'sans', 32, CREAM, max_width=w - 170,
                           leading=1.4) + 44
    draw_text(d, (0, h - 130), f'{BRAND} · {CITY}', 'display', 40, CREAM, tracking=3)
    framed = add_margins(img, 70)
    save(framed, os.path.join(OUT, '07-posti', 'post-03-chesno-1080x1350.jpg'))

    # --- Пост 4: мы ---
    img = Image.new('RGB', (w, h), CREAM)
    top = photo('team/robert-measure@2x.webp', (w, 700), bright=0.95, focus=(0.5, 0.28))
    img.paste(top, (0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 700, w, 704], fill=GOLDLINE)
    y = 768
    draw_text(d, (0, y), 'ЭТО МЫ', 'sans-medium', 22, GOLD, tracking=6)
    y += 36
    y = draw_paragraph(d, (0, y), 'Роберт приезжает\nна замер сам', 'display', 66, INK,
                       max_width=w - 140, leading=1.14)
    y += 10
    y = draw_paragraph(d, (0, y + 14),
                       'Снимает размеры, смотрит короба, вентиляцию и выводы коммуникаций. '
                       'Потом сам звонит вашему прорабу и электрику.',
                       'sans', 30, STONE, max_width=w - 140, leading=1.55)
    rule(d, 0, 70, y + 30, GOLDLINE, 2)
    draw_text(d, (0, y + 62), '+7 (910) 836-05-06', 'sans-medium', 32, INK)
    draw_text(d, (w, h - 70), f'{BRAND} · {CITY}', 'display', 34, INK, anchor='ra')
    framed = add_margins(img, 70)
    save(framed, os.path.join(OUT, '07-posti', 'post-04-eto-my-1080x1350.jpg'))


def add_margins(img, pad):
    """Оборачивает макет в паспарту: содержимое целиком в масштабе
    внутри, снаружи — чистое поле цвета подложки."""
    w, h = img.size
    bg = img.getpixel((w - 2, h - 2))
    frame = Image.new('RGB', (w, h), bg)
    inner = img.resize((w - pad * 2, h - pad * 2), Image.LANCZOS)
    frame.paste(inner, (pad, pad))
    return frame


# ==================================================================
# 08 · ОБЛОЖКА ВИДЕО 1280×720
# ==================================================================

def make_video_cover():
    print('08 · Обложка видео')
    w, h = 1280, 720
    img = photo('kitchens/kitchen-17@2x.webp', (w, h), bright=0.9)
    img = darken(img, strength=0.72, direction='bottom')
    img = vignette(img, strength=0.35)
    d = ImageDraw.Draw(img)

    draw_text(d, (90, 200), 'КАК МЫ ЭТО ДЕЛАЕМ', 'sans-medium', 22, GOLD_ON_DARK, tracking=6)
    y = 250
    for line in ['Кухня от замера\nдо первой готовки']:
        for part in line.split('\n'):
            draw_text(d, (90, y), part, 'display-light', 78, CREAM, tracking=1)
            y += 84
    rule(d, 90, 90 + 200, y + 20, GOLD_ON_DARK, 2)
    draw_text(d, (90, y + 52), '10 шагов · проект бесплатно · гарантия 24 месяца',
              'sans', 26, CREAM_DIM)
    #右上: знак
    draw_mark(d, (w - 190, 90, w - 90, 190), color=GOLDSOFT, accent=GOLDSOFT, lw=3)
    save(img, os.path.join(OUT, '08-video', 'oblozhka-video-1280x720.jpg'))


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
        img = photo(src, (w, h), bright=0.9)
        img = darken(img, strength=0.70, direction='bottom')
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, w - 1, h - 1], outline=(90, 106, 134), width=2)
        draw_text(d, (70, 60), f'{i:02d}', 'sans-medium', 22, GOLD_ON_DARK, tracking=3)

        y = h - 210
        for part in title.split('\n'):
            draw_text(d, (70, y), part, 'display-light', 82, CREAM, tracking=1)
            y += 88
        rule(d, 70, 70 + 120, y + 18, GOLD_ON_DARK, 2)
        draw_text(d, (70, y + 46), sub.upper(), 'sans-medium', 22, GOLD_ON_DARK, tracking=6)
        name = title.lower().replace(' ', '-').replace('ё', 'e')
        save(img, os.path.join(OUT, '09-albomy', f'albom-{i:02d}-{name}-1200x800.jpg'))


# ==================================================================

def main():
    print(f'Собираю пакет оформления для «{BRAND}» ({CITY})\n')
    for fn in (make_cover, make_live_cover, make_avatar, make_menu, make_services,
               make_stories, make_posts, make_video_cover, make_albums):
        fn()
        print()
    print('Готово: папка vk/')


if __name__ == '__main__':
    main()
