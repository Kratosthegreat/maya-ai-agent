#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מייצר את תמונות הרקע של המשחק — תמונות רסטר אמיתיות עם טקסטורה, תאורה ועומק,
ומטביע אותן בקובץ JS כ-data URI (הדרך הנתמכת להטמיע תמונות בדף).

    python3 web/art/render.py
"""

from __future__ import annotations

import base64
import io
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size: int):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()

W, H = 900, 372                      # יחס 2.42:1 — רצועה רחבה לראש הדף
RNG = np.random.default_rng(7)

# ---------------------------------------------------------------------------
# עזרי ציור
# ---------------------------------------------------------------------------

def canvas(color=(0, 0, 0)) -> np.ndarray:
    return np.zeros((H, W, 3), dtype=np.float32) + np.array(color, dtype=np.float32) / 255.0


def vgrad(stops) -> np.ndarray:
    """מדרג אנכי. stops = [(מיקום 0-1, (r,g,b)), ...]"""
    ys = np.linspace(0, 1, H, dtype=np.float32)
    out = np.zeros((H, 3), dtype=np.float32)
    stops = sorted(stops, key=lambda s: s[0])
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        mask = (ys >= p0) & (ys <= p1)
        if not mask.any():
            continue
        t = ((ys[mask] - p0) / max(1e-6, p1 - p0))[:, None]
        out[mask] = (np.array(c0) / 255.0) * (1 - t) + (np.array(c1) / 255.0) * t
    out[ys < stops[0][0]] = np.array(stops[0][1]) / 255.0
    out[ys > stops[-1][0]] = np.array(stops[-1][1]) / 255.0
    return np.repeat(out[:, None, :], W, axis=1)


def noise(scale: float, seed: int = 0, shape=None) -> np.ndarray:
    """רעש חלק — בסיס לטקסטורות (דשא, קהל, גרעיניות)."""
    h, w = shape or (H, W)
    small_h = max(2, int(h / scale))
    small_w = max(2, int(w / scale))
    rng = np.random.default_rng(seed)
    base = rng.random((small_h, small_w)).astype(np.float32)
    img = Image.fromarray((base * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(img, dtype=np.float32) / 255.0


def fbm(seed: int = 0, octaves=4, base_scale=90.0, shape=None) -> np.ndarray:
    """רעש רב-שכבתי — נותן טקסטורה טבעית ולא מלאכותית."""
    total = None
    amp, scale = 1.0, base_scale
    for o in range(octaves):
        layer = noise(scale, seed + o * 37, shape) * amp
        total = layer if total is None else total + layer
        amp *= 0.5
        scale = max(2.0, scale / 2.2)
    total -= total.min()
    return total / max(1e-6, total.max())


def radial(cx: float, cy: float, r: float, power: float = 2.0) -> np.ndarray:
    """נפילה רדיאלית — לזוהר של פנסים ותאורה."""
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) / max(1e-6, r)
    return np.clip(1.0 - d, 0, 1) ** power


def add_light(img: np.ndarray, mask: np.ndarray, color, strength: float = 1.0) -> np.ndarray:
    """מוסיף אור (screen blend) — כך זוהר נראה כמו אור ולא כמו צבע."""
    c = np.array(color, dtype=np.float32) / 255.0
    light = mask[:, :, None] * c[None, None, :] * strength
    return 1.0 - (1.0 - np.clip(img, 0, 1)) * (1.0 - np.clip(light, 0, 1))


def shade(img: np.ndarray, mask: np.ndarray, amount: float = 0.5) -> np.ndarray:
    return img * (1.0 - mask[:, :, None] * amount)


def to_pil(img: np.ndarray) -> Image.Image:
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))


def from_pil(im: Image.Image) -> np.ndarray:
    return np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0


def draw_layer(fn) -> tuple[np.ndarray, np.ndarray]:
    """מצייר שכבה עם שקיפות ומחזיר (צבע, אלפא)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fn(ImageDraw.Draw(layer))
    arr = np.asarray(layer, dtype=np.float32) / 255.0
    return arr[:, :, :3], arr[:, :, 3]


def over(img: np.ndarray, color: np.ndarray, alpha: np.ndarray, blur: float = 0.0) -> np.ndarray:
    if blur > 0:
        a = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8))
                       .filter(ImageFilter.GaussianBlur(blur)), dtype=np.float32) / 255.0
        alpha = a
    return img * (1 - alpha[:, :, None]) + color * alpha[:, :, None]


def blur(img: np.ndarray, radius: float) -> np.ndarray:
    return from_pil(to_pil(img).filter(ImageFilter.GaussianBlur(radius)))


def vignette(img: np.ndarray, strength: float = 0.55) -> np.ndarray:
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xs - W / 2) / (W / 2)) ** 2 + ((ys - H / 2) / (H / 2)) ** 2)
    mask = np.clip((d - 0.55) / 0.85, 0, 1) ** 1.6
    return img * (1 - mask[:, :, None] * strength)


def grain(img: np.ndarray, amount: float = 0.022, seed: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    g = rng.normal(0, 1, (H, W, 1)).astype(np.float32) * amount
    return np.clip(img + g, 0, 1)


def expose(img: np.ndarray, stops: float = 0.35) -> np.ndarray:
    """מרים חשיפה בלי לשרוף הארות (עקומת גמא רכה)."""
    return np.clip(1.0 - (1.0 - np.clip(img, 0, 1)) ** (1.0 + stops), 0, 1)


def saturate(img: np.ndarray, amount: float = 1.35) -> np.ndarray:
    """מגביר רוויה — בלי זה כל תמונה מרונדרת נראית שטופה."""
    lum = (img * np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)).sum(axis=2, keepdims=True)
    return np.clip(lum + (img - lum) * amount, 0, 1)


def contrast(img: np.ndarray, amount: float = 1.12, pivot: float = 0.46) -> np.ndarray:
    return np.clip((img - pivot) * amount + pivot, 0, 1)


def grade(img: np.ndarray, shadow_tint, highlight_tint, amount: float = 0.18) -> np.ndarray:
    """דירוג צבע: גוון לצללים וגוון להארות — מה שנותן ל'תמונה' מראה מצולם."""
    lum = img.mean(axis=2, keepdims=True)
    sh = np.array(shadow_tint, dtype=np.float32) / 255.0
    hi = np.array(highlight_tint, dtype=np.float32) / 255.0
    tint = sh[None, None, :] * (1 - lum) + hi[None, None, :] * lum
    return np.clip(img * (1 - amount) + tint * amount, 0, 1)


# ---------------------------------------------------------------------------
# אלמנטים חוזרים
# ---------------------------------------------------------------------------

def turf(img: np.ndarray, horizon: float, stripe_count: int = 9,
         base=(26, 78, 44), light=(46, 112, 62), seed: int = 11) -> np.ndarray:
    """דשא עם פסי כיסוח בפרספקטיבה, טקסטורה ותאורה — לא מלבן ירוק."""
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    y0 = horizon * H
    depth = np.clip((ys - y0) / max(1e-6, (H - y0)), 0, 1)
    on_pitch = ys >= y0

    base_c = np.array(base, dtype=np.float32) / 255.0
    light_c = np.array(light, dtype=np.float32) / 255.0
    # רחוק = כהה ודחוס, קרוב = בהיר ופתוח
    field = base_c[None, None, :] * (0.55 + 0.45 * depth[:, :, None])

    # פסי כיסוח מתרחבים עם הקרבה
    u = (xs - W / 2) / (W / 2)
    perspective_u = u / np.clip(0.25 + 0.75 * depth, 0.08, 1.0)
    stripes = np.sin(perspective_u * stripe_count * math.pi)
    stripe_mask = (stripes > 0).astype(np.float32)
    field = field * (1 - 0.16 * stripe_mask[:, :, None]) + \
        light_c[None, None, :] * 0.16 * stripe_mask[:, :, None]

    # טקסטורת דשא: רעש דק שנעשה עדין ככל שרחוק
    blades = fbm(seed, octaves=4, base_scale=26)
    fine = noise(2.2, seed + 5)
    tex = (blades - 0.5) * 0.20 + (fine - 0.5) * 0.10 * depth
    field = field + tex[:, :, None]

    out = np.where(on_pitch[:, :, None], np.clip(field, 0, 1), img)
    return out


def crowd(img: np.ndarray, top: float, bottom: float, seed: int = 21,
          tint=(96, 108, 120), density: float = 1.0) -> np.ndarray:
    """יציע: אלפי נקודות קטנות בגדלים משתנים — נקרא כקהל, לא כמלבן."""
    y0, y1 = int(top * H), int(bottom * H)
    if y1 <= y0:
        return img
    band_h = y1 - y0
    rng = np.random.default_rng(seed)
    layer = Image.new("RGBA", (W, band_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    count = int(W * band_h * 0.016 * density)
    for _ in range(count):
        x = rng.integers(0, W)
        y = rng.integers(0, band_h)
        depth = y / band_h
        r = max(0.6, rng.normal(1.1 + depth * 1.7, 0.5))
        shade_v = rng.normal(0.85, 0.35)
        col = tuple(int(np.clip(c * shade_v, 0, 255)) for c in tint)
        a = int(np.clip(rng.normal(150, 55), 40, 235))
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (a,))
    layer = layer.filter(ImageFilter.GaussianBlur(0.45))
    arr = np.asarray(layer, dtype=np.float32) / 255.0
    out = img.copy()
    region = out[y0:y1]
    a = arr[:, :, 3:4]
    out[y0:y1] = region * (1 - a) + arr[:, :, :3] * a
    return out


def silhouette(img: np.ndarray, points, color=(6, 10, 8), blur_px: float = 0.0,
               alpha: float = 1.0) -> np.ndarray:
    col, a = draw_layer(lambda d: d.polygon(points, fill=tuple(color) + (int(alpha * 255),)))
    return over(img, col, a, blur_px)


def person(draw: ImageDraw.ImageDraw, x: float, ground: float, scale: float,
           color, alpha: int = 255, pose: str = "stand") -> None:
    """צללית אדם בפרופורציות אנושיות. scale=1 ≈ 52px גובה."""
    s = scale
    c = tuple(color) + (alpha,)
    total = 52.0 * s
    head_r = total * 0.085
    head_cy = ground - total * 0.90
    neck_y = head_cy + head_r * 1.5
    shoulder_y = neck_y + total * 0.045
    hip_y = ground - total * 0.46
    knee_y = ground - total * 0.23
    sh_w = total * 0.15
    hip_w = total * 0.105

    # ראש וצוואר
    draw.ellipse([x - head_r, head_cy - head_r * 1.12,
                  x + head_r, head_cy + head_r * 1.12], fill=c)
    draw.polygon([(x - head_r * 0.42, head_cy + head_r * 0.7),
                  (x + head_r * 0.42, head_cy + head_r * 0.7),
                  (x + head_r * 0.5, shoulder_y), (x - head_r * 0.5, shoulder_y)], fill=c)

    if pose == "sit":
        draw.polygon([(x - sh_w, shoulder_y), (x + sh_w, shoulder_y),
                      (x + hip_w, hip_y + total * 0.10), (x - hip_w, hip_y + total * 0.10)], fill=c)
        # ירכיים קדימה
        draw.polygon([(x - hip_w, hip_y + total * 0.04),
                      (x + total * 0.30, hip_y + total * 0.09),
                      (x + total * 0.30, hip_y + total * 0.20),
                      (x - hip_w, hip_y + total * 0.16)], fill=c)
        # שוקיים למטה
        draw.polygon([(x + total * 0.20, hip_y + total * 0.16),
                      (x + total * 0.30, hip_y + total * 0.17),
                      (x + total * 0.28, ground), (x + total * 0.17, ground)], fill=c)
        # זרוע
        draw.polygon([(x + sh_w * 0.8, shoulder_y + total * 0.02),
                      (x + sh_w * 1.15, shoulder_y + total * 0.04),
                      (x + total * 0.22, hip_y + total * 0.06),
                      (x + total * 0.16, hip_y + total * 0.07)], fill=c)
        return

    # גוף
    draw.polygon([(x - sh_w, shoulder_y), (x + sh_w, shoulder_y),
                  (x + hip_w, hip_y), (x - hip_w, hip_y)], fill=c)

    if pose == "run":
        # רגל אחורית
        draw.polygon([(x - hip_w * 0.9, hip_y), (x - hip_w * 0.1, hip_y),
                      (x - total * 0.14, knee_y), (x - total * 0.21, knee_y)], fill=c)
        draw.polygon([(x - total * 0.21, knee_y), (x - total * 0.14, knee_y),
                      (x - total * 0.24, ground), (x - total * 0.32, ground)], fill=c)
        # רגל קדמית מורמת
        draw.polygon([(x + hip_w * 0.1, hip_y), (x + hip_w * 0.9, hip_y),
                      (x + total * 0.20, knee_y + total * 0.03),
                      (x + total * 0.13, knee_y + total * 0.05)], fill=c)
        draw.polygon([(x + total * 0.13, knee_y + total * 0.05),
                      (x + total * 0.20, knee_y + total * 0.03),
                      (x + total * 0.33, ground - total * 0.06),
                      (x + total * 0.28, ground - total * 0.01)], fill=c)
        # זרועות
        draw.polygon([(x - sh_w * 0.95, shoulder_y + total * 0.01),
                      (x - sh_w * 0.55, shoulder_y),
                      (x - total * 0.02, hip_y - total * 0.02),
                      (x - total * 0.07, hip_y)], fill=c)
        draw.polygon([(x + sh_w * 0.55, shoulder_y),
                      (x + sh_w * 0.95, shoulder_y + total * 0.01),
                      (x + total * 0.26, shoulder_y + total * 0.12),
                      (x + total * 0.21, shoulder_y + total * 0.15)], fill=c)
        return

    # עמידה
    leg_gap = total * 0.018
    draw.polygon([(x - hip_w, hip_y), (x - leg_gap, hip_y),
                  (x - leg_gap * 1.4, knee_y), (x - hip_w * 0.95, knee_y)], fill=c)
    draw.polygon([(x - hip_w * 0.95, knee_y), (x - leg_gap * 1.4, knee_y),
                  (x - leg_gap * 1.6, ground), (x - hip_w * 1.0, ground)], fill=c)
    draw.polygon([(x + leg_gap, hip_y), (x + hip_w, hip_y),
                  (x + hip_w * 0.95, knee_y), (x + leg_gap * 1.4, knee_y)], fill=c)
    draw.polygon([(x + leg_gap * 1.4, knee_y), (x + hip_w * 0.95, knee_y),
                  (x + hip_w * 1.0, ground), (x + leg_gap * 1.6, ground)], fill=c)
    # זרועות צמודות לגוף
    draw.polygon([(x - sh_w, shoulder_y + total * 0.01),
                  (x - sh_w * 0.72, shoulder_y),
                  (x - hip_w * 0.85, hip_y + total * 0.06),
                  (x - hip_w * 1.25, hip_y + total * 0.05)], fill=c)
    draw.polygon([(x + sh_w * 0.72, shoulder_y),
                  (x + sh_w, shoulder_y + total * 0.01),
                  (x + hip_w * 1.25, hip_y + total * 0.05),
                  (x + hip_w * 0.85, hip_y + total * 0.06)], fill=c)


# ---------------------------------------------------------------------------
# הסצנות
# ---------------------------------------------------------------------------

def scene_stadium() -> np.ndarray:
    """אצטדיון בלילה — זרקורים, קהל, ערפל אור ודשא."""
    img = vgrad([(0.0, (8, 14, 22)), (0.34, (14, 24, 34)), (0.46, (20, 32, 42))])
    # גג היציע
    img = silhouette(img, [(0, 0), (W, 0), (W, int(H * 0.13)), (0, int(H * 0.17))], (5, 9, 14))
    # יציעים
    img = silhouette(img, [(0, int(H * 0.17)), (W, int(H * 0.13)),
                           (W, int(H * 0.44)), (0, int(H * 0.44))], (16, 25, 33))
    img = crowd(img, 0.16, 0.43, seed=31, tint=(120, 132, 146), density=1.25)
    # מעקה
    img = silhouette(img, [(0, int(H * 0.43)), (W, int(H * 0.42)),
                           (W, int(H * 0.455)), (0, int(H * 0.465))], (9, 14, 19))
    img = turf(img, 0.455, stripe_count=11, base=(22, 74, 42), light=(44, 116, 62), seed=13)

    # קווי המגרש בפרספקטיבה
    def lines(d):
        y0, y1 = int(H * 0.46), H
        d.line([(int(W * 0.06), y1), (int(W * 0.30), y0)], fill=(226, 240, 226, 130), width=3)
        d.line([(int(W * 0.94), y1), (int(W * 0.70), y0)], fill=(226, 240, 226, 130), width=3)
        d.line([(int(W * 0.30), y0), (int(W * 0.70), y0)], fill=(226, 240, 226, 110), width=2)
        d.ellipse([int(W * 0.34), int(H * 0.62), int(W * 0.66), int(H * 0.82)],
                  outline=(226, 240, 226, 100), width=3)
        d.line([(int(W * 0.42), y1), (int(W * 0.47), y0)], fill=(226, 240, 226, 60), width=2)
    col, a = draw_layer(lines)
    img = over(img, col, a, 0.6)

    # זרקורים: מגדל, מנורות, קרן וזוהר
    for cx in (int(W * 0.17), int(W * 0.83)):
        col, a = draw_layer(lambda d, cx=cx: (
            d.rectangle([cx - 46, 16, cx + 46, 40], fill=(24, 32, 40, 255)),
            d.rectangle([cx - 4, 40, cx + 4, 74], fill=(24, 32, 40, 255)),
            [d.ellipse([cx - 38 + i * 25, 20, cx - 24 + i * 25, 34],
                       fill=(255, 244, 214, 255)) for i in range(4)]))
        img = over(img, col, a)
        img = add_light(img, radial(cx, 27, 190, 2.6), (255, 236, 190), 0.55)
        img = add_light(img, radial(cx, 27, 70, 1.6), (255, 250, 235), 0.85)
        # קרן אור אל המגרש
        beam_col, beam_a = draw_layer(lambda d, cx=cx: d.polygon(
            [(cx - 30, 34), (cx + 30, 34),
             (cx + (240 if cx < W / 2 else -60), H), (cx + (-60 if cx < W / 2 else 60) - 120, H)],
            fill=(255, 238, 196, 34)))
        img = over(img, beam_col, beam_a, 26)

    # ערפל אור מעל הדשא
    haze = radial(W / 2, H * 0.5, W * 0.75, 1.4) * 0.30
    img = add_light(img, haze, (150, 190, 160), 0.5)
    img = grade(img, (10, 20, 34), (255, 240, 205), 0.16)
    return grain(vignette(saturate(contrast(expose(img, 0.24), 1.10), 1.44), 0.50))


def scene_pitch_day() -> np.ndarray:
    """מגרש אימונים באור יום."""
    img = vgrad([(0.0, (150, 178, 200)), (0.22, (186, 205, 216)), (0.36, (206, 214, 208))])
    # קו עצים רחוק
    rng = np.random.default_rng(5)
    def trees(d):
        for i in range(90):
            x = rng.integers(-20, W + 20)
            h_ = rng.normal(34, 12)
            w_ = rng.normal(26, 8)
            y = int(H * 0.36)
            d.ellipse([x - w_, y - h_, x + w_, y + 8], fill=(48, 70, 52, 255))
    col, a = draw_layer(trees)
    img = over(img, col, a, 1.6)
    img = silhouette(img, [(0, int(H * 0.355)), (W, int(H * 0.355)),
                           (W, int(H * 0.40)), (0, int(H * 0.40))], (54, 78, 56), 1.0)
    img = turf(img, 0.385, stripe_count=8, base=(40, 106, 56), light=(66, 140, 74), seed=17)

    # שער
    def goal(d):
        gx, gy, gw, gh = int(W * 0.60), int(H * 0.40), int(W * 0.30), int(H * 0.20)
        d.rectangle([gx, gy, gx + gw, gy + gh], outline=(238, 244, 238, 235), width=5)
        for i in range(11):
            x = gx + i * gw / 10
            d.line([(x, gy), (x, gy + gh)], fill=(226, 236, 226, 105), width=1)
        for i in range(6):
            y = gy + i * gh / 5
            d.line([(gx, y), (gx + gw, y)], fill=(226, 236, 226, 105), width=1)
    col, a = draw_layer(goal)
    img = over(img, col, a)

    # קונוסים וכדורים
    def props(d):
        for i in range(6):
            x = int(W * 0.06) + i * int(W * 0.075)
            y = int(H * 0.72) + i * 14
            s = 12 + i * 2.2
            d.polygon([(x - s * 0.55, y), (x + s * 0.55, y), (x, y - s)],
                      fill=(244, 150, 40, 255))
            d.ellipse([x - s * 0.7, y - 3, x + s * 0.7, y + 4], fill=(226, 132, 28, 255))
        for i, (bx, by, br) in enumerate([(W * 0.36, H * 0.80, 15), (W * 0.52, H * 0.68, 11)]):
            d.ellipse([bx - br, by - br, bx + br, by + br], fill=(246, 248, 244, 255))
            d.polygon([(bx, by - br * 0.75), (bx + br * 0.7, by - br * 0.15),
                       (bx + br * 0.42, by + br * 0.65), (bx - br * 0.42, by + br * 0.65),
                       (bx - br * 0.7, by - br * 0.15)], fill=(40, 48, 44, 255))
    col, a = draw_layer(props)
    img = over(img, col, a)

    col, a = draw_layer(lambda d: (
        person(d, W * 0.30, H * 0.86, 2.3, (24, 34, 30), 255, "run"),
        person(d, W * 0.78, H * 0.60, 1.5, (30, 42, 36), 235, "stand")))
    img = over(img, col, a, 0.35)
    img = add_light(img, radial(W * 0.22, -40, 520, 2.0), (255, 246, 214), 0.45)
    img = grade(img, (30, 46, 60), (255, 248, 220), 0.14)
    return grain(vignette(saturate(contrast(img, 1.08), 1.34), 0.42), 0.016)


def scene_dressing() -> np.ndarray:
    """חדר הלבשה — תאים, ספסל, חולצה תלויה, אור נקודתי."""
    img = vgrad([(0.0, (26, 30, 34)), (0.55, (34, 40, 44)), (1.0, (18, 21, 24))])
    def lockers(d):
        for i in range(7):
            x = int(i * W / 7)
            w_ = int(W / 7) - 6
            d.rectangle([x + 3, int(H * 0.06), x + 3 + w_, int(H * 0.70)],
                        fill=(46, 56, 60, 255), outline=(22, 27, 30, 255), width=3)
            d.rectangle([x + 3, int(H * 0.06), x + 3 + w_, int(H * 0.14)], fill=(38, 47, 51, 255))
            d.ellipse([x + 3 + w_ * 0.5 - 4, int(H * 0.30), x + 3 + w_ * 0.5 + 4, int(H * 0.30) + 8],
                      fill=(150, 158, 160, 255))
    col, a = draw_layer(lockers)
    img = over(img, col, a)

    # חולצה תלויה במרכז
    def shirt(d):
        cx, top = int(W * 0.5), int(H * 0.20)
        body = [(cx - 52, top + 18), (cx - 26, top), (cx + 26, top), (cx + 52, top + 18),
                (cx + 62, top + 52), (cx + 40, top + 62), (cx + 40, top + 168),
                (cx - 40, top + 168), (cx - 40, top + 62), (cx - 62, top + 52)]
        d.polygon(body, fill=(232, 176, 38, 255))
        d.polygon([(cx - 26, top), (cx, top + 20), (cx + 26, top)], fill=(196, 142, 20, 255))
        d.text((cx, top + 96), "9", fill=(58, 42, 10, 255), font=font(76), anchor="mm")
    col, a = draw_layer(shirt)
    img = over(img, col, a)
    # מספר גדול על החולצה
    # ספסל וקיר תחתון
    img = silhouette(img, [(0, int(H * 0.70)), (W, int(H * 0.70)),
                           (W, int(H * 0.78)), (0, int(H * 0.78))], (58, 44, 30))
    img = silhouette(img, [(0, int(H * 0.78)), (W, int(H * 0.78)), (W, H), (0, H)], (24, 27, 30))
    col, a = draw_layer(lambda d: (
        person(d, W * 0.16, H * 0.70, 2.1, (18, 22, 26), 255, "sit"),
        person(d, W * 0.86, H * 0.70, 2.0, (20, 25, 28), 240, "sit")))
    img = over(img, col, a, 0.3)

    img = add_light(img, radial(W * 0.5, H * 0.16, 300, 2.2), (255, 232, 180), 0.55)
    img = add_light(img, radial(W * 0.12, H * 0.05, 200, 2.6), (200, 220, 255), 0.22)
    img = grade(img, (18, 22, 34), (255, 236, 196), 0.2)
    return grain(vignette(saturate(contrast(img, 1.10), 1.40), 0.62))


def scene_tunnel() -> np.ndarray:
    """מנהרת השחקנים — חושך, ואור המגרש בקצה."""
    img = canvas((10, 12, 14))
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    # פרספקטיבה של קירות
    cx, cy = W * 0.5, H * 0.46
    dx = np.abs(xs - cx) / (W * 0.5)
    dy = np.abs(ys - cy) / (H * 0.5)
    wall = np.clip(np.maximum(dx, dy), 0, 1)
    tone = 0.10 + 0.34 * wall
    img = np.dstack([tone * 0.72, tone * 0.80, tone * 0.76]).astype(np.float32)

    # פתח המגרש
    ox0, ox1 = int(W * 0.34), int(W * 0.66)
    oy0, oy1 = int(H * 0.18), int(H * 0.80)
    opening = np.zeros((H, W), dtype=np.float32)
    opening[oy0:oy1, ox0:ox1] = 1.0
    pitch = turf(canvas((0, 0, 0)), 0.0, stripe_count=5, base=(52, 130, 68), light=(78, 168, 88), seed=23)
    pitch = add_light(pitch, np.ones((H, W), dtype=np.float32) * 0.35, (255, 250, 230), 0.6)
    img = np.where(opening[:, :, None] > 0, pitch, img)

    # מסגרת הפתח
    col, a = draw_layer(lambda d: d.rectangle([ox0, oy0, ox1, oy1],
                                              outline=(16, 18, 20, 255), width=8))
    img = over(img, col, a)
    # שחקנים בצללית מול האור
    col, a = draw_layer(lambda d: (
        person(d, W * 0.44, H * 0.78, 3.0, (8, 12, 10), 255, "stand"),
        person(d, W * 0.57, H * 0.79, 3.2, (8, 12, 10), 255, "stand")))
    img = over(img, col, a, 0.5)
    img = add_light(img, radial(W * 0.5, H * 0.48, W * 0.42, 2.2), (240, 255, 235), 0.5)
    img = grade(img, (16, 20, 30), (240, 255, 230), 0.16)
    return grain(vignette(saturate(contrast(expose(img, 0.34), 1.10), 1.40), 0.58))


def scene_physio() -> np.ndarray:
    """חדר טיפולים — אור קר, מיטה, רגל חבושה."""
    img = vgrad([(0.0, (206, 214, 218)), (0.6, (180, 190, 196)), (1.0, (150, 160, 166))])
    img = silhouette(img, [(0, int(H * 0.62)), (W, int(H * 0.62)), (W, H), (0, H)], (120, 132, 138))
    def room(d):
        d.rectangle([int(W * 0.05), int(H * 0.10), int(W * 0.30), int(H * 0.42)],
                    fill=(228, 236, 240, 255), outline=(160, 172, 178, 255), width=4)
        for i in range(3):
            x = int(W * 0.05) + (i + 1) * int(W * 0.0625)
            d.line([(x, int(H * 0.10)), (x, int(H * 0.42))], fill=(180, 192, 198, 255), width=3)
        d.rectangle([int(W * 0.36), int(H * 0.60), int(W * 0.86), int(H * 0.68)],
                    fill=(60, 74, 86, 255))
        d.rectangle([int(W * 0.39), int(H * 0.68), int(W * 0.42), int(H * 0.84)],
                    fill=(90, 100, 110, 255))
        d.rectangle([int(W * 0.80), int(H * 0.68), int(W * 0.83), int(H * 0.84)],
                    fill=(90, 100, 110, 255))
    col, a = draw_layer(room)
    img = over(img, col, a)
    # מטופל ורגל חבושה
    def patient(d):
        y = int(H * 0.60)
        d.ellipse([int(W * 0.40), y - 30, int(W * 0.46), y - 4], fill=(58, 66, 74, 255))
        d.polygon([(int(W * 0.44), y - 22), (int(W * 0.66), y - 26),
                   (int(W * 0.67), y - 2), (int(W * 0.44), y - 2)], fill=(46, 56, 64, 255))
        for i in range(6):
            x0 = int(W * 0.66) + i * 16
            d.polygon([(x0, y - 30 + i * 2), (x0 + 18, y - 34 + i * 2),
                       (x0 + 18, y - 8 + i * 2), (x0, y - 4 + i * 2)],
                      fill=(244, 246, 240, 255) if i % 2 == 0 else (226, 230, 220, 255))
    col, a = draw_layer(patient)
    img = over(img, col, a)
    col, a = draw_layer(lambda d: person(d, W * 0.90, H * 0.86, 2.4, (52, 62, 72), 255, "stand"))
    img = over(img, col, a, 0.3)
    img = add_light(img, radial(W * 0.55, H * 0.05, 380, 2.0), (215, 235, 255), 0.5)
    img = grade(img, (40, 60, 84), (250, 252, 255), 0.2)
    return grain(vignette(saturate(contrast(img, 1.06), 1.28), 0.4), 0.015)


def scene_press() -> np.ndarray:
    """אולם עיתונאים — קיר לוגואים, מיקרופונים, מבזקי מצלמה."""
    img = vgrad([(0.0, (30, 44, 40)), (0.62, (24, 36, 33)), (1.0, (14, 20, 18))])
    def backdrop(d):
        for r in range(4):
            for c in range(7):
                x = 20 + c * int(W / 7)
                y = 16 + r * int(H * 0.16)
                d.rounded_rectangle([x, y, x + int(W / 9), y + 22], 5, fill=(40, 58, 52, 255))
    col, a = draw_layer(backdrop)
    img = over(img, col, a)
    col, a = draw_layer(lambda d: person(d, W * 0.5, H * 0.80, 3.4, (18, 26, 24), 255, "sit"))
    img = over(img, col, a, 0.4)
    def desk(d):
        d.rectangle([int(W * 0.18), int(H * 0.68), int(W * 0.82), int(H * 0.88)],
                    fill=(20, 28, 26, 255))
        d.rectangle([int(W * 0.18), int(H * 0.68), int(W * 0.82), int(H * 0.71)],
                    fill=(232, 176, 38, 255))
        for i in range(5):
            x = int(W * 0.34) + i * int(W * 0.08)
            d.line([(x, int(H * 0.68)), (x + 6, int(H * 0.50))], fill=(70, 80, 78, 255), width=5)
            d.ellipse([x + 1, int(H * 0.44), x + 17, int(H * 0.53)],
                      fill=(232, 176, 38, 255) if i == 2 else (110, 120, 118, 255))
    col, a = draw_layer(desk)
    img = over(img, col, a)
    rng = np.random.default_rng(9)
    for _ in range(7):
        fx = rng.uniform(0.05, 0.95) * W
        fy = rng.uniform(0.88, 1.0) * H
        img = add_light(img, radial(fx, fy, rng.uniform(60, 150), 2.4), (255, 250, 235),
                        rng.uniform(0.25, 0.7))
    img = grade(img, (16, 30, 26), (255, 246, 210), 0.18)
    return grain(vignette(saturate(contrast(expose(img, 0.42), 1.08), 1.42), 0.50))


def scene_board() -> np.ndarray:
    """חדר ישיבות — אור מהחלון, שולחן ארוך."""
    img = vgrad([(0.0, (52, 56, 60)), (0.5, (44, 48, 52)), (1.0, (26, 29, 32))])
    def window(d):
        x0, y0, x1, y1 = int(W * 0.52), int(H * 0.06), int(W * 0.97), int(H * 0.56)
        d.rectangle([x0, y0, x1, y1], fill=(176, 196, 214, 255))
        for i in range(11):
            y = y0 + i * (y1 - y0) / 10
            d.rectangle([x0, y, x1, y + 8], fill=(120, 140, 160, 255))
        d.rectangle([x0 - 6, y0 - 6, x1 + 6, y1 + 6], outline=(30, 34, 38, 255), width=7)
    col, a = draw_layer(window)
    img = over(img, col, a)
    col, a = draw_layer(lambda d: (
        person(d, W * 0.18, H * 0.74, 2.6, (26, 30, 34), 255, "sit"),
        person(d, W * 0.36, H * 0.75, 2.6, (24, 28, 32), 255, "sit"),
        person(d, W * 0.62, H * 0.75, 2.5, (22, 26, 30), 255, "sit")))
    img = over(img, col, a, 0.35)
    def table(d):
        d.ellipse([int(W * -0.05), int(H * 0.72), int(W * 1.05), int(H * 1.25)],
                  fill=(64, 48, 34, 255))
        d.ellipse([int(W * -0.02), int(H * 0.74), int(W * 1.02), int(H * 1.2)],
                  fill=(88, 66, 46, 255))
        d.rectangle([int(W * 0.40), int(H * 0.80), int(W * 0.56), int(H * 0.92)],
                    fill=(238, 240, 232, 255))
        for i in range(4):
            d.line([(int(W * 0.42), int(H * 0.83) + i * 8), (int(W * 0.54), int(H * 0.83) + i * 8)],
                   fill=(150, 152, 146, 255), width=2)
    col, a = draw_layer(table)
    img = over(img, col, a)
    img = add_light(img, radial(W * 0.78, H * 0.28, 460, 1.8), (220, 236, 255), 0.55)
    img = grade(img, (28, 32, 46), (255, 244, 220), 0.16)
    return grain(vignette(saturate(contrast(expose(img, 0.34), 1.06), 1.36), 0.48))


def scene_trophy() -> np.ndarray:
    """ארון תארים — חושך, זרקורים, גביע מוזהב."""
    img = vgrad([(0.0, (14, 16, 20)), (0.6, (22, 24, 30)), (1.0, (10, 11, 14))])
    img = add_light(img, radial(W * 0.5, H * 0.16, 420, 2.2), (255, 226, 150), 0.42)
    def plinth(d):
        d.polygon([(int(W * 0.34), int(H * 0.80)), (int(W * 0.66), int(H * 0.80)),
                   (int(W * 0.72), H), (int(W * 0.28), H)], fill=(38, 40, 46, 255))
        d.rectangle([int(W * 0.36), int(H * 0.76), int(W * 0.64), int(H * 0.80)],
                    fill=(54, 56, 62, 255))
    col, a = draw_layer(plinth)
    img = over(img, col, a)
    def cup(d):
        cx = int(W * 0.5)
        top, bottom = int(H * 0.26), int(H * 0.62)
        d.polygon([(cx - 62, top), (cx + 62, top), (cx + 40, bottom), (cx - 40, bottom)],
                  fill=(226, 174, 44, 255))
        d.polygon([(cx - 54, top + 6), (cx + 10, top + 6), (cx - 4, bottom - 6), (cx - 34, bottom - 6)],
                  fill=(246, 208, 96, 255))
        for side in (-1, 1):
            d.arc([cx + side * 46 - 42, top - 4, cx + side * 46 + 42, top + 74],
                  start=280 if side > 0 else 190, end=100 if side > 0 else 10,
                  fill=(226, 174, 44, 255), width=13)
        d.rectangle([cx - 14, bottom, cx + 14, bottom + 26], fill=(206, 156, 36, 255))
        d.rectangle([cx - 46, bottom + 26, cx + 46, int(H * 0.78)], fill=(226, 174, 44, 255))
    col, a = draw_layer(cup)
    img = over(img, col, a)
    img = add_light(img, radial(W * 0.5, H * 0.44, 240, 2.0), (255, 216, 130), 0.5)
    # קונפטי
    rng = np.random.default_rng(15)
    def confetti(d):
        for _ in range(150):
            x, y = rng.uniform(0, W), rng.uniform(0, H * 0.9)
            w_, h_ = rng.uniform(4, 11), rng.uniform(7, 16)
            c = [(232, 176, 38), (240, 240, 235), (196, 142, 20), (150, 160, 158)][rng.integers(0, 4)]
            d.rectangle([x, y, x + w_, y + h_], fill=tuple(c) + (int(rng.uniform(90, 230)),))
    col, a = draw_layer(confetti)
    img = over(img, col, a, 0.5)
    img = grade(img, (18, 16, 26), (255, 232, 176), 0.22)
    return grain(vignette(saturate(contrast(expose(img, 0.44), 1.10), 1.46), 0.54))


def scene_airport() -> np.ndarray:
    """שדה תעופה בשקיעה."""
    img = vgrad([(0.0, (28, 44, 82)), (0.30, (96, 92, 120)), (0.52, (222, 140, 88)),
                 (0.62, (250, 190, 120)), (0.70, (60, 62, 70)), (1.0, (28, 30, 36))])
    img = add_light(img, radial(W * 0.70, H * 0.60, 330, 2.2), (255, 190, 120), 0.6)
    def plane(d):
        cx, cy = int(W * 0.44), int(H * 0.34)
        d.polygon([(cx - 150, cy + 22), (cx + 110, cy - 16), (cx + 150, cy - 6),
                   (cx + 120, cy + 22), (cx - 120, cy + 40)], fill=(18, 20, 26, 255))
        d.polygon([(cx + 10, cy + 6), (cx - 40, cy - 62), (cx - 14, cy - 66),
                   (cx + 60, cy - 2)], fill=(18, 20, 26, 255))
        d.polygon([(cx - 96, cy + 32), (cx - 130, cy + 6), (cx - 148, cy + 12),
                   (cx - 128, cy + 38)], fill=(18, 20, 26, 255))
        d.polygon([(cx + 24, cy + 10), (cx + 66, cy + 30), (cx + 92, cy + 26),
                   (cx + 52, cy + 6)], fill=(24, 26, 32, 255))
    col, a = draw_layer(plane)
    img = over(img, col, a, 0.4)
    img = silhouette(img, [(0, int(H * 0.66)), (W, int(H * 0.64)), (W, H), (0, H)], (24, 26, 32))
    def ground(d):
        d.rectangle([int(W * 0.02), int(H * 0.70), int(W * 0.16), int(H * 0.92)],
                    fill=(44, 48, 56, 255))
        d.rectangle([int(W * 0.02), int(H * 0.78), int(W * 0.16), int(H * 0.80)],
                    fill=(30, 32, 38, 255))
        d.rectangle([int(W * 0.06), int(H * 0.66), int(W * 0.11), int(H * 0.70)],
                    fill=(60, 64, 72, 255))
        d.rectangle([int(W * 0.62), int(H * 0.70), int(W * 0.96), int(H * 0.90)],
                    fill=(16, 18, 22, 255))
        for i in range(5):
            d.rectangle([int(W * 0.65), int(H * 0.73) + i * 16, int(W * 0.93) - i * 18,
                         int(H * 0.755) + i * 16],
                        fill=(232, 176, 38, 255) if i == 0 else (120, 128, 134, 255))
        for i in range(9):
            d.rectangle([i * int(W / 9) + 20, int(H * 0.96), i * int(W / 9) + 70, int(H * 0.975)],
                        fill=(210, 214, 208, 190))
    col, a = draw_layer(ground)
    img = over(img, col, a)
    img = grade(img, (30, 34, 62), (255, 206, 150), 0.2)
    return grain(vignette(saturate(contrast(expose(img, 0.20), 1.08), 1.44), 0.46))


def scene_studio() -> np.ndarray:
    """אולפן שידור — תאורה צבעונית, שולחן, מסך טקטי."""
    img = vgrad([(0.0, (18, 22, 34)), (0.55, (24, 30, 44)), (1.0, (12, 14, 22))])
    img = add_light(img, radial(W * 0.16, H * 0.10, 320, 2.0), (90, 140, 255), 0.42)
    img = add_light(img, radial(W * 0.88, H * 0.12, 300, 2.0), (255, 120, 90), 0.34)
    def screen(d):
        x0, y0, x1, y1 = int(W * 0.06), int(H * 0.12), int(W * 0.44), int(H * 0.60)
        d.rounded_rectangle([x0 - 6, y0 - 6, x1 + 6, y1 + 6], 8, fill=(10, 12, 16, 255))
        d.rectangle([x0, y0, x1, y1], fill=(28, 86, 48, 255))
        for i in range(6):
            d.rectangle([x0, y0 + i * (y1 - y0) / 6, x1, y0 + (i + 0.5) * (y1 - y0) / 6],
                        fill=(36, 100, 56, 255))
        d.rectangle([x0, y0, x1, y1], outline=(220, 235, 220, 150), width=3)
        d.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], fill=(220, 235, 220, 150), width=3)
        d.ellipse([(x0 + x1) / 2 - 34, (y0 + y1) / 2 - 34, (x0 + x1) / 2 + 34, (y0 + y1) / 2 + 34],
                  outline=(220, 235, 220, 150), width=3)
        for (px, py) in [(0.3, 0.35), (0.45, 0.6), (0.62, 0.3), (0.7, 0.7), (0.55, 0.45)]:
            cx = x0 + (x1 - x0) * px
            cy = y0 + (y1 - y0) * py
            d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(232, 176, 38, 255))
    col, a = draw_layer(screen)
    img = over(img, col, a)
    col, a = draw_layer(lambda d: (
        person(d, W * 0.66, H * 0.78, 3.2, (20, 24, 34), 255, "sit"),
        person(d, W * 0.84, H * 0.78, 3.0, (18, 22, 32), 255, "sit")))
    img = over(img, col, a, 0.35)
    def desk(d):
        d.rounded_rectangle([int(W * 0.50), int(H * 0.66), int(W * 0.98), int(H * 0.92)], 10,
                            fill=(22, 28, 40, 255))
        d.rectangle([int(W * 0.50), int(H * 0.66), int(W * 0.98), int(H * 0.695)],
                    fill=(232, 176, 38, 255))
    col, a = draw_layer(desk)
    img = over(img, col, a)
    img = grade(img, (24, 30, 60), (255, 240, 220), 0.2)
    return grain(vignette(saturate(contrast(expose(img, 0.46), 1.08), 1.44), 0.50))


def scene_home() -> np.ndarray:
    """סלון בערב — אור מנורה חמים, ספה, חלון לילה."""
    img = vgrad([(0.0, (58, 46, 40)), (0.55, (46, 37, 33)), (1.0, (26, 21, 19))])
    def room(d):
        d.rectangle([int(W * 0.05), int(H * 0.10), int(W * 0.34), int(H * 0.50)],
                    fill=(16, 22, 34, 255), outline=(72, 58, 48, 255), width=8)
        d.line([(int(W * 0.195), int(H * 0.10)), (int(W * 0.195), int(H * 0.50))],
               fill=(72, 58, 48, 255), width=6)
        d.ellipse([int(W * 0.24), int(H * 0.15), int(W * 0.30), int(H * 0.24)],
                  fill=(226, 226, 200, 235))
        d.rounded_rectangle([int(W * 0.42), int(H * 0.60), int(W * 0.86), int(H * 0.86)], 14,
                            fill=(74, 58, 52, 255))
        d.rounded_rectangle([int(W * 0.42), int(H * 0.52), int(W * 0.86), int(H * 0.64)], 12,
                            fill=(88, 70, 62, 255))
        d.polygon([(int(W * 0.90), int(H * 0.30)), (int(W * 0.98), int(H * 0.30)),
                   (int(W * 0.955), int(H * 0.46)), (int(W * 0.925), int(H * 0.46))],
                  fill=(238, 196, 120, 255))
        d.rectangle([int(W * 0.936), int(H * 0.46), int(W * 0.944), int(H * 0.86)],
                    fill=(60, 48, 42, 255))
    col, a = draw_layer(room)
    img = over(img, col, a)
    col, a = draw_layer(lambda d: person(d, W * 0.62, H * 0.72, 2.6, (36, 28, 26), 255, "sit"))
    img = over(img, col, a, 0.3)
    img = add_light(img, radial(W * 0.94, H * 0.38, 300, 1.9), (255, 196, 120), 0.62)
    img = add_light(img, radial(W * 0.20, H * 0.30, 190, 2.4), (150, 190, 255), 0.16)
    img = grade(img, (32, 24, 30), (255, 214, 160), 0.24)
    return grain(vignette(saturate(contrast(expose(img, 0.60), 1.06), 1.42), 0.48))


def scene_street() -> np.ndarray:
    """מגרש שכונתי בין הבניינים, בין הערביים."""
    img = vgrad([(0.0, (52, 68, 104)), (0.24, (128, 122, 138)), (0.36, (206, 146, 106)),
                 (0.46, (86, 88, 92)), (1.0, (44, 48, 50))])
    rng = np.random.default_rng(3)
    def blocks(d):
        x = -30
        while x < W + 30:
            bw = rng.integers(60, 130)
            bh = rng.integers(70, 190)
            top = int(H * 0.42) - bh
            d.rectangle([x, top, x + bw, int(H * 0.44)], fill=(38, 42, 52, 255))
            for r in range(int(bh / 26)):
                for c in range(int(bw / 24)):
                    if rng.random() < 0.42:
                        wx = x + 8 + c * 24
                        wy = top + 10 + r * 26
                        d.rectangle([wx, wy, wx + 11, wy + 14],
                                    fill=(240, 206, 130, int(rng.uniform(120, 235))))
            x += bw + rng.integers(2, 14)
    col, a = draw_layer(blocks)
    img = over(img, col, a, 0.4)
    img = turf(img, 0.44, stripe_count=6, base=(46, 92, 58), light=(64, 118, 70), seed=29)
    # גדר רשת
    def fence(d):
        y0, y1 = int(H * 0.06), int(H * 0.58)
        step = 13
        for i in range(-y1, W + y1, step):
            d.line([(i, y0), (i + (y1 - y0), y1)], fill=(168, 176, 178, 46), width=1)
            d.line([(i + (y1 - y0), y0), (i, y1)], fill=(168, 176, 178, 46), width=1)
        for x in range(0, W + 1, 150):
            d.rectangle([x - 3, y0 - 10, x + 3, y1], fill=(84, 90, 92, 190))
        d.rectangle([0, y0 - 10, W, y0 - 4], fill=(84, 90, 92, 210))
    col, a = draw_layer(fence)
    img = over(img, col, a)
    def goal(d):
        gx, gy, gw, gh = int(W * 0.06), int(H * 0.42), int(W * 0.26), int(H * 0.22)
        d.rectangle([gx, gy, gx + gw, gy + gh], outline=(232, 238, 232, 230), width=6)
        for i in range(9):
            d.line([(gx + i * gw / 8, gy), (gx + i * gw / 8, gy + gh)],
                   fill=(226, 232, 226, 110), width=1)
    col, a = draw_layer(goal)
    img = over(img, col, a)
    col, a = draw_layer(lambda d: (
        person(d, W * 0.62, H * 0.90, 2.6, (24, 30, 30), 255, "run"),
        person(d, W * 0.34, H * 0.70, 1.7, (30, 36, 36), 235, "stand")))
    img = over(img, col, a, 0.32)
    col, a = draw_layer(lambda d: (
        d.ellipse([int(W * 0.70), int(H * 0.86), int(W * 0.70) + 26, int(H * 0.86) + 26],
                  fill=(244, 246, 240, 255)),
        d.polygon([(int(W * 0.70) + 13, int(H * 0.86) + 4),
                   (int(W * 0.70) + 23, int(H * 0.86) + 12),
                   (int(W * 0.70) + 19, int(H * 0.86) + 22),
                   (int(W * 0.70) + 7, int(H * 0.86) + 22),
                   (int(W * 0.70) + 3, int(H * 0.86) + 12)], fill=(38, 44, 42, 255))))
    img = over(img, col, a)
    img = add_light(img, radial(W * 0.5, H * 0.34, 460, 1.8), (255, 200, 150), 0.32)
    img = grade(img, (30, 38, 62), (255, 214, 168), 0.2)
    return grain(vignette(saturate(contrast(expose(img, 0.30), 1.08), 1.40), 0.44))


SCENES = {
    "stadium": scene_stadium,
    "training": scene_pitch_day,
    "dressing": scene_dressing,
    "tunnel": scene_tunnel,
    "physio": scene_physio,
    "press": scene_press,
    "boardroom": scene_board,
    "trophy": scene_trophy,
    "airport": scene_airport,
    "studio": scene_studio,
    "home": scene_home,
    "youthpitch": scene_street,
}


def main() -> None:
    out_dir = os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)
    entries = []
    total = 0
    for name, fn in SCENES.items():
        img = to_pil(fn())
        img.save(os.path.join(out_dir, f"{name}.jpg"), "JPEG", quality=82, optimize=True)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=80, optimize=True, progressive=True)
        data = base64.b64encode(buf.getvalue()).decode("ascii")
        total += len(data)
        entries.append(f'  {name}: "data:image/jpeg;base64,{data}"')
        print(f"  {name}: {len(buf.getvalue()) / 1024:.0f}KB")

    js = ("// נוצר אוטומטית על ידי web/art/render.py — אין לערוך ידנית.\n"
          "// תמונות הרקע מוטבעות בקובץ עצמו (data URI).\n"
          "const ART = {\n" + ",\n".join(entries) + ",\n};\n")
    with open(os.path.join(os.path.dirname(HERE), "art.js"), "w", encoding="utf-8") as fh:
        fh.write(js)
    print(f"\nweb/art.js: {total / 1024:.0f}KB base64 סה\"כ")


if __name__ == "__main__":
    main()
